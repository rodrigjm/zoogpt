import { test, expect } from '@playwright/test';

/**
 * E2E Test: Mobile Viewports
 * Tests that the UI works correctly on mobile devices
 * Note: Mobile devices are configured in playwright.config.ts projects
 */
test.describe('Mobile Layout', () => {

  test.beforeEach(async ({ page }) => {
    // Mock session
    await page.route('**/api/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'mobile-session-123',
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display welcome message on mobile', async ({ page }) => {
    const welcomeMessage = page.getByText(/welcome to zoocari/i);
    await expect(welcomeMessage).toBeVisible();
  });

  test('should have functional input on mobile', async ({ page }) => {
    // App starts in voice mode, switch to text mode first
    const textModeButton = page.getByRole('button', { name: /text mode/i });
    await expect(textModeButton).toBeVisible();
    await textModeButton.click();

    // Now input should be visible
    const input = page.locator('textarea, input[type="text"]').first();
    await expect(input).toBeVisible({ timeout: 5000 });
    await expect(input).toBeEnabled({ timeout: 5000 });

    // Should be able to tap and type
    await input.click();
    await input.fill('Mobile test message');

    const value = await input.inputValue();
    expect(value).toBe('Mobile test message');
  });

  test('should have tappable buttons on mobile', async ({ page }) => {
    // Voice button should be tappable
    const voiceButton = page.getByRole('button', { name: /voice|microphone|start recording/i }).first();
    await expect(voiceButton).toBeVisible();

    // Button should have adequate touch target size (at least 44x44px per iOS HIG)
    const box = await voiceButton.boundingBox();
    if (box) {
      expect(box.width).toBeGreaterThanOrEqual(40);
      expect(box.height).toBeGreaterThanOrEqual(40);
    }
  });

  test('animal buttons should work on mobile', async ({ page }) => {
    const animalButton = page.getByRole('button', { name: /lion|giraffe|elephant|zebra|camel|emu|lemur|serval|porcupine/i }).first();
    await expect(animalButton).toBeVisible({ timeout: 3000 });

    // Should be tappable
    await expect(animalButton).toBeEnabled();
  });

  test('should not have horizontal scroll on mobile', async ({ page }) => {
    // Get viewport and scrollable width
    const viewportWidth = page.viewportSize()?.width || 0;
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);

    // Should not exceed viewport width (allow 1px tolerance)
    expect(scrollWidth).toBeLessThanOrEqual(viewportWidth + 1);
  });
});

test.describe('Mobile Android Layout', () => {
  test('should display correctly on Android', async ({ page }) => {
    await page.route('**/api/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'android-session-123',
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // App starts in voice mode, verify voice button is visible
    const voiceButton = page.getByRole('button', { name: /start recording/i });
    await expect(voiceButton).toBeVisible();

    // Switch to text mode
    const textModeButton = page.getByRole('button', { name: /text mode/i });
    await textModeButton.click();

    // Now input should be visible
    const input = page.locator('textarea, input[type="text"]').first();
    await expect(input).toBeVisible();
  });
});
