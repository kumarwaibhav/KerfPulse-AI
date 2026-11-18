import { expect, test } from '@playwright/test';

test('operations workspace separates named login from research access', async ({ page }) => {
  let demoSessionRequests = 0;
  await page.route('**/api/session', route => { demoSessionRequests++; return route.fulfill({ status: 409, json: { detail: 'Demo session capacity reached' } }); });
  await page.goto('/?workspace=operations');
  await expect(page.getByRole('heading', { name: 'Operations workspace', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'New replay', exact: true })).toHaveCount(0);
  // Render fixture only; real OIDC signature, PKCE and grants are tested separately.
  await page.route('**/api/auth/me', route => route.fulfill({ json: { configured: true, authenticated: true, person: {
    id: 'test-person', display_name: 'Operator UI fixture', csrf: 'test-csrf', expires_at: '2030-01-01T00:00:00Z',
    grants: [{ org_id: 'fixture-org', site_id: 'fixture-site', asset_id: 'fixture-asset', role: 'operator' }],
  } } }));
  await page.route('**/api/operations/sources', route => route.fulfill({ json: { workspace_id: 'test-person', sources: [], access: 'Exact grants' } }));
  await page.getByRole('button', { name: 'Refresh account' }).click();
  await expect(page.getByRole('heading', { name: 'Operator UI fixture' })).toBeVisible();
  await expect(page.getByText('fixture-org / fixture-site / fixture-asset · operator')).toBeVisible();
  await expect(page.getByRole('region', { name: 'Source qualification and health' })).toContainText('No sources assigned');
  await page.route('**/api/auth/logout', async route => {
    expect(route.request().headers()['x-csrf-token']).toBe('test-csrf');
    await page.route('**/api/auth/me', r => r.fulfill({ json: { configured: true, authenticated: false, person: null } }));
    await route.fulfill({ json: { signed_out: true } });
  });
  await page.getByRole('button', { name: 'Sign out of application' }).click();
  await expect(page.getByRole('link', { name: 'Sign in with organization' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Source qualification and health' })).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(demoSessionRequests).toBe(0);
});
