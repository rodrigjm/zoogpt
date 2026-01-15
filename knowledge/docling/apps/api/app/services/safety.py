"""
Content safety guardrails for Zoocari.
Uses OpenAI Moderation API for input/output filtering.
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass, field

from openai import OpenAI

from ..config import settings
from ..utils.timing import timed_print

logger = logging.getLogger(__name__)

# Lazy-loaded client
_moderation_client: Optional[OpenAI] = None


def get_moderation_client() -> OpenAI:
    """Get or create OpenAI client for moderation."""
    global _moderation_client
    if _moderation_client is None:
        _moderation_client = OpenAI(api_key=settings.openai_api_key)
    return _moderation_client


# PII detection patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "address": r"\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|boulevard|blvd)\b",
}

# Maximum input length for kid Q&A
MAX_INPUT_LENGTH = 500


@dataclass
class SafetyResult:
    """Result of a safety check."""

    is_safe: bool
    reason: Optional[str] = None
    categories: list[str] = field(default_factory=list)


def check_content_moderation(text: str) -> SafetyResult:
    """
    Check text using OpenAI Moderation API.

    Categories detected:
    - sexual, sexual/minors
    - violence, violence/graphic
    - hate, hate/threatening
    - harassment, harassment/threatening
    - self-harm, self-harm/intent, self-harm/instructions
    - illicit, illicit/violent

    Args:
        text: Content to check

    Returns:
        SafetyResult with is_safe=False if flagged
    """
    if not text or not text.strip():
        return SafetyResult(is_safe=True)

    try:
        timed_print("  [SAFETY] Calling OpenAI Moderation API...")
        client = get_moderation_client()
        response = client.moderations.create(input=text)
        result = response.results[0]

        if result.flagged:
            # Extract which categories were flagged
            flagged_cats = [
                cat
                for cat, is_flagged in result.categories.model_dump().items()
                if is_flagged
            ]
            timed_print(f"  [SAFETY] Content FLAGGED: {flagged_cats}")
            logger.warning(f"Content flagged by moderation: {flagged_cats}")

            return SafetyResult(
                is_safe=False,
                reason="Content flagged by safety filter",
                categories=flagged_cats,
            )

        timed_print("  [SAFETY] Content passed moderation")
        return SafetyResult(is_safe=True)

    except Exception as e:
        logger.error(f"Moderation API error: {e}")
        timed_print(f"  [SAFETY] Moderation API error: {e}")
        # Fail open for availability, but log for monitoring
        return SafetyResult(is_safe=True)


def check_pii(text: str) -> SafetyResult:
    """
    Check for PII patterns in text.

    Detects: email, phone, SSN, street addresses

    Args:
        text: Content to check

    Returns:
        SafetyResult with is_safe=False if PII detected
    """
    found_pii = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_pii.append(pii_type)

    if found_pii:
        timed_print(f"  [SAFETY] PII detected: {found_pii}")
        logger.warning(f"PII detected in input: {found_pii}")
        return SafetyResult(
            is_safe=False,
            reason="Personal information detected - please don't share personal details",
            categories=found_pii,
        )

    return SafetyResult(is_safe=True)


def validate_input(text: str) -> SafetyResult:
    """
    Full input validation pipeline.

    Checks:
    1. Length limit
    2. PII detection
    3. Content moderation

    Args:
        text: User input to validate

    Returns:
        SafetyResult - first failure or success if all pass
    """
    timed_print(f"  [SAFETY] Validating input ({len(text)} chars)...")

    # 1. Length check
    if len(text) > MAX_INPUT_LENGTH:
        timed_print(f"  [SAFETY] Input too long: {len(text)} > {MAX_INPUT_LENGTH}")
        return SafetyResult(
            is_safe=False,
            reason=f"Message too long - please keep it under {MAX_INPUT_LENGTH} characters",
        )

    # 2. PII check (fast, local)
    pii_result = check_pii(text)
    if not pii_result.is_safe:
        return pii_result

    # 3. Content moderation (API call)
    moderation_result = check_content_moderation(text)
    if not moderation_result.is_safe:
        return moderation_result

    timed_print("  [SAFETY] Input validation passed")
    return SafetyResult(is_safe=True)


def validate_output(text: str) -> SafetyResult:
    """
    Validate LLM output for safety.

    Args:
        text: LLM response to validate

    Returns:
        SafetyResult
    """
    timed_print("  [SAFETY] Validating output...")
    return check_content_moderation(text)


# Safe fallback response when content is blocked
SAFE_FALLBACK_RESPONSE = (
    "Oops! Let's talk about something else. "
    "What animal at Leesburg Animal Park would you like to learn about?"
)

# Fallback for when user sends inappropriate content
BLOCKED_INPUT_RESPONSE = (
    "Hmm, I'm not sure about that question! "
    "I love talking about animals - ask me about lions, elephants, or any other animal at the park!"
)
