# Local Inference Options for Latency Improvement

> Research Date: January 2026

## Executive Summary

Your Zoocari codebase already uses **Faster-Whisper** for local STT and **Kokoro-ONNX** for local TTS. The main latency bottleneck is the **OpenAI API for LLM inference** in your RAG pipeline. Switching to local LLM inference can reduce latency by 2-10x for typical Q&A responses.

---

## Current Architecture Analysis

| Component | Current Implementation | Latency Profile |
|-----------|----------------------|-----------------|
| **STT** | Faster-Whisper (local, base, int8) | ~2-4s for short audio |
| **TTS** | Kokoro-ONNX (local) | Fast, ~300ms/chunk |
| **LLM** | OpenAI API (gpt-4o-mini likely) | 500ms-2s network + inference |

**Your STT is already optimized locally.** The main opportunity is replacing OpenAI for text generation.

---

## Option 1: Optimize Existing STT (Faster-Whisper)

You're using `base` model with `int8` quantization on CPU. Potential improvements:

### Model Upgrade Options
| Model | Size | RTFx | WER | VRAM/RAM |
|-------|------|------|-----|----------|
| `base` (current) | 74M | ~10x | 4.2% | ~200MB |
| `small` | 244M | ~5x | 3.4% | ~500MB |
| `distil-whisper-small` | 166M | ~15x | 3.5% | ~350MB |
| `turbo` | 809M | ~20x | 3.0% | ~2GB GPU |

### Recommended STT Improvements
1. **Use `distil-whisper-small`** - 50% faster than base, similar accuracy
2. **Enable GPU** if available - 3-5x speedup
3. **Use VAD (Voice Activity Detection)** - skip silence for faster processing

```python
# Upgrade in stt.py
_stt_model = WhisperModel("distil-whisper-small", device="cuda", compute_type="float16")
```

---

## Option 2: Local LLM for RAG (Primary Recommendation)

Replace OpenAI API calls in your RAG service with local inference.

### Best Models for Your Use Case (Kid Q&A)

| Model | Parameters | VRAM | Latency (TTFT) | Quality |
|-------|-----------|------|----------------|---------|
| **Qwen2.5-1.5B-Instruct** | 1.5B | 3GB | ~100ms | Good for simple Q&A |
| **Phi-4** | 3.8B | 8GB | ~150ms | Excellent reasoning |
| **Gemma2-2B** | 2B | 4GB | ~120ms | Good multilingual |
| **Llama-3.2-3B** | 3B | 6GB | ~140ms | Strong general |
| **SmolLM3-3B** | 3B | 6GB | ~130ms | Optimized for efficiency |

### Inference Engine Comparison

| Engine | Best For | Throughput | Ease of Use |
|--------|----------|------------|-------------|
| **Ollama** | Development, single user | 1-3 req/s | ⭐⭐⭐⭐⭐ |
| **vLLM** | Production, high concurrency | 120+ req/s | ⭐⭐⭐ |
| **llama.cpp** | Edge/CPU deployment | 2-5 req/s | ⭐⭐⭐⭐ |

### Recommended Setup: Ollama + Qwen2.5

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull optimized model for kid Q&A
ollama pull qwen2.5:1.5b-instruct-q4_K_M
```

```python
# rag.py modification
import requests

class RAGService:
    def __init__(self):
        self.llm_endpoint = "http://localhost:11434/api/generate"
        self.model = "qwen2.5:1.5b-instruct-q4_K_M"

    def generate_response(self, prompt: str, context: str) -> str:
        response = requests.post(self.llm_endpoint, json={
            "model": self.model,
            "prompt": f"{self.system_prompt}\n\nContext: {context}\n\nQuestion: {prompt}",
            "stream": False
        })
        return response.json()["response"]
```

---

## Option 3: Alternative STT Models (If Faster-Whisper Insufficient)

### Ultra-Low Latency Options

| Model | Latency | Quality | Notes |
|-------|---------|---------|-------|
| **Moonshine** | ~200ms | Good | Designed for edge devices |
| **Kyutai 1B** | ~1s first chunk | Excellent | Real-time streaming |
| **NVIDIA Parakeet** | ~500ms | Excellent | Requires NVIDIA GPU |

### Moonshine Integration (Fastest Option)

```bash
pip install moonshine
```

```python
from moonshine import transcribe

def transcribe_moonshine(audio_bytes):
    return transcribe(audio_bytes, model_name="base")
```

---

## Latency Comparison: API vs Local

### OpenAI Whisper API
- Network round-trip: 100-300ms
- Queue/rate limiting: 50-500ms variable
- Inference: 500ms-2s
- **Total: 700ms-3s** (highly variable)

### Local Faster-Whisper (current)
- Model load: 0ms (preloaded)
- Inference: 2-4s (base, CPU)
- **Total: 2-4s** (consistent)

### Local Distil-Whisper (optimized)
- Model load: 0ms (preloaded)
- Inference: 1-2s (GPU), 2-3s (CPU)
- **Total: 1-3s** (consistent)

### Local LLM (Qwen2.5-1.5B)
- API overhead: 10ms (localhost)
- Inference: 100-300ms (GPU), 500ms-1s (CPU)
- **Total: 100ms-1s** vs OpenAI's 500ms-2s

---

## Implementation Recommendations

### Quick Wins (Low Effort)
1. **Upgrade Faster-Whisper model** to `distil-whisper-small` - 30-50% faster
2. **Enable CUDA** if GPU available - 3-5x faster STT

### Medium Effort (Recommended)
3. **Add Ollama for LLM** - Replace OpenAI API calls, 2-5x latency reduction
4. **Use streaming responses** - Show partial results while generating

### High Effort (Maximum Performance)
5. **Deploy vLLM** for production-scale LLM inference
6. **Switch to Moonshine** for ultra-low latency STT
7. **Implement speculative decoding** for even faster LLM responses

---

## Hardware Requirements

### Minimum (CPU-only)
- 16GB RAM
- 8-core CPU
- Latency: ~3-5s total pipeline

### Recommended (Consumer GPU)
- 16GB RAM
- RTX 3060 12GB or better
- Latency: ~1-2s total pipeline

### Production (High Performance)
- 32GB RAM
- RTX 4090 24GB or A100
- Latency: ~500ms-1s total pipeline

---

## Sources

- [Northflank STT Benchmarks 2026](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2025-benchmarks)
- [Modal Top Open Source STT](https://modal.com/blog/open-source-stt)
- [Red Hat vLLM vs Ollama](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)
- [Ionio Edge STT Benchmark](https://www.ionio.ai/blog/2025-edge-speech-to-text-model-benchmark-whisper-vs-competitors)
- [AssemblyAI Whisper Options](https://www.assemblyai.com/blog/openai-whisper-developers-choosing-api-local-server-side-transcription)
- [Kolosal Top 5 Local LLMs](https://www.kolosal.ai/blog-detail/top-5-best-llm-models-to-run-locally-in-cpu-2025-edition)
- [DataCamp Small Language Models 2026](https://www.datacamp.com/blog/top-small-language-models)
- [Home Assistant Faster Whisper Discussion](https://community.home-assistant.io/t/even-faster-whisper-for-local-voice-low-latency-stt/864762)
- [GitHub faster-whisper](https://github.com/SYSTRAN/faster-whisper)
