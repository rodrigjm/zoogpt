# Mobile Mic Stop Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the mobile voice recording overlay's center button interactive so users can stop and submit a recording, and add a 20-second auto-stop safety net.

**Architecture:** The live voice flow uses the Zustand `voiceStore` (not the unused `useVoiceRecorder` hook). `VoiceOverlay` becomes interactive — its center mic-circle gains an `onStop` handler. `NewChatInterface` owns a new `handleVoiceStop` callback that runs `stopRecording → transcribe → sendPipelined`, plus a 20s auto-stop timer that calls the same handler. No store changes — the timer lives in the consumer to avoid coupling the store to `sessionId`.

**Tech Stack:** React 18, TypeScript, Zustand, Vitest, React Testing Library, Tailwind CSS, Playwright (for e2e — limited by mic permission constraints).

**Branch:** `fix/mobile-mic-stop-recording` (already created off `origin/main`).

**Spec:** `docs/active/mobile-mic-stop-fix/design.md`

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `apps/web/src/components/chat/VoiceOverlay.tsx` | Modify | UI: render interactive Stop button while recording; wire `onStop`; remove backdrop cancel |
| `apps/web/src/components/chat/__tests__/VoiceOverlay.test.tsx` | Create | Vitest coverage for Stop / Cancel / backdrop / processing states |
| `apps/web/src/components/ChatInterface/NewChatInterface.tsx` | Modify | Provide `handleVoiceStop`, wire to overlay, register 20s auto-stop timer |
| `docs/active/mobile-mic-stop-fix/implementation.md` | Create | Append-only execution log per CLAUDE.md workflow |
| `docs/ProjectPlan.md` | Modify | Add to "Active Features" section |

---

## Task 1: Make `VoiceOverlay` Stop Button Interactive (TDD)

**Files:**
- Create: `apps/web/src/components/chat/__tests__/VoiceOverlay.test.tsx`
- Modify: `apps/web/src/components/chat/VoiceOverlay.tsx` (entire file rewrite — keep existing imports/structure)

### Step 1.1: Write the failing tests

- [ ] Create test file with the content below.

```tsx
// apps/web/src/components/chat/__tests__/VoiceOverlay.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import VoiceOverlay from '../VoiceOverlay';
import { useVoiceStore } from '../../../stores/voiceStore';

// Helper to set the voice store's mode for a test
function setVoiceMode(mode: 'idle' | 'recording' | 'processing' | 'playing') {
  useVoiceStore.setState({ mode });
}

describe('VoiceOverlay', () => {
  beforeEach(() => {
    useVoiceStore.getState().reset();
  });

  it('renders a "Tap to Stop" button while recording', () => {
    setVoiceMode('recording');
    render(<VoiceOverlay onStop={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole('button', { name: /stop recording/i })).toBeInTheDocument();
    expect(screen.getByText(/tap to stop/i)).toBeInTheDocument();
  });

  it('calls onStop when the center stop button is tapped', () => {
    setVoiceMode('recording');
    const onStop = vi.fn();
    render(<VoiceOverlay onStop={onStop} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /stop recording/i }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when the cancel pill is tapped', () => {
    setVoiceMode('recording');
    const onCancel = vi.fn();
    render(<VoiceOverlay onStop={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole('button', { name: /^cancel$/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('does NOT call onCancel when the backdrop is tapped', () => {
    setVoiceMode('recording');
    const onCancel = vi.fn();
    const { container } = render(<VoiceOverlay onStop={vi.fn()} onCancel={onCancel} />);
    // The backdrop is the outermost div with the fixed inset-0 class
    const backdrop = container.querySelector('div.fixed.inset-0');
    expect(backdrop).not.toBeNull();
    fireEvent.click(backdrop!);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it('disables the stop button while processing and shows "Sending…"', () => {
    setVoiceMode('processing');
    render(<VoiceOverlay onStop={vi.fn()} onCancel={vi.fn()} />);
    const stopButton = screen.getByRole('button', { name: /processing/i });
    expect(stopButton).toBeDisabled();
    expect(screen.getByText(/sending/i)).toBeInTheDocument();
  });
});
```

### Step 1.2: Run tests and confirm they fail

- [ ] Run the new test file.

```bash
cd apps/web && npx vitest run src/components/chat/__tests__/VoiceOverlay.test.tsx
```

Expected: FAIL — current `VoiceOverlay` does not accept `onStop`, has no interactive stop button, has no "Tap to Stop" text, and the backdrop currently calls `onCancel`.

### Step 1.3: Rewrite `VoiceOverlay.tsx` to satisfy the tests

- [ ] Replace the entire contents of `apps/web/src/components/chat/VoiceOverlay.tsx` with:

```tsx
import React from 'react';
import { useVoiceStore } from '../../stores/voiceStore';

interface VoiceOverlayProps {
  onStop: () => void;
  onCancel: () => void;
}

export default function VoiceOverlay({ onStop, onCancel }: VoiceOverlayProps) {
  const mode = useVoiceStore((state) => state.mode);

  const isRecording = mode === 'recording';
  const isProcessing = mode === 'processing';

  const stopAriaLabel = isProcessing ? 'Processing audio' : 'Stop recording';
  const stopLabel = isProcessing ? 'Sending…' : 'Tap to Stop';

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-8">
        {/* Big interactive stop button (replaces the previously decorative mic) */}
        <button
          type="button"
          onClick={onStop}
          disabled={isProcessing}
          aria-label={stopAriaLabel}
          className={`
            relative w-32 h-32 rounded-full flex items-center justify-center
            ${isRecording ? 'bg-voice-recording animate-pulse-ring' : 'bg-voice-processing'}
            shadow-2xl active:scale-95 transition-transform duration-150
            disabled:cursor-not-allowed
          `}
        >
          {isProcessing ? (
            <svg
              className="w-16 h-16 text-white animate-spin"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            // Stop-square glyph
            <span className="block w-12 h-12 rounded-md bg-white" aria-hidden="true" />
          )}
        </button>

        {/* Status / instruction text */}
        <p className="text-2xl font-heading font-semibold text-white drop-shadow-lg">
          {stopLabel}
        </p>

        {/* Secondary cancel pill */}
        <button
          onClick={onCancel}
          disabled={isProcessing}
          className="
            px-8 py-3 rounded-full
            bg-white/20 hover:bg-white/30
            text-white font-body font-medium
            backdrop-blur-sm transition-all duration-200
            active:scale-95 disabled:opacity-50
          "
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
```

### Step 1.4: Run tests and confirm they pass

- [ ] Re-run the test file.

```bash
cd apps/web && npx vitest run src/components/chat/__tests__/VoiceOverlay.test.tsx
```

Expected: 5 tests PASS.

### Step 1.5: Commit

- [ ] Stage and commit.

```bash
git add apps/web/src/components/chat/VoiceOverlay.tsx \
         apps/web/src/components/chat/__tests__/VoiceOverlay.test.tsx
git commit -m "$(cat <<'EOF'
fix(voice): interactive Stop in VoiceOverlay (mobile)

The overlay covered the InputBar mic button with no interactive stop
control, leaving mobile users unable to end a recording. The center
mic graphic is now a real button wired to onStop, with a "Tap to Stop"
label and a stop-square glyph. Backdrop tap no longer cancels.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Wire `onStop` and 20s Auto-Stop in `NewChatInterface`

**Files:**
- Modify: `apps/web/src/components/ChatInterface/NewChatInterface.tsx`
  - Add `handleVoiceStop` callback (around the existing `handleVoiceCancel` at line 162)
  - Add a 20s auto-stop `useEffect` watching `voiceMode`
  - Update the `<VoiceOverlay>` call site (line 274–276) to pass `onStop`

### Step 2.1: Add the `handleVoiceStop` callback

- [ ] In `NewChatInterface.tsx`, find `handleVoiceCancel` (line ~162) and add `handleVoiceStop` directly above it.

Locate this block in `apps/web/src/components/ChatInterface/NewChatInterface.tsx` (around line 161–165):

```tsx
  // Handle voice overlay cancel
  const handleVoiceCancel = useCallback(() => {
    // Voice store will handle the state reset
    useVoiceStore.getState().reset();
  }, []);
```

Replace it with:

```tsx
  // Handle voice overlay stop — flush recording, transcribe, then send through pipelined TTS.
  // Used by the overlay's Stop button AND by the 20s auto-stop timer.
  const handleVoiceStop = useCallback(async () => {
    if (!sessionId) return;
    const store = useVoiceStore.getState();
    if (store.mode !== 'recording') return; // already stopped or never started
    try {
      const blob = await store.stopRecording();
      if (!blob) return;
      const text = await store.transcribe(sessionId, blob);
      if (text && text.trim()) {
        sendPipelined(text.trim());
      }
    } catch (err) {
      console.error('Voice stop/transcribe failed:', err);
      useVoiceStore.getState().reset();
    }
  }, [sessionId, sendPipelined]);

  // Handle voice overlay cancel
  const handleVoiceCancel = useCallback(() => {
    // Voice store will handle the state reset
    useVoiceStore.getState().reset();
  }, []);
```

### Step 2.2: Add the 20s auto-stop effect

- [ ] Immediately after `handleVoiceCancel` is defined (still in `NewChatInterface`), add:

```tsx
  // Safety net: auto-stop and submit any recording that runs longer than 20s
  // (kids' answers are short; this prevents stuck recordings on mobile).
  useEffect(() => {
    if (voiceMode !== 'recording') return;
    const MAX_RECORDING_MS = 20_000;
    const timer = setTimeout(() => {
      handleVoiceStop();
    }, MAX_RECORDING_MS);
    return () => clearTimeout(timer);
  }, [voiceMode, handleVoiceStop]);
```

### Step 2.3: Pass `onStop` to `<VoiceOverlay>`

- [ ] Find the overlay render site (around line 273–276):

```tsx
      {/* Voice overlay */}
      {showVoiceOverlay && (
        <VoiceOverlay onCancel={handleVoiceCancel} />
      )}
```

Replace with:

```tsx
      {/* Voice overlay */}
      {showVoiceOverlay && (
        <VoiceOverlay onStop={handleVoiceStop} onCancel={handleVoiceCancel} />
      )}
```

### Step 2.4: Run the existing test suite to confirm no regressions

- [ ] Run all web unit tests.

```bash
cd apps/web && npx vitest run
```

Expected: all tests PASS, including the new `VoiceOverlay.test.tsx` from Task 1. If any existing test referencing `VoiceOverlay` breaks because it instantiated the component without `onStop`, update it to pass `onStop={vi.fn()}`.

### Step 2.5: Type-check

- [ ] Run TypeScript build.

```bash
cd apps/web && npx tsc --noEmit
```

Expected: 0 errors. (`VoiceOverlay`'s new `onStop` is required, so any caller missing it will surface here.)

### Step 2.6: Commit

- [ ] Stage and commit.

```bash
git add apps/web/src/components/ChatInterface/NewChatInterface.tsx
git commit -m "$(cat <<'EOF'
fix(voice): wire overlay onStop + 20s auto-stop safety net

NewChatInterface now owns handleVoiceStop, which runs stopRecording →
transcribe → sendPipelined. The overlay's new Stop button calls it,
and a useEffect auto-fires it 20s after recording starts so a stuck
mobile recording self-submits instead of trapping the user.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Verification — Local Dev Server + iPhone Safari

**Files:**
- Modify: `docs/active/mobile-mic-stop-fix/qa-report.md` (create if missing)

### Step 3.1: Start the dev server

- [ ] Start the web app locally.

```bash
cd apps/web && npm run dev
```

Expected: dev server running, prints local + network URLs (e.g., `https://localhost:5173` and `https://<lan-ip>:5173`). Confirm HTTPS — without it the iPhone will refuse mic access.

### Step 3.2: Manual desktop sanity test (Chrome)

- [ ] Open the local URL in desktop Chrome. Click the mic button. Verify:
  - Permission prompt appears (first time only).
  - Overlay opens with red pulsing circle and "Tap to Stop" label.
  - Tap the big circle → overlay closes, message is sent and a response streams.
  - Repeat: start recording, wait 20s without doing anything → overlay auto-closes and a (likely empty/short) message is submitted.
  - Repeat: start recording, tap "Cancel" → overlay closes, no message sent.

### Step 3.3: iPhone Safari test

- [ ] Connect iPhone to the same Wi-Fi as the dev machine. Open the LAN HTTPS URL in Safari (accept the self-signed cert if prompted). Run the same three flows:
  - Stop via center button — works.
  - 20s auto-stop — works.
  - Cancel pill — works.
  - Backdrop tap — does NOT close/cancel.

### Step 3.4: Document results

- [ ] Create `docs/active/mobile-mic-stop-fix/qa-report.md` with the content below, filling in actual results.

```markdown
# QA Report — Mobile Mic Stop Fix

**Date:** YYYY-MM-DD
**Tester:** [name]
**Branch:** fix/mobile-mic-stop-recording
**Build:** [git short SHA]

## Vitest
- VoiceOverlay.test.tsx: PASS (5/5)
- Full suite: [PASS/FAIL — paste failing names if any]

## TypeScript
- `tsc --noEmit`: 0 errors

## Manual — Desktop Chrome
- [ ] Tap-to-stop submits transcript
- [ ] 20s auto-stop submits
- [ ] Cancel discards
- [ ] Backdrop tap does nothing

## Manual — iPhone Safari (model + iOS version: ____)
- [ ] Permission prompt accepted
- [ ] Tap-to-stop submits transcript
- [ ] 20s auto-stop submits
- [ ] Cancel discards
- [ ] Backdrop tap does nothing

## Issues Found
[None / list any]
```

### Step 3.5: Commit QA report and update tracking

- [ ] Update `docs/ProjectPlan.md` to add this feature under "Active Features" with a link to `docs/active/mobile-mic-stop-fix/`.

- [ ] Stage and commit.

```bash
git add docs/active/mobile-mic-stop-fix/qa-report.md docs/ProjectPlan.md
git commit -m "$(cat <<'EOF'
docs(voice): QA report + ProjectPlan entry for mobile mic stop fix

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Step 3.6: Push branch

- [ ] Push the branch to origin (do NOT open the PR until the user requests it).

```bash
git push -u origin fix/mobile-mic-stop-recording
```

---

## Self-Review

**Spec coverage:**
| Spec requirement | Task |
|---|---|
| Center mic becomes interactive Stop | Task 1 |
| Same button, switched wording (`Tap to Stop` / `Sending…`) | Task 1 |
| Backdrop tap no longer cancels | Task 1 (test + impl) |
| Overlay receives `onStop` prop | Task 1 + Task 2 wiring |
| 20s hard cap | Task 2 (Step 2.2) |
| Cancel still discards | Task 1 (kept) + Task 2 (handleVoiceCancel unchanged) |
| iPhone Safari verification | Task 3 |
| No changes to `voiceStore` (consumer owns timer) | Task 2 architecture |
| `useVoiceRecorder` hook untouched | Confirmed not in live path |

**Placeholder scan:** none.

**Type consistency:** `onStop: () => void`, `onCancel: () => void` — used identically in test, component, and call site. `handleVoiceStop` is `useCallback(async () => …, [sessionId, sendPipelined])` — both deps already exist in `NewChatInterface`.

---

## Execution Notes

- Existing duplicate `VoiceButton` at `apps/web/src/components/VoiceButton/index.tsx` is **not** in the live path — leave alone.
- `apps/web/e2e/voice.spec.ts` cannot be meaningfully extended (no real mic in headless CI); skip e2e changes.
- `apps/web/src/hooks/useVoiceRecorder.ts` is **not** touched — the live path is the Zustand `voiceStore`.
