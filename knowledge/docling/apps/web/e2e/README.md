# E2E Tests - Playwright

End-to-end tests for Zoocari web application using Playwright.

## Test Coverage

| Test Suite | Description | Status |
|------------|-------------|--------|
| `welcome.spec.ts` | Welcome message display | ✓ |
| `chat.spec.ts` | Text messaging, follow-ups | ✓ |
| `animals.spec.ts` | Quick animal buttons | ✓ |
| `voice.spec.ts` | Voice button visibility/clickable | ✓ |
| `session.spec.ts` | Session persistence across refresh | ✓ |
| `mobile.spec.ts` | Mobile viewport tests (iOS/Android) | ✓ |

## Running Tests

### Local Development
```bash
# Run all E2E tests (headless)
npm run e2e

# Run with UI mode (interactive)
npm run e2e:ui

# Run in headed mode (see browser)
npm run e2e:headed

# View last test report
npm run e2e:report
```

### Run specific test file
```bash
npx playwright test e2e/chat.spec.ts
```

### Run specific project (browser)
```bash
npx playwright test --project=chromium
npx playwright test --project=mobile-chrome
```

## Test Coverage

| Scenario | Test File | Status |
|----------|-----------|--------|
| Welcome message displays | `e2e/welcome.spec.ts` | ✓ |
| Send text message, receive response | `e2e/chat.spec.ts` | ✓ |
| Quick animal buttons work | `e2e/animals.spec.ts` | ✓ |
| Follow-up questions clickable | `e2e/chat.spec.ts` | ✓ |
| Voice button visible/clickable | `e2e/voice.spec.ts` | ✓ |
| Session persists across refresh | `e2e/session.spec.ts` | ✓ |
| Mobile layout works | `e2e/mobile.spec.ts` | ✓ |

## Notes
- Tests use mocked API responses (session, chat stream) to avoid backend dependency
- Voice tests only verify UI presence/clickability (cannot test actual recording without browser permissions)
- Mobile tests verify touch targets, responsiveness, and no horizontal scroll
- Session persistence tests verify localStorage/state management

## Running Tests

**Local development:**
```bash
cd apps/web
npm run e2e          # Run all tests headless
npm run e2e:ui       # Interactive UI mode
npm run e2e:headed   # Run with browser visible
npm run e2e:report   # View last test report
```

**CI:**
- Tests run automatically on push/PR via `.github/workflows/e2e-tests.yml`
- Only runs on chromium in CI for speed
- Uploads reports and failure artifacts

**Docker:**
```bash
# From repository root
docker compose exec web npm run e2e
```

Note: E2E tests use mocked API responses so they can run without backend.
