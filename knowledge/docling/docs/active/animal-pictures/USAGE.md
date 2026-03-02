# Animal Image Components - Usage Guide

## Component Overview

### AnimalImageGallery (Main Component)

The primary component for displaying animal images in chat messages.

```tsx
import { AnimalImageGallery } from '../components';

// Example usage
<AnimalImageGallery
  images={[
    'https://example.com/lion1.jpg',
    'https://example.com/lion2.jpg',
    'https://example.com/lion3.jpg'
  ]}
  animal="Lion"
  thumbnail="https://example.com/lion_thumb.jpg" // optional
  alt="Lion photos from Leesburg Animal Park" // optional
/>
```

**Props:**
- `images: string[]` - Array of image URLs to display
- `animal: string` - Name of the animal (used in button text)
- `thumbnail?: string` - Optional thumbnail URL (will be added to gallery if not in images array)
- `alt?: string` - Optional alt text (defaults to "{animal} photos")

**Behavior:**
- Renders nothing if `images` is empty or undefined
- Default state: collapsed with "📷 See {animal} photos (N)" button
- Expanded state: 2-column grid (mobile) or 3-column grid (desktop)
- Click image to open lightbox

---

### AnimalImage (Single Image)

Individual image component with lazy loading and error handling.

```tsx
import { AnimalImage } from '../components';

<AnimalImage
  src="https://example.com/elephant.jpg"
  alt="African elephant"
  onClick={() => console.log('Image clicked')}
/>
```

**Props:**
- `src: string` - Image URL
- `alt: string` - Alt text for accessibility
- `onClick?: () => void` - Optional click handler

**Features:**
- Lazy loads when within 50px of viewport
- 16:9 aspect ratio lock
- Fallback to emoji (🦁) on error
- Smooth fade-in on load

---

### ImageLightbox (Fullscreen Viewer)

Modal overlay for viewing images at full size.

```tsx
import { ImageLightbox } from '../components';

const [lightboxOpen, setLightboxOpen] = useState(false);

{lightboxOpen && (
  <ImageLightbox
    images={['url1.jpg', 'url2.jpg', 'url3.jpg']}
    initialIndex={0}
    alt="Lion gallery"
    onClose={() => setLightboxOpen(false)}
  />
)}
```

**Props:**
- `images: string[]` - Array of image URLs
- `initialIndex?: number` - Starting image index (default: 0)
- `alt: string` - Alt text base
- `onClose: () => void` - Callback when lightbox closes

**Features:**
- Click/tap outside to close
- Swipe left/right to navigate (50px minimum)
- Arrow keys for navigation
- ESC key to close
- Image counter (e.g., "2 / 5")
- Body scroll lock while open

---

### ImageSkeleton (Loading State)

Animated placeholder for loading images.

```tsx
import { ImageSkeleton } from '../components';

<ImageSkeleton />
```

**Features:**
- 16:9 aspect ratio (matches loaded images)
- Shimmer animation (2s loop)
- Leesburg color palette

---

## Integration Example

Here's how to use AnimalImageGallery in MessageBubble:

```tsx
// In MessageBubble.tsx (future integration)

import { AnimalImageGallery } from './';

// Extract images from sources
const getAnimalImages = (sources: Source[]) => {
  const imageMap: Record<string, string[]> = {};

  sources.forEach(source => {
    if (source.image_urls && source.image_urls.length > 0) {
      if (!imageMap[source.animal]) {
        imageMap[source.animal] = [];
      }
      imageMap[source.animal].push(...source.image_urls);
    }
  });

  return imageMap;
};

// In component render
const animalImages = sources ? getAnimalImages(sources) : {};

{Object.entries(animalImages).map(([animal, images]) => (
  <AnimalImageGallery
    key={animal}
    images={images}
    animal={animal}
  />
))}
```

---

## Responsive Behavior

### Mobile (375px - 767px)
- Gallery: 2-column grid
- Image size: ~130px per image
- Gap: 8px between images

### Tablet/Desktop (768px+)
- Gallery: 3-column grid
- Image size: ~120px per image
- Gap: 8px between images

### Lightbox (All sizes)
- Full viewport overlay
- Max width: 4xl (896px)
- Max height: 90vh

---

## Accessibility

All components include proper ARIA attributes:

- `AnimalImageGallery`: `aria-expanded`, `aria-controls`
- `ImageLightbox`: `role="dialog"`, `aria-modal="true"`, `aria-label`
- `AnimalImage`: Fallback `role="img"` for error state
- `ImageSkeleton`: `role="status"`, `aria-label="Loading image"`

Keyboard navigation:
- ESC: Close lightbox
- Arrow Left/Right: Navigate images in lightbox
- Tab: Focus navigation through buttons

---

## Performance Considerations

### Lazy Loading
Images only load when scrolled into view (50px margin):
```tsx
// IntersectionObserver with rootMargin: '50px'
```

### No Layout Shift
All images use `aspect-video` (16:9) to reserve space before loading.

### Optimized Animations
- `fadeIn`: 0.3s ease-out
- `shimmer`: 2s linear loop
- CSS transitions instead of JavaScript

### Bundle Impact
- Total addition: ~3KB (4 components)
- No external dependencies
- Tree-shakeable exports

---

## Testing Locally

Run dev server:
```bash
cd apps/web
npm run dev
```

Test components in browser console:
```javascript
// Simulate source with images
const mockSources = [{
  animal: 'Lion',
  title: 'Lion Facts',
  url: 'https://example.com',
  image_urls: [
    'https://via.placeholder.com/400x225/f5d224/3d332a?text=Lion+1',
    'https://via.placeholder.com/400x225/f29021/3d332a?text=Lion+2',
  ]
}];
```

---

## Next Steps (Phase 2B)

Before these components can be used in production:

1. Update `Source` type to include `image_urls` and `thumbnail`
2. Create `animal_images.json` config file
3. Update backend to populate image URLs in sources
4. Integrate into `MessageBubble.tsx`
