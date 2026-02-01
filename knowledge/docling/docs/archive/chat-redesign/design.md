# Chat Redesign - Design Specification

> **Version:** 1.0
> **Created:** 2026-01-31
> **Inspiration:** Leesburg Animal Park visual aesthetic

---

## 1. Chat UX Audit (Mobile-First)

### Common Mobile Chatbot UX Issues

| Issue | Impact | Current State |
|-------|--------|---------------|
| Input obscured by keyboard | Users can't see recent messages while typing | Partially addressed, no safe-area handling |
| Tiny touch targets | Frustrating taps, accessibility failures | Good (buttons use scale effects) |
| No visual breathing room | Claustrophobic, overwhelming | Moderate—bubbles are dense |
| Unclear who's speaking | Confusion in long threads | ✅ Distinct user/assistant colors |
| No typing/thinking indicator | User assumes broken | ⚠️ Only skeleton shimmer |
| Scroll hijacking | Disorienting jumps | ✅ Auto-scroll on new message |
| Voice mode confusion | Unclear recording state | ⚠️ States exist but visually subtle |

### How This Redesign Improves Clarity, Comfort & Trust

1. **Generous negative space** — Bubbles breathe; no edge-to-edge cramming
2. **Calm color palette** — Earthy tones reduce cognitive load
3. **Clear voice state machine** — Distinct visual/audio feedback per state
4. **Warm typing indicator** — Animated dots in brand colors, not sterile spinner
5. **Sticky input with safe-area** — Keyboard-aware, always accessible
6. **Trust signals** — Zoocari logo persistent, source citations styled as friendly footnotes
7. **One-hand friendly** — Primary actions (send, voice) in thumb zone

---

## 2. Visual Design System (Chat-Optimized)

### Color Palette

```
ZOOCARI CHAT PALETTE
═══════════════════════════════════════════════════════════════

BACKGROUNDS
───────────
Canvas:        #FDFCFA   (warm white, main bg)
Surface:       #F7F5F2   (card/modal bg)
Elevated:      #FFFFFF   (input bar, floating elements)

CHAT BUBBLES
────────────
User:          #4A6741   (forest green)
User Text:     #FFFFFF
Assistant:     #F4F2EF   (warm beige, keep existing)
Assistant Text:#3D332A   (leesburg-brown, keep existing)

ACCENTS
───────
Primary CTA:   #4A6741   (forest green)
Primary Hover: #3D5636   (darker green)
Secondary:     #F5D224   (leesburg-yellow, highlights)
Info/Link:     #76B9DB   (leesburg-blue, keep)
Error:         #C45C4A   (warm terracotta)
Success:       #5D8A5A   (sage green)

TEXT
────
Primary:       #2D2620   (warm charcoal)
Secondary:     #6B635B   (muted brown)
Muted:         #9C948B   (placeholder, captions)

VOICE STATES
────────────
Idle:          #4A6741   (forest green)
Recording:     #E85D4A   (warm red pulse)
Processing:    #F5D224   (yellow shimmer)
Playing:       #76B9DB   (blue wave)
```

### Typography

**Font Stack:**
```css
--font-heading: 'Nunito', system-ui, sans-serif;
--font-body: 'Inter', system-ui, sans-serif;
```

**Why these fonts:**
- **Nunito** — Rounded, friendly, approachable for headers
- **Inter** — Highly legible at small sizes, excellent for chat bubbles

**Mobile-First Scale:**

| Element | Mobile | Desktop |
|---------|--------|---------|
| Header Title | 18px | 20px |
| Chat Bubble | 16px | 16px |
| Bubble Meta | 12px | 13px |
| Input Text | 16px | 16px |
| Followup Btn | 14px | 15px |
| Caption/Source | 12px | 12px |

**Critical:** Input must be **16px minimum** to prevent iOS zoom on focus.

### Spacing & Radius

```
SPACING TOKENS
──────────────
space-xs:    4px     (inline gaps)
space-sm:    8px     (bubble internal padding top/bottom)
space-md:    12px    (between messages same sender)
space-lg:    16px    (between message groups)
space-xl:    24px    (section gaps, container padding)
space-2xl:   32px    (header/footer padding)

RADIUS TOKENS
─────────────
radius-sm:   8px     (buttons, inputs)
radius-md:   16px    (cards, modals)
radius-lg:   20px    (chat bubbles)
radius-full: 9999px  (pills, avatars)

BUBBLE SHAPE
────────────
User bubble:      rounded-[20px] rounded-br-[4px]
Assistant bubble: rounded-[20px] rounded-bl-[4px]
(Tail on speaking side creates conversational flow)
```

---

## 3. Chat Interface Layout

### Mobile-First Wireframe

```
┌─────────────────────────────────────────┐
│  ┌─────────────────────────────────┐    │ ← Safe area top
│  │ 🐘 Zoocari          [🎤│⌨️]    │    │ ← Header (56px)
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │   👋 Welcome to Zoocari!        │    │ ← Welcome (conditional)
│  │   I'm here to answer your       │    │
│  │   questions about the animals   │    │
│  │   at Leesburg Animal Park.      │    │
│  │                                 │    │
│  │   [🦁 Lion] [🐘 Elephant]       │    │ ← Quick picks
│  │   [🦒 Giraffe] [🐫 Camel]       │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  ┌──────────────────────────┐   │    │
│  │  │ Tell me about elephants! │───│    │ ← User bubble (right)
│  │  └──────────────────────────┘   │    │
│  │                                 │    │
│  │ ┌───────────────────────────┐   │    │
│  │ │ 🐘                        │   │    │ ← Assistant bubble (left)
│  │ │ Elephants at Leesburg     │   │    │
│  │ │ Animal Park are African   │   │    │
│  │ │ elephants! They can...    │   │    │
│  │ │                           │   │    │
│  │ │ 📷 [image gallery]        │   │    │ ← Inline images
│  │ │ 📚 View sources           │   │    │ ← Collapsible
│  │ │                           │   │    │
│  │ │ [👍] [👎]                 │   │    │ ← Rating (subtle)
│  │ └───────────────────────────┘   │    │
│  │                                 │    │
│  │  ● ● ●                          │    │ ← Typing indicator
│  │                                 │    │
│  └─────────────────────────────────┘    │ ← Scroll container
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ [What do they eat?]             │    │ ← Follow-up chips
│  │ [How big are they?]             │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ ┌─────────────────────┐  [🎤]  │    │ ← Input bar (elevated)
│  │ │ Ask about animals...│  [➤]  │    │
│  │ └─────────────────────┘        │    │
│  └─────────────────────────────────┘    │
│                                         │ ← Safe area bottom
└─────────────────────────────────────────┘
```

### Component Breakdown

**Header (56px fixed)**
- Zoocari elephant logo (24px) + wordmark
- Mode toggle: voice/text (pill switch)
- Optional: session indicator dot (green = active)

**Message List**
- `flex-1 overflow-y-auto` with momentum scrolling
- `scroll-padding-bottom` to account for input bar
- Messages grouped by sender with reduced gap within groups

**Chat Bubbles**
- Max-width: 85% on mobile, 70% on desktop
- User: right-aligned, forest green, white text
- Assistant: left-aligned, warm beige, brown text
- Timestamp: hidden by default, shown on tap/long-press

**Input Composer (sticky bottom)**
- Elevated with subtle shadow
- Safe-area-inset-bottom padding
- Text input: 16px font, auto-grow up to 120px
- Voice button: prominent when in voice mode
- Send button: appears when text present

**Voice Mode Overlay**
```
┌─────────────────────────────────────────┐
│                                         │
│                                         │
│            ┌───────────┐                │
│            │           │                │
│            │   🎤      │ ← Pulsing ring │
│            │           │   when recording
│            └───────────┘                │
│                                         │
│         "Listening..."                  │
│                                         │
│           [Cancel]                      │
│                                         │
└─────────────────────────────────────────┘
```

### UX Considerations

**One-hand use:**
- All primary actions in bottom 40% of screen
- Voice button in bottom-right (right thumb zone)
- Swipe gestures avoided (conflict with system gestures)

**Long conversations:**
- "Jump to bottom" FAB appears when scrolled up
- Date separators for multi-day sessions
- New message indicator when scrolled up

**System/Status messages:**
- Centered, muted text (no bubble)
- Examples: "Session started", "Connection restored"
- Styled distinctly from chat content

---

## 4. Tailwind Implementation

### Tailwind Config Extension

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Existing Leesburg colors (keep)
        'leesburg-yellow': '#F5D224',
        'leesburg-brown': '#3D332A',
        'leesburg-beige': '#F4F2EF',
        'leesburg-orange': '#F29021',
        'leesburg-blue': '#76B9DB',

        // New semantic tokens
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
      },
      fontFamily: {
        'heading': ['Nunito', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'bubble': '20px',
        'bubble-tail': '4px',
      },
      spacing: {
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-top': 'env(safe-area-inset-top)',
      },
      animation: {
        'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typing-dot': 'typing-dot 1.4s infinite ease-in-out',
      },
      keyframes: {
        'pulse-ring': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(1.1)' },
        },
        'typing-dot': {
          '0%, 80%, 100%': { transform: 'translateY(0)' },
          '40%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
}
```

### Component Examples

See `implementation.md` for full component code snippets.

---

## 5. Zustand Store Architecture

### Recommended Store Boundaries

```
STORE ARCHITECTURE
═══════════════════════════════════════════════════════════════

UI STATE (ephemeral, not persisted)
───────────────────────────────────
uiStore.ts
├─ inputMode: 'voice' | 'text'
├─ isInputFocused: boolean
├─ showJumpToBottom: boolean
├─ expandedSources: Set<messageId>
├─ feedbackModalOpen: boolean
└─ feedbackMessageId: string | null

DOMAIN STATE (core data)
────────────────────────
chatStore.ts (existing, keep)
├─ messages: Message[]
├─ isLoading: boolean
├─ isStreaming: boolean
├─ streamingContent: string
├─ sources: Source[]
├─ followupQuestions: string[]
├─ ratings: Map<id, 'up'|'down'>
└─ error: string | null

voiceStore.ts (existing, refactor state machine)
├─ state: 'idle'|'recording'|'processing'|'playing'
├─ audioUrl: string | null
├─ transcribedText: string
├─ selectedVoice: VoiceId
└─ playbackQueue: AudioChunk[]

sessionStore.ts (existing, keep)
├─ sessionId: string
├─ session: Session | null
└─ isLoading: boolean
[persisted to localStorage]
```

### Key Architectural Decisions

1. **Separate UI from domain** — `uiStore` handles view-only state, preventing unnecessary re-renders
2. **Voice as state machine** — Single `state` field prevents impossible states
3. **Derived state over stored** — `showTypingIndicator` computed at render
4. **Session gates everything** — No chat/voice actions without valid `sessionId`

---

## 6. Motion & Feedback

### Animation Principles

- **Duration:** 150-250ms for UI, 300ms for content
- **Easing:** `ease-out` for entrances, `ease-in` for exits
- **Reduce motion:** Respect `prefers-reduced-motion`

### Specific Animations

**Message Arrival:**
```css
@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

**Typing Indicator:**
- Three dots with staggered bounce
- 1.4s duration, infinite

**Voice Recording Pulse:**
```css
@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(232, 93, 74, 0.4);
  }
  50% {
    box-shadow: 0 0 0 12px rgba(232, 93, 74, 0);
  }
}
```

### Loading States

| State | Visual |
|-------|--------|
| Initial load | Skeleton with shimmer |
| Message streaming | Typing indicator → fade to content |
| Voice processing | Pulsing mic icon + "Processing..." |
| Image loading | Blur placeholder → sharp |
| Error | Shake + terracotta border flash |

---

## 7. Accessibility & Testing

### Color Contrast (WCAG AA)

| Combination | Ratio | Pass |
|-------------|-------|------|
| User bubble (#FFF on #4A6741) | 5.2:1 | ✅ |
| Assistant bubble (#3D332A on #F4F2EF) | 9.1:1 | ✅ |
| Muted text (#9C948B on #FDFCFA) | 3.1:1 | ⚠️ Large text only |
| Primary CTA (#FFF on #4A6741) | 5.2:1 | ✅ |
| Error (#C45C4A on #FDFCFA) | 4.6:1 | ✅ |

**Action:** Bump muted text to `#7A746C` for 4.5:1 if used on small text.

### Touch Target Sizing

| Element | Minimum | Recommended | Design |
|---------|---------|-------------|--------|
| Buttons | 44×44px | 48×48px | 48×48px ✅ |
| Followup chips | 44px height | 48px | 44px ✅ |
| Rating buttons | 44×44px | — | 44×44px ✅ |
| Input field | 44px height | — | 48px ✅ |

### Screen Reader Considerations

- Live region for new messages (`aria-live="polite"`)
- Voice state announcements (`aria-live="assertive"`)
- Message list as `<ol role="log">`
- Proper button labels for all icons

### Playwright Mobile Tests

Required test coverage:
- Touch targets meet 44px minimum
- Input stays visible with keyboard open
- Messages scroll into view on arrival
- Voice recording shows visual feedback
- Respects prefers-reduced-motion
- Safe area insets applied on iOS

---

## Summary

| Before | After |
|--------|-------|
| Bright yellow bubbles | Calm forest green user bubbles |
| Dense message layout | Generous breathing room |
| Generic spinner | Friendly typing dots |
| Flat voice states | Clear visual state machine |
| Mixed touch targets | Consistent 48px buttons |

The forest green + warm beige palette creates a **nature-inspired calm** without being childish. The architecture cleanly separates UI state from domain logic, and all components are built mobile-first with accessibility baked in.
