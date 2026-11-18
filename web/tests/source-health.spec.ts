import { expect, test } from '@playwright/test';

test('source health shows default denial and scoped reasons with recovery', async ({ page }) => {
  let releaseSession!: () => void;
  const sessionReady = new Promise<void>(resolve => { releaseSession = resolve; });
  await page.route('**/api/session', async route => { await sessionReady; await route.continue(); });
  await page.goto('/');
  // Source reads require the session cookie, even when account startup is slow.
  await expect(page.getByRole('button', { name: 'Score a New Cut', exact: true })).toBeDisabled();
  releaseSession();
  await page.getByRole('button', { name: 'Score a New Cut', exact: true }).click();
  const panel = page.getByRole('region', { name: 'Source qualification and health' });
  await expect(panel).toContainText('No sources assigned to this workspace');
  let fail = false;
  // UI rendering fixture only. Actual scope/qualification behavior has server integration tests.
  await page.route('**/api/fresh/source-health', async route => {
    if (fail) return route.fulfill({ status: 503, contentType: 'application/json', body: '{}' });
    await route.fulfill({ json: { workspace_id: 'a'.repeat(64), access: 'Explicit grant', sources: [{
      device_id: 'ui-fixture', asset_id: 'UI test mill', site_id: 'Fixture site', health: 'attention_required',
      qualification: { id: null, state: 'unqualified', revision: 0, reason: 'source_not_qualified' },
      physical_connection: 'uncommissioned', last_received_at: '2026-01-01T00:00:00Z', evidence_cutoff: '2026-01-01T00:00:00Z',
      reason_codes: ['source_not_qualified', 'stale_observation', 'transport_gap'],
      processing: { state: 'abstained', assessment: { five_cut_score: null, action: 'monitor', reason_codes: ['sensor_or_domain_qualification_pending'], model_version: null } },
    }] } });
  });
  await panel.getByRole('button', { name: 'Refresh source health' }).click();
  await expect(panel).toContainText('UI test mill');
  await expect(panel).toContainText('stale observation');
  await expect(panel).toContainText('transport gap');
  await expect(panel).toContainText('Stored assessment score: Unavailable');
  fail = true;
  await panel.getByRole('button', { name: 'Refresh source health' }).click();
  await expect(panel.getByRole('alert')).toContainText('Previously displayed status may be outdated');
  fail = false;
  await panel.getByRole('button', { name: 'Refresh source health' }).click();
  await expect(panel.getByRole('alert')).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/source-health-fixture-mobile.png', fullPage: true });
});
