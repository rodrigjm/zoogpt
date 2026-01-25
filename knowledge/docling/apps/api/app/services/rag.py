"""
RAG service for Zoocari chatbot.
Implements LanceDB retrieval and LLM response generation (Ollama-first, OpenAI fallback).
"""

import re
import json
import httpx
import lancedb
from pathlib import Path
from openai import OpenAI

from ..config import settings, dynamic_config
from ..utils.timing import timed_print
from .llm import LLMService, is_ollama_available


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


# Note: System prompt is now loaded dynamically from admin_config.json
# via dynamic_config.system_prompt


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
        self._llm_service = None
        self._animal_images = None

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

    @property
    def llm_service(self) -> LLMService:
        """Lazy-load LLM service."""
        if self._llm_service is None:
            self._llm_service = LLMService(openai_api_key=settings.openai_api_key)
        return self._llm_service

    @property
    def animal_images(self) -> dict:
        """Lazy-load animal images config."""
        if self._animal_images is None:
            config_path = Path(settings.lancedb_path).parent / "animal_images.json"
            try:
                with open(config_path, "r") as f:
                    self._animal_images = json.load(f)
                timed_print(f"  [RAG] Loaded animal images config: {len(self._animal_images)} animals")
            except FileNotFoundError:
                timed_print(f"  [RAG] Warning: animal_images.json not found at {config_path}")
                self._animal_images = {}
            except json.JSONDecodeError as e:
                timed_print(f"  [RAG] Warning: Failed to parse animal_images.json: {e}")
                self._animal_images = {}
        return self._animal_images

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

            # Build source object with image URLs if available
            source = {"animal": animal_name, "title": title, "url": url}

            # Add image data if this animal has configured images
            if animal_name in self.animal_images:
                image_data = self.animal_images[animal_name]
                source["thumbnail"] = image_data.get("thumbnail")
                source["image_urls"] = image_data.get("images", [])
                source["alt"] = image_data.get("alt")

            sources.append(source)

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
        Generate response using LLM (Ollama or OpenAI) with Zoocari persona.

        Args:
            messages: Chat history in OpenAI format [{"role": "user", "content": "..."}]
            context: Retrieved context from LanceDB

        Returns:
            Generated response string
        """
        # Build system prompt with context (loaded dynamically)
        system_prompt = dynamic_config.system_prompt.format(context=context)

        # Prepend system message
        messages_with_context = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # Generate response using LLM service (local-first with cloud fallback)
        timed_print(f"  [RAG] LLM generation starting (provider: {settings.llm_provider})")
        response = self.llm_service.generate(
            messages=messages_with_context,
            model=dynamic_config.model_name,
            temperature=dynamic_config.model_temperature,
            max_tokens=dynamic_config.model_max_tokens,
        )
        timed_print(f"  [RAG] LLM generation complete ({len(response)} chars)")

        return response

    def _stream_ollama(self, messages_with_context: list[dict]):
        """
        Stream response from Ollama.

        Args:
            messages_with_context: Messages with system prompt

        Yields:
            Text chunks from Ollama streaming response
        """
        timed_print(f"  [RAG] Ollama streaming API call starting ({settings.ollama_model})")

        with httpx.stream(
            "POST",
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages_with_context,
                "stream": True,
                "options": {
                    "temperature": dynamic_config.model_temperature,
                    "num_predict": dynamic_config.model_max_tokens
                }
            },
            timeout=60.0
        ) as response:
            response.raise_for_status()
            first_chunk = True
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        if content:
                            if first_chunk:
                                timed_print("  [RAG] Ollama first streaming chunk received")
                                first_chunk = False
                            yield content
        timed_print("  [RAG] Ollama streaming complete")

    def _stream_openai(self, messages_with_context: list[dict]):
        """
        Stream response from OpenAI.

        Args:
            messages_with_context: Messages with system prompt

        Yields:
            Text chunks from OpenAI streaming response
        """
        model_name = dynamic_config.model_name
        timed_print(f"  [RAG] OpenAI streaming API call starting ({model_name})")
        stream = self.openai_client.chat.completions.create(
            model=model_name,
            messages=messages_with_context,
            temperature=dynamic_config.model_temperature,
            max_tokens=dynamic_config.model_max_tokens,
            stream=True,
        )

        first_chunk = True
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                if first_chunk:
                    timed_print("  [RAG] OpenAI first streaming chunk received")
                    first_chunk = False
                yield chunk.choices[0].delta.content
        timed_print("  [RAG] OpenAI streaming complete")

    def generate_response_stream(self, messages: list[dict], context: str):
        """
        Generate streaming response using LLM (Ollama-first, OpenAI fallback) with Zoocari persona.

        Args:
            messages: Chat history in OpenAI format [{"role": "user", "content": "..."}]
            context: Retrieved context from LanceDB

        Yields:
            Text chunks from LLM streaming response
        """
        # Build system prompt with context (loaded dynamically)
        system_prompt = dynamic_config.system_prompt.format(context=context)

        # Prepend system message
        messages_with_context = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]

        # Try Ollama first if configured and available
        if settings.llm_provider == "ollama" and is_ollama_available():
            try:
                timed_print(f"  [RAG] Using Ollama for streaming (provider: {settings.llm_provider})")
                yield from self._stream_ollama(messages_with_context)
                return
            except Exception as e:
                timed_print(f"  [RAG] Ollama streaming failed, falling back to OpenAI: {e}")

        # Fallback to OpenAI
        timed_print(f"  [RAG] Using OpenAI for streaming (provider: {settings.llm_provider})")
        yield from self._stream_openai(messages_with_context)

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
