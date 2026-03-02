import { test, expect } from '@playwright/test';

/**
 * E2E Test: Welcome Message
 * Verifies that the welcome message displays correctly on page load
 */
test.describe('Welcome Message', () => {
  test('should display welcome message on initial load', async ({ page }) => {
    await page.goto('/');

    // Wait for welcome message to be visible
    const welcomeMessage = page.getByText(/welcome to zoocari/i);
    await expect(welcomeMessage).toBeVisible();
  });

  test('should show Zoocari branding', async ({ page }) => {
    await page.goto('/');

    // Check for logo or app title
    const title = page.locator('text=/zoocari/i').first();
    await expect(title).toBeVisible();
  });
});
