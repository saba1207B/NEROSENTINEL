import { expect, test } from '@playwright/test';

const apiBase = process.env.AQUASENTINEL_API_URL || 'http://127.0.0.1:8000/api/v1';
const appAlert = (page: import('@playwright/test').Page) => page.locator('[role="alert"]:not(#__next-route-announcer__)');

test('production pages hydrate real synthetic pilot data', async ({ page }) => {
  const browserErrors: string[] = [];
  page.on('pageerror', (error) => browserErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && !message.text().includes('ERR_ABORTED')) browserErrors.push(message.text());
  });
  const pages = [
    ['/dashboard', 'Climate Command Center', 'Synthetic pilot'],
    ['/dashboard/climate', 'Climate Intelligence', 'Synthetic pilot'],
    ['/dashboard/water', 'Water Resources', 'Synthetic pilot'],
    ['/dashboard/map', 'Pilot Risk Explorer', 'synthetic Coimbatore pilot point'],
    ['/dashboard/twin', 'Water Digital Twin', 'Synthetic pilot'],
    ['/dashboard/warnings', 'Early Warning Center', 'local-test alert'],
    ['/dashboard/copilot', 'NeroSentinel Evidence Assistant', 'Deterministic backend explanations'],
    ['/dashboard/simulator', 'Scenario Simulator', 'synthetic Coimbatore pilot'],
    ['/dashboard/settings', 'Connection & Demo Access', 'Connected · healthy'],
  ] as const;
  for (const [path, heading, evidence] of pages) {
    await page.goto(path);
    await expect(page).toHaveTitle(/NeroSentinel/);
    await expect(page.getByRole('link', { name: 'NeroSentinel overview' })).toBeVisible();
    await expect(page.getByText('AquaSentinel', { exact: false })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    await expect(page.getByText(evidence, { exact: false }).first()).toBeVisible();
    await expect(appAlert(page), `No application error on ${path}`).toHaveCount(0);
  }
  expect(browserErrors, 'no uncaught page or browser-console errors').toEqual([]);
});

test('API uses the browser origin and allows the configured CORS preflight', async ({ request }) => {
  const response = await request.fetch(`${apiBase}/scenarios`, {
    method: 'OPTIONS',
    headers: {
      Origin: 'http://127.0.0.1:3000',
      'Access-Control-Request-Method': 'POST',
      'Access-Control-Request-Headers': 'authorization,content-type',
    },
  });
  expect(response.status()).toBe(200);
  expect(response.headers()['access-control-allow-origin']).toBe('http://127.0.0.1:3000');
});

test('auth and input validation fail closed over HTTP', async ({ request }) => {
  const scenario = { name: 'Browser validation', region_id: 'tn-coimbatore', months: 6 };
  expect((await request.post(`${apiBase}/scenarios`, { data: scenario })).status()).toBe(401);
  expect((await request.post(`${apiBase}/scenarios`, { data: scenario, headers: { Authorization: 'Bearer invalid' } })).status()).toBe(401);
  expect((await request.post(`${apiBase}/assistant/query`, { data: { question: 'a', region_id: 'tn-coimbatore' } })).status()).toBe(422);
});

test('simulator refuses a run without a token', async ({ page }) => {
  await page.goto('/dashboard/simulator');
  await page.getByRole('button', { name: 'Run on backend' }).click();
  await expect(appAlert(page)).toContainText('demo bearer token is required');
  await expect(page.getByText('Baseline unmet demand')).toHaveCount(0);
});

test('backend unavailability is visible without mock fallback', async ({ page }) => {
  await page.route(`${apiBase}/dashboard/summary`, (route) => route.abort('failed'));
  await page.goto('/dashboard');
  await expect(appAlert(page)).toContainText('Backend unreachable', { timeout: 20_000 });
  await expect(page.getByText('Drought screening score')).toHaveCount(0);
});

test('dashboard shows a loading state while API data is delayed', async ({ page }) => {
  await page.route(`${apiBase}/dashboard/summary`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.continue();
  });
  await page.goto('/dashboard');
  await expect(page.getByText('Loading the pilot command center…')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Climate Command Center' })).toBeVisible();
});

test('water search and synthetic map marker remain interactive', async ({ page }) => {
  await page.goto('/dashboard/water');
  await expect(page.getByRole('table')).toContainText('demo-reservoir-1');
  await page.getByRole('textbox', { name: 'Search reservoirs' }).fill('no such reservoir');
  await expect(page.getByText('No pilot reservoir matches that search.')).toBeVisible();
  await page.goto('/dashboard/map');
  await page.getByRole('button', { name: 'Open synthetic pilot point' }).click();
  await expect(page.getByText('Synthetic pilot marker')).toBeVisible();
});

test('settings reports backend unavailability and allows retry', async ({ page }) => {
  await page.route(`${apiBase}/health`, (route) => route.abort('failed'));
  await page.goto('/dashboard/settings');
  await expect(page.getByText('Unavailable: Backend unreachable', { exact: false })).toBeVisible();
  await page.unroute(`${apiBase}/health`);
  await page.getByRole('button', { name: 'Check again' }).click();
  await expect(page.getByText('Connected · healthy')).toBeVisible();
});

test('design tokens, typography, grain, mobile navigation and responsive widths', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle('NeroSentinel');
  await expect(page.getByRole('link', { name: 'NeroSentinel home' }).locator('img')).toBeVisible();
  await expect(page.locator('link[rel="icon"][type="image/svg+xml"]').first()).toHaveAttribute('href', '/nerosentinel-mark.svg');
  await expect(page.locator('link[rel="icon"][type="image/x-icon"]')).toHaveCount(0);
  await expect(page.locator('meta[property="og:site_name"]')).toHaveAttribute('content', 'NeroSentinel');
  await expect(page.getByText('Intelligent Water Intelligence & Drought Resilience Platform')).toBeVisible();
  await expect(page.getByText('AquaSentinel', { exact: false })).toHaveCount(0);
  const theme = await page.evaluate(() => ({
    forest: getComputedStyle(document.documentElement).getPropertyValue('--forest').trim(),
    display: getComputedStyle(document.querySelector('h1')!).fontFamily,
    grainOpacity: getComputedStyle(document.body, '::after').opacity,
  }));
  expect(theme.forest).toBe('#01472e');
  expect(theme.display.toLowerCase()).toContain('anton');
  expect(theme.grainOpacity).toBe('0.04');
  const firstCard = page.locator('.feature-card').first();
  await firstCard.scrollIntoViewIfNeeded();
  await expect(firstCard).toHaveAttribute('data-visible', 'true');

  const homeNav = page.locator('.site-nav');
  for (const width of [320, 375, 430, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect.poll(async () => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(await homeNav.evaluate((element) => element.scrollWidth <= element.clientWidth), `home navigation at ${width}px`).toBe(true);
  }

  await page.goto('/dashboard');
  await expect(page).toHaveTitle('NeroSentinel');
  await expect(page.getByRole('link', { name: 'NeroSentinel overview' }).locator('img')).toBeVisible();
  await expect(page.getByText('NeroSentinel', { exact: true }).first()).toBeVisible();
  for (const width of [320, 375, 430, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect.poll(async () => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.goto('/dashboard/map');
  for (const width of [320, 375, 430, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await expect.poll(async () => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await expect(page.getByRole('button', { name: 'Open synthetic pilot point' })).toBeVisible();
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/dashboard');
  await page.getByRole('button', { name: 'Open navigation menu' }).click();
  await expect(page.getByRole('navigation', { name: 'Platform modules' }).last()).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('navigation', { name: 'Platform modules' })).toHaveCount(0);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
});

test('copilot returns a bounded backend explanation', async ({ page }) => {
  await page.goto('/dashboard/copilot');
  await page.getByRole('textbox', { name: 'Ask the evidence assistant' }).fill('Why is drought risk elevated?');
  await page.getByRole('button', { name: 'Send question' }).click();
  await expect(page.getByText('Consulting backend rules…')).toHaveCount(0);
  await expect(page.getByRole('note').first()).toBeVisible();
  await expect(appAlert(page)).toHaveCount(0);
});

test('researcher scenario results match backend totals and conserve mass', async ({ page }) => {
  const token = process.env.AQUASENTINEL_TEST_RESEARCHER_TOKEN;
  test.skip(!token, 'Set AQUASENTINEL_TEST_RESEARCHER_TOKEN from the local demo token script');
  await page.addInitScript((value) => sessionStorage.setItem('aquasentinel_demo_token', value), token!);
  const runs: { data: { trajectory: { unmet_mcm: number }[]; total_unmet_mcm: number; mass_balance_error_mcm: number } }[] = [];
  page.on('response', async (response) => {
    if (response.request().method() === 'POST' && /\/scenarios\/[^/]+\/run$/.test(response.url()) && response.ok()) {
      runs.push(await response.json());
    }
  });
  await page.goto('/dashboard/simulator');
  await page.getByRole('button', { name: 'Run on backend' }).click();
  await expect(page.getByText('Baseline unmet demand')).toBeVisible();
  await expect.poll(() => runs.length).toBe(2);
  for (const run of runs) {
    expect(run.data.trajectory).toHaveLength(12);
    const sum = run.data.trajectory.reduce((total, month) => total + month.unmet_mcm, 0);
    expect(Math.abs(sum - run.data.total_unmet_mcm)).toBeLessThan(1e-6);
    expect(Math.abs(run.data.mass_balance_error_mcm)).toBeLessThan(1e-6);
    await expect(page.getByText(`${run.data.total_unmet_mcm.toFixed(2)} MCM`, { exact: true }).first()).toBeVisible();
  }
  await expect(appAlert(page)).toHaveCount(0);
});

test('researcher cannot acknowledge an alert', async ({ request }) => {
  const token = process.env.AQUASENTINEL_TEST_RESEARCHER_TOKEN;
  test.skip(!token, 'Set AQUASENTINEL_TEST_RESEARCHER_TOKEN from the local demo token script');
  const response = await request.post(`${apiBase}/alerts/demo-low-storage/acknowledge`, {
    data: {}, headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.status()).toBe(403);
});

test('authority acknowledgement is a local record only', async ({ page, request }) => {
  const token = process.env.AQUASENTINEL_TEST_AUTHORITY_TOKEN;
  test.skip(!token, 'Set AQUASENTINEL_TEST_AUTHORITY_TOKEN from the local demo token script');
  const created = await request.post(`${apiBase}/alerts/rules?threshold=0.25`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(created.ok()).toBe(true);
  const { data: rule } = await created.json();
  await page.addInitScript((value) => sessionStorage.setItem('aquasentinel_demo_token', value), token!);
  await page.goto('/dashboard/warnings');
  const acknowledgement = page.waitForResponse((response) =>
    response.request().method() === 'POST' && response.url().includes(`/alerts/${rule.id}/acknowledge`),
  );
  await page.getByRole('button', { name: 'Acknowledge with authority token' }).last().click();
  const acknowledged = await (await acknowledgement).json();
  expect(acknowledged.data.id).toBe(rule.id);
  expect(acknowledged.data.status).toBe('acknowledged');
  await expect(page.getByRole('button', { name: 'Acknowledge with authority token' })).toHaveCount(0);
  await expect(page.getByText('no SMS, email or public warning delivery', { exact: false })).toBeVisible();
});
