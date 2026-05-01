# Design — Mobile Mic Stop Fix

**Date:** 2026-05-01
**Branch:** `fix/mobile-mic-stop-recording`
**Status:** Approved (pending user review of this spec)

## Problem
On mobile (iPhone Safari reproduction): user taps mic, grants permission, the `VoiceOverlay` appears — and there is no way to stop and submit the recording. The overlay covers the InputBar's mic button (`fixed inset-0 z-50`), and the overlay's own center mic graphic has no `onClick`. The only control available is the "Cancel" pill, which calls `cancelRecording()` and discards the audio.

## Root Cause (verified by reading code)
- `apps/web/src/components/chat/VoiceOverlay.tsx:30-71` — center mic icon is decorative, no handler
- `apps/web/src/components/chat/VoiceOverlay.tsx:79-91` — only "Cancel" interactive control
- `apps/web/src/components/ChatInterface/NewChatInterface.tsx:274-275` — overlay shown whenever `voiceMode ∈ {recording, processing}`
- `apps/web/src/components/chat/VoiceButton.tsx:32-50` — stop+transcribe path lives here, but its DOM is hidden under the overlay

## Solution — Option A (improved tap-to-start / tap-to-stop)
Same circular center button in the overlay; switch its state and wording so the *one* mic button doubles as Stop.

### UX
| State | Center button | Label / icon | Tap behavior |
|---|---|---|---|
| `recording` | Active, pulsing ring | "Tap to Stop" + stop-square icon | Calls `onStop` → flush + transcribe + close overlay |
| `processing` | Spinner | "Sending…" | Disabled |

- Secondary "Cancel" pill stays as-is — discards audio.
- Backdrop click is **removed** as a cancel trigger (too easy to mis-tap on mobile).
- 20-second hard cap: auto-stop and submit (no silence detection in this iteration).

### Code changes (live path uses Zustand `voiceStore`, NOT `useVoiceRecorder` hook)

1. **`apps/web/src/components/chat/VoiceOverlay.tsx`**
   - New props: `onStop: () => void` (required), keep `onCancel: () => void`.
   - Wrap the center circle in a `<button type="button" onClick={onStop} disabled={isProcessing}>`.
   - Swap mic icon for a stop-square SVG when `mode === 'recording'`.
   - Add visible label under the button: "Tap to Stop" / "Sending…".
   - Remove `onClick={onCancel}` from the backdrop `div`.

2. **`apps/web/src/components/ChatInterface/NewChatInterface.tsx`**
   - Add `handleVoiceStop` callback: `useVoiceStore.getState().stopRecording()` → `transcribe(sessionId, blob)` → `sendPipelined(text)`.
   - Pass `onStop={handleVoiceStop}` to `<VoiceOverlay>`.
   - Add a 20s auto-stop effect: when `voiceMode === 'recording'`, start a `setTimeout(handleVoiceStop, 20_000)`; clear it on mode change or unmount.

3. **`apps/web/src/stores/voiceStore.ts`** — no changes required for this iteration. Existing `startRecording`/`stopRecording`/`transcribe` are sufficient. (Auto-stop timer lives in the consumer to keep the store free of session-id coupling.)

4. **`apps/web/src/components/chat/VoiceButton.tsx`** — no changes for this iteration. User-tap path still works; if the user taps the overlay button instead, `NewChatInterface.handleVoiceStop` runs and the store transitions to idle, which the button observes via `useVoiceStore`.

### Out of scope
- Press-and-hold (walkie-talkie) interaction — deferred.
- Silence detection / VAD — deferred (hard cap is sufficient for this iteration).
- Refactoring duplicate `VoiceButton` components (`apps/web/src/components/VoiceButton/index.tsx` is unused by the live flow; leave alone).
- Permission re-prompt UX (already handled in `useVoiceRecorder.ts:103-112`).

## iPhone Safari Considerations
- `getUserMedia` must be called inside a user gesture. Current code at `voiceStore.ts:69` is awaited directly inside the click handler chain (no intermediary awaits). ✅ keep this pattern.
- iOS Safari supports `audio/mp4` only. MIME selection at `voiceStore.ts:72-74` already falls back to `audio/mp4`. ✅
- Existing bug noted: blob is named `recording.webm` regardless of MIME at `voiceStore.ts:134`. STT backend appears to accept either (works on desktop today). Out of scope for this branch but flagged.
- HTTPS required for mic access in production — already a project constraint per `CLAUDE.md`.

## Acceptance Criteria
1. On iPhone Safari, user can tap mic → grant permission → tap the overlay button → audio is transcribed and inserted into the input.
2. If the user does nothing for 20s after recording starts, recording auto-stops and submits.
3. "Cancel" pill still discards audio without calling STT.
4. Backdrop tap does **not** cancel the recording.
5. Existing Vitest suite for `useVoiceRecorder` still passes; new tests cover auto-stop and overlay stop path.
6. Existing Playwright `voice.spec.ts` extended with a "stop from overlay" assertion (where feasible — e2e mic mocking is limited; document gap if not testable headlessly).

## Verification Plan
- **Unit (Vitest):**
  - `useVoiceRecorder.test.ts` — new test: recorder auto-stops at 20s and resolves blob.
  - New `VoiceOverlay.test.tsx` — Stop button calls `onStop`; Cancel calls `onCancel`; backdrop click does NOT call cancel.
- **e2e (Playwright):** extend `voice.spec.ts` for overlay stop click (use mocked recorder if direct mic capture isn't testable in CI).
- **Manual (iPhone Safari):**
  - Record short utterance → tap stop → transcript appears in input.
  - Start recording, do nothing → auto-stops at 20s → transcript appears.
  - Cancel pill → no transcript, overlay closes.
  - Tap backdrop → no effect.

## Risks
- iOS Safari `requestData()` flush timing — if auto-stop produces an empty blob, fall back to `mediaRecorder.stop()` event handler aggregation (already handled by `chunksRef`).
- The unused secondary `VoiceButton` at `apps/web/src/components/VoiceButton/index.tsx` will diverge further from the live one. Acceptable for this iteration; flagged for future cleanup.
