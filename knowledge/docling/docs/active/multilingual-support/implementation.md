# Multi-Lingual Support: Implementation Plan

> **Last Updated:** 2026-01-20

## Phase Overview

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: API Contracts (Sequential - Foundation)            │
│ - Add language to API models                                │
│ - Update config schema                                      │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AGENT 1:        │  │ AGENT 2:        │  │ AGENT 3:        │
│ Voice Pipeline  │  │ LLM/RAG Prompts │  │ Frontend i18n   │
│ (Phase 2)       │  │ (Phase 3)       │  │ (Phase 4)       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Knowledge Base (Spanish content)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Safety/Guardrails (Spanish patterns)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ QA → TROUBLESHOOT → QA (Iterative until pass)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ DEVOPS: Build & Deploy                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: API Contracts (Foundation)

**Dependencies:** None
**Parallel:** No (must complete before Phases 2-4)

### Tasks

| Task | File | Description |
|------|------|-------------|
| 1.1 | `models/chat.py` | Add `language: str = "en"` to ChatRequest |
| 1.2 | `models/voice.py` | Add `language` to TTSRequest, STTRequest |
| 1.3 | `config.py` | Add SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE |
| 1.4 | `.env.example` | Document DEFAULT_LANGUAGE env var |
| 1.5 | `src/types/index.ts` | Mirror language field in TypeScript types |

### Acceptance Criteria
- [ ] All request models accept `language` parameter
- [ ] Default language is "en" for backward compatibility
- [ ] TypeScript types match Python models
- [ ] No breaking changes to existing API calls

---

## Phase 2: Voice Pipeline

**Dependencies:** Phase 1
**Parallel:** Yes (with Phases 3, 4)

### Tasks

| Task | File | Description |
|------|------|-------------|
| 2.1 | `services/stt.py` | Parameterize `language` in transcribe() |
| 2.2 | `services/stt.py` | Update OpenAI Whisper fallback language |
| 2.3 | `services/tts.py` | Create language-aware voice selection |
| 2.4 | `services/tts.py` | Add OpenAI TTS fallback for Spanish |
| 2.5 | `routers/voice.py` | Extract language from request, pass to services |
| 2.6 | `admin_config.json` | Add Spanish voice configuration |

### Acceptance Criteria
- [ ] STT correctly transcribes Spanish speech
- [ ] TTS outputs Spanish audio (via OpenAI if Kokoro unavailable)
- [ ] Voice quality acceptable for kids
- [ ] Latency within bounds (<2s for TTS)

---

## Phase 3: LLM/RAG Prompts

**Dependencies:** Phase 1
**Parallel:** Yes (with Phases 2, 4)

### Tasks

| Task | File | Description |
|------|------|-------------|
| 3.1 | `admin_config.json` | Create Spanish system prompt |
| 3.2 | `admin_config.json` | Create Spanish fallback responses |
| 3.3 | `services/rag.py` | Language-aware prompt selection |
| 3.4 | `services/rag.py` | Spanish followup questions pool |
| 3.5 | `services/llm.py` | Pass language to system prompt formatter |
| 3.6 | `routers/chat.py` | Extract language, pass to RAG service |

### Spanish System Prompt (Draft)
```
Eres Zoocari el Elefante, el experto en animales del Leesburg Animal Park!
- Eres cálido, juguetón y alentador
- Usas palabras simples que niños de 6-12 años entienden
- Respondes SOLO sobre los animales del zoológico
...
```

### Acceptance Criteria
- [ ] LLM responds in Spanish when language="es"
- [ ] Responses are kid-friendly in Spanish
- [ ] Followup questions are in Spanish
- [ ] Fallback responses are in Spanish

---

## Phase 4: Frontend i18n

**Dependencies:** Phase 1
**Parallel:** Yes (with Phases 2, 3)

### Tasks

| Task | File | Description |
|------|------|-------------|
| 4.1 | `package.json` | Add react-i18next, i18next |
| 4.2 | `src/i18n/index.ts` | Configure i18n (NEW) |
| 4.3 | `src/i18n/en.json` | English translations (NEW) |
| 4.4 | `src/i18n/es.json` | Spanish translations (NEW) |
| 4.5 | `src/stores/languageStore.ts` | Language state with Zustand (NEW) |
| 4.6 | `src/components/LanguageSwitcher.tsx` | Toggle component (NEW) |
| 4.7 | `src/components/WelcomeMessage/index.tsx` | Use t() for strings |
| 4.8 | `src/components/ChatInterface/index.tsx` | Use t() for strings |
| 4.9 | `src/components/ChatInput.tsx` | Use t() for placeholder |
| 4.10 | `src/lib/api.ts` | Include language in API calls |
| 4.11 | `src/hooks/useVoiceRecorder.ts` | Pass language to STT |
| 4.12 | `src/hooks/useTTSWebSocket.ts` | Pass language to TTS |

### String Extraction (Key Strings)

```json
// en.json
{
  "welcome": {
    "title": "Welcome to Zoocari!",
    "subtitle": "I'm your friendly zoo guide!",
    "description": "Ask me anything about the amazing animals at Leesburg Animal Park!",
    "tryAsking": "Try asking me:"
  },
  "chat": {
    "placeholder": "Ask me about the animals...",
    "textMode": "Text Mode",
    "voiceMode": "Voice Mode"
  }
}

// es.json
{
  "welcome": {
    "title": "¡Bienvenido a Zoocari!",
    "subtitle": "¡Soy tu guía amigable del zoológico!",
    "description": "¡Pregúntame sobre los animales increíbles del Leesburg Animal Park!",
    "tryAsking": "Intenta preguntarme:"
  },
  "chat": {
    "placeholder": "Pregúntame sobre los animales...",
    "textMode": "Modo Texto",
    "voiceMode": "Modo Voz"
  }
}
```

### Acceptance Criteria
- [ ] Language switcher visible in UI
- [ ] All UI text switches with language
- [ ] Language preference persists in localStorage
- [ ] API calls include selected language

---

## Phase 5: Knowledge Base

**Dependencies:** Phase 3
**Parallel:** No

### Tasks

| Task | File | Description |
|------|------|-------------|
| 5.1 | - | Translate animal knowledge to Spanish |
| 5.2 | `scripts/build_lancedb_es.py` | Create Spanish embedding script |
| 5.3 | `data/zoo_lancedb_es/` | Build Spanish vector database |
| 5.4 | `services/rag.py` | Language-aware database selection |

### Acceptance Criteria
- [ ] Spanish knowledge base built and embedded
- [ ] RAG returns Spanish content for Spanish queries
- [ ] No degradation in retrieval quality

---

## Phase 6: Safety/Guardrails

**Dependencies:** Phase 3
**Parallel:** No

### Tasks

| Task | File | Description |
|------|------|-------------|
| 6.1 | `services/safety.py` | Create ZOO_KEYWORDS_ES list |
| 6.2 | `services/safety.py` | Create INJECTION_PATTERNS_ES |
| 6.3 | `services/safety.py` | Language-aware safety check routing |
| 6.4 | `services/safety.py` | Spanish off-topic response |

### Spanish Keywords (Draft)
```python
ZOO_KEYWORDS_ES = [
    "animal", "animales", "zoológico", "parque", "leesburg",
    "alimentar", "acariciar", "visitar", "león", "tigre", "elefante",
    ...
]
```

### Acceptance Criteria
- [ ] Spanish off-topic detection works
- [ ] Spanish prompt injection blocked
- [ ] No false positives on legitimate Spanish queries

---

## QA Validation Checklist

### Functional Tests
- [ ] English text chat works (regression)
- [ ] English voice chat works (regression)
- [ ] Spanish text chat works
- [ ] Spanish voice chat works
- [ ] Language switching mid-session works
- [ ] Followup questions match selected language

### Edge Cases
- [ ] Mixed language input (e.g., "Tell me about leones")
- [ ] Language switch during voice recording
- [ ] Network failure during TTS (Spanish)
- [ ] Very long Spanish responses

### Performance Tests
- [ ] STT latency < 1s (Spanish)
- [ ] TTS latency < 2s (Spanish)
- [ ] Total response time < 3s (Spanish)

### Safety Tests
- [ ] Spanish prompt injection blocked
- [ ] Spanish off-topic redirected
- [ ] Spanish PII detection works

---

## Rollback Plan

If issues arise post-deployment:
1. Set `DEFAULT_LANGUAGE=en` in environment
2. Hide language switcher via feature flag
3. Revert to English-only TTS
4. Spanish content remains but is not served
