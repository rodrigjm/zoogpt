import { test, expect } from '@playwright/test';

/**
 * E2E Test: Animal Pictures Feature
 * Tests "Want to see a picture?" button that appears after chat response with animal sources
 */
test.describe('Animal Pictures Feature', () => {
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

    // Mock chat stream with animal sources containing images
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"text","content":"Lions are fascinating animals! "}\n\n',
        'data: {"type":"text","content":"They live in prides and are known as the king of the jungle."}\n\n',
        'data: {"type":"done","sources":[{"animal":"Lion","title":"Lion Facts","thumbnail":"https://picsum.photos/seed/lion1/400/300","image_urls":["https://picsum.photos/seed/lion2/800/600","https://picsum.photos/seed/lion3/800/600"],"alt":"Lion in the wild"}],"followup_questions":[]}\n\n',
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

  test('should display "Want to see a picture?" button after response with images', async ({ page }) => {
    // Click Lion button to start chat (use specific aria-label to avoid matching followup chips)
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for assistant response
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Check for "Want to see a picture?" button
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await expect(pictureButton).toBeVisible({ timeout: 5000 });
  });

  test('should show image message when "Want to see a picture?" is clicked', async ({ page }) => {
    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for response
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Click the picture button
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await expect(pictureButton).toBeVisible({ timeout: 5000 });
    await pictureButton.click();

    // Verify new image message appears
    await expect(page.getByText(/Here's a picture of/i)).toBeVisible({ timeout: 5000 });

    // Verify images are displayed
    const images = page.locator('img[alt*="Animal picture"]');
    await expect(images.first()).toBeVisible({ timeout: 5000 });
  });

  test('should not show picture button when no images in sources', async ({ page }) => {
    // Override mock with no image_urls
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"text","content":"Lions are fascinating animals!"}\n\n',
        'data: {"type":"done","sources":[{"animal":"Lion","title":"Lion Facts"}],"followup_questions":[]}\n\n',
      ].join('');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: streamResponse,
      });
    });

    // Click Lion button
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for response
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Picture button should NOT appear (no images in sources)
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await expect(pictureButton).not.toBeVisible({ timeout: 2000 });
  });

  test('should not show picture button on image-only messages', async ({ page }) => {
    // Click Lion button
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for response and click picture button
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await expect(pictureButton).toBeVisible({ timeout: 5000 });
    await pictureButton.click();

    // Wait for image message
    await expect(page.getByText(/Here's a picture of/i)).toBeVisible({ timeout: 5000 });

    // The image-only message should NOT have another picture button (prevents infinite loop)
    const allPictureButtons = page.getByRole('button', { name: /Want to see a picture/i });
    const count = await allPictureButtons.count();
    // Should still only have 1 button (on original message), not on image message
    expect(count).toBe(1);
  });

  test('should display multiple images when sources have multiple image_urls', async ({ page }) => {
    // Click Lion button
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for response
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Click picture button
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await pictureButton.click();

    // Wait for image message
    await expect(page.getByText(/Here's a picture of/i)).toBeVisible({ timeout: 5000 });

    // Count images - mock has 2 image_urls
    const images = page.locator('img[alt*="Animal picture"]');
    const count = await images.count();
    expect(count).toBe(2);
  });

  test('should handle mobile viewport correctly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Click Lion button
    const lionButton = page.getByRole('button', { name: 'Learn about Lion' });
    await lionButton.click();

    // Wait for response
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Picture button should be visible and have proper touch target
    const pictureButton = page.getByRole('button', { name: /Want to see a picture/i });
    await expect(pictureButton).toBeVisible({ timeout: 5000 });

    // Click and verify image appears
    await pictureButton.click();
    await expect(page.getByText(/Here's a picture of/i)).toBeVisible({ timeout: 5000 });

    // Verify images fit within viewport
    const firstImage = page.locator('img[alt*="Animal picture"]').first();
    await expect(firstImage).toBeVisible();
    const boundingBox = await firstImage.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
  });
});
