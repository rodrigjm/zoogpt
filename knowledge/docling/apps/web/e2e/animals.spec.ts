import { test, expect } from '@playwright/test';

/**
 * E2E Test: Animal Quick Buttons
 * Tests the animal grid quick-select buttons
 */
test.describe('Animal Quick Buttons', () => {
  test.beforeEach(async ({ page }) => {
    // Mock session and chat endpoints
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

    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"content","content":"Here is information about that animal!"}\n\n',
        'data: {"type":"done"}\n\n',
      ].join('');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: streamResponse,
      });
    });

    await page.goto('/');
    await page.waitForTimeout(500);
  });

  test('should display animal quick buttons', async ({ page }) => {
    // Look for common animals - at least one should be visible
    const animalButtons = page.locator('button:has-text(/lion|giraffe|elephant|zebra/i)');
    await expect(animalButtons.first()).toBeVisible({ timeout: 3000 });
  });

  test('should send message when animal button clicked', async ({ page }) => {
    // Find and click an animal button
    const animalButton = page.locator('button:has-text(/lion|giraffe|elephant|zebra/i)').first();
    await animalButton.click();

    // Verify message appears in chat
    await expect(page.locator('text=/Here is information about/i')).toBeVisible({ timeout: 5000 });
  });

  test('should have multiple animal options', async ({ page }) => {
    // Should have at least 3 animal buttons
    const animalButtons = page.locator('button:has-text(/lion|giraffe|elephant|zebra|monkey|bear/i)');
    const count = await animalButtons.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});
