# QA Report: Image Management Feature

**Date**: 2026-01-24
**Feature**: Image Management API + Admin UI
**Status**: FAILED - Multiple issues found

## Test Results Summary

| Test Category | Status | Details |
|--------------|--------|---------|
| Backend Syntax Check | PASS | All Python files compile without syntax errors |
| Backend Unit Tests | FAIL | 5/6 tests failed due to fixture error |
| Frontend TypeScript | FAIL | 2 unused variable warnings |
| Frontend Build | FAIL | Build blocked by TypeScript errors |
| Import Resolution | PASS | All imports resolve correctly with proper env |

## Issues Found

### 1. Backend Test Fixture Error
**File**: `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api/tests/conftest.py:25`

**Error**:
```
TypeError: create_access_token() got an unexpected keyword argument 'data'
```

**Cause**: Test fixture uses wrong parameter name for `create_access_token()`

**Expected signature**: `create_access_token(username: str, expires_delta: Optional[timedelta] = None)`

**Current fixture code**:
```python
token = create_access_token(data={"sub": settings.admin_username})
```

**Fix Required**:
```python
token = create_access_token(username=settings.admin_username)
```

**Impact**: 5 of 6 backend tests fail (test_upload_image_requires_auth passes because it doesn't need auth_headers fixture)

---

### 2. Frontend TypeScript Unused Variables
**File**: `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/components/Images/ImageCard.tsx:10`

**Error**:
```
error TS6133: 'onRefresh' is declared but its value is never read.
```

**Fix Required**: Remove unused parameter from Props interface and function signature:
```typescript
// Current
interface Props {
  name: string
  config: AnimalImageConfig
  onRefresh: () => void  // <- Remove this
  onSelect: (name: string) => void
}

export default function ImageCard({ name, config, onRefresh, onSelect }: Props) {
  // ...
}

// Fixed
interface Props {
  name: string
  config: AnimalImageConfig
  onSelect: (name: string) => void
}

export default function ImageCard({ name, config, onSelect }: Props) {
  // ...
}
```

---

### 3. Frontend TypeScript Unused Variable
**File**: `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/components/Images/ImageDetailModal.tsx:15`

**Error**:
```
error TS6133: 'animal' is declared but its value is never read.
```

**Fix Required**: Remove unused state variable:
```typescript
// Current - line 15
const [animal, setAnimal] = useState<AnimalImageDetail | null>(null)

// The variable 'animal' is set in loadAnimal() but never used
// Only setAnimal is called, the value is never read

// Fixed - either remove it or use it
// Option 1: Remove if truly unused
// Remove the line entirely and use separate state for each field

// Option 2: If needed for loading state, use it
if (!animal) return <div>Loading...</div>
```

---

### 4. API Type Mismatch
**File**: `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/api/client.ts:191`

**Issue**: syncImages return type mismatch

**Backend returns** (from `/apps/admin-api/routers/images.py:184-190`):
```python
{
    "ok": True,
    "added": result["added"],        # list[str]
    "removed": result["removed"],    # list[str]
    "total_files": result["total_files"]  # int
}
```

**Frontend expects** (`client.ts:191`):
```typescript
api<{ synced: number; orphaned: string[] }>('/images/sync', { method: 'POST' })
```

**Fix Required**: Update frontend type to match backend:
```typescript
syncImages: () =>
  api<{ ok: boolean; added: string[]; removed: string[]; total_files: number }>('/images/sync', { method: 'POST' }),
```

---

## Missing Dependencies

The following dependencies were not installed in the virtual environment but are required:
- `python-jose[cryptography]` - INSTALLED during QA
- `passlib[bcrypt]` - INSTALLED during QA
- `Pillow` - Already present

These need to be verified in production deployments.

---

## Files Requiring Changes

1. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api/tests/conftest.py`
   - Fix `create_access_token` call to use `username` parameter

2. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/components/Images/ImageCard.tsx`
   - Remove unused `onRefresh` parameter

3. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/components/Images/ImageDetailModal.tsx`
   - Remove or use `animal` state variable

4. `/Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin/src/api/client.ts`
   - Fix syncImages return type to match backend

---

## Verification Commands

### Backend Tests
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api
source ../../.venv/bin/activate
ADMIN_PASSWORD=test OPENAI_API_KEY=test python -m pytest tests/test_images.py -v
```

### Frontend Type Check
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin
npx tsc --noEmit
```

### Frontend Build
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin
npm run build
```

---

## Backend API Contract (Verified)

All endpoints are correctly implemented and match the spec:

- `GET /api/admin/images/animals` - List all animals with image configs
- `GET /api/admin/images/animals/{name}` - Get specific animal detail
- `PUT /api/admin/images/animals/{name}` - Update animal config (alt, thumbnail, images)
- `POST /api/admin/images/animals/{name}/upload` - Upload image file
- `DELETE /api/admin/images/animals/{name}/{filename}` - Delete image
- `POST /api/admin/images/sync` - Sync filesystem with JSON

---

## Notes

- Backend code quality is good - clean separation of concerns, proper error handling
- Frontend components follow React best practices
- Type safety is enforced but needs cleanup for unused variables
- All file imports resolve correctly once environment is configured
- Router is properly registered in `main.py`
