# Chat Redesign - Implementation Plan

> **Created:** 2026-01-31
> **Estimated Phases:** 5
> **Parallel Agents:** Phase 2 runs 3 agents in parallel

---

## Phase Overview

```
Phase 1: Foundation (Sequential)
    │
    ▼
Phase 2: Components (3 Parallel Agents)
    ├── Agent A: Layout + Container
    ├── Agent B: Messages + Bubbles
    └── Agent C: Input + Voice
    │
    ▼
Phase 3: Integration (Sequential)
    │
    ▼
Phase 4: QA (Iterative: QA → Troubleshoot → Fix)
    │
    ▼
Phase 5: DevOps + Deploy
```

---

## Phase 1: Foundation

**Agent:** Frontend Agent (sequential)
**Dependencies:** None
**Output:** Tailwind config + fonts + UI store ready

### Tasks

| ID | Task | Description | Files |
|----|------|-------------|-------|
| 1.1 | Extend Tailwind config | Add all new color tokens, fonts, animations | `apps/web/tailwind.config.ts` |
| 1.2 | Add Google Fonts | Add Nunito + Inter to index.html | `apps/web/index.html` |
| 1.3 | Create UI store | New uiStore.ts for ephemeral UI state | `apps/web/src/stores/uiStore.ts` |
| 1.4 | Update voice store | Refactor to state machine pattern | `apps/web/src/stores/voiceStore.ts` |
| 1.5 | Verify build | Ensure `npm run build` passes | - |

### Acceptance Criteria

- [ ] New color tokens available: `chat-*`, `bubble-*`, `accent-*`, `text-*`, `voice-*`
- [ ] Fonts load correctly (check Network tab)
- [ ] UI store exports: `inputMode`, `isInputFocused`, `showJumpToBottom`, `expandedSources`
- [ ] Voice store has single `state` field instead of multiple booleans
- [ ] Build passes with no TypeScript errors

### Tailwind Config Changes

```typescript
// ADD to tailwind.config.ts theme.extend.colors:
'chat': {
  'canvas': '#FDFCFA',
  'surface': '#F7F5F2',
  'elevated': '#FFFFFF',
},
'bubble': {
  'user': '#4A6741',
  'user-text': '#FFFFFF',
  'assistant': '#F4F2EF',
  'assistant-text': '#3D332A',
},
'accent': {
  'primary': '#4A6741',
  'primary-hover': '#3D5636',
  'secondary': '#F5D224',
  'error': '#C45C4A',
  'success': '#5D8A5A',
},
'text': {
  'primary': '#2D2620',
  'secondary': '#6B635B',
  'muted': '#9C948B',
},
'voice': {
  'idle': '#4A6741',
  'recording': '#E85D4A',
  'processing': '#F5D224',
  'playing': '#76B9DB',
},

// ADD to theme.extend.fontFamily:
'heading': ['Nunito', 'system-ui', 'sans-serif'],
'body': ['Inter', 'system-ui', 'sans-serif'],

// ADD to theme.extend.borderRadius:
'bubble': '20px',
'bubble-tail': '4px',

// ADD to theme.extend.animation:
'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
'typing-dot': 'typing-dot 1.4s infinite ease-in-out',
'message-in': 'message-in 200ms ease-out',

// ADD to theme.extend.keyframes:
'pulse-ring': {
  '0%, 100%': { opacity: '1', transform: 'scale(1)' },
  '50%': { opacity: '0.5', transform: 'scale(1.1)' },
},
'typing-dot': {
  '0%, 80%, 100%': { transform: 'translateY(0)' },
  '40%': { transform: 'translateY(-6px)' },
},
'message-in': {
  from: { opacity: '0', transform: 'translateY(8px)' },
  to: { opacity: '1', transform: 'translateY(0)' },
},
```

---

## Phase 2: Components (Parallel)

**Agents:** 3 Frontend Agents in parallel
**Dependencies:** Phase 1 complete
**Output:** All new UI components created

### Agent A: Layout + Container

| ID | Task | Description | Files |
|----|------|-------------|-------|
| 2A.1 | Create ChatContainer | Main layout with header, messages, footer | `src/components/chat/ChatContainer.tsx` |
| 2A.2 | Create ChatHeader | Logo, mode toggle, session indicator | `src/components/chat/ChatHeader.tsx` |
| 2A.3 | Create ModeToggle | Voice/text pill switch | `src/components/chat/ModeToggle.tsx` |
| 2A.4 | Create ScrollToBottom | FAB that appears when scrolled up | `src/components/chat/ScrollToBottom.tsx` |
| 2A.5 | Update WelcomeMessage | Restyle with new design tokens | `src/components/WelcomeMessage.tsx` |

**Acceptance:**
- [ ] ChatContainer fills viewport with safe-area handling
- [ ] Header is 56px, sticky at top
- [ ] Mode toggle switches between voice/text
- [ ] ScrollToBottom FAB appears when scrolled up >100px

### Agent B: Messages + Bubbles

| ID | Task | Description | Files |
|----|------|-------------|-------|
| 2B.1 | Create UserBubble | Green, right-aligned, tail on bottom-right | `src/components/chat/UserBubble.tsx` |
| 2B.2 | Create AssistantBubble | Beige, left-aligned, with sources/rating | `src/components/chat/AssistantBubble.tsx` |
| 2B.3 | Create TypingIndicator | 3 bouncing dots animation | `src/components/chat/TypingIndicator.tsx` |
| 2B.4 | Create MessageList | Scrollable container with grouping | `src/components/chat/MessageList.tsx` |
| 2B.5 | Create SystemMessage | Centered, muted status messages | `src/components/chat/SystemMessage.tsx` |

**Acceptance:**
- [ ] User bubbles: max-width 85%, green bg, white text
- [ ] Assistant bubbles: max-width 85%, beige bg, brown text
- [ ] Bubbles have correct tail direction (rounded-br-[4px] vs rounded-bl-[4px])
- [ ] Typing indicator animates with staggered delays
- [ ] Messages animate in with message-in animation

### Agent C: Input + Voice

| ID | Task | Description | Files |
|----|------|-------------|-------|
| 2C.1 | Create InputBar | Text input + voice/send buttons | `src/components/chat/InputBar.tsx` |
| 2C.2 | Create VoiceOverlay | Full-screen recording overlay | `src/components/chat/VoiceOverlay.tsx` |
| 2C.3 | Create FollowupChips | Horizontal scrolling chip list | `src/components/chat/FollowupChips.tsx` |
| 2C.4 | Create VoiceButton | Mic button with state colors | `src/components/chat/VoiceButton.tsx` |
| 2C.5 | Create SendButton | Arrow button, appears when text present | `src/components/chat/SendButton.tsx` |

**Acceptance:**
- [ ] InputBar sticky at bottom with safe-area padding
- [ ] Input auto-grows up to 120px height
- [ ] Voice button shows correct color per state (idle/recording/processing)
- [ ] VoiceOverlay shows pulsing animation when recording
- [ ] Followup chips scroll horizontally on overflow

---

## Phase 3: Integration

**Agent:** Frontend Agent (sequential)
**Dependencies:** Phase 2 complete
**Output:** New components wired up and replacing old UI

### Tasks

| ID | Task | Description | Files |
|----|------|-------------|-------|
| 3.1 | Wire ChatContainer | Connect to chatStore, voiceStore, uiStore | `src/components/chat/ChatContainer.tsx` |
| 3.2 | Replace ChatInterface | Swap old ChatInterface with new ChatContainer | `src/App.tsx` |
| 3.3 | Integrate voice flow | Connect VoiceOverlay/VoiceButton to voiceStore | Multiple |
| 3.4 | Integrate message flow | Connect MessageList to chatStore | Multiple |
| 3.5 | Add accessibility | aria-live regions, roles, labels | Multiple |
| 3.6 | Add animations | message-in, reduced-motion support | Multiple |
| 3.7 | Polish & edge cases | Empty states, error states, long messages | Multiple |

### Acceptance Criteria

- [ ] All existing functionality preserved (send message, voice record, TTS playback)
- [ ] Messages render correctly from chatStore
- [ ] Voice states trigger correct UI updates
- [ ] Followup questions appear after assistant response
- [ ] Sources collapsible in assistant bubbles
- [ ] Rating buttons work (thumbs up/down)
- [ ] Reduced motion respected via media query
- [ ] No console errors or warnings

---

## Phase 4: QA (Iterative)

**Agents:** QA Agent → Troubleshoot Agent → Frontend Agent (loop)
**Dependencies:** Phase 3 complete
**Output:** All tests passing, accessibility verified

### QA Tasks

| ID | Task | Description |
|----|------|-------------|
| 4.1 | Unit tests | Run `npm run test` - all components covered |
| 4.2 | Playwright mobile | Run mobile E2E tests (Chrome, Safari) |
| 4.3 | Accessibility audit | Check color contrast, touch targets, screen reader |
| 4.4 | Cross-browser | Verify Chrome, Safari, Firefox on desktop |
| 4.5 | Performance | Check bundle size, no layout thrashing |

### Required Playwright Tests

```typescript
// tests/e2e/chat-redesign.spec.ts

describe('Mobile Chat UX', () => {
  test('touch targets meet 44px minimum');
  test('input stays visible with keyboard open');
  test('messages scroll into view on arrival');
  test('voice recording shows visual feedback');
  test('respects prefers-reduced-motion');
  test('safe area insets applied');
  test('user bubble styled correctly');
  test('assistant bubble styled correctly');
  test('typing indicator animates');
  test('followup chips are tappable');
});
```

### Acceptance Criteria

- [ ] All unit tests pass
- [ ] All Playwright tests pass
- [ ] Color contrast WCAG AA (verified with tool)
- [ ] Touch targets >= 44px (verified in Playwright)
- [ ] No accessibility violations (axe-core or similar)
- [ ] Bundle size not increased by >10%

### Troubleshoot Loop

```
QA finds issue → Document in qa-report.md
    → Troubleshoot agent diagnoses
    → Frontend agent fixes
    → QA re-tests
    → Repeat until all pass
```

---

## Phase 5: DevOps + Deploy

**Agent:** DevOps Agent
**Dependencies:** Phase 4 complete (all tests passing)
**Output:** Production deployment

### Tasks

| ID | Task | Description |
|----|------|-------------|
| 5.1 | Production build | `npm run build` in apps/web |
| 5.2 | Docker verification | Rebuild web container, verify locally |
| 5.3 | Staging deploy | Deploy to staging environment |
| 5.4 | Staging smoke test | Manual verification on staging |
| 5.5 | Production deploy | Deploy to production |
| 5.6 | Production verify | Verify production is working |
| 5.7 | Update ProjectPlan | Mark feature complete, move to archive |

### Acceptance Criteria

- [ ] Production build completes without errors
- [ ] Docker container starts and serves correctly
- [ ] Staging environment shows new design
- [ ] Production environment shows new design
- [ ] No regressions in existing functionality
- [ ] ProjectPlan.md updated

---

## Component Code Reference

### ChatContainer

```tsx
<div className="flex flex-col h-[100dvh] bg-chat-canvas font-body text-text-primary">
  <ChatHeader />
  <main className="flex-1 overflow-y-auto overscroll-contain px-4 py-4">
    <MessageList />
  </main>
  <footer className="sticky bottom-0 bg-chat-elevated border-t border-black/5 pb-safe-bottom">
    <FollowupChips />
    <InputBar />
  </footer>
  {showVoiceOverlay && <VoiceOverlay />}
</div>
```

### UserBubble

```tsx
<div className="flex justify-end">
  <div className="max-w-[85%] sm:max-w-[70%] bg-bubble-user text-bubble-user-text rounded-bubble rounded-br-bubble-tail px-4 py-3 shadow-sm animate-message-in">
    <p className="text-base leading-relaxed whitespace-pre-wrap">{content}</p>
  </div>
</div>
```

### AssistantBubble

```tsx
<div className="flex gap-2 max-w-[85%] sm:max-w-[70%]">
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-sm">
    🐘
  </div>
  <div className="bg-bubble-assistant text-bubble-assistant-text rounded-bubble rounded-bl-bubble-tail px-4 py-3 shadow-sm animate-message-in">
    <p className="text-base leading-relaxed whitespace-pre-wrap">{content}</p>
    {sources && <SourcesCollapsible sources={sources} />}
    <RatingButtons messageId={id} />
  </div>
</div>
```

### TypingIndicator

```tsx
<div className="flex gap-2 max-w-[85%]">
  <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-sm">
    🐘
  </div>
  <div className="bg-bubble-assistant rounded-bubble rounded-bl-bubble-tail px-4 py-3 flex items-center gap-1">
    <span className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot" style={{ animationDelay: '0ms' }} />
    <span className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot" style={{ animationDelay: '160ms' }} />
    <span className="w-2 h-2 rounded-full bg-accent-primary animate-typing-dot" style={{ animationDelay: '320ms' }} />
  </div>
</div>
```

### InputBar

```tsx
<div className="flex items-end gap-2 px-4 py-3">
  <div className="flex-1 flex items-center bg-chat-surface rounded-full border border-black/10 focus-within:border-accent-primary focus-within:ring-2 focus-within:ring-accent-primary/20 transition-all px-4 py-2">
    <textarea
      className="flex-1 bg-transparent text-base text-text-primary placeholder:text-text-muted resize-none outline-none min-h-[24px] max-h-[120px]"
      placeholder="Ask about animals..."
      rows={1}
    />
  </div>
  <VoiceButton />
  {hasText && <SendButton />}
</div>
```

---

## File Structure (After Implementation)

```
apps/web/src/
├── components/
│   ├── chat/
│   │   ├── ChatContainer.tsx      (NEW)
│   │   ├── ChatHeader.tsx         (NEW)
│   │   ├── MessageList.tsx        (NEW)
│   │   ├── UserBubble.tsx         (NEW)
│   │   ├── AssistantBubble.tsx    (NEW)
│   │   ├── TypingIndicator.tsx    (NEW)
│   │   ├── InputBar.tsx           (NEW)
│   │   ├── VoiceButton.tsx        (NEW - replaces old)
│   │   ├── VoiceOverlay.tsx       (NEW)
│   │   ├── SendButton.tsx         (NEW)
│   │   ├── FollowupChips.tsx      (NEW - replaces FollowupQuestions)
│   │   ├── ModeToggle.tsx         (NEW)
│   │   ├── ScrollToBottom.tsx     (NEW)
│   │   ├── SystemMessage.tsx      (NEW)
│   │   └── index.ts               (exports)
│   ├── WelcomeMessage.tsx         (UPDATED)
│   ├── AnimalGrid.tsx             (UPDATED styling)
│   └── ... (other existing)
├── stores/
│   ├── chatStore.ts               (existing)
│   ├── voiceStore.ts              (UPDATED - state machine)
│   ├── sessionStore.ts            (existing)
│   └── uiStore.ts                 (NEW)
└── ...
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Keep old ChatInterface until Phase 3 complete, feature flag if needed |
| Voice store refactor breaks audio | Add unit tests for voice state machine before refactoring |
| Performance regression | Measure bundle size before/after, use React.memo |
| Accessibility gaps | Run axe-core in CI, add Playwright a11y tests |

---

## Success Metrics

- [ ] All existing E2E tests still pass
- [ ] New mobile-specific tests pass
- [ ] Lighthouse accessibility score >= 95
- [ ] Bundle size increase < 10%
- [ ] User feedback positive (if collecting)
