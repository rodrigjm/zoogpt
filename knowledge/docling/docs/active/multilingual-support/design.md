# Multi-Lingual Support: Design Document

> **Last Updated:** 2026-01-20

## Executive Summary

**Scope:** English/Spanish language toggle for Zoocari chatbot
**Complexity:** Medium-High (no existing i18n infrastructure)
**Estimated Files:** ~35-45 files across frontend and backend

---

## Current State Analysis

| Area | Current State | Gap |
|------|---------------|-----|
| **Frontend** | No i18n library, ~50 hardcoded strings in TSX | Need react-i18next + string extraction |
| **STT** | Hardcoded `language="en"` in stt.py:99,187 | Parameterize language |
| **TTS** | Kokoro English-only voices | Need Spanish voice solution |
| **LLM/RAG** | English system prompt in admin_config.json | Spanish prompt variants |
| **Knowledge Base** | English content in LanceDB | Spanish animal facts |
| **Safety** | English keywords in safety.py:54-61 | Spanish equivalents |
| **API Models** | No language field in requests | Add language parameter |

---

## Architecture Decisions

### Decision 1: TTS Strategy

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| A. OpenAI TTS for Spanish | High quality, easy integration | Higher latency, cost per request |
| B. Coqui/Piper Spanish models | Local, low latency | Setup complexity, quality varies |
| C. Kokoro Spanish voices | Consistent architecture | May not exist, needs research |

**Recommendation:** Option A (OpenAI fallback) for MVP, research Option B for cost optimization.

### Decision 2: Knowledge Base Strategy

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| A. LLM-translate existing content | Fast, consistent | May miss kid-friendly nuance |
| B. Separate Spanish LanceDB table | Clean separation, simple queries | Duplicate maintenance |
| C. Single table with language tags | Single source of truth | Complex query logic |

**Recommendation:** Option B for simplicity - `data/zoo_lancedb_es/`

### Decision 3: Language Selection

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| A. Explicit user toggle | Clear user control | Extra UI step |
| B. Auto-detect from speech | Seamless experience | May misdetect, confusing |
| C. Browser locale + override | Smart default | May not match user preference |

**Recommendation:** Option A (explicit toggle) with Option C as enhancement.

---

## Component Impact Analysis

### Backend Files (~20 files)

| File | Changes Required |
|------|------------------|
| `models/chat.py` | Add `language: str = "en"` to ChatRequest |
| `models/voice.py` | Add `language` to TTSRequest, STTRequest |
| `services/stt.py` | Parameterize `language` param (lines 99, 187) |
| `services/tts.py` | Language-aware voice selection, Spanish fallback |
| `services/rag.py` | Language-aware prompt selection, followup questions |
| `services/llm.py` | Pass language context to system prompt |
| `services/safety.py` | Language-specific keyword lists, patterns |
| `routers/chat.py` | Extract language from request, pass to services |
| `routers/voice.py` | Extract language from request |
| `config.py` | Add language configuration |
| `admin_config.json` | Spanish system prompt, fallback responses |

### Frontend Files (~15 files)

| File | Changes Required |
|------|------------------|
| `package.json` | Add react-i18next, i18next dependencies |
| `src/i18n/index.ts` | i18n configuration (NEW) |
| `src/i18n/en.json` | English translations (NEW) |
| `src/i18n/es.json` | Spanish translations (NEW) |
| `src/components/LanguageSwitcher.tsx` | Toggle component (NEW) |
| `src/stores/languageStore.ts` | Language state management (NEW) |
| `src/components/WelcomeMessage/index.tsx` | Replace hardcoded strings |
| `src/components/ChatInterface/index.tsx` | Replace hardcoded strings |
| `src/components/ChatInput.tsx` | Replace placeholder |
| `src/lib/api.ts` | Add language to API calls |
| `src/hooks/useVoiceRecorder.ts` | Pass language to STT |
| `src/hooks/useTTSWebSocket.ts` | Pass language to TTS |

### Data Files

| File | Changes Required |
|------|------------------|
| `data/zoo_lancedb_es/` | Spanish knowledge base (NEW) |
| `.env.example` | Add DEFAULT_LANGUAGE setting |

---

## API Contract Changes

### ChatRequest (Before)
```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "rag"
    metadata: Optional[Dict[str, Any]] = None
```

### ChatRequest (After)
```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "rag"
    language: str = "en"  # NEW: "en" | "es"
    metadata: Optional[Dict[str, Any]] = None
```

### TTSRequest (After)
```python
class TTSRequest(BaseModel):
    session_id: str
    text: str
    voice: str = "default"
    language: str = "en"  # NEW: "en" | "es"
```

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Kokoro lacks Spanish voices | High | High | Plan OpenAI TTS fallback from start |
| Translation quality for kids | Medium | Medium | LLM translation + human review |
| Latency increase | Medium | Medium | Cache outputs, lazy model loading |
| Safety bypasses in Spanish | Medium | Low | Comprehensive Spanish guardrail testing |
| Context window with dual prompts | Low | Low | Prompts are small (~500 tokens each) |

---

## Success Criteria

1. User can toggle between English/Spanish in UI
2. STT correctly transcribes Spanish speech
3. TTS outputs natural Spanish audio
4. LLM responds in selected language with kid-friendly tone
5. Safety guardrails work in both languages
6. No regression in English functionality
7. Latency within acceptable bounds (<3s total response time)
