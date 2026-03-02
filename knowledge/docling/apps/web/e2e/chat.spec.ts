import { test, expect } from '@playwright/test';

/**
 * E2E Test: Chat Interaction
 * Tests sending messages and receiving responses via mocked API
 */
test.describe('Chat Interaction', () => {
  test.beforeEach(async ({ page }) => {
    // Mock session creation
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

    // Mock chat stream endpoint
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"content","content":"Lions are amazing big cats!"}\n\n',
        'data: {"type":"sources","sources":[{"title":"Lion Info","score":0.95}]}\n\n',
        'data: {"type":"followup","questions":["What do lions eat?","Where do lions live?"]}\n\n',
        'data: {"type":"done"}\n\n',
      ].join('');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: streamResponse,
      });
    });

    await page.goto('/');

    // Wait for session to initialize
    await page.waitForTimeout(500);
  });

  test('should send text message and receive response', async ({ page }) => {
    // Find text input
    const input = page.locator('textarea, input[type="text"]').first();
    await expect(input).toBeVisible();

    // Type a message
    await input.fill('Tell me about lions');

    // Find and click send button
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();

    // Wait for user message to appear
    await expect(page.locator('text=Tell me about lions')).toBeVisible();

    // Wait for assistant response
    await expect(page.locator('text=/Lions are amazing/i')).toBeVisible({ timeout: 5000 });
  });

  test('should display follow-up questions', async ({ page }) => {
    const input = page.locator('textarea, input[type="text"]').first();
    await input.fill('Tell me about lions');

    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();

    // Wait for response and followup questions
    await expect(page.locator('text=/What do lions eat/i')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=/Where do lions live/i')).toBeVisible();
  });

  test('should handle follow-up question clicks', async ({ page }) => {
    const input = page.locator('textarea, input[type="text"]').first();
    await input.fill('Tell me about lions');

    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();

    // Wait for followup to appear
    const followupButton = page.locator('text=/What do lions eat/i');
    await expect(followupButton).toBeVisible({ timeout: 5000 });

    // Click followup (should be clickable)
    await expect(followupButton).toBeEnabled();
    await followupButton.click();

    // Verify the question was sent
    await expect(page.locator('text=What do lions eat?')).toBeVisible();
  });
});
