# Feature: Mobile Mic Stop Fix

> **Status:** 🔄 In Progress
> **Started:** 2026-05-01
> **Owner:** main agent
> **Branch:** `fix/mobile-mic-stop-recording`

## Overview
Mobile users (iPhone Safari in particular) cannot stop a voice recording once it starts. The full-screen `VoiceOverlay` covers the InputBar's mic button, and the overlay's center mic icon has no click handler — only a "Cancel" pill exists, which discards the audio.

## Goals
- Make the overlay's center mic button interactive — tap = stop + submit
- Add a 20s hard cap so a stuck recording auto-submits
- Verify on iPhone Safari (record → stop → transcribe)

## Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Research | ✅ Done | Root cause: overlay covers stop control; center icon decorative |
| Design | ✅ Done | See `design.md` |
| Implementation | ⬜ Pending | |
| QA | ⬜ Pending | iPhone Safari + Vitest + Playwright |
| Deployment | ⬜ Pending | |

## Files in this Directory
- `README.md` — this file
- `design.md` — technical design and acceptance criteria

## Related
- `apps/web/src/components/chat/VoiceOverlay.tsx` — needs Stop affordance
- `apps/web/src/components/chat/VoiceButton.tsx` — current tap-to-toggle source of truth
- `apps/web/src/components/ChatInterface/NewChatInterface.tsx` — wires overlay
- `apps/web/src/hooks/useVoiceRecorder.ts` — start/stop primitives
