# Animal Pictures: Implementation Plan

> **Last Updated:** 2026-01-20

## Phase Overview

```
┌─────────────────────────────────────────────────────────────┐
│ DECISIONS NEEDED (Before Implementation)                    │
│ - UX approach (Featured Image vs Collapsible vs Thumbnail)  │
│ - Image source (Config file vs LanceDB metadata)            │
│ - Image assets (Park photos vs stock vs placeholder)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Config & Data Setup                                │
│ - Create animal_images.json mapping                         │
│ - Update Source type with image fields                      │
│ - Backend: include image URLs in response                   │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│ PHASE 2A: UI Components │              │ PHASE 2B: Image Assets  │
│ (Can run in parallel)   │              │ (Can run in parallel)   │
│ - AnimalImageGallery    │              │ - Source/create images  │
│ - Lightbox component    │              │ - Optimize for web      │
│ - Loading states        │              │ - Generate thumbnails   │
└─────────────────────────┘              └─────────────────────────┘
         │                                         │
         └────────────────────┬────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Integration                                        │
│ - Update MessageBubble to render images                     │
│ - Connect to real image data                                │
│ - Handle edge cases                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: QA & Polish                                        │
│ - Mobile testing (375px, 414px, 768px)                      │
│ - Performance testing (lazy load, network)                  │
│ - Accessibility review                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Config & Data Setup

**Dependencies:** Decisions on UX and image source
**Parallel:** No

### Tasks

| Task | File | Description |
|------|------|-------------|
| 1.1 | `data/animal_images.json` | Create animal-to-image URL mapping (NEW) |
| 1.2 | `src/types/index.ts` | Add `image_urls?: string[]`, `thumbnail?: string` to Source |
| 1.3 | `apps/api/app/services/rag.py` | Include image URLs in source dict |
| 1.4 | `apps/api/app/routers/chat.py` | Pass image URLs through StreamChunk |

### Config File Structure

```json
{
  "Lion": {
    "thumbnail": "/images/animals/lion_thumb.webp",
    "images": [
      "/images/animals/lion_1.webp",
      "/images/animals/lion_2.webp"
    ],
    "alt": "African Lion at Leesburg Animal Park"
  },
  "Elephant": {
    "thumbnail": "/images/animals/elephant_thumb.webp",
    "images": [
      "/images/animals/elephant_1.webp"
    ],
    "alt": "Asian Elephant at Leesburg Animal Park"
  }
}
```

### Type Updates

```typescript
// src/types/index.ts
interface Source {
  animal: string;
  title: string;
  url?: string;
  thumbnail?: string;      // NEW
  image_urls?: string[];   // NEW
  alt?: string;            // NEW
}
```

### Acceptance Criteria
- [ ] Config file loads without errors
- [ ] Source type includes image fields
- [ ] Backend returns image URLs for known animals
- [ ] Unknown animals return empty image arrays (graceful)

---

## Phase 2A: UI Components

**Dependencies:** Phase 1
**Parallel:** Yes (with Phase 2B)

### Tasks

| Task | File | Description |
|------|------|-------------|
| 2A.1 | `src/components/AnimalImage.tsx` | Single responsive image component (NEW) |
| 2A.2 | `src/components/AnimalImageGallery.tsx` | Grid/carousel of images (NEW) |
| 2A.3 | `src/components/ImageLightbox.tsx` | Fullscreen tap-to-expand (NEW) |
| 2A.4 | `src/components/ImageSkeleton.tsx` | Loading placeholder (NEW) |

### AnimalImage Component

```tsx
// Basic responsive image with lazy loading
interface AnimalImageProps {
  src: string;
  alt: string;
  thumbnail?: string;
  className?: string;
  onClick?: () => void;
}

// Features:
// - IntersectionObserver for lazy loading
// - Blur-up from thumbnail
// - Error fallback to emoji/placeholder
// - Aspect ratio lock (16:9)
```

### AnimalImageGallery Component

```tsx
interface AnimalImageGalleryProps {
  images: string[];
  animal: string;
  variant: 'featured' | 'thumbnails' | 'collapsible';
}

// Variants:
// - featured: Single large image + "more photos" link
// - thumbnails: Row of small images
// - collapsible: Hidden by default, expand on tap
```

### Acceptance Criteria
- [ ] Images lazy load when scrolled into view
- [ ] Loading skeleton shows during fetch
- [ ] Tap opens lightbox on mobile
- [ ] Graceful fallback on image error
- [ ] No layout shift during load

---

## Phase 2B: Image Assets

**Dependencies:** None (can start immediately)
**Parallel:** Yes (with Phase 2A)

### Tasks

| Task | Description |
|------|-------------|
| 2B.1 | Identify animals in knowledge base (~20 animals) |
| 2B.2 | Source images (park photos, stock, or placeholder) |
| 2B.3 | Optimize images for web (WebP, <100KB) |
| 2B.4 | Generate thumbnails (60px, <20KB) |
| 2B.5 | Place in `apps/web/public/images/animals/` |

### Image Specifications

| Type | Dimensions | Format | Max Size |
|------|------------|--------|----------|
| Full | 800×450 (16:9) | WebP | 100KB |
| Thumbnail | 120×68 (16:9) | WebP | 20KB |

### Animal List (from AnimalGrid + Knowledge Base)

Priority animals (currently in UI):
1. Lion
2. Elephant
3. Giraffe
4. Camel
5. Emu
6. Serval
7. Porcupine
8. Lemur

Additional animals (from knowledge base - TBD):
- Zebra, Tiger, Bear, etc. (need to audit LanceDB)

### Acceptance Criteria
- [ ] At least 8 priority animals have images
- [ ] All images optimized for web
- [ ] Thumbnails generated for all images
- [ ] Alt text defined for accessibility

---

## Phase 3: Integration

**Dependencies:** Phases 2A, 2B
**Parallel:** No

### Tasks

| Task | File | Description |
|------|------|-------------|
| 3.1 | `src/components/MessageBubble.tsx` | Render AnimalImageGallery from sources |
| 3.2 | `src/components/MessageBubble.tsx` | Extract unique animals from sources |
| 3.3 | `src/components/MessageBubble.tsx` | Handle multiple animals in one response |
| 3.4 | `src/lib/animalImages.ts` | Helper to load/lookup animal images (NEW) |

### MessageBubble Integration

```tsx
// MessageBubble.tsx changes
const MessageBubble = ({ message, isStreaming, sources }) => {
  // Extract unique animals mentioned
  const animals = useMemo(() =>
    [...new Set(sources?.map(s => s.animal).filter(Boolean))],
    [sources]
  );

  return (
    <div className="...">
      {/* Existing text content */}
      <p>{message}</p>

      {/* NEW: Animal images */}
      {animals.length > 0 && !isStreaming && (
        <AnimalImageGallery
          animals={animals}
          variant={animals.length === 1 ? 'featured' : 'thumbnails'}
        />
      )}

      {/* Existing sources */}
      {sources && <SourcesList sources={sources} />}
    </div>
  );
};
```

### Edge Cases

| Case | Handling |
|------|----------|
| No images for animal | Show nothing (graceful skip) |
| Multiple animals | Show thumbnail strip |
| Streaming in progress | Don't show images until done |
| Image load error | Show animal emoji fallback |
| Very long response | Images below fold, lazy load |

### Acceptance Criteria
- [ ] Single animal shows featured image
- [ ] Multiple animals show thumbnail strip
- [ ] No images during streaming
- [ ] Graceful handling of missing images
- [ ] No duplicate images for same animal

---

## Phase 4: QA & Polish

**Dependencies:** Phase 3
**Parallel:** No

### Tasks

| Task | Description |
|------|-------------|
| 4.1 | Test on mobile devices (375px, 414px) |
| 4.2 | Test on tablet (768px) |
| 4.3 | Test on desktop (1024px, 1440px) |
| 4.4 | Test slow network (3G throttling) |
| 4.5 | Test image load failures |
| 4.6 | Accessibility audit (alt text, keyboard nav) |
| 4.7 | Performance audit (Lighthouse) |

### Mobile Testing Checklist

| Device Width | Test |
|--------------|------|
| 375px (iPhone SE) | Images fit, no horizontal scroll |
| 414px (iPhone Plus) | Images fit, no horizontal scroll |
| 768px (iPad) | 2-column gallery works |
| 1024px+ (Desktop) | 3-column gallery works |

### Performance Targets

| Metric | Target |
|--------|--------|
| First image visible | <500ms after message renders |
| All images loaded | <2s on 3G |
| Layout shift (CLS) | <0.1 |
| Lighthouse Performance | >90 |

### Acceptance Criteria
- [ ] No horizontal scroll on any device
- [ ] Images load within performance targets
- [ ] Lightbox works with touch gestures
- [ ] Screen reader announces image content
- [ ] Keyboard navigation works for gallery

---

## Files Changed Summary

### New Files (~6)
- `data/animal_images.json`
- `src/components/AnimalImage.tsx`
- `src/components/AnimalImageGallery.tsx`
- `src/components/ImageLightbox.tsx`
- `src/components/ImageSkeleton.tsx`
- `src/lib/animalImages.ts`

### Modified Files (~4)
- `src/types/index.ts`
- `src/components/MessageBubble.tsx`
- `apps/api/app/services/rag.py`
- `apps/api/app/routers/chat.py`

### Assets (~20+ images)
- `apps/web/public/images/animals/*.webp`

**Total: ~10 code files + image assets**

---

## Future: Admin Panel Integration

**Not in MVP scope** - to be added after initial release.

| Task | Description |
|------|-------------|
| Admin endpoint: GET /images | List all animal images |
| Admin endpoint: POST /images | Add new animal image |
| Admin endpoint: PUT /images/:animal | Update animal images |
| Admin endpoint: DELETE /images/:animal/:index | Remove specific image |
| Admin UI | Simple CRUD interface in `apps/admin-api` |

This will allow park staff to manage images without developer intervention.
