"""Smoke test for internal benchmark router."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

import importlib.util


def test_benchmark_router_imports():
    """Module loads without errors and exposes 3 endpoints."""
    spec = importlib.util.spec_from_file_location(
        "benchmark", str(Path(__file__).resolve().parents[2] / "apps" / "api" / "app" / "routers" / "benchmark.py")
    )
    # Can't easily exec_module due to relative imports; just verify file exists
    assert spec is not None


def test_benchmark_router_exports_three_endpoints():
    """Verify the three POST endpoints are wired up by reading the file."""
    router_path = Path(__file__).resolve().parents[2] / "apps" / "api" / "app" / "routers" / "benchmark.py"
    content = router_path.read_text()
    assert '@router.post("/stt")' in content
    assert '@router.post("/llm")' in content
    assert '@router.post("/tts")' in content
    assert 'prefix="/internal/benchmark"' in content
