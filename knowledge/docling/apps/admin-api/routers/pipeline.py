"""
Pipeline management API endpoints.

Provides model selection per pipeline stage (hot-swap)
and per-stage benchmark execution.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user, User
from config import settings
from models.pipeline import (
    PipelineStageConfig,
    PipelineConfig,
    PipelineStageUpdate,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkStatus,
    AVAILABLE_MODELS,
)
from services.benchmark import (
    BenchmarkResultStore,
    get_benchmark_status,
    run_benchmark,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# Shared result store
_result_store = BenchmarkResultStore(
    results_path=str(Path(settings.admin_config_path).parent / "benchmark_results.json")
)


def _get_config_path() -> Path:
    """Get path to admin config file."""
    path = Path(settings.admin_config_path)
    if not path.is_absolute():
        current = Path(__file__).resolve()
        for parent in current.parents:
            target = parent / settings.admin_config_path
            if target.parent.exists():
                return target
    return path


def _load_config() -> dict:
    path = _get_config_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_config(config: dict):
    path = _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2, default=str)


# =============================================================================
# Model Selection
# =============================================================================

@router.get("", response_model=PipelineConfig)
async def get_pipeline_config(user: User = Depends(get_current_user)):
    """Get current pipeline configuration for all stages."""
    config = _load_config()
    pipeline = config.get("pipeline", {})

    return PipelineConfig(
        stt=PipelineStageConfig(
            provider=pipeline.get("stt", {}).get("provider", "faster-whisper"),
            model=pipeline.get("stt", {}).get("model", "base"),
        ),
        llm=PipelineStageConfig(
            provider=pipeline.get("llm", {}).get("provider", "ollama"),
            model=pipeline.get("llm", {}).get("model", "qwen2.5:3b"),
        ),
        tts=PipelineStageConfig(
            provider=pipeline.get("tts", {}).get("provider", "kokoro"),
            model=pipeline.get("tts", {}).get("model", "af_heart"),
        ),
    )


@router.put("/{stage}", response_model=PipelineStageConfig)
async def update_stage_config(
    stage: str,
    body: PipelineStageUpdate,
    user: User = Depends(get_current_user),
):
    """Update provider/model for a pipeline stage. Takes effect within 5 seconds (hot-swap)."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    # Validate provider exists for this stage
    stage_providers = AVAILABLE_MODELS.get(stage, {})
    if body.provider not in stage_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{body.provider}' for {stage}. "
                   f"Available: {list(stage_providers.keys())}",
        )

    # Validate model exists for this provider (if model specified)
    if body.model:
        valid_models = [m["id"] for m in stage_providers[body.provider]]
        if body.model not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model '{body.model}' for {body.provider}. "
                       f"Available: {valid_models}",
            )

    config = _load_config()
    if "pipeline" not in config:
        config["pipeline"] = {}
    config["pipeline"][stage] = {
        "provider": body.provider,
        "model": body.model,
    }
    _save_config(config)

    return PipelineStageConfig(provider=body.provider, model=body.model)


@router.get("/models")
async def get_available_models(user: User = Depends(get_current_user)):
    """Get all available models grouped by stage and provider."""
    return AVAILABLE_MODELS


# =============================================================================
# Benchmarks
# =============================================================================

@router.post("/{stage}/benchmark", response_model=BenchmarkStatus)
async def start_benchmark(
    stage: str,
    body: BenchmarkRequest,
    user: User = Depends(get_current_user),
):
    """Start a benchmark run for a pipeline stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    if body.concurrency not in (1, 5, 10, 20, 50):
        raise HTTPException(status_code=400, detail="Concurrency must be 1, 5, 10, 20, or 50")

    if body.rounds not in (1, 3, 5):
        raise HTTPException(status_code=400, detail="Rounds must be 1, 3, or 5")

    # Check if already running
    current = get_benchmark_status(stage)
    if current.get("running"):
        raise HTTPException(status_code=409, detail=f"Benchmark already running for {stage}")

    # Get current provider/model for this stage
    config = _load_config()
    pipeline = config.get("pipeline", {})
    stage_config = pipeline.get(stage, {})
    defaults = {"stt": "faster-whisper", "llm": "ollama", "tts": "kokoro"}
    provider = stage_config.get("provider", defaults[stage])
    model = stage_config.get("model")

    main_api_url = settings.zoocari_api_url

    # Launch benchmark in background
    asyncio.create_task(
        run_benchmark(
            stage=stage,
            concurrency=body.concurrency,
            rounds=body.rounds,
            main_api_url=main_api_url,
            store=_result_store,
            provider=provider,
            model=model,
        )
    )

    return BenchmarkStatus(
        stage=stage,
        running=True,
        progress=f"0/{body.concurrency * body.rounds} requests",
        total_requests=body.concurrency * body.rounds,
    )


@router.get("/{stage}/benchmark/status", response_model=BenchmarkStatus)
async def get_stage_benchmark_status(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get status of a running benchmark for a stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    status_data = get_benchmark_status(stage)
    return BenchmarkStatus(**status_data)


@router.get("/{stage}/benchmark/latest", response_model=Optional[BenchmarkResult])
async def get_latest_benchmark(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get the most recent benchmark result for a stage."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    result = _result_store.get_latest(stage)
    if result is None:
        return None
    return BenchmarkResult(**result)


@router.get("/{stage}/benchmark/history")
async def get_benchmark_history(
    stage: str,
    user: User = Depends(get_current_user),
):
    """Get all benchmark results for a stage (most recent first)."""
    if stage not in ("stt", "llm", "tts"):
        raise HTTPException(status_code=400, detail="Stage must be 'stt', 'llm', or 'tts'")

    return _result_store.get_history(stage)
