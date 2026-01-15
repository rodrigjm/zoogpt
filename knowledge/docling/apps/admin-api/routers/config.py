"""
Configuration management API endpoints.
"""

import json
import base64
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from auth import get_current_user, User
from config import settings
from models.config import (
    PromptsConfig,
    ModelConfig,
    TTSConfig,
    VoicePreset,
    TTSPreviewRequest,
    TTSPreviewResponse,
    FullConfig,
)


router = APIRouter(prefix="/config", tags=["configuration"])


def get_config_path() -> Path:
    """Get path to admin config file."""
    path = Path(settings.admin_config_path)
    if not path.is_absolute():
        current = Path(__file__).resolve()
        for parent in current.parents:
            target = parent / settings.admin_config_path
            if target.parent.exists():
                return target
    return path


def load_config() -> dict:
    """Load admin config from JSON file."""
    path = get_config_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return get_default_config()


def save_config(config: dict):
    """Save admin config to JSON file."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2, default=str)


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        "version": "1.0",
        "prompts": {
            "system_prompt": """You are Zoocari the Elephant, the friendly animal expert at Leesburg Animal Park! You LOVE helping kids learn about all the amazing animals they can meet at the park!

YOUR PERSONALITY:
- You're warm, playful, and encouraging - like a fun zoo guide!
- You use simple words that 6-12 year olds understand
- You show genuine excitement about animal facts
- You speak like a fun friend, not a boring textbook

CRITICAL RULES:
1. ONLY answer questions using information from the CONTEXT provided
2. If the context doesn't contain information, say you don't know
3. NEVER make up facts - kids trust you!
4. Keep answers short (1-2 paragraphs, under 100 words)
5. Use age-appropriate language""",
            "fallback_response": "Hmm, I don't know about that yet! Maybe ask one of the zookeepers when you visit Leesburg Animal Park, or check out a book from your library!",
            "followup_questions": [
                "What do lions like to eat?",
                "How fast can a cheetah run?",
                "Why do zebras have stripes?",
            ],
        },
        "model": {
            "name": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 500,
        },
        "tts": {
            "provider": "kokoro",
            "default_voice": "af_heart",
            "speed": 1.0,
            "fallback_provider": "openai",
            "available_voices": {
                "kokoro": [
                    {"id": "af_bella", "name": "Bella", "description": "Friendly female, clear pronunciation"},
                    {"id": "af_heart", "name": "Heart", "description": "Expressive, upbeat female"},
                    {"id": "af_nova", "name": "Nova", "description": "Warm, engaging female"},
                    {"id": "af_sarah", "name": "Sarah", "description": "Calm, gentle female"},
                    {"id": "am_adam", "name": "Adam", "description": "Clear male voice"},
                    {"id": "am_eric", "name": "Eric", "description": "Friendly male"},
                ],
                "openai": [
                    {"id": "nova", "name": "Nova", "description": "Warm female"},
                    {"id": "shimmer", "name": "Shimmer", "description": "Upbeat female"},
                    {"id": "alloy", "name": "Alloy", "description": "Neutral"},
                    {"id": "echo", "name": "Echo", "description": "Male voice"},
                    {"id": "onyx", "name": "Onyx", "description": "Deep male"},
                ],
            },
        },
    }


# =============================================================================
# Prompts
# =============================================================================

@router.get("/prompts", response_model=PromptsConfig)
async def get_prompts(user: User = Depends(get_current_user)):
    """Get current prompt configuration."""
    config = load_config()
    prompts = config.get("prompts", {})
    return PromptsConfig(
        system_prompt=prompts.get("system_prompt", ""),
        fallback_response=prompts.get("fallback_response", ""),
        followup_questions=prompts.get("followup_questions", []),
    )


@router.put("/prompts", response_model=PromptsConfig)
async def update_prompts(
    body: PromptsConfig,
    user: User = Depends(get_current_user),
):
    """Update prompt configuration."""
    config = load_config()
    config["prompts"] = {
        "system_prompt": body.system_prompt,
        "fallback_response": body.fallback_response,
        "followup_questions": body.followup_questions,
    }
    save_config(config)
    return body


# =============================================================================
# Model Settings
# =============================================================================

@router.get("/model", response_model=ModelConfig)
async def get_model_config(user: User = Depends(get_current_user)):
    """Get LLM model configuration."""
    config = load_config()
    model = config.get("model", {})
    return ModelConfig(
        name=model.get("name", "gpt-4o-mini"),
        temperature=model.get("temperature", 0.7),
        max_tokens=model.get("max_tokens", 500),
    )


@router.put("/model", response_model=ModelConfig)
async def update_model_config(
    body: ModelConfig,
    user: User = Depends(get_current_user),
):
    """Update LLM model configuration."""
    # Validate model name
    valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    if body.name not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model. Must be one of: {valid_models}",
        )

    # Validate temperature
    if not 0.0 <= body.temperature <= 2.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0.0 and 2.0",
        )

    # Validate max tokens
    if not 100 <= body.max_tokens <= 4000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max tokens must be between 100 and 4000",
        )

    config = load_config()
    config["model"] = {
        "name": body.name,
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
    }
    save_config(config)
    return body


# =============================================================================
# TTS Settings
# =============================================================================

@router.get("/tts", response_model=TTSConfig)
async def get_tts_config(user: User = Depends(get_current_user)):
    """Get TTS configuration with available voices."""
    config = load_config()
    tts = config.get("tts", {})
    available = tts.get("available_voices", {})

    return TTSConfig(
        provider=tts.get("provider", "kokoro"),
        default_voice=tts.get("default_voice", "af_heart"),
        speed=tts.get("speed", 1.0),
        fallback_provider=tts.get("fallback_provider", "openai"),
        available_voices={
            provider: [VoicePreset(**v) for v in voices]
            for provider, voices in available.items()
        },
    )


@router.put("/tts", response_model=TTSConfig)
async def update_tts_config(
    body: TTSConfig,
    user: User = Depends(get_current_user),
):
    """Update TTS configuration."""
    # Validate provider
    if body.provider not in ["kokoro", "openai"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'kokoro' or 'openai'",
        )

    # Validate speed
    if not 0.5 <= body.speed <= 2.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speed must be between 0.5 and 2.0",
        )

    config = load_config()
    config["tts"] = {
        "provider": body.provider,
        "default_voice": body.default_voice,
        "speed": body.speed,
        "fallback_provider": body.fallback_provider,
        "available_voices": config.get("tts", {}).get("available_voices", {}),
    }
    save_config(config)
    return body


@router.post("/tts/preview")
async def preview_tts(
    body: TTSPreviewRequest,
    user: User = Depends(get_current_user),
):
    """
    Generate a TTS preview with specified settings.

    Returns audio as WAV bytes.
    """
    # TODO: Implement actual TTS preview
    # This would call the TTS service with the specified voice/speed
    # For now, return a placeholder response

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="TTS preview not yet implemented. Coming soon!",
    )


# =============================================================================
# Full Config
# =============================================================================

@router.get("/full", response_model=FullConfig)
async def get_full_config(user: User = Depends(get_current_user)):
    """Get complete configuration."""
    config = load_config()

    prompts = config.get("prompts", {})
    model = config.get("model", {})
    tts = config.get("tts", {})
    available = tts.get("available_voices", {})

    return FullConfig(
        version=config.get("version", "1.0"),
        prompts=PromptsConfig(
            system_prompt=prompts.get("system_prompt", ""),
            fallback_response=prompts.get("fallback_response", ""),
            followup_questions=prompts.get("followup_questions", []),
        ),
        model=ModelConfig(
            name=model.get("name", "gpt-4o-mini"),
            temperature=model.get("temperature", 0.7),
            max_tokens=model.get("max_tokens", 500),
        ),
        tts=TTSConfig(
            provider=tts.get("provider", "kokoro"),
            default_voice=tts.get("default_voice", "af_heart"),
            speed=tts.get("speed", 1.0),
            fallback_provider=tts.get("fallback_provider", "openai"),
            available_voices={
                provider: [VoicePreset(**v) for v in voices]
                for provider, voices in available.items()
            },
        ),
    )
