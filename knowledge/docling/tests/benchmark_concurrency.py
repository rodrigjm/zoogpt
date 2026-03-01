"""
Zoocari Concurrency Benchmark Suite
====================================
Measures latency, throughput, and time-to-first-token under concurrent load.

Usage:
    # Basic run (5 concurrent users, default endpoint)
    python tests/benchmark_concurrency.py

    # Custom concurrency levels
    python tests/benchmark_concurrency.py --concurrency 1 2 5 10 15

    # Target a specific host
    python tests/benchmark_concurrency.py --base-url http://192.168.1.100:8000

    # Include TTS benchmark
    python tests/benchmark_concurrency.py --include-tts

    # JSON output for CI
    python tests/benchmark_concurrency.py --output json
"""

import asyncio
import argparse
import json
import time
import statistics
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. Install with: pip install httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Test questions (diverse to avoid caching bias)
# ---------------------------------------------------------------------------
TEST_QUESTIONS = [
    "What do lions eat?",
    "How fast can a cheetah run?",
    "Why do zebras have stripes?",
    "What sounds do elephants make?",
    "How long do giraffes sleep?",
    "Can parrots really talk?",
    "How do penguins stay warm?",
    "What's the biggest animal at the zoo?",
    "Do snakes have bones?",
    "Why do flamingos stand on one leg?",
    "How strong is a gorilla?",
    "What do baby animals eat?",
    "How do chameleons change color?",
    "What animals can you pet at Leesburg Animal Park?",
    "Why do peacocks have colorful feathers?",
]


@dataclass
class RequestResult:
    """Result of a single benchmark request."""
    user_id: int
    question: str
    total_latency_ms: float
    time_to_first_token_ms: Optional[float] = None
    response_length: int = 0
    status_code: int = 0
    error: Optional[str] = None
    chunks_received: int = 0


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results for a concurrency level."""
    concurrency: int
    total_requests: int
    successful: int
    failed: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    avg_ttft_ms: Optional[float] = None  # time to first token
    throughput_rps: float = 0.0
    wall_clock_ms: float = 0.0
    individual_results: list = field(default_factory=list)


def percentile(data: list[float], p: float) -> float:
    """Calculate percentile from sorted data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


async def create_session(client: httpx.AsyncClient, base_url: str) -> Optional[str]:
    """Create a new chat session and return session_id."""
    try:
        response = await client.post(
            f"{base_url}/api/session",
            json={"client": "web", "metadata": {}},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("session_id") or data.get("id")
        elif response.status_code == 201:
            data = response.json()
            return data.get("session_id") or data.get("id")
        else:
            print(f"  Session creation failed: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  Session creation error: {e}")
        return None


async def benchmark_chat_stream(
    client: httpx.AsyncClient,
    base_url: str,
    session_id: str,
    question: str,
    user_id: int,
) -> RequestResult:
    """Benchmark a single streaming chat request."""
    start = time.perf_counter()
    ttft = None
    chunks = 0
    response_text = ""

    try:
        async with client.stream(
            "POST",
            f"{base_url}/api/chat/stream",
            json={"session_id": session_id, "message": question},
            timeout=120.0,
        ) as response:
            if response.status_code != 200:
                elapsed = (time.perf_counter() - start) * 1000
                body = b""
                async for chunk in response.aiter_bytes():
                    body += chunk
                return RequestResult(
                    user_id=user_id,
                    question=question,
                    total_latency_ms=elapsed,
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}: {body.decode()[:200]}",
                )

            buffer = ""
            async for raw_chunk in response.aiter_text():
                buffer += raw_chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line.startswith("data: "):
                        if ttft is None:
                            ttft = (time.perf_counter() - start) * 1000
                        chunks += 1
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "text":
                                response_text += data.get("content", "")
                        except json.JSONDecodeError:
                            pass

    except httpx.ReadTimeout:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            user_id=user_id,
            question=question,
            total_latency_ms=elapsed,
            error="ReadTimeout",
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            user_id=user_id,
            question=question,
            total_latency_ms=elapsed,
            error=str(e),
        )

    elapsed = (time.perf_counter() - start) * 1000

    return RequestResult(
        user_id=user_id,
        question=question,
        total_latency_ms=elapsed,
        time_to_first_token_ms=ttft,
        response_length=len(response_text),
        status_code=200,
        chunks_received=chunks,
    )


async def benchmark_chat_non_stream(
    client: httpx.AsyncClient,
    base_url: str,
    session_id: str,
    question: str,
    user_id: int,
) -> RequestResult:
    """Benchmark a single non-streaming chat request."""
    start = time.perf_counter()

    try:
        response = await client.post(
            f"{base_url}/api/chat",
            json={"session_id": session_id, "message": question},
            timeout=120.0,
        )
        elapsed = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            reply = data.get("reply", "")
            return RequestResult(
                user_id=user_id,
                question=question,
                total_latency_ms=elapsed,
                response_length=len(reply),
                status_code=200,
            )
        else:
            return RequestResult(
                user_id=user_id,
                question=question,
                total_latency_ms=elapsed,
                status_code=response.status_code,
                error=f"HTTP {response.status_code}",
            )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            user_id=user_id,
            question=question,
            total_latency_ms=elapsed,
            error=str(e),
        )


async def benchmark_tts(
    client: httpx.AsyncClient,
    base_url: str,
    text: str,
    user_id: int,
) -> RequestResult:
    """Benchmark a single TTS request."""
    start = time.perf_counter()

    try:
        response = await client.post(
            f"{base_url}/api/voice/tts",
            json={"text": text, "voice": "af_heart", "speed": 1.0},
            timeout=60.0,
        )
        elapsed = (time.perf_counter() - start) * 1000

        return RequestResult(
            user_id=user_id,
            question=f"TTS: {text[:40]}",
            total_latency_ms=elapsed,
            response_length=len(response.content),
            status_code=response.status_code,
            error=None if response.status_code == 200 else f"HTTP {response.status_code}",
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            user_id=user_id,
            question=f"TTS: {text[:40]}",
            total_latency_ms=elapsed,
            error=str(e),
        )


async def run_benchmark_level(
    base_url: str,
    concurrency: int,
    mode: str = "stream",
    include_tts: bool = False,
) -> BenchmarkResult:
    """Run benchmark at a specific concurrency level."""
    print(f"\n{'='*60}")
    print(f"  Concurrency Level: {concurrency} users ({mode} mode)")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        # Create sessions for each concurrent user
        print(f"  Creating {concurrency} sessions...")
        sessions = []
        for i in range(concurrency):
            sid = await create_session(client, base_url)
            if sid:
                sessions.append(sid)
            else:
                print(f"  WARNING: Could not create session for user {i+1}")

        if not sessions:
            print("  ERROR: No sessions created. Is the API running?")
            return BenchmarkResult(
                concurrency=concurrency,
                total_requests=0,
                successful=0,
                failed=concurrency,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
            )

        # Prepare tasks - each user asks a different question
        tasks = []
        for i in range(concurrency):
            session_id = sessions[i % len(sessions)]
            question = TEST_QUESTIONS[i % len(TEST_QUESTIONS)]

            if mode == "stream":
                tasks.append(
                    benchmark_chat_stream(client, base_url, session_id, question, i)
                )
            else:
                tasks.append(
                    benchmark_chat_non_stream(client, base_url, session_id, question, i)
                )

        # Fire all requests simultaneously and time the wall clock
        print(f"  Firing {len(tasks)} concurrent requests...")
        wall_start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        wall_elapsed = (time.perf_counter() - wall_start) * 1000

        # TTS benchmark (optional)
        tts_results = []
        if include_tts:
            print(f"  Running TTS benchmark ({concurrency} concurrent)...")
            tts_tasks = []
            for i in range(concurrency):
                text = f"Hello! I'm Zoocari the elephant. Did you know that {TEST_QUESTIONS[i % len(TEST_QUESTIONS)].lower()}"
                tts_tasks.append(benchmark_tts(client, base_url, text, i))

            tts_results = await asyncio.gather(*tts_tasks)

        # Aggregate results
        latencies = [r.total_latency_ms for r in results if r.error is None]
        ttfts = [r.time_to_first_token_ms for r in results if r.time_to_first_token_ms is not None]
        successful = len([r for r in results if r.error is None])
        failed = len([r for r in results if r.error is not None])

        result = BenchmarkResult(
            concurrency=concurrency,
            total_requests=len(results),
            successful=successful,
            failed=failed,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=percentile(latencies, 50),
            p95_latency_ms=percentile(latencies, 95),
            p99_latency_ms=percentile(latencies, 99),
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            avg_ttft_ms=statistics.mean(ttfts) if ttfts else None,
            throughput_rps=(successful / (wall_elapsed / 1000)) if wall_elapsed > 0 else 0,
            wall_clock_ms=wall_elapsed,
        )

        # Print results
        print(f"\n  Results:")
        print(f"    Successful: {successful}/{len(results)}")
        if failed > 0:
            for r in results:
                if r.error:
                    print(f"    FAILED [user {r.user_id}]: {r.error}")
        if latencies:
            print(f"    Avg latency:  {result.avg_latency_ms:,.0f} ms")
            print(f"    P50 latency:  {result.p50_latency_ms:,.0f} ms")
            print(f"    P95 latency:  {result.p95_latency_ms:,.0f} ms")
            print(f"    P99 latency:  {result.p99_latency_ms:,.0f} ms")
            print(f"    Min/Max:      {result.min_latency_ms:,.0f} / {result.max_latency_ms:,.0f} ms")
            if result.avg_ttft_ms is not None:
                print(f"    Avg TTFT:     {result.avg_ttft_ms:,.0f} ms")
            print(f"    Throughput:   {result.throughput_rps:.2f} req/s")
            print(f"    Wall clock:   {result.wall_clock_ms:,.0f} ms")

        if tts_results:
            tts_latencies = [r.total_latency_ms for r in tts_results if r.error is None]
            if tts_latencies:
                print(f"\n  TTS Results:")
                print(f"    Avg TTS latency: {statistics.mean(tts_latencies):,.0f} ms")
                print(f"    P95 TTS latency: {percentile(tts_latencies, 95):,.0f} ms")

        return result


async def run_health_check(base_url: str) -> bool:
    """Check if the API is reachable."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"  API health check: OK")
                return True
            # Try root endpoint
            response = await client.get(f"{base_url}/", timeout=5.0)
            if response.status_code == 200:
                print(f"  API reachable (no /health endpoint)")
                return True
    except Exception as e:
        print(f"  API health check FAILED: {e}")
    return False


async def main():
    parser = argparse.ArgumentParser(description="Zoocari Concurrency Benchmark")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--concurrency",
        nargs="+",
        type=int,
        default=[1, 2, 5, 10],
        help="Concurrency levels to test (default: 1 2 5 10)",
    )
    parser.add_argument(
        "--mode",
        choices=["stream", "non-stream"],
        default="stream",
        help="Chat endpoint mode (default: stream)",
    )
    parser.add_argument(
        "--include-tts",
        action="store_true",
        help="Include TTS endpoint in benchmark",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup requests before benchmark (default: 1)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  ZOOCARI CONCURRENCY BENCHMARK")
    print("=" * 60)
    print(f"  Target: {args.base_url}")
    print(f"  Mode: {args.mode}")
    print(f"  Concurrency levels: {args.concurrency}")
    print(f"  Include TTS: {args.include_tts}")

    # Health check
    print(f"\n  Checking API availability...")
    if not await run_health_check(args.base_url):
        print("\n  ERROR: API not reachable. Make sure the server is running.")
        print(f"  Tried: {args.base_url}")
        sys.exit(1)

    # Warmup
    if args.warmup > 0:
        print(f"\n  Running {args.warmup} warmup request(s)...")
        await run_benchmark_level(args.base_url, args.warmup, args.mode)
        print("  Warmup complete. Starting benchmark...")

    # Run benchmarks at each concurrency level
    all_results = []
    for level in args.concurrency:
        result = await run_benchmark_level(
            args.base_url, level, args.mode, args.include_tts
        )
        all_results.append(result)

        # Brief pause between levels to let the system settle
        if level != args.concurrency[-1]:
            print(f"\n  Cooling down for 3 seconds...")
            await asyncio.sleep(3)

    # Summary
    print(f"\n{'='*60}")
    print(f"  BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Concurrency':>12} | {'Avg (ms)':>10} | {'P95 (ms)':>10} | {'Max (ms)':>10} | {'TTFT (ms)':>10} | {'RPS':>8} | {'Fail':>5}")
    print(f"  {'-'*12}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*5}")
    for r in all_results:
        ttft_str = f"{r.avg_ttft_ms:>10,.0f}" if r.avg_ttft_ms else f"{'N/A':>10}"
        print(
            f"  {r.concurrency:>12} | {r.avg_latency_ms:>10,.0f} | {r.p95_latency_ms:>10,.0f} | "
            f"{r.max_latency_ms:>10,.0f} | {ttft_str} | {r.throughput_rps:>8.2f} | {r.failed:>5}"
        )

    # Scaling analysis
    if len(all_results) >= 2 and all_results[0].avg_latency_ms > 0:
        baseline = all_results[0].avg_latency_ms
        print(f"\n  Scaling Analysis (relative to {all_results[0].concurrency}-user baseline):")
        for r in all_results[1:]:
            if r.avg_latency_ms > 0:
                ratio = r.avg_latency_ms / baseline
                ideal_ratio = r.concurrency / all_results[0].concurrency
                efficiency = (ideal_ratio / ratio) * 100 if ratio > 0 else 0
                print(
                    f"    {r.concurrency} users: {ratio:.1f}x slower than baseline "
                    f"(ideal={ideal_ratio:.0f}x, efficiency={efficiency:.0f}%)"
                )

    # JSON output
    if args.output == "json":
        output = {
            "config": {
                "base_url": args.base_url,
                "mode": args.mode,
                "concurrency_levels": args.concurrency,
            },
            "results": [
                {
                    "concurrency": r.concurrency,
                    "successful": r.successful,
                    "failed": r.failed,
                    "avg_latency_ms": round(r.avg_latency_ms, 1),
                    "p50_latency_ms": round(r.p50_latency_ms, 1),
                    "p95_latency_ms": round(r.p95_latency_ms, 1),
                    "p99_latency_ms": round(r.p99_latency_ms, 1),
                    "min_latency_ms": round(r.min_latency_ms, 1),
                    "max_latency_ms": round(r.max_latency_ms, 1),
                    "avg_ttft_ms": round(r.avg_ttft_ms, 1) if r.avg_ttft_ms else None,
                    "throughput_rps": round(r.throughput_rps, 2),
                    "wall_clock_ms": round(r.wall_clock_ms, 1),
                }
                for r in all_results
            ],
        }
        print(f"\n--- JSON OUTPUT ---")
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
