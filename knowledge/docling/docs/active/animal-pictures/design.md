# Animal Pictures: Design Document

> **Last Updated:** 2026-01-20

## Executive Summary

**Scope:** Display animal pictures in chat responses
**Complexity:** Low-Medium
**Key Advantage:** Animal names already extracted from RAG sources

---

## Current State

| Component | State | Notes |
|-----------|-------|-------|
| Animal name extraction | ✅ Done | `sources[].animal` available in responses |
| Image assets | ❌ None | No animal images in codebase |
| Image display component | ❌ None | MessageBubble is text-only |
| Mobile responsiveness | ✅ Good | Tailwind mobile-first patterns exist |

### Available Screen Real Estate

| Device | Message Bubble Width | Usable Image Width |
|--------|---------------------|-------------------|
| Mobile (375px) | ~280px | ~260px |
| Mobile (414px) | ~310px | ~290px |
| Tablet (768px) | ~400px | ~380px |
| Desktop (1024px+) | ~670px | ~650px |

---

## UX Options (Decision Needed)

### Option A: Thumbnail Strip

Small thumbnails in a row below message text.

```
┌─────────────────────────────────┐
│ Lions live in prides and are    │
│ known as the "king of the       │
│ jungle"...                      │
│                                 │
│ [60px] [60px] [60px]           │
│  🦁     🦁     🦁              │
└─────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Minimal space usage | Images too small for detail |
| Works well with multiple animals | Less engaging |
| No layout shift | Tap target small on mobile |

**Best for:** Quick visual reference, multiple animals mentioned

---

### Option B: Featured Image (Recommended for Single Animal)

Single prominent image with tap-to-expand.

```
┌─────────────────────────────────┐
│ Lions live in prides and are    │
│ known as the "king of the       │
│ jungle"...                      │
│                                 │
│ ┌─────────────────────────────┐ │
│ │                             │ │
│ │      [Lion Photo]           │ │
│ │      280px × 157px          │ │
│ │                             │ │
│ └─────────────────────────────┘ │
│ 📷 Tap for more photos          │
└─────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Engaging, clear image | Takes vertical space |
| Good mobile UX | Only shows one image initially |
| Natural fit below text | |

**Best for:** Single animal responses, engaging experience

---

### Option C: Collapsible Gallery

Hidden by default, expands on tap.

```
┌─────────────────────────────────┐
│ Lions live in prides and are    │
│ known as the "king of the       │
│ jungle"...                      │
│                                 │
│ [📷 See lion photos (3)]        │  ← Collapsed
└─────────────────────────────────┘

         ↓ After tap ↓

┌─────────────────────────────────┐
│ Lions live in prides and are    │
│ known as the "king of the       │
│ jungle"...                      │
│                                 │
│ [📷 Hide photos]                │
│ ┌───────┐ ┌───────┐ ┌───────┐  │
│ │       │ │       │ │       │  │
│ │ img1  │ │ img2  │ │ img3  │  │
│ └───────┘ └───────┘ └───────┘  │
└─────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| User controls when to see images | Extra tap required |
| No vertical space by default | May be overlooked |
| Good for multiple images | Slightly more complex |

**Best for:** Power users, multiple images per animal

---

### Option D: Floating Sidebar (Desktop Only)

Images in right sidebar, skipped on mobile.

```
Desktop:
┌────────────────────────┬──────────┐
│ Lions live in prides   │ [Image]  │
│ and are known as the   │          │
│ "king of the jungle"   │ [Image]  │
│ ...                    │          │
└────────────────────────┴──────────┘

Mobile: No images (text only)
```

| Pros | Cons |
|------|------|
| Doesn't affect text flow | No mobile experience |
| Desktop has plenty of space | Major layout change |

**Best for:** Desktop-focused apps (not recommended for Zoocari)

---

### Option E: Avatar Accent

Small animal avatar next to assistant message.

```
┌─────────────────────────────────┐
│ [🦁]  Lions live in prides and  │
│  48px are known as the "king    │
│       of the jungle"...         │
└─────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Minimal space | Very small image |
| Adds personality | Not a "photo" experience |
| Works on all sizes | Limited to one animal |

**Best for:** Subtle enhancement, not primary image display

---

## Recommended Approach: Adaptive

Combine options based on context:

| Scenario | UX |
|----------|-----|
| Single animal, 1 image | Option B (Featured Image) |
| Single animal, multiple images | Option C (Collapsible Gallery) |
| Multiple animals mentioned | Option A (Thumbnail Strip) + tap to expand |

---

## Image Source Options (Decision Needed)

### Option 1: Static Config File (Recommended for MVP)

Create `animal_images.json` mapping:

```json
{
  "Lion": {
    "thumbnail": "/images/animals/lion_thumb.jpg",
    "images": [
      "/images/animals/lion_1.jpg",
      "/images/animals/lion_2.jpg"
    ]
  },
  "Elephant": {
    "thumbnail": "/images/animals/elephant_thumb.jpg",
    "images": [...]
  }
}
```

| Pros | Cons |
|------|------|
| Simple to implement | Separate from knowledge base |
| Easy to update | Manual maintenance |
| Works immediately | Not scalable long-term |

### Option 2: LanceDB Metadata

Add `image_urls` to animal document metadata:

```python
{
  "text": "Lions are...",
  "metadata": {
    "animal_name": "Lion",
    "image_urls": ["url1", "url2"],  # NEW
    "thumbnail_url": "thumb_url"      # NEW
  }
}
```

| Pros | Cons |
|------|------|
| Single source of truth | Requires re-indexing |
| Per-document images | Schema change |
| Scales well | More backend work |

### Option 3: External CDN (Cloudinary, S3)

Store images externally, reference by URL.

| Pros | Cons |
|------|------|
| Scalable | External dependency |
| Image optimization built-in | Potential costs |
| Easy updates | Network dependency |

**Decision:** Option 1 (Config File) for MVP.

**Future Enhancement:** Add admin panel (via `apps/admin-api`) to manage animal images without code changes - add/remove/edit images, update alt text, reorder galleries.

---

## Technical Integration Points

### Already Available (No Changes Needed)

| Component | Data |
|-----------|------|
| RAG search results | `animal_name` in metadata |
| Source type | `{ animal: string, title: string, url?: string }` |
| StreamChunk | Passes sources to frontend |
| MessageBubble props | Receives `sources` array |

### Changes Required

| Component | Change |
|-----------|--------|
| `Source` type | Add `image_urls?: string[]`, `thumbnail?: string` |
| `animal_images.json` | NEW: Animal-to-image mapping |
| `AnimalImageGallery.tsx` | NEW: Image display component |
| `MessageBubble.tsx` | Render images from sources |
| `rag.py` | Include image URLs in source dict |

---

## Mobile Performance Considerations

1. **Lazy Loading:** Use IntersectionObserver, don't load off-screen images
2. **Responsive Images:** Use `srcset` for different screen densities
3. **Aspect Ratio:** Lock 16:9 to prevent layout shift
4. **File Size:** Thumbnails <20KB, full images <100KB
5. **Loading State:** Skeleton placeholder while loading
6. **Error State:** Fallback to emoji or placeholder if image fails

---

## Success Criteria

1. Images display for mentioned animals
2. No layout shift during image load
3. Mobile images load in <1s on 3G
4. Tap-to-expand works smoothly
5. Graceful fallback when no image available
6. No regression in chat performance
