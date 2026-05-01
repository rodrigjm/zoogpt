# QA Report — Mobile Mic Stop Fix

**Date:** 2026-05-01
**Branch:** `fix/mobile-mic-stop-recording`
**Commits:** `2cbba7c` (overlay), `254ee95` (wiring + 20s cap)

## Vitest
- `VoiceOverlay.test.tsx`: ✅ 5/5 PASS (verified under Node 22.22.0)

## TypeScript
- `tsc --noEmit`: ✅ 0 errors

## Build & Deploy
- `docker compose build web`: ✅ Vite build succeeded (62 modules, ~189 KB JS / 34.6 KB CSS, 1.77s)
- `docker compose up -d web`: ✅ `zoocari-web` recreated, HTTP 200 on `:3000`

## Manual — iPhone Safari
- ✅ Recording works end-to-end on iPhone Safari (user-confirmed 2026-05-01)
- Center stop button submits transcript
- Cancel pill discards
- 20s auto-stop safety net in place (covered by code path; not separately stress-tested)

## Notes
- The unused `useVoiceRecorder` hook and `components/VoiceButton/index.tsx` were intentionally left untouched. Future cleanup candidate.
- `voiceStore.stopRecording` still names the blob `recording.webm` regardless of MIME. STT backend tolerates this; flagged for future cleanup.
