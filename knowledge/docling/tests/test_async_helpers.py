"""Unit tests for async_helpers module."""
import asyncio
import pytest
import time

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.utils.async_helpers import run_sync, async_wrap_generator, fire_and_forget


# --- run_sync tests ---

@pytest.mark.asyncio
async def test_run_sync_basic():
    """run_sync should execute a sync function in a background thread."""
    def add(a, b):
        return a + b
    result = await run_sync(add, 2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_run_sync_with_kwargs():
    """run_sync should handle keyword arguments."""
    def greet(name, greeting="Hello"):
        return f"{greeting}, {name}!"
    result = await run_sync(greet, "Zoo", greeting="Welcome")
    assert result == "Welcome, Zoo!"


@pytest.mark.asyncio
async def test_run_sync_exception():
    """run_sync should propagate exceptions from the sync function."""
    def fail():
        raise ValueError("test error")
    with pytest.raises(ValueError, match="test error"):
        await run_sync(fail)


@pytest.mark.asyncio
async def test_run_sync_does_not_block_loop():
    """run_sync should not block the event loop."""
    def slow():
        time.sleep(0.1)
        return "done"

    start = time.perf_counter()
    # Run two slow tasks concurrently
    results = await asyncio.gather(run_sync(slow), run_sync(slow))
    elapsed = time.perf_counter() - start

    assert results == ["done", "done"]
    # Should complete in ~0.1s (parallel), not ~0.2s (sequential)
    assert elapsed < 0.18


# --- async_wrap_generator tests ---

@pytest.mark.asyncio
async def test_async_wrap_generator_basic():
    """async_wrap_generator should yield items from a sync generator."""
    def gen():
        for i in range(5):
            yield i

    items = []
    async for item in async_wrap_generator(gen):
        items.append(item)
    assert items == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_async_wrap_generator_with_args():
    """async_wrap_generator should pass args to the sync generator."""
    def gen(start, count):
        for i in range(start, start + count):
            yield i

    items = []
    async for item in async_wrap_generator(gen, 10, 3):
        items.append(item)
    assert items == [10, 11, 12]


@pytest.mark.asyncio
async def test_async_wrap_generator_empty():
    """async_wrap_generator should handle empty generators."""
    def gen():
        return
        yield  # Make it a generator

    items = []
    async for item in async_wrap_generator(gen):
        items.append(item)
    assert items == []


@pytest.mark.asyncio
async def test_async_wrap_generator_exception():
    """async_wrap_generator should propagate exceptions from the generator."""
    def gen():
        yield 1
        raise RuntimeError("generator error")

    items = []
    with pytest.raises(RuntimeError, match="generator error"):
        async for item in async_wrap_generator(gen):
            items.append(item)
    assert items == [1]  # First item should have been yielded


# --- fire_and_forget tests ---

@pytest.mark.asyncio
async def test_fire_and_forget_executes():
    """fire_and_forget should execute the function."""
    results = []

    def record(value):
        results.append(value)

    fire_and_forget(record, "test")
    # Give the background task time to complete
    await asyncio.sleep(0.2)
    assert results == ["test"]


@pytest.mark.asyncio
async def test_fire_and_forget_with_kwargs():
    """fire_and_forget should handle keyword arguments."""
    results = []

    def record(key, value="default"):
        results.append(f"{key}={value}")

    fire_and_forget(record, "name", value="zoo")
    await asyncio.sleep(0.2)
    assert results == ["name=zoo"]


@pytest.mark.asyncio
async def test_fire_and_forget_error_does_not_propagate():
    """fire_and_forget should log but not raise on error."""
    def fail():
        raise ValueError("should not propagate")

    # This should not raise
    fire_and_forget(fail)
    await asyncio.sleep(0.2)
    # If we get here without exception, the test passes
