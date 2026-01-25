# Animal Images Directory

Stock photos for Zoocari animal-pictures feature.

## Image Specifications

| Type | Dimensions | Aspect Ratio | Format | Max Size |
|------|-----------|--------------|--------|----------|
| Full | 800x450 | 16:9 | WebP | <100KB |
| Thumbnail | 120x68 | 16:9 | WebP | <20KB |

## Naming Convention

- Full size: `{animal}_1.webp`, `{animal}_2.webp`, etc.
- Thumbnail: `{animal}_thumb.webp`
- Use lowercase animal names (e.g., `lion_1.webp`, `elephant_thumb.webp`)

## Attribution Requirements

All stock photos must include:
1. License type (Creative Commons, royalty-free, etc.)
2. Source URL
3. Photographer credit (if required by license)

Document attributions in `ATTRIBUTIONS.md` in this directory.

## Animal Image Status

| Animal | Thumbnail | Full Images | Status |
|--------|-----------|-------------|--------|
| Lion | Placeholder | Placeholder | Needs stock photo |
| Elephant | Placeholder | Placeholder | Needs stock photo |
| Giraffe | Placeholder | Placeholder | Needs stock photo |
| Camel | Placeholder | Placeholder | Needs stock photo |
| Emu | Placeholder | Placeholder | Needs stock photo |
| Serval | Placeholder | Placeholder | Needs stock photo |
| Porcupine | Placeholder | Placeholder | Needs stock photo |
| Lemur | Placeholder | Placeholder | Needs stock photo |

## Placeholder URLs

Until real stock photos are sourced, use placeholder service URLs in `data/animal_images.json`:

```
https://placehold.co/{width}x{height}/{color}/white?text={AnimalName}
```

## Recommended Stock Photo Sources

- [Unsplash](https://unsplash.com) - Free, high quality
- [Pexels](https://pexels.com) - Free, commercial use
- [Pixabay](https://pixabay.com) - Free, no attribution required
- [Adobe Stock](https://stock.adobe.com) - Paid, high quality

## Adding New Images

1. Source image meeting specifications above
2. Convert to WebP format
3. Create thumbnail version
4. Add to this directory with proper naming
5. Update `data/animal_images.json` with local paths
6. Add attribution to `ATTRIBUTIONS.md`
7. Update status table in this README
