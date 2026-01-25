# Image Management Feature

**Status**: In Progress
**Started**: 2026-01-24

## Overview
Add image management capabilities to the Zoocari admin portal for viewing, uploading, editing, and deleting animal images.

## Architecture
- **JSON Source of Truth**: Admin portal reads/writes `data/animal_images.json` directly
- **RAG Service**: Continues lazy-loading JSON unchanged
- **Image Storage**: `/images/animals/` directory

## Phases

### Phase 1: Backend (admin-api) ⏳
- [ ] Create `models/images.py` - Pydantic models
- [ ] Create `services/image_manager.py` - JSON/file operations
- [ ] Create `routers/images.py` - REST endpoints
- [ ] Update `config.py` with image path settings
- [ ] Update `requirements.txt` with Pillow, python-multipart
- [ ] Register router in `main.py`

### Phase 2: Frontend Core ⏳
- [ ] Add image types to `types/index.ts`
- [ ] Add `imagesApi` to `api/client.ts`
- [ ] Create `pages/Images.tsx`
- [ ] Create `components/Images/` (ImageGrid, ImageCard)
- [ ] Add Images nav item to Layout
- [ ] Add `/images` route to App.tsx

### Phase 3: Upload & Management ⏳
- [ ] Create `ImageDetailModal.tsx`
- [ ] Create `ImageUploader.tsx` (drag-drop)
- [ ] Create `ImageGallery.tsx` (reorderable)
- [ ] Create `ThumbnailSelector.tsx`

### Phase 4: QA & Polish ⏳
- [ ] Loading/error states
- [ ] Toast notifications
- [ ] End-to-end testing with RAG
- [ ] Docker verification

## Files Changed/Created

### Backend
- `apps/admin-api/models/images.py` (new)
- `apps/admin-api/services/image_manager.py` (new)
- `apps/admin-api/routers/images.py` (new)
- `apps/admin-api/routers/__init__.py` (modified)
- `apps/admin-api/main.py` (modified)
- `apps/admin-api/config.py` (modified)
- `apps/admin-api/requirements.txt` (modified)

### Frontend
- `apps/admin/src/types/index.ts` (modified)
- `apps/admin/src/api/client.ts` (modified)
- `apps/admin/src/pages/Images.tsx` (new)
- `apps/admin/src/components/Images/` (new directory)
- `apps/admin/src/components/Layout/index.tsx` (modified)
- `apps/admin/src/App.tsx` (modified)
