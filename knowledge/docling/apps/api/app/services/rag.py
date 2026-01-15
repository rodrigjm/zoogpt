"""
RAG service for Zoocari chatbot.
Implements LanceDB retrieval and OpenAI response generation.
"""

import re
import lancedb
from openai import OpenAI

from ..config import settings
from ..utils.timing import timed_print


# Fallback follow-up questions for when LLM doesn't provide any
# Rotates through these 30 kid-friendly zoo questions
FALLBACK_FOLLOWUP_QUESTIONS = [
    "What do lions like to eat?",
    "How fast can a cheetah run?",
    "Why do zebras have stripes?",
    "What sounds do elephants make?",
    "How long do giraffes sleep?",
    "What do monkeys eat for breakfast?",
    "Can camels really store water in their humps?",
    "Why do flamingos stand on one leg?",
    "How do penguins stay warm?",
    "What's the biggest animal at the zoo?",
    "Do snakes have bones?",
    "Why do owls come out at night?",
    "How do chameleons change color?",
    "What do baby animals eat?",
    "Can parrots really talk?",
    "How strong is a gorilla?",
    "What do tortoises eat?",
    "Why do peacocks have colorful feathers?",
    "How do animals stay cool in summer?",
    "What's the fastest bird?",
    "Do all bears hibernate?",
    "How do kangaroos carry their babies?",
    "What do lemurs like to do for fun?",
    "Why do wolves howl at the moon?",
    "How do otters sleep in the water?",
    "What's special about a tiger's stripes?",
    "Do hippos really swim?",
    "What do porcupines eat?",
    "How do meerkats warn each other of danger?",
    "What animals can you pet at Leesburg Animal Park?",
]

# Counter for rotating through fallback questions
_fallback_question_index = 0


def get_fallback_questions(count: int = 3) -> list[str]:
    """
    Get the next set of fallback follow-up questions.
    Rotates through the pool to provide variety.

    Args:
        count: Number of questions to return (default 3)

    Returns:
        List of fallback questions
    """
    global _fallback_question_index
    questions = []
    pool_size = len(FALLBACK_FOLLOWUP_QUESTIONS)

    for _ in range(count):
        questions.append(FALLBACK_FOLLOWUP_QUESTIONS[_fallback_question_index])
        _fallback_question_index = (_fallback_question_index + 1) % pool_size

    timed_print(f"  [RAG] Using {count} fallback follow-up questions")
    return questions


# Zoocari system prompt - ported from legacy/zoo_chat.py
ZUCARI_SYSTEM_PROMPT = """You are Zoocari the Elephant, the friendly animal expert at Leesburg Animal Park! You LOVE helping kids learn about all the amazing animals they can meet at the park!

YOUR PERSONALITY:
- You're warm, playful, and encouraging - like a fun zoo guide!
- You use simple words that 6-12 year olds understand
- You show genuine excitement about animal facts
- You speak like a fun friend, not a boring textbook
- You occasionally make gentle elephant sounds like "Ooh!" or trumpet sounds
- You sometimes mention that kids can see these animals at Leesburg Animal Park!

CRITICAL RULES (YOU MUST FOLLOW THESE):
1. ONLY answer questions using information from the CONTEXT provided below
2. If the context doesn't contain information to answer the question, say: "Hmm, I don't know about that yet! Maybe ask one of the zookeepers when you visit Leesburg Animal Park, or check out a book from your library!"
3. NEVER make up facts or guess - kids trust you!
4. Keep answers short (1-2 short paragraphs max) - keep under 100 words
5. Use age-appropriate language - no complex scientific terms without explanation
6. Handle nature's realities gently (predators hunt, but no graphic details or inappropriate content/language)

RESPONSE FORMAT:
1. Start with an enthusiastic greeting related to the question
2. Give your answer based ONLY on the context
3. End with exactly 3 follow-up questions in this format:
4. no emojis in response or follow up questions

**Want to explore more? Here are some fun questions to ask me:**
1. [First follow-up question]
2. [Second follow-up question]
3. [Third follow-up question]

The follow-up questions should:
- Be related to what you just talked about
- Be things kids would find interesting
- Be about interesting animal facts or behaviors

CONTEXT (Use ONLY this information to answer):
{context}

Remember: You're Zoocari the Elephant at Leesburg Animal Park! Be fun, be accurate, and help kids fall in love with learning about animals!"""


class RAGService:
    """
    RAG service for Zoocari.
    Handles LanceDB retrieval and OpenAI response generation.
    """

    def __init__(self):
        """Initialize RAG service with lazy-loaded connections."""
        self._db = None
        self._table = None
        self._openai_client = None

    @property
    def db(self):
        """Lazy-load LanceDB connection."""
        if self._db is None:
            self._db = lancedb.connect(settings.lancedb_path)
        return self._db

    @property
    def table(self):
        """Lazy-load LanceDB table."""
        if self._table is None:
            self._table = self.db.open_table("animals")
        return self._table

    @property
    def openai_client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    def search_context(
        self, query: str, num_results: int = 5
    ) -> tuple[str, list[dict], float]:
        """
        Search LanceDB for relevant context.

        Args:
            query: User's question
            num_results: Number of results to retrieve

        Returns:
            Tuple of (context_string, sources_list, confidence_score)
        """
        # Search the table (using to_list() to avoid pandas dependency)
        timed_print(f"  [RAG] LanceDB query: '{query[:40]}...'")
        results = self.table.search(query).limit(num_results).to_list()
        timed_print(f"  [RAG] LanceDB returned {len(results)} results")

        contexts = []
        sources = []
        distances = []

        for row in results:
            # Extract metadata with safe defaults
            metadata = row.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            animal_name = metadata.get("animal_name", "Unknown")
            title = metadata.get("title", "")
            url = metadata.get("url", "")

            # Build source object
            sources.append({"animal": animal_name, "title": title, "url": url})

            # Track distance for confidence calculation
            if "_distance" in row:
                distances.append(row["_distance"])

            # Build context string
            contexts.append(f"[About: {animal_name}]\n{row['text']}")

        # Calculate confidence score (inverse of average distance)
        avg_distance = sum(distances) / len(distances) if distances else 1.0
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))

        # Join contexts
        context_string = "\n\n---\n\n".join(contexts)

        return context_string, sources, confidence

    def generate_response(self, messages: list[dict], context: str) -> str:
        """
        Generate response using OpenAI with Zoocari persona.

        Args:
            messages: Chat history in OpenAI format [{"role": "user", "content": "..."}]
            context: Retrieved context from LanceDB

        Returns:
            Generated response string
        """
        # Build system prompt with context
        system_prompt = ZUCARI_SYSTEM_PROMPT.format(context=context)

        # Prepend system message
        messages_with_context = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # Generate response (non-streaming)
        timed_print("  [RAG] OpenAI API call starting (gpt-4o-mini)")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_context,
            temperature=0.7,
        )
        timed_print(f"  [RAG] OpenAI API response received ({len(response.choices[0].message.content)} chars)")

        return response.choices[0].message.content

    def generate_response_stream(self, messages: list[dict], context: str):
        """
        Generate streaming response using OpenAI with Zoocari persona.

        Args:
            messages: Chat history in OpenAI format [{"role": "user", "content": "..."}]
            context: Retrieved context from LanceDB

        Yields:
            Text chunks from OpenAI streaming response
        """
        # Build system prompt with context
        system_prompt = ZUCARI_SYSTEM_PROMPT.format(context=context)

        # Prepend system message
        messages_with_context = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # Generate streaming response
        timed_print("  [RAG] OpenAI streaming API call starting (gpt-4o-mini)")
        stream = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_context,
            temperature=0.7,
            stream=True,
        )

        # Yield text chunks
        first_chunk = True
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                if first_chunk:
                    timed_print("  [RAG] OpenAI first streaming chunk received")
                    first_chunk = False
                yield chunk.choices[0].delta.content
        timed_print("  [RAG] OpenAI streaming complete")

    def extract_followup_questions(self, response: str) -> tuple[str, list[str]]:
        """
        Extract follow-up questions from Zoocari's response.

        Args:
            response: Full response from LLM

        Returns:
            Tuple of (main_response, list_of_questions)
        """
        # Try multiple patterns to handle LLM format variations
        # Pattern 1: Bold header with questions on following lines
        # Pattern 2: Just the text without bold markers
        # Pattern 3: Questions might be on same line or following lines
        patterns = [
            # **Want to explore more? ...**\n1. question
            r'\*\*Want to explore more\?[^*]*\*\*\s*\n?((?:\d+\.\s+.+(?:\n|$))+)',
            # Want to explore more? (without bold)
            r'Want to explore more\?[^\n]*\n((?:\d+\.\s+.+(?:\n|$))+)',
            # Any numbered list after "explore more" or "questions to ask"
            r'(?:explore more|questions to ask)[^\n]*\n((?:\d+\.\s+.+(?:\n|$))+)',
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                # Extract the questions part
                questions_text = match.group(1)
                # Parse individual questions
                questions = re.findall(r'\d+\.\s+(.+?)(?:\n|$)', questions_text)
                questions = [q.strip().rstrip('?') + '?' for q in questions if q.strip()]

                if questions:  # Only return if we actually found questions
                    # Get main response (everything before the follow-up section)
                    main_response = response[: match.start()].strip()
                    timed_print(f"  [RAG] Extracted {len(questions)} follow-up questions (pattern {i+1})")
                    return main_response, questions

        # Log when no follow-up questions found for debugging
        if "want to explore" in response.lower() or "questions to ask" in response.lower():
            timed_print(f"  [RAG] Warning: Follow-up section detected but pattern didn't match")
            # Log last 200 chars for debugging
            timed_print(f"  [RAG] Response tail: {response[-200:]!r}")
        else:
            timed_print("  [RAG] No follow-up questions section in response")

        # Return fallback questions when LLM doesn't provide any
        fallback = get_fallback_questions(3)
        return response, fallback
