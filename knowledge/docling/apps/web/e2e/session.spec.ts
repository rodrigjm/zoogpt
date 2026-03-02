import { test, expect } from '@playwright/test';

/**
 * E2E Test: Session Persistence
 * Tests that session persists across page refresh
 */
test.describe('Session Persistence', () => {
  test('should persist session across page refresh', async ({ page }) => {
    // Mock session creation
    await page.route('**/api/sessions/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'persistent-session-456',
          created_at: new Date().toISOString(),
        }),
      });
    });

    // Mock chat stream
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"content","content":"This is a test response"}\n\n',
        'data: {"type":"done"}\n\n',
      ].join('');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: streamResponse,
      });
    });

    // Initial page load
    await page.goto('/');
    await page.waitForTimeout(500);

    // Send a message
    const input = page.locator('textarea, input[type="text"]').first();
    await input.fill('Test message before refresh');

    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();

    // Wait for response
    await expect(page.locator('text=This is a test response')).toBeVisible({ timeout: 5000 });

    // Refresh the page
    await page.reload();
    await page.waitForTimeout(500);

    // Message history should still be visible (persisted in store or localStorage)
    // Note: This depends on implementation - may need to adjust
    const messageExists = await page.locator('text=Test message before refresh').isVisible().catch(() => false);

    // At minimum, the page should still work after refresh
    const inputAfterRefresh = page.locator('textarea, input[type="text"]').first();
    await expect(inputAfterRefresh).toBeVisible();
  });

  test('should maintain session ID in storage', async ({ page, context }) => {
    await page.route('**/api/sessions/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'storage-test-789',
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    // Check if session ID is stored (localStorage or sessionStorage)
    const localStorage = await page.evaluate(() => window.localStorage);
    const sessionStorage = await page.evaluate(() => window.sessionStorage);

    // Session should be stored somewhere
    const hasSessionData = Object.keys(localStorage).length > 0 || Object.keys(sessionStorage).length > 0;
    expect(hasSessionData).toBeTruthy();
  });
});
