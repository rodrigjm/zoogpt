"""
Async helper utilities for wrapping sync services at the router layer.
Zero new dependencies — uses only stdlib asyncio + concurrent.futures.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, AsyncGenerator

logger = logging.getLogger(__name__)

# Shared thread pool for all sync→async offloading
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sync-worker")


async def run_sync(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Run a synchronous function in a background thread.
    Frees the event loop to handle other requests while blocking I/O runs.

    Usage:
        result = await run_sync(session_service.get_session, session_id)
    """
    loop = asyncio.get_running_loop()
    if kwargs:
        return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
    return await loop.run_in_executor(_executor, func, *args)


async def async_wrap_generator(sync_gen_func: Callable, *args: Any) -> AsyncGenerator[Any, None]:
    """
    Bridge a synchronous generator to an async generator via thread + queue.
    The sync generator runs in a background thread and pushes items
    through an asyncio.Queue to the async consumer.

    Usage:
        async for chunk in async_wrap_generator(rag_service.generate_response_stream, messages, context):
            yield chunk
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    _sentinel = object()

    def _producer():
        try:
            for item in sync_gen_func(*args):
                loop.call_soon_threadsafe(queue.put_nowait, item)
            loop.call_soon_threadsafe(queue.put_nowait, _sentinel)
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, e)

    loop.run_in_executor(_executor, _producer)

    while True:
        item = await queue.get()
        if item is _sentinel:
            break
        if isinstance(item, Exception):
            raise item
        yield item


def fire_and_forget(func: Callable, *args: Any, **kwargs: Any) -> None:
    """
    Schedule a sync function to run in the background without awaiting.
    Errors are logged but do not propagate. Used for non-critical writes
    like analytics recording and chat history saves.

    Usage:
        fire_and_forget(analytics_service.record_interaction, session_id=..., ...)
    """
    async def _run():
        try:
            await run_sync(func, *args, **kwargs)
        except Exception:
            logger.exception(f"fire_and_forget failed for {func.__name__}")

    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(_run())
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
    except RuntimeError:
        logger.warning(f"No event loop for fire_and_forget({func.__name__})")
