# Zoocari Design Specification
## Voice-First, Kid-Friendly Zoo Chatbot

---

## 1. Current State Analysis

### Strengths
- Strong brand identity (Leesburg Animal Park colors/fonts)
- Good persona (Zoocari the elephant)
- Voice STT/TTS integration working
- Follow-up questions encourage exploration

### Issues Identified
| Issue | Impact | Priority |
|-------|--------|----------|
| Voice button not centered/prominent | Kids miss primary CTA | Critical |
| Two-panel layout confusing on mobile | Poor mobile UX | Critical |
| Small toggle for voice mode | Hard to discover | High |
| Text input as default | Against voice-first goal | High |
| Welcome message text-heavy | Not engaging for kids | Medium |
| Quick questions buried below input | Low discoverability | Medium |

---

## 2. Design Principles for Kids (6-12)

```
1. BIG & COLORFUL    - Large touch targets, vibrant colors
2. VOICE-FIRST       - Speaking is natural for kids
3. VISUAL FEEDBACK   - Animations show what's happening
4. SIMPLE HIERARCHY  - One clear action at a time
5. PLAYFUL           - Fun interactions, not boring forms
6. FORGIVING         - Easy to undo, no dead ends
```

---

## 3. Proposed Architecture

### Layout: Single-Column Mobile-First

```
┌─────────────────────────────────┐
│  ┌─────────────────────────┐    │
│  │    ZOOCARI MASCOT       │    │  <- Friendly face first
│  │    "Hi! I'm Zoocari!"   │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │                         │    │
│  │   ████████████████      │    │  <- GIANT voice button
│  │   ██  TALK TO ME  ██    │    │     Primary CTA
│  │   ████████████████      │    │     140-180px diameter
│  │                         │    │
│  │   "Hold & Talk!"        │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │  Or tap an animal:      │    │  <- Quick questions
│  │  🦁 🐘 🦒 🐪 🦘 🐆       │    │     as animal icons
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │  [Type instead...]      │    │  <- Secondary: text input
│  └─────────────────────────┘    │     collapsed by default
│                                 │
│  ┌─────────────────────────┐    │
│  │    RESPONSE AREA        │    │  <- Zoocari's answer
│  │    with audio player    │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

---

## 4. Voice Button Design Specification

### Primary CTA: "Talk to Zoocari" Button

```
┌────────────────────────────────────────┐
│                                        │
│         ╭──────────────────╮           │
│        ╱                    ╲          │
│       │   ┌──────────────┐   │         │
│       │   │              │   │         │  <- Outer glow ring
│       │   │   🎙️ MIC     │   │         │     (pulses when ready)
│       │   │   ICON       │   │         │
│       │   │              │   │         │
│       │   └──────────────┘   │         │
│        ╲                    ╱          │
│         ╰──────────────────╯           │
│                                        │
│        "Talk to Zoocari!"              │  <- Inviting label
│        Hold the button & speak         │  <- Clear instruction
│                                        │
└────────────────────────────────────────┘
```

### Button States

| State | Visual | Feedback |
|-------|--------|----------|
| **Idle** | Yellow/gold gradient (#f5d224 → #e8c41f) | Gentle pulse glow |
| **Hover** | Scale 1.05x, brighter | Cursor pointer |
| **Recording** | Orange/red (#f29021 → #e63946) | Active pulse animation, "Listening..." |
| **Processing** | Gray with spinner | "Thinking..." |
| **Success** | Green flash | Checkmark, play audio |

### CSS Specification

```css
.zoocari-voice-btn {
  /* Size: Large and tappable */
  width: 160px;
  height: 160px;
  border-radius: 50%;

  /* Colors: Leesburg yellow */
  background: linear-gradient(145deg, #f5d224 0%, #e8c41f 100%);

  /* Depth & Presence */
  box-shadow:
    0 8px 32px rgba(245, 210, 36, 0.4),      /* Drop shadow */
    0 0 0 6px rgba(245, 210, 36, 0.2),        /* Outer ring */
    inset 0 2px 4px rgba(255, 255, 255, 0.3); /* Inner highlight */

  /* Animation */
  transition: all 0.2s ease;
  animation: gentle-pulse 2s ease-in-out infinite;
}

.zoocari-voice-btn:hover {
  transform: scale(1.08);
  box-shadow:
    0 12px 40px rgba(245, 210, 36, 0.5),
    0 0 0 8px rgba(245, 210, 36, 0.3),
    inset 0 2px 4px rgba(255, 255, 255, 0.3);
}

.zoocari-voice-btn.recording {
  background: linear-gradient(145deg, #f29021 0%, #e63946 100%);
  animation: recording-pulse 0.8s ease-in-out infinite;
}

@keyframes gentle-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 210, 36, 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(245, 210, 36, 0); }
}

@keyframes recording-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

### Microphone Icon

```svg
<!-- Kid-friendly rounded microphone -->
<svg viewBox="0 0 24 24" width="64" height="64">
  <path fill="#3d332a" d="
    M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z
    M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08
    c3.39-.49 6-3.39 6-6.92h-2z
  "/>
</svg>
```

---

## 5. Quick Questions as Animal Buttons

### Current (Text-Heavy)
```
⚡ Quick:
[🐒 Lemurs] [🐪 Camels] [🦘 Emus]
```

### Proposed (Visual-First)
```
Pick an animal to learn about!

  🦁      🐘      🦒      🐪
 Lion   Elephant Giraffe  Camel

  🦘      🐆      🦔      🐒
  Emu   Serval  Porcupine Lemur
```

### Button Style
```css
.animal-btn {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  background: white;
  border: 3px solid var(--leesburg-yellow);
  font-size: 2rem;  /* Large emoji */
  transition: all 0.2s ease;
}

.animal-btn:hover, .animal-btn:active {
  transform: scale(1.1);
  background: var(--leesburg-yellow);
  border-color: var(--leesburg-orange);
}

.animal-btn-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--leesburg-brown);
  margin-top: 4px;
}
```

---

## 6. Welcome State (Voice-First)

### Current Welcome (Text-Heavy)
```
👋 Welcome, Young Explorer!
I'm Zoocari the Elephant, and I LOVE helping kids learn...
[Long paragraph of text]
```

### Proposed Welcome (Action-Oriented)

```
┌─────────────────────────────────────┐
│                                     │
│         [Zoocari Mascot]            │
│              🐘                      │
│                                     │
│    "Hi! I'm Zoocari!"               │
│                                     │
│    ┌───────────────────────┐        │
│    │                       │        │
│    │   🎙️ TALK TO ME!      │        │  <- Primary CTA
│    │                       │        │
│    └───────────────────────┘        │
│                                     │
│    Ask me about any animal!         │
│                                     │
│    ────── or tap one ──────         │
│                                     │
│    🦁  🐘  🦒  🐪  🦘  🐆            │  <- Animal shortcuts
│                                     │
└─────────────────────────────────────┘
```

---

## 7. Response Area Design

### Speech Bubble Style
```
┌─────────────────────────────────────┐
│  🧒 "What do lions eat?"            │  <- User's question
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  🐘 Zoocari                         │
│  ─────────────────────────────────  │
│                                     │
│  "ROAR! Great question about lions! │
│   Lions are carnivores, which means │
│   they eat meat..."                 │
│                                     │
│  🔊 [▶ Listen to Answer]            │  <- Audio player
│                                     │
│  ─────────────────────────────────  │
│  Ask me more:                       │
│  [🦁 How fast can lions run?]       │
│  [🦁 Where do lions live?]          │
│  [🦁 Do lions live in groups?]      │
└─────────────────────────────────────┘
```

### Response CSS
```css
.response-bubble {
  background: white;
  border-radius: 20px;
  border: 3px solid var(--leesburg-yellow);
  padding: 20px;
  margin: 16px 0;
  box-shadow: 0 4px 16px rgba(61, 51, 42, 0.1);
}

.response-bubble::before {
  /* Speech bubble tail pointing up */
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-bottom: 12px solid var(--leesburg-yellow);
}
```

---

## 8. Mobile Responsive Design

### Breakpoints
```css
/* Mobile First */
@media (max-width: 480px) {
  .zoocari-voice-btn { width: 140px; height: 140px; }
  .animal-btn { width: 60px; height: 60px; }
}

/* Tablet */
@media (min-width: 481px) and (max-width: 768px) {
  .zoocari-voice-btn { width: 160px; height: 160px; }
}

/* Desktop */
@media (min-width: 769px) {
  /* Two-column layout optional */
  .main-container {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    gap: 24px;
  }
}
```

### Touch Targets (Accessibility)
- Minimum 44x44px for all interactive elements
- Voice button: 140-180px
- Animal buttons: 60-72px
- Adequate spacing (12px minimum between targets)

---

## 9. Animation & Micro-interactions

### Voice Button Animation States
```css
/* Idle: Gentle breathing pulse */
@keyframes breathe {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(245, 210, 36, 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 0 8px rgba(245, 210, 36, 0);
  }
}

/* Recording: Active pulse with color */
@keyframes recording {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(230, 57, 70, 0.6);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 16px rgba(230, 57, 70, 0);
  }
}

/* Success: Quick bounce */
@keyframes success-bounce {
  0% { transform: scale(1); }
  30% { transform: scale(1.2); }
  60% { transform: scale(0.95); }
  100% { transform: scale(1); }
}
```

### Sound Feedback (Optional)
- Recording start: Soft "bloop" sound
- Recording end: Gentle "ding"
- Answer ready: Cheerful notification

---

## 10. Implementation Priority

### Phase 1: Core Voice UX (Critical)
1. **Redesign voice button** - Large, centered, animated
2. **Default to voice mode** - Remove toggle, voice is primary
3. **Single-column mobile layout** - Stack elements vertically

### Phase 2: Visual Engagement (High)
4. **Animal button grid** - Visual quick questions
5. **Speech bubble responses** - Friendlier response display
6. **Simplified welcome** - Less text, more action

### Phase 3: Polish (Medium)
7. **Animations & transitions** - Micro-interactions
8. **Loading states** - Fun waiting indicators
9. **Sound effects** - Optional audio feedback

---

## 11. Component Specification

### VoiceButton Component

```python
def render_voice_button():
    """
    Renders the primary voice CTA button with:
    - Large circular design (160px)
    - Yellow/gold gradient (Leesburg brand)
    - Pulse animation when idle
    - Recording animation when active
    - Centered layout
    """

    st.markdown(VOICE_BUTTON_CSS, unsafe_allow_html=True)

    # Centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('''
        <div class="voice-cta-wrapper">
            <div class="voice-cta-label">Talk to Zoocari!</div>
        </div>
        ''', unsafe_allow_html=True)

        audio_bytes = audio_recorder(
            text="",
            recording_color="#e63946",
            neutral_color="#f5d224",
            icon_name="microphone",
            icon_size="5x",
            pause_threshold=2.5,
            sample_rate=16000
        )

        st.markdown('''
        <div class="voice-cta-hint">
            Click to start • Click again to stop
        </div>
        ''', unsafe_allow_html=True)

    return audio_bytes
```

### AnimalGrid Component

```python
def render_animal_grid():
    """
    Renders visual animal selection grid:
    - 4x2 grid of animal buttons
    - Large emoji icons
    - Touch-friendly sizing
    """

    animals = [
        ("🦁", "Lions"), ("🐘", "Elephants"),
        ("🦒", "Giraffes"), ("🐪", "Camels"),
        ("🦘", "Emus"), ("🐆", "Servals"),
        ("🦔", "Porcupines"), ("🐒", "Lemurs")
    ]

    st.markdown('<p class="animal-grid-label">Or pick an animal:</p>',
                unsafe_allow_html=True)

    cols = st.columns(4)
    for i, (emoji, name) in enumerate(animals):
        with cols[i % 4]:
            if st.button(emoji, key=f"animal_{i}",
                        help=f"Learn about {name}"):
                return f"Tell me about {name.lower()}!"

    return None
```

---

## 12. File Changes Required

| File | Changes |
|------|---------|
| `zoo_chat.py` | Restructure layout, new voice button, animal grid |
| (new) `components/voice_button.py` | Optional: Extract voice button component |
| (new) `components/animal_grid.py` | Optional: Extract animal grid component |

---

## 13. Success Metrics

| Metric | Target |
|--------|--------|
| Voice button visibility | Above the fold, centered |
| Touch target size | ≥140px diameter |
| Time to first interaction | <3 seconds |
| Mobile usability score | ≥90 (Lighthouse) |
| Voice interaction rate | Primary input method |

---

## Summary

The key transformation is from a **text-first, two-panel layout** to a **voice-first, single-column mobile experience** where:

1. **Zoocari's voice button is the hero** - Big, beautiful, unmissable
2. **Speaking feels natural** - Like talking to a friendly elephant
3. **Visual animals replace text buttons** - Tap the animal you're curious about
4. **Everything works on phones** - Where kids actually use this

The design keeps the Leesburg Animal Park branding (yellow, brown, playful fonts) while making the interface truly kid-friendly and voice-centric.
