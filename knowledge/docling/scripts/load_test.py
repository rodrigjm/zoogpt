#!/usr/bin/env python3
"""
Zoocari Load Test — End-to-End Latency & OpenAI Cost Estimation

Measures: session creation → chat (RAG+LLM) → TTS → audio received
Concurrency levels: 1, 5, 10, 20

Usage: python3 scripts/load_test.py [--base-url http://localhost:8000] [--rounds 3]
"""

import asyncio
import aiohttp
import argparse
import json
import time
import statistics
import base64
from dataclasses import dataclass, field
from typing import Optional

# ── OpenAI Pricing (per 1M units) ──────────────────────────────────
# https://openai.com/api/pricing/ (as of 2026-04)
PRICING = {
    "embedding_input":  0.13,    # text-embedding-3-large per 1M tokens
    "gpt4o_mini_input": 0.15,    # gpt-4o-mini per 1M input tokens
    "gpt4o_mini_output": 0.60,   # gpt-4o-mini per 1M output tokens
    "whisper_per_min":  0.006,   # whisper per minute of audio
    "tts_per_1m_chars": 15.00,   # tts-1 per 1M characters
}

# Approximate token ratios (1 token ≈ 4 chars English)
CHARS_PER_TOKEN = 4

# ── Test Questions ──────────────────────────────────────────────────
QUESTIONS = [
    "What do elephants eat?",
    "How fast can a cheetah run?",
    "Do penguins live at the zoo?",
    "What sounds does a lion make?",
    "How long do turtles live?",
    "What is the biggest animal at the zoo?",
    "Do monkeys eat bananas?",
    "How do flamingos turn pink?",
    "What animals are nocturnal?",
    "Can parrots really talk?",
    "How much does a hippo weigh?",
    "What do goats eat?",
    "Are zebras black or white?",
    "How tall is a giraffe?",
    "Do snakes have bones?",
    "What animals can you pet at the zoo?",
    "How do chameleons change color?",
    "What is the fastest bird?",
    "Do bears hibernate?",
    "How many animals live at the park?",
]

BASE_URL = "http://localhost:8000"


@dataclass
class StepTiming:
    session_ms: float = 0
    chat_first_token_ms: float = 0
    chat_total_ms: float = 0
    tts_first_chunk_ms: float = 0
    tts_total_ms: float = 0
    e2e_ms: float = 0  # session → last TTS byte
    reply_text: str = ""
    reply_chars: int = 0
    reply_tokens_est: int = 0
    input_tokens_est: int = 0
    tts_audio_bytes: int = 0
    error: Optional[str] = None


@dataclass
class ConcurrencyResult:
    concurrency: int
    timings: list = field(default_factory=list)

    @property
    def successful(self):
        return [t for t in self.timings if t.error is None]

    @property
    def failed(self):
        return [t for t in self.timings if t.error is not None]


def estimate_cost(results: list[StepTiming]) -> dict:
    """Estimate OpenAI API cost for a batch of requests."""
    total_input_tokens = sum(r.input_tokens_est for r in results)
    total_output_tokens = sum(r.reply_tokens_est for r in results)
    total_reply_chars = sum(r.reply_chars for r in results)
    # Embedding: query gets embedded for RAG search
    total_query_tokens = sum(len(r.reply_text[:100]) // CHARS_PER_TOKEN for r in results)

    embedding_cost = (total_query_tokens / 1_000_000) * PRICING["embedding_input"]
    llm_input_cost = (total_input_tokens / 1_000_000) * PRICING["gpt4o_mini_input"]
    llm_output_cost = (total_output_tokens / 1_000_000) * PRICING["gpt4o_mini_output"]
    tts_cost = (total_reply_chars / 1_000_000) * PRICING["tts_per_1m_chars"]

    return {
        "embedding": embedding_cost,
        "llm_input": llm_input_cost,
        "llm_output": llm_output_cost,
        "tts": tts_cost,
        "total": embedding_cost + llm_input_cost + llm_output_cost + tts_cost,
        "total_requests": len(results),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tts_chars": total_reply_chars,
    }


async def run_single_e2e(session: aiohttp.ClientSession, question: str) -> StepTiming:
    """Run one full end-to-end request: session → chat/stream → tts → audio."""
    timing = StepTiming()
    e2e_start = time.perf_counter()

    try:
        # ── Step 1: Create Session ──────────────────────────────────
        t0 = time.perf_counter()
        async with session.post(
            f"{BASE_URL}/api/session",
            json={"client": "loadtest"},
        ) as resp:
            if resp.status != 200:
                timing.error = f"Session creation failed: {resp.status}"
                return timing
            data = await resp.json()
            session_id = data["session_id"]
        timing.session_ms = (time.perf_counter() - t0) * 1000

        # ── Step 2: Chat Stream (RAG + LLM) ────────────────────────
        t0 = time.perf_counter()
        first_token_received = False
        full_reply = []

        async with session.post(
            f"{BASE_URL}/api/chat/stream",
            json={"session_id": session_id, "message": question},
        ) as resp:
            if resp.status != 200:
                timing.error = f"Chat failed: {resp.status} {await resp.text()}"
                return timing

            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if not decoded:
                    continue

                # Handle SSE format: "data: {...}"
                if decoded.startswith("data: "):
                    decoded = decoded[6:]
                elif decoded.startswith("event:"):
                    continue

                try:
                    chunk = json.loads(decoded)
                except json.JSONDecodeError:
                    continue

                if chunk.get("type") == "text":
                    if not first_token_received:
                        timing.chat_first_token_ms = (time.perf_counter() - t0) * 1000
                        first_token_received = True
                    full_reply.append(chunk.get("content", ""))
                elif chunk.get("type") == "done":
                    break
                elif chunk.get("type") == "error":
                    timing.error = f"Chat stream error: {chunk.get('content')}"
                    return timing

        timing.chat_total_ms = (time.perf_counter() - t0) * 1000
        timing.reply_text = "".join(full_reply)
        timing.reply_chars = len(timing.reply_text)
        timing.reply_tokens_est = timing.reply_chars // CHARS_PER_TOKEN
        # Rough input estimate: system prompt (~500 tokens) + RAG context (~800 tokens) + question
        timing.input_tokens_est = 500 + 800 + (len(question) // CHARS_PER_TOKEN)

        if not timing.reply_text:
            timing.error = "Empty chat reply"
            return timing

        # ── Step 3: TTS ─────────────────────────────────────────────
        t0 = time.perf_counter()
        first_audio = False
        audio_size = 0

        async with session.post(
            f"{BASE_URL}/api/voice/tts/stream",
            json={"session_id": session_id, "message": question},
        ) as resp:
            if resp.status != 200:
                # Fallback to sync TTS
                async with session.post(
                    f"{BASE_URL}/api/voice/tts",
                    json={"session_id": session_id, "text": timing.reply_text},
                ) as tts_resp:
                    if tts_resp.status == 200:
                        audio_data = await tts_resp.read()
                        audio_size = len(audio_data)
                        timing.tts_first_chunk_ms = (time.perf_counter() - t0) * 1000
                        timing.tts_total_ms = timing.tts_first_chunk_ms
                    else:
                        timing.error = f"TTS failed: {tts_resp.status}"
                        return timing
            else:
                async for line in resp.content:
                    decoded = line.decode("utf-8").strip()
                    if not decoded:
                        continue
                    if decoded.startswith("data: "):
                        decoded = decoded[6:]
                    elif decoded.startswith("event:"):
                        continue

                    try:
                        chunk = json.loads(decoded)
                    except json.JSONDecodeError:
                        continue

                    if chunk.get("chunk") or chunk.get("type") == "audio":
                        if not first_audio:
                            timing.tts_first_chunk_ms = (time.perf_counter() - t0) * 1000
                            first_audio = True
                        audio_b64 = chunk.get("chunk") or chunk.get("data", "")
                        if audio_b64:
                            try:
                                audio_size += len(base64.b64decode(audio_b64))
                            except Exception:
                                audio_size += len(audio_b64)
                    elif chunk.get("type") == "done":
                        break

        timing.tts_total_ms = (time.perf_counter() - t0) * 1000
        timing.tts_audio_bytes = audio_size
        timing.e2e_ms = (time.perf_counter() - e2e_start) * 1000

    except asyncio.TimeoutError:
        timing.error = "Request timed out (60s)"
    except Exception as e:
        timing.error = f"Exception: {type(e).__name__}: {e}"

    return timing


async def run_concurrency_level(concurrency: int, rounds: int) -> ConcurrencyResult:
    """Run multiple rounds at a given concurrency level."""
    result = ConcurrencyResult(concurrency=concurrency)
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for round_num in range(rounds):
            questions = [
                QUESTIONS[(round_num * concurrency + i) % len(QUESTIONS)]
                for i in range(concurrency)
            ]
            tasks = [run_single_e2e(session, q) for q in questions]
            timings = await asyncio.gather(*tasks)
            result.timings.extend(timings)

            # Brief pause between rounds
            if round_num < rounds - 1:
                await asyncio.sleep(1)

    return result


def print_stats(label: str, values: list[float]) -> str:
    """Format percentile stats for a list of values."""
    if not values:
        return f"  {label}: no data"
    values.sort()
    mean = statistics.mean(values)
    p50 = values[len(values) // 2]
    p95 = values[int(len(values) * 0.95)] if len(values) >= 2 else values[-1]
    p99 = values[int(len(values) * 0.99)] if len(values) >= 2 else values[-1]
    mn, mx = min(values), max(values)
    return f"  {label:30s}  mean={mean:7.0f}ms  p50={p50:7.0f}ms  p95={p95:7.0f}ms  p99={p99:7.0f}ms  min={mn:7.0f}ms  max={mx:7.0f}ms"


def print_report(results: list[ConcurrencyResult]):
    """Print the full load test report."""
    print("\n" + "=" * 100)
    print("  ZOOCARI LOAD TEST REPORT — End-to-End Latency & OpenAI Cost")
    print("=" * 100)

    all_successful = []

    for r in results:
        ok = r.successful
        fail = r.failed
        all_successful.extend(ok)
        n = len(r.timings)

        print(f"\n{'─' * 100}")
        print(f"  CONCURRENCY: {r.concurrency}  |  Requests: {n}  |  Success: {len(ok)}  |  Failed: {len(fail)}")
        print(f"{'─' * 100}")

        if fail:
            for f in fail[:3]:
                print(f"  ❌ Error: {f.error}")

        if not ok:
            print("  No successful requests.")
            continue

        print(print_stats("Session Create", [t.session_ms for t in ok]))
        print(print_stats("Chat First Token (TTFT)", [t.chat_first_token_ms for t in ok]))
        print(print_stats("Chat Total (RAG+LLM)", [t.chat_total_ms for t in ok]))
        print(print_stats("TTS First Audio Chunk", [t.tts_first_chunk_ms for t in ok if t.tts_first_chunk_ms > 0]))
        print(print_stats("TTS Total", [t.tts_total_ms for t in ok]))
        print(print_stats("End-to-End (Full Pipeline)", [t.e2e_ms for t in ok]))

        avg_reply = statistics.mean([t.reply_chars for t in ok])
        avg_audio = statistics.mean([t.tts_audio_bytes for t in ok])
        print(f"\n  Avg reply length: {avg_reply:.0f} chars (~{avg_reply/CHARS_PER_TOKEN:.0f} tokens)")
        print(f"  Avg audio size:   {avg_audio/1024:.1f} KB")

    # ── Cost Estimation ─────────────────────────────────────────────
    if all_successful:
        print(f"\n{'=' * 100}")
        print("  OPENAI COST ESTIMATION")
        print(f"{'=' * 100}")

        cost = estimate_cost(all_successful)
        n = cost["total_requests"]

        print(f"\n  Total requests analyzed: {n}")
        print(f"  Total input tokens:     {cost['total_input_tokens']:,}")
        print(f"  Total output tokens:    {cost['total_output_tokens']:,}")
        print(f"  Total TTS characters:   {cost['total_tts_chars']:,}")

        print(f"\n  {'Component':<25s} {'Total':>12s} {'Per Request':>12s}")
        print(f"  {'─' * 50}")
        print(f"  {'Embedding (RAG query)':<25s} ${cost['embedding']:>10.6f}  ${cost['embedding']/n:>10.6f}")
        print(f"  {'LLM Input (gpt-4o-mini)':<25s} ${cost['llm_input']:>10.6f}  ${cost['llm_input']/n:>10.6f}")
        print(f"  {'LLM Output (gpt-4o-mini)':<25s} ${cost['llm_output']:>10.6f}  ${cost['llm_output']/n:>10.6f}")
        print(f"  {'TTS (tts-1)':<25s} ${cost['tts']:>10.6f}  ${cost['tts']/n:>10.6f}")
        print(f"  {'─' * 50}")
        print(f"  {'TOTAL':<25s} ${cost['total']:>10.6f}  ${cost['total']/n:>10.6f}")

        # Projection
        per_req = cost['total'] / n
        print(f"\n  Projected costs:")
        print(f"    100 questions/day:   ${per_req * 100:>8.4f}/day   ${per_req * 100 * 30:>8.2f}/month")
        print(f"    500 questions/day:   ${per_req * 500:>8.4f}/day   ${per_req * 500 * 30:>8.2f}/month")
        print(f"    1000 questions/day:  ${per_req * 1000:>8.4f}/day   ${per_req * 1000 * 30:>8.2f}/month")

    print(f"\n{'=' * 100}")
    print("  NOTE: Cost estimates use approximate token counts (1 token ≈ 4 chars).")
    print("  Actual costs may vary based on system prompt size, RAG context length,")
    print("  and OpenAI pricing changes. Check your OpenAI dashboard for actuals.")
    print(f"{'=' * 100}\n")


async def main():
    parser = argparse.ArgumentParser(description="Zoocari Load Test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--rounds", type=int, default=3, help="Rounds per concurrency level")
    parser.add_argument("--levels", default="1,5,10,20", help="Comma-separated concurrency levels")
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url.rstrip("/")
    levels = [int(x) for x in args.levels.split(",")]
    rounds = args.rounds

    # Health check
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(f"{BASE_URL}/health") as r:
                if r.status != 200:
                    print(f"Health check failed: {r.status}")
                    return
        except Exception as e:
            print(f"Cannot reach API at {BASE_URL}: {e}")
            return

    total_requests = sum(l * rounds for l in levels)
    print(f"\nZoocari Load Test")
    print(f"  API:          {BASE_URL}")
    print(f"  Concurrency:  {levels}")
    print(f"  Rounds:       {rounds} per level")
    print(f"  Total:        {total_requests} requests")
    print(f"  Pipeline:     Session → Chat/Stream (RAG+LLM) → TTS/Stream → Audio")
    print()

    results = []
    for level in levels:
        print(f"  Running concurrency={level} ({level * rounds} requests)...", flush=True)
        result = await run_concurrency_level(level, rounds)
        ok = len(result.successful)
        fail = len(result.failed)
        print(f"    Done: {ok} ok, {fail} failed")
        results.append(result)

    print_report(results)


if __name__ == "__main__":
    asyncio.run(main())
