# Image Management API

Backend endpoints for managing animal images in the admin portal.

## Endpoints

All endpoints require authentication via JWT Bearer token.

### 1. List All Animals with Images
```
GET /api/admin/images/animals
```

Returns all animals with their image configurations.

**Response:**
```json
{
  "animals": {
    "Lion": {
      "thumbnail": "/images/animals/lion_thumb.webp",
      "images": ["/images/animals/lion_1.webp"],
      "alt": "African Lion"
    },
    ...
  }
}
```

### 2. Get Specific Animal
```
GET /api/admin/images/animals/{name}
```

Returns image configuration for a specific animal.

**Response:**
```json
{
  "name": "Lion",
  "thumbnail": "/images/animals/lion_thumb.webp",
  "images": ["/images/animals/lion_1.webp"],
  "alt": "African Lion"
}
```

### 3. Update Animal Images
```
PUT /api/admin/images/animals/{name}
```

Update alt text, thumbnail, or image order for an animal.

**Request Body:**
```json
{
  "alt": "Updated description",
  "thumbnail": "/images/animals/lion_thumb.webp",
  "images": ["/images/animals/lion_1.webp", "/images/animals/lion_2.webp"]
}
```

All fields are optional.

### 4. Upload Image
```
POST /api/admin/images/animals/{name}/upload
```

Upload a new image for an animal. Automatically converts to WebP and generates thumbnail.

**Parameters:**
- `file` (form-data): Image file to upload
- `is_thumbnail` (query, optional): Set to `true` to upload as thumbnail only

**Response:**
```json
{
  "filename": "lion_2.webp",
  "url": "/images/animals/lion_2.webp",
  "thumbnail_url": "/images/animals/lion_thumb.webp"
}
```

### 5. Delete Image
```
DELETE /api/admin/images/animals/{name}/{filename}
```

Delete an image file and remove from configuration.

**Response:** 204 No Content

### 6. Sync with Filesystem
```
POST /api/admin/images/sync
```

Reconcile `animal_images.json` with actual files in the images directory.

**Response:**
```json
{
  "ok": true,
  "added": [],
  "removed": [],
  "total_files": 150
}
```

## Configuration

Add to `.env`:
```
ANIMAL_IMAGES_PATH=data/animal_images.json
IMAGE_STORAGE_PATH=apps/web/public/images/animals
```

## Image Processing

- All images converted to WebP format (quality 85)
- Thumbnails automatically generated at 120x68 pixels
- File naming: `{animal_slug}_{n}.webp` and `{animal_slug}_thumb.webp`

## File Locking

All read/write operations to `animal_images.json` use file locking (`fcntl.LOCK_SH` for reads, `fcntl.LOCK_EX` for writes) to prevent race conditions.
