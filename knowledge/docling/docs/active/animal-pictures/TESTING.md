# Animal Pictures: Testing Guide

> **Last Updated:** 2026-01-24
> **Purpose:** Guide for running automated and manual tests for animal pictures feature

---

## Automated Testing

### Playwright E2E Tests

#### Test Coverage

| Test Suite | File | Tests | Description |
|------------|------|-------|-------------|
| Animal Pictures | `apps/web/e2e/animal-pictures.spec.ts` | 6 | Gallery display, expand/collapse, lightbox, mobile |

#### Test Cases

1. **Gallery Button Display** - Verifies gallery button appears after chat response with animal
2. **Expand/Collapse** - Tests toggling gallery visibility
3. **Image Count** - Validates correct number of images displayed
4. **Lightbox** - Tests clicking image opens lightbox/fullscreen view
5. **Streaming Behavior** - Ensures gallery hidden during streaming
6. **Mobile Responsive** - Tests gallery on mobile viewport (375px)

---

## Quick Start

### Prerequisites

```bash
# Ensure you're in the web app directory
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/web

# Install dependencies (if not done)
npm install

# Install Playwright browsers
npx playwright install webkit chromium
```

### Run Tests

```bash
# Run all animal-pictures tests (chromium only)
npx playwright test animal-pictures --project=chromium --reporter=list

# Run with all browsers (chromium, mobile-chrome, mobile-safari)
npx playwright test animal-pictures

# Run with UI for debugging
npx playwright test animal-pictures --ui

# Run specific test
npx playwright test animal-pictures --grep "expand and collapse"
```

---

## Current Test Status

| Test | Chromium | Mobile Chrome | Mobile Safari | Notes |
|------|----------|---------------|---------------|-------|
| Gallery button shows | ⚠️ | ⚠️ | ⚠️ | Requires backend |
| Expand/collapse works | ⚠️ | ⚠️ | ⚠️ | Requires backend |
| Image count correct | ⚠️ | ⚠️ | ⚠️ | Requires backend |
| Lightbox opens | ⚠️ | ⚠️ | ⚠️ | Requires backend |
| Hidden during stream | ✅ | ⚠️ | ⚠️ | Passing on chromium |
| Mobile responsive | ⚠️ | ⚠️ | ⚠️ | Requires backend |

**Status Legend:**
- ✅ PASS - Test passing
- ⚠️ BLOCKED - Requires backend API or mock fixes
- ❌ FAIL - Test failing

---

## Known Issues

### Issue 1: Mock Routes Not Intercepting

**Symptom:** Tests timeout waiting for mocked API responses

**Cause:** Playwright route mocks may not be intercepting Vite proxy requests correctly

**Workarounds:**
1. Run tests with live backend API
2. Update mocks to match exact routing pattern

**Fix Needed:** Investigate Vite proxy + Playwright route interaction

### Issue 2: Welcome Screen UX Change

**Symptom:** Existing chat tests fail (e.g., `chat.spec.ts`)

**Cause:** Welcome screen now shows animal buttons instead of chat input

**Status:** Not specific to animal-pictures feature; affects all chat tests

**Fix Needed:** Update all e2e tests to handle welcome screen flow

---

## Running with Backend API

For reliable E2E testing, run with actual backend:

### Terminal 1: Start Backend

```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/api
python -m uvicorn main:app --reload --port 8000
```

### Terminal 2: Run Tests

```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/web
npx playwright test animal-pictures
```

Playwright will automatically start the web dev server on port 5173 (configured in `playwright.config.ts`).

---

## Manual Testing

### Test Checklist

#### Desktop (Chrome)

- [ ] Click animal button (e.g., Lion)
- [ ] Wait for response to complete
- [ ] Gallery button appears (e.g., "See Lion photos (3)")
- [ ] Click gallery button - images expand in 2-3 column grid
- [ ] Button changes to "Hide photos"
- [ ] Click image - lightbox opens fullscreen
- [ ] Navigate between images in lightbox
- [ ] Close lightbox
- [ ] Click "Hide photos" - gallery collapses

#### Mobile (375px viewport)

- [ ] Repeat desktop flow on mobile viewport
- [ ] Images fit within screen width
- [ ] Grid shows 2 columns on mobile
- [ ] Touch interactions work smoothly

#### Edge Cases

- [ ] Animal with no images configured - no gallery button
- [ ] Image fails to load - fallback or error state
- [ ] Multiple messages about same animal - no duplicates
- [ ] Different animals in same response - appropriate handling

---

## Docker Setup (Future Enhancement)

```yaml
# docker-compose.yml (TODO)
version: '3.8'
services:
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
  web:
    build: ./apps/web
    ports:
      - "5173:5173"
    depends_on:
      - api
```

```bash
# Future command
docker-compose up -d
npx playwright test
```

---

## CI/CD Integration (Future)

### GitHub Actions (Recommended)

```yaml
# .github/workflows/e2e-tests.yml (TODO)
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: npm ci
        working-directory: apps/web
      - name: Install Playwright
        run: npx playwright install --with-deps
        working-directory: apps/web
      - name: Run tests
        run: npx playwright test
        working-directory: apps/web
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: apps/web/playwright-report/
```

---

## Debugging Tips

### View Test in UI Mode

```bash
npx playwright test animal-pictures --ui
```

- Step through tests
- Inspect page state
- View screenshots

### Generate Trace

```bash
npx playwright test animal-pictures --trace on
```

Then view:
```bash
npx playwright show-trace test-results/.../trace.zip
```

### Screenshot on Failure

Already configured in `playwright.config.ts`:
```typescript
use: {
  screenshot: 'only-on-failure',
}
```

Find screenshots in `test-results/` directory.

---

## Next Steps

1. **Fix Mock Issue** - Update route mocks or recommend backend-only testing
2. **Update Existing Tests** - Fix chat.spec.ts and other tests for welcome screen
3. **Add Visual Regression** - Consider Percy.io or similar for image comparison
4. **Docker Setup** - Create docker-compose for full stack testing
5. **CI Integration** - Add GitHub Actions workflow for automated testing
