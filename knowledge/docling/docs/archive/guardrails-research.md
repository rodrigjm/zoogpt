# Guardrails for Child-Safe LLM Applications

## Executive Summary

For Zoocari (a public, child-facing chatbot), implementing a **layered defense approach** is critical. This document outlines recommended guardrails for preventing inappropriate content in both user inputs and LLM outputs.

---

## 1. Input Filtering (Pre-LLM Guardrails)

### 1.1 OpenAI Moderation API (Recommended - Free)
- **Endpoint**: `POST https://api.openai.com/v1/moderations`
- **Categories detected**:
  - `sexual`, `sexual/minors` - Critical for child safety
  - `violence`, `violence/graphic`
  - `hate`, `hate/threatening`
  - `self-harm`, `self-harm/intent`, `self-harm/instructions`
  - `harassment`, `harassment/threatening`
- **Cost**: Free with any OpenAI API key
- **Latency**: ~100-200ms

```python
# Example implementation
from openai import OpenAI

def check_input_safety(text: str) -> tuple[bool, list[str]]:
    """Check if user input is safe. Returns (is_safe, flagged_categories)."""
    client = OpenAI()
    response = client.moderations.create(input=text)
    result = response.results[0]

    if result.flagged:
        flagged = [cat for cat, flagged in result.categories.model_dump().items() if flagged]
        return False, flagged
    return True, []
```

### 1.2 Keyword/Pattern Blocklist
- Maintain a curated blocklist of explicit terms
- Use fuzzy matching to catch l33tspeak variations (e.g., "s3x" → "sex")
- Consider libraries like `better-profanity` or `profanity-filter`

### 1.3 Input Sanitization
- Strip special characters that could be used for prompt injection
- Limit input length (e.g., 500 characters max for a kids' Q&A)
- Remove URLs and email addresses from input

---

## 2. Output Filtering (Post-LLM Guardrails)

### 2.1 Same Moderation API on Output
- Run the same OpenAI Moderation check on LLM responses
- Block and regenerate if flagged
- Log incidents for review

### 2.2 Allowlist Approach (Strongest for Kids)
For Zoocari's domain-specific use case:
- The RAG system already constrains responses to animal facts
- The system prompt explicitly instructs safe content
- Consider adding explicit output validation for:
  - No URLs in responses
  - No personal information requests
  - No off-topic content

### 2.3 Response Regeneration Strategy
```python
MAX_RETRIES = 3

async def safe_generate_response(messages, context):
    for attempt in range(MAX_RETRIES):
        response = rag_service.generate_response(messages, context)
        is_safe, flags = check_output_safety(response)
        if is_safe:
            return response
        logger.warning(f"Unsafe output attempt {attempt+1}: {flags}")

    # Fallback to safe canned response
    return "I'm not sure about that! Let's talk about the amazing animals at the park instead!"
```

---

## 3. PII Detection & Redaction

### 3.1 Why It Matters
- Children may inadvertently share personal info (name, school, address)
- COPPA requires parental consent for collecting data from children under 13
- Even if not stored, PII in logs creates liability

### 3.2 Recommended Solutions

| Solution | Pros | Cons |
|----------|------|------|
| **Microsoft Presidio** (Open Source) | Free, customizable, local | Requires setup |
| **AWS Comprehend PII** | Managed, accurate | $0.0001/unit |
| **Google DLP API** | Comprehensive | Usage-based pricing |
| **spaCy NER + regex** | Free, fast | Less accurate |

### 3.3 Implementation Approach
```python
# Lightweight regex-based PII detection for common patterns
import re

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'address': r'\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr)\b',
}

def detect_pii(text: str) -> list[str]:
    """Return list of PII types found in text."""
    found = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(pii_type)
    return found
```

---

## 4. COPPA Compliance Considerations

### 4.1 Key Requirements
- **No data collection** from children under 13 without verifiable parental consent
- **Privacy policy** clearly stating data practices
- **Data minimization** - only collect what's necessary

### 4.2 Zoocari Recommendations
1. **Don't store conversation history** tied to identifiable users
2. **Session-only** data (current implementation is good)
3. **No account creation** for children
4. **Clear disclaimers** about anonymous usage
5. **No PII in prompts** sent to OpenAI (they may log)

---

## 5. Recommended Implementation for Zoocari

### Phase 1: Essential (Implement Now)
1. **Input moderation** via OpenAI Moderation API before RAG
2. **Output moderation** via same API after LLM response
3. **Basic PII regex** to warn/block obvious personal info
4. **Input length limit** (500 chars)

### Phase 2: Enhanced (Future)
1. **Profanity filter** with fuzzy matching
2. **Prompt injection detection**
3. **Rate limiting** per session
4. **Incident logging** for review

### Phase 3: Advanced (If Scaling)
1. **Custom fine-tuned classifier** for domain-specific issues
2. **Human review queue** for edge cases
3. **A/B testing** different safety thresholds

---

## 6. Quick Implementation Code

```python
# apps/api/app/services/safety.py
"""Content safety guardrails for Zoocari."""

import re
from openai import OpenAI
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Initialize once
_moderation_client: Optional[OpenAI] = None

def get_moderation_client() -> OpenAI:
    global _moderation_client
    if _moderation_client is None:
        _moderation_client = OpenAI()
    return _moderation_client

# PII patterns
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'address': r'\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct)\b',
}

class SafetyCheckResult:
    def __init__(self, is_safe: bool, reason: Optional[str] = None, categories: list[str] = None):
        self.is_safe = is_safe
        self.reason = reason
        self.categories = categories or []

def check_content_safety(text: str) -> SafetyCheckResult:
    """
    Check text for inappropriate content using OpenAI Moderation API.
    Returns SafetyCheckResult with is_safe=False if flagged.
    """
    if not text or not text.strip():
        return SafetyCheckResult(is_safe=True)

    try:
        client = get_moderation_client()
        response = client.moderations.create(input=text)
        result = response.results[0]

        if result.flagged:
            flagged_cats = [
                cat for cat, is_flagged in result.categories.model_dump().items()
                if is_flagged
            ]
            logger.warning(f"Content flagged: {flagged_cats}")
            return SafetyCheckResult(
                is_safe=False,
                reason="Content flagged by moderation",
                categories=flagged_cats
            )

        return SafetyCheckResult(is_safe=True)

    except Exception as e:
        logger.error(f"Moderation API error: {e}")
        # Fail open for availability, but log for monitoring
        return SafetyCheckResult(is_safe=True)

def check_pii(text: str) -> SafetyCheckResult:
    """Check for PII patterns in text."""
    found_pii = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_pii.append(pii_type)

    if found_pii:
        logger.warning(f"PII detected: {found_pii}")
        return SafetyCheckResult(
            is_safe=False,
            reason="Personal information detected",
            categories=found_pii
        )

    return SafetyCheckResult(is_safe=True)

def validate_input(text: str, max_length: int = 500) -> SafetyCheckResult:
    """
    Full input validation pipeline.
    Returns first failure or success if all pass.
    """
    # Length check
    if len(text) > max_length:
        return SafetyCheckResult(
            is_safe=False,
            reason=f"Message too long (max {max_length} characters)"
        )

    # PII check
    pii_result = check_pii(text)
    if not pii_result.is_safe:
        return pii_result

    # Content moderation
    safety_result = check_content_safety(text)
    if not safety_result.is_safe:
        return safety_result

    return SafetyCheckResult(is_safe=True)

# Safe fallback response when content is blocked
SAFE_FALLBACK = (
    "Oops! Let's talk about something else. "
    "What animal at Leesburg Animal Park would you like to learn about?"
)
```

---

## 7. Integration Points

### In Chat Router (`app/routers/chat.py`)
```python
from ..services.safety import validate_input, check_content_safety, SAFE_FALLBACK

@router.post("/chat")
async def chat(body: ChatRequest):
    # Validate input BEFORE sending to LLM
    input_check = validate_input(body.message)
    if not input_check.is_safe:
        return ChatResponse(
            reply=SAFE_FALLBACK,
            sources=[],
            followup_questions=get_fallback_questions(3),
            confidence=0.0,
            # ... other fields
        )

    # Generate response...
    response = rag_service.generate_response(...)

    # Validate output AFTER LLM response
    output_check = check_content_safety(response)
    if not output_check.is_safe:
        return ChatResponse(reply=SAFE_FALLBACK, ...)

    return ChatResponse(reply=response, ...)
```

---

## Summary

| Layer | Tool | Cost | Priority |
|-------|------|------|----------|
| Input Moderation | OpenAI Moderation API | Free | P0 |
| Output Moderation | OpenAI Moderation API | Free | P0 |
| PII Detection | Regex patterns | Free | P1 |
| Input Length Limit | Code | Free | P1 |
| Profanity Filter | better-profanity lib | Free | P2 |
| Prompt Injection | Custom rules | Free | P2 |

**Total cost for essential guardrails: $0** (using existing OpenAI API key)
