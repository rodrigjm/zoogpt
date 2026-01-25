import { test, expect } from '@playwright/test';

/**
 * E2E Test: Animal Pictures Feature
 * Tests collapsible image gallery that appears after chat response with animal mentions
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

    // Mock chat stream with animal sources
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"content","content":"Lions are fascinating animals! "}\n\n',
        'data: {"type":"content","content":"They live in prides and are known as the king of the jungle."}\n\n',
        'data: {"type":"sources","sources":[{"animal":"Lion","thumbnail":"https://picsum.photos/seed/lion1/400/300","image_urls":["https://picsum.photos/seed/lion2/800/600","https://picsum.photos/seed/lion3/800/600"],"alt":"Lion in the wild"}]}\n\n',
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

  test('should display collapsible gallery button after response', async ({ page }) => {
    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait a bit for stream to complete
    await page.waitForTimeout(3000);

    // Check for any assistant message text
    const assistantMessage = page.locator('text=/Lions/i');
    await expect(assistantMessage.first()).toBeVisible({ timeout: 5000 });

    // Check for collapsible gallery button with "photos"
    const galleryButton = page.getByRole('button', { name: /photos/i });
    await expect(galleryButton).toBeVisible({ timeout: 5000 });
  });

  test('should expand and collapse gallery on button click', async ({ page }) => {
    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait for response to complete
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Wait for gallery button
    const galleryButton = page.getByRole('button', { name: /See.*Lion.*photos/i });
    await expect(galleryButton).toBeVisible({ timeout: 5000 });

    // Click to expand gallery
    await galleryButton.click();

    // Verify button text changes to "Hide photos"
    await expect(page.getByRole('button', { name: /Hide photos/i })).toBeVisible({ timeout: 3000 });

    // Verify images are shown in grid
    const gallery = page.locator('#animal-gallery');
    await expect(gallery).toBeVisible();

    // Click to collapse
    const hideButton = page.getByRole('button', { name: /Hide photos/i });
    await hideButton.click();

    // Verify gallery is hidden
    await expect(gallery).not.toBeVisible();
  });

  test('should display correct number of images', async ({ page }) => {
    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait for response to complete
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Wait and expand gallery
    const galleryButton = page.getByRole('button', { name: /See.*photos/i });
    await expect(galleryButton).toBeVisible({ timeout: 5000 });

    // Check button shows count in parentheses
    const buttonText = await galleryButton.textContent();
    expect(buttonText).toMatch(/\(\d+\)/);

    await galleryButton.click();

    // Count images in grid
    const images = page.locator('#animal-gallery img');
    const count = await images.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should open lightbox when image is clicked', async ({ page }) => {
    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait for response to complete
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Expand gallery
    const galleryButton = page.getByRole('button', { name: /See.*photos/i });
    await expect(galleryButton).toBeVisible({ timeout: 5000 });
    await galleryButton.click();

    // Click first image
    const firstImage = page.locator('#animal-gallery img').first();
    await firstImage.click();

    // Verify lightbox appears - check for fixed overlay
    const lightbox = page.locator('.fixed.inset-0');
    await expect(lightbox.first()).toBeVisible({ timeout: 3000 });
  });

  test('should not show gallery before streaming completes', async ({ page }) => {
    // Override mock with incomplete stream
    await page.route('**/api/chat/stream', async (route) => {
      const streamResponse = [
        'data: {"type":"content","content":"Lions are fascinating... "}\n\n',
        // Note: no "done" event yet
      ].join('');

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: streamResponse,
      });
    });

    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait a moment
    await page.waitForTimeout(2000);

    // Gallery button should not appear yet
    const galleryButton = page.getByRole('button', { name: /See.*photos/i });
    await expect(galleryButton).not.toBeVisible();
  });

  test('should handle mobile viewport correctly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Click Lion button to start chat
    const lionButton = page.getByRole('button', { name: 'Lion' });
    await lionButton.click();

    // Wait for response to complete
    await expect(page.getByText(/Lions are fascinating/i)).toBeVisible({ timeout: 10000 });

    // Expand gallery
    const galleryButton = page.getByRole('button', { name: /See.*photos/i });
    await expect(galleryButton).toBeVisible({ timeout: 5000 });
    await galleryButton.click();

    // Verify gallery grid is visible and responsive
    const gallery = page.locator('#animal-gallery');
    await expect(gallery).toBeVisible();

    // Check that images fit within viewport
    const firstImage = page.locator('#animal-gallery img').first();
    const boundingBox = await firstImage.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
  });
});
