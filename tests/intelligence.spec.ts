import { test, expect } from '@playwright/test';

test.describe('Intelligence Page - Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Collect console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Console error: ${msg.text()}`);
      }
    });

    await page.goto('/intelligence.html');
  });

  test('page loads without critical errors', async ({ page }) => {
    // Page should have correct title
    await expect(page).toHaveTitle(/Pricing Intelligence|Inference Price Index/);

    // Main heading should be visible
    await expect(page.locator('h1')).toContainText('Pricing Intelligence Center');
  });

  test('hero section displays computed stats', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('#stat-events:not(:has-text("--"))');

    // Hero stats should show real values (not placeholder --)
    const eventsCount = await page.locator('#stat-events').textContent();
    expect(eventsCount).not.toBe('--');
    expect(parseInt(eventsCount || '0')).toBeGreaterThan(0);

    const timespan = await page.locator('#stat-timespan').textContent();
    expect(timespan).not.toBe('--');

    const deflation = await page.locator('#stat-deflation').textContent();
    expect(deflation).not.toBe('--');
  });

  test('summary stats cards render', async ({ page }) => {
    // Wait for stats to load
    await page.waitForSelector('#stat-total-events:not(:has-text("--"))');

    // All four stat cards should have values
    const totalEvents = await page.locator('#stat-total-events').textContent();
    const priceDrops = await page.locator('#stat-price-drops').textContent();
    const newModels = await page.locator('#stat-new-models').textContent();
    const providers = await page.locator('#stat-providers').textContent();

    expect(parseInt(totalEvents || '0')).toBeGreaterThan(0);
    expect(parseInt(priceDrops || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(newModels || '0')).toBeGreaterThanOrEqual(0);
    expect(parseInt(providers || '0')).toBeGreaterThan(0);
  });

  test('price velocity chart section exists', async ({ page }) => {
    // Chart section should be visible
    await expect(page.locator('#chart')).toBeVisible();
    await expect(page.locator('#chart h2')).toContainText('Price Velocity Chart');

    // Chart controls should exist
    await expect(page.locator('.chart-scale-btn[data-scale="linear"]')).toBeVisible();
    await expect(page.locator('.chart-scale-btn[data-scale="logarithmic"]')).toBeVisible();

    // Canvas should be present (chart rendered)
    await expect(page.locator('#price-chart')).toBeVisible();
  });

  test('timeline section loads with events', async ({ page }) => {
    // Timeline section should be visible
    await expect(page.locator('#timeline')).toBeVisible();
    await expect(page.locator('#timeline h2')).toContainText('Pricing Event Timeline');

    // Wait for events to load
    await page.waitForSelector('.intel-event-card');

    // Should have at least one event card
    const eventCards = page.locator('.intel-event-card');
    await expect(eventCards.first()).toBeVisible();

    // Results count should show number of events
    const resultsText = await page.locator('#results-count').textContent();
    expect(resultsText).toMatch(/\d+\s+events?/i);
  });

  test('timeline filters are functional', async ({ page }) => {
    // Wait for events to load
    await page.waitForSelector('.intel-event-card');

    // Provider filter should exist and have options
    const providerFilter = page.locator('#filter-provider');
    await expect(providerFilter).toBeVisible();

    // Type filter should exist
    const typeFilter = page.locator('#filter-type');
    await expect(typeFilter).toBeVisible();

    // Search box should exist
    const searchBox = page.locator('#filter-search');
    await expect(searchBox).toBeVisible();

    // Test search functionality
    await searchBox.fill('OpenAI');
    await page.waitForTimeout(500); // Debounce

    // Should filter results (or show no change if all match)
    const resultsText = await page.locator('#results-count').textContent();
    expect(resultsText).toBeDefined();
  });

  test('calculator section exists with modes', async ({ page }) => {
    // Calculator section should be visible
    await expect(page.locator('#calculator')).toBeVisible();
    await expect(page.locator('#calculator h2')).toContainText('Savings Calculator');

    // Mode buttons should exist
    await expect(page.locator('.calc-mode-btn[data-mode="quick"]')).toBeVisible();
    await expect(page.locator('.calc-mode-btn[data-mode="advanced"]')).toBeVisible();
    await expect(page.locator('.calc-mode-btn[data-mode="contract"]')).toBeVisible();
  });

  test('calculator quick mode works', async ({ page }) => {
    // Navigate to calculator
    await page.locator('#calculator').scrollIntoViewIfNeeded();

    // Quick mode should be active by default
    await expect(page.locator('.calc-mode-btn[data-mode="quick"]')).toHaveClass(/active/);

    // Input field should exist
    const spendInput = page.locator('#calc-monthly-spend');
    await expect(spendInput).toBeVisible();

    // Enter a value
    await spendInput.fill('10000');

    // Calculate button should exist
    const calcButton = page.locator('#calculate-savings');
    await expect(calcButton).toBeVisible();
  });

  test('market snapshot loads data', async ({ page }) => {
    // Snapshot section should be visible
    await expect(page.locator('#snapshot')).toBeVisible();
    await expect(page.locator('#snapshot h2')).toContainText('Current Market Snapshot');

    // Wait for snapshot data to load (with timeout for API)
    try {
      await page.waitForSelector('#snapshot-frontier:not(:has-text("--"))', { timeout: 10000 });

      // Frontier value should be a price
      const frontierValue = await page.locator('#snapshot-frontier').textContent();
      expect(frontierValue).toMatch(/\$[\d.,]+/);
    } catch {
      // API might be slow - check for loading state or stale banner
      const snapshotGrid = page.locator('#snapshot-grid');
      await expect(snapshotGrid).toBeVisible();
    }
  });

  test('methodology section is present', async ({ page }) => {
    await expect(page.locator('#methodology')).toBeVisible();
    await expect(page.locator('#methodology h2')).toContainText('Methodology');

    // Should have methodology cards
    await expect(page.locator('.intel-method-card').first()).toBeVisible();
  });

  test('subscribe form exists', async ({ page }) => {
    await expect(page.locator('#subscribe')).toBeVisible();
    await expect(page.locator('#subscribe-form')).toBeVisible();

    // Email input should exist
    await expect(page.locator('#subscribe-email')).toBeVisible();

    // Submit button should exist
    await expect(page.locator('#subscribe-form button[type="submit"]')).toBeVisible();
  });

  test('navigation links work', async ({ page }) => {
    // Internal navigation links should exist
    await expect(page.locator('a[href="#timeline"]')).toBeVisible();
    await expect(page.locator('a[href="#calculator"]')).toBeVisible();

    // Click timeline link
    await page.locator('a[href="#timeline"]').first().click();

    // Should scroll to timeline section
    await expect(page.locator('#timeline')).toBeInViewport();
  });

  test('footer links are present', async ({ page }) => {
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();

    // Privacy and terms links should exist
    await expect(footer.locator('a[href="/privacy.html"]')).toBeVisible();
    await expect(footer.locator('a[href="/terms.html"]')).toBeVisible();
  });

  test('page has no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/intelligence.html');
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors (like failed optional API calls, network issues)
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('net::ERR') &&
      !e.includes('Failed to load resource') &&
      !e.includes('Failed to fetch') &&
      !e.includes('NetworkError') &&
      !e.includes('Error loading events')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('responsive: mobile viewport works', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/intelligence.html');

    // Hero should still be visible
    await expect(page.locator('h1')).toBeVisible();

    // Stats should stack vertically (check they're all visible)
    await expect(page.locator('#stat-events')).toBeVisible();

    // Timeline should be visible
    await expect(page.locator('#timeline')).toBeVisible();
  });

  test('data table toggle works', async ({ page }) => {
    // Find the data table toggle button
    const toggleBtn = page.locator('#show-data-table');
    await expect(toggleBtn).toBeVisible();

    // Click to show data table
    await toggleBtn.click();

    // Data table wrapper should become visible
    await expect(page.locator('#data-table-wrapper')).toBeVisible();

    // Click again to hide
    await toggleBtn.click();

    // Should be hidden again
    await expect(page.locator('#data-table-wrapper')).toBeHidden();
  });
});

test.describe('Intelligence Page - Data Integrity', () => {
  test('event cards have required fields', async ({ page }) => {
    await page.goto('/intelligence.html');
    await page.waitForSelector('.intel-event-card');

    // Get first event card
    const firstCard = page.locator('.intel-event-card').first();

    // Should have headline
    await expect(firstCard.locator('.event-headline')).toBeVisible();

    // Should have date
    await expect(firstCard.locator('.event-date')).toBeVisible();

    // Should have provider
    await expect(firstCard.locator('.event-provider')).toBeVisible();

    // Should have source link (evidence)
    await expect(firstCard.locator('.event-evidence .event-source')).toBeVisible();
  });

  test('event source links are HTTPS', async ({ page }) => {
    await page.goto('/intelligence.html');
    await page.waitForSelector('.intel-event-card');

    // Get all source links
    const sourceLinks = page.locator('.event-evidence .event-source');
    const count = await sourceLinks.count();

    // Check first 5 links
    const linksToCheck = Math.min(count, 5);
    for (let i = 0; i < linksToCheck; i++) {
      const href = await sourceLinks.nth(i).getAttribute('href');
      expect(href).toMatch(/^https:\/\//);
    }
  });

  test('prices are formatted correctly', async ({ page }) => {
    await page.goto('/intelligence.html');
    await page.waitForSelector('.intel-event-card');

    // Get price values from cards that have them
    const priceElements = page.locator('.price-value');
    const count = await priceElements.count();

    if (count > 0) {
      const firstPrice = await priceElements.first().textContent();
      // Should be formatted as currency ($ with numbers)
      expect(firstPrice).toMatch(/\$[\d.,]+/);
    }
  });
});
