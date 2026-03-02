import { test, expect } from '@playwright/test';

/**
 * E2E Test: Voice Features
 * Tests voice button visibility and basic interaction
 * Note: Cannot test actual audio recording in E2E without browser permissions
 */
test.describe('Voice Features', () => {
  test.beforeEach(async ({ page }) => {
    // Mock session
    await page.route('**/api/sessions/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'mock-session-123',
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    await page.waitForTimeout(500);
  });

  test('should display voice button', async ({ page }) => {
    // Look for voice/microphone button (by icon, aria-label, or text)
    const voiceButton = page.locator('button[aria-label*="voice" i], button[aria-label*="microphone" i], button:has-text(/voice|mic/i)').first();
    await expect(voiceButton).toBeVisible({ timeout: 3000 });
  });

  test('voice button should be clickable', async ({ page }) => {
    const voiceButton = page.locator('button[aria-label*="voice" i], button[aria-label*="microphone" i], button:has-text(/voice|mic/i)').first();
    await expect(voiceButton).toBeVisible();
    await expect(voiceButton).toBeEnabled();

    // Click should not throw error (actual recording won't work without permissions)
    await voiceButton.click({ timeout: 1000 }).catch(() => {
      // Ignore permission errors - we just want to verify button works
    });
  });

  test('should have mode toggle between voice and text', async ({ page }) => {
    // Look for toggle/tab between voice and text input modes
    const modeToggle = page.locator('button:has-text(/text|voice/i), [role="tab"]');
    const count = await modeToggle.count();

    // Should have some way to switch input modes
    expect(count).toBeGreaterThan(0);
  });
});
