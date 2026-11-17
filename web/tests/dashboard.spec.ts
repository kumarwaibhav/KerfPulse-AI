import { expect, test } from '@playwright/test';
import { createServer, request, type ServerResponse } from 'node:http';

test('recorded replay supports pause, recovery, inspection and export', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('/');
  await expect(page).toHaveTitle(/KerfPulse AI/);
  await expect(page.getByRole('heading', { name: 'Shop floor.' })).toBeVisible();
  await page.getByRole('button', { name: 'New replay', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Cutter life').selectOption('2');
  await dialog.getByLabel('Evidence policy').selectOption('current');
  await dialog.getByLabel('Replay pace').selectOption('100');
  await dialog.getByLabel('Run a paired comparison').uncheck();
  await dialog.getByRole('button', { name: 'Start replay', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await page.getByRole('button', { name: 'Pause replay', exact: true }).click();
  await expect(page.locator('.run-toolbar .status-tag')).toHaveText('paused');
  await page.reload();
  await expect(page.locator('.run-toolbar .status-tag')).toHaveText('paused');
  await page.getByRole('button', { name: 'Resume replay', exact: true }).click();
  await expect(page.locator('.run-toolbar .status-tag')).toHaveText('completed', { timeout: 20000 });
  await expect(page.locator('.order-card').first()).toBeVisible();
  await page.getByRole('button', { name: 'Approve', exact: true }).first().click();
  await expect(page.locator('.order-card .status-tag').first()).toHaveText('approved');
  await page.getByRole('button', { name: 'Record completion', exact: true }).first().click();
  await page.getByLabel('Inspection finding').fill('Replay exercise. Reviewed archived tool evidence, no physical inspection performed.');
  await page.getByRole('button', { name: 'Save completion' }).click();
  await expect(page.locator('.order-card .status-tag').first()).toHaveText('completed');
  const download = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Export run' }).click();
  expect((await download).suggestedFilename()).toMatch(/^kerfpulse-.+\.json$/);
  await page.getByRole('button', { name: 'Evidence audit', exact: true }).click();
  await expect(page.locator('tbody tr')).not.toHaveCount(0);
  await page.getByRole('button', { name: 'Data quality', exact: true }).click();
  await expect(page.locator('tbody tr').first()).toContainText(/gap|conflict/);
  await page.getByRole('button', { name: 'Dark theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('button', { name: 'Light theme' }).click();
  await page.screenshot({ path: 'test-results/kerfpulse-light-desktop.png', fullPage: true });
  expect(failures).toEqual([]);
});

test('paired replay and research metrics remain readable across views', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('/');
  await page.getByRole('button', { name: 'New replay', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Cutter life').selectOption('2');
  await dialog.getByLabel('Evidence policy').selectOption('decision');
  await dialog.getByLabel('Replay pace').selectOption('100');
  await dialog.getByRole('button', { name: 'Start replay', exact: true }).click();
  await expect(page.locator('.run-card')).toHaveCount(2);
  await page.getByRole('button', { name: 'Pause replay', exact: true }).click();
  await page.reload();
  await expect(page.locator('.run-card')).toHaveCount(2);
  await page.getByRole('button', { name: 'Performance', exact: true }).click();
  await expect(page.locator('#compare-run')).not.toHaveValue('');
  await expect(page.getByRole('heading', { name: 'Held-out policy benchmark' })).toBeVisible();
  await expect(page.locator('.benchmark-row')).toHaveCount(4);
  await page.getByRole('button', { name: 'Shop floor', exact: true }).click();
  await page.getByRole('button', { name: 'Resume replay', exact: true }).click();
  await expect(page.locator('.run-toolbar .status-tag')).toHaveText('completed', { timeout: 30000 });
  await page.getByRole('button', { name: 'Dark theme' }).click();
  await page.screenshot({ path: 'test-results/kerfpulse-dark-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/kerfpulse-dark-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Data and method' }).click();
  await expect(page.getByRole('heading', { name: 'A measured foundation for every decision.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open pinned data' })).toHaveAttribute('href', 'https://doi.org/10.6084/m9.figshare.28589216.v1');
  expect(failures).toEqual([]);
});

test('first-cut damage shows measured outcome without fabricated forecast', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'New replay', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Cutter life').selectOption('11');
  await dialog.getByLabel('Run a paired comparison').uncheck();
  await dialog.getByRole('button', { name: 'Start replay', exact: true }).click();
  await expect(page.locator('.run-toolbar .status-tag')).toHaveText('completed');
  await expect(page.locator('.order-card')).toHaveCount(0);
  await page.getByRole('button', { name: 'Evidence audit', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(page.locator('tbody tr').first()).toContainText('Damage observed');
  await expect(page.getByText('No released feature values', { exact: true })).toHaveCount(2);
});

test('SSE catches up after the transport socket drops', async ({ page, baseURL }) => {
  const activeStreams = new Set<ServerResponse>();
  let streamRequests = 0;
  const proxy = createServer((source, response) => {
    const isStream = new URL(source.url!, baseURL).pathname.endsWith('/events');
    if (isStream) {
      activeStreams.add(response);
      streamRequests++;
    }
    const upstream = request(new URL(source.url!, baseURL), { method: source.method, headers: source.headers }, (result) => {
      response.writeHead(result.statusCode ?? 502, result.headers);
      result.pipe(response);
    });
    upstream.on('error', () => response.destroy());
    response.on('close', () => { activeStreams.delete(response); upstream.destroy(); });
    source.pipe(upstream);
  });
  await new Promise<void>((resolve, reject) => {
    proxy.on('error', reject);
    proxy.listen(0, '127.0.0.1', resolve);
  });
  try {
    const address = proxy.address();
    if (!address || typeof address === 'string') throw new Error('Expected proxy TCP address');
    await page.goto(`http://127.0.0.1:${address.port}/`);
    await page.getByRole('button', { name: 'New replay', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel('Cutter life').selectOption('2');
    await dialog.getByLabel('Evidence policy').selectOption('current');
    await dialog.getByLabel('Replay pace').selectOption('100');
    await dialog.getByLabel('Run a paired comparison').uncheck();
    await dialog.getByRole('button', { name: 'Start replay', exact: true }).click();
    await expect(page.locator('.run-toolbar .status-tag')).toHaveText('running');
    await expect(page.locator('.connection-label')).toHaveText('Stream connected');
    expect(activeStreams.size).toBe(1);
    for (const stream of activeStreams) stream.destroy();
    await expect.poll(() => streamRequests).toBeGreaterThan(1);
    await expect(page.locator('.run-toolbar .status-tag')).toHaveText('completed', { timeout: 30000 });
    await page.getByRole('button', { name: 'Evidence audit', exact: true }).click();
    await expect(page.locator('tbody tr')).toHaveCount(50);
    await expect(page.locator('tbody tr').first()).toContainText('Damage observed');
  } finally {
    proxy.closeAllConnections();
    await new Promise<void>((resolve) => proxy.close(() => resolve()));
  }
});
