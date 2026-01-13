"""
RAG service for Zoocari chatbot.
Implements LanceDB retrieval and OpenAI response generation.
"""

import re
import lancedb
from openai import OpenAI

from ..config import settings


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
        results = self.table.search(query).limit(num_results).to_list()

        contexts = []
        sources = []
        distances = []

        for row in results:
            # Extract metadata
            metadata = row.get("metadata", {})
            if metadata is None:
                metadata = {}

            animal_name = (
                metadata.get("animal_name", "Unknown")
                if isinstance(metadata, dict)
                else "Unknown"
            )
            title = metadata.get("title", "") if isinstance(metadata, dict) else ""
            url = metadata.get("url", "") if isinstance(metadata, dict) else ""

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
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_context,
            temperature=0.7,
        )

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
        stream = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_context,
            temperature=0.7,
            stream=True,
        )

        # Yield text chunks
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def extract_followup_questions(self, response: str) -> tuple[str, list[str]]:
        """
        Extract follow-up questions from Zoocari's response.

        Args:
            response: Full response from LLM

        Returns:
            Tuple of (main_response, list_of_questions)
        """
        # Pattern to find the follow-up section
        pattern = r'\*\*Want to explore more\?.*?\*\*\s*\n((?:\d+\.\s+.+\n?)+)'
        match = re.search(pattern, response, re.IGNORECASE)

        if match:
            # Extract the questions part
            questions_text = match.group(1)
            # Parse individual questions
            questions = re.findall(r'\d+\.\s+(.+?)(?:\n|$)', questions_text)
            questions = [q.strip().rstrip('?') + '?' for q in questions if q.strip()]

            # Get main response (everything before the follow-up section)
            main_response = response[: match.start()].strip()
            return main_response, questions

        return response, []
