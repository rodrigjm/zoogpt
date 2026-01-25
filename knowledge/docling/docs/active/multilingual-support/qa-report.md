# Multi-Lingual Support: QA Report

> **Last Updated:** 2026-01-20
> **Status:** Not Started

## Test Summary

| Category | Pass | Fail | Skip | Total |
|----------|------|------|------|-------|
| Regression (English) | - | - | - | 0 |
| Spanish Text Chat | - | - | - | 0 |
| Spanish Voice Chat | - | - | - | 0 |
| Language Switching | - | - | - | 0 |
| Edge Cases | - | - | - | 0 |
| Performance | - | - | - | 0 |
| Safety | - | - | - | 0 |
| **Total** | **0** | **0** | **0** | **0** |

---

## Test Cases

### Regression Tests (English)

| ID | Test | Status | Notes |
|----|------|--------|-------|
| R1 | English text chat responds correctly | ⬜ | |
| R2 | English voice input transcribes correctly | ⬜ | |
| R3 | English TTS outputs audio | ⬜ | |
| R4 | Safety blocks English prompt injection | ⬜ | |
| R5 | Followup questions appear in English | ⬜ | |

### Spanish Functional Tests

| ID | Test | Status | Notes |
|----|------|--------|-------|
| S1 | Spanish text chat responds in Spanish | ⬜ | |
| S2 | Spanish voice input transcribes correctly | ⬜ | |
| S3 | Spanish TTS outputs audio | ⬜ | |
| S4 | Spanish followup questions appear | ⬜ | |
| S5 | Spanish fallback response works | ⬜ | |

### Language Switching Tests

| ID | Test | Status | Notes |
|----|------|--------|-------|
| L1 | Toggle EN→ES switches UI text | ⬜ | |
| L2 | Toggle ES→EN switches UI text | ⬜ | |
| L3 | API calls include correct language | ⬜ | |
| L4 | Language persists across page reload | ⬜ | |
| L5 | Mid-conversation switch works | ⬜ | |

### Edge Cases

| ID | Test | Status | Notes |
|----|------|--------|-------|
| E1 | Mixed language input handled | ⬜ | |
| E2 | Language switch during recording | ⬜ | |
| E3 | TTS failure fallback works | ⬜ | |
| E4 | Very long Spanish response | ⬜ | |

### Performance Tests

| ID | Test | Target | Actual | Status |
|----|------|--------|--------|--------|
| P1 | Spanish STT latency | <1s | - | ⬜ |
| P2 | Spanish TTS latency | <2s | - | ⬜ |
| P3 | Total Spanish response | <3s | - | ⬜ |

### Safety Tests

| ID | Test | Status | Notes |
|----|------|--------|-------|
| SF1 | Spanish prompt injection blocked | ⬜ | |
| SF2 | Spanish off-topic redirected | ⬜ | |
| SF3 | Spanish PII detection | ⬜ | |

---

## Issues Found

_None yet - QA not started._

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| - | - | - | - |

---

## Sign-Off

| Role | Name | Date | Approved |
|------|------|------|----------|
| QA | - | - | ⬜ |
| Dev | - | - | ⬜ |
| PM | - | - | ⬜ |
