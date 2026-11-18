// Actual loopback Keycloak browser journey; no mocked tokens or sensor data.
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';
const require = createRequire(new URL('../web/package.json', import.meta.url));
const { chromium } = require('@playwright/test');
const credentials = JSON.parse(await readFile(new URL('../artifacts/private-identity/engineer.json', import.meta.url), 'utf8'));
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  const context = await browser.newContext({ baseURL: 'http://localhost:8000', viewport: { width: 1440, height: 1024 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/?workspace=operations');
  await page.getByRole('link', { name: 'Sign in with organization', exact: true }).click();
  await page.locator('#username').fill(credentials.username);
  await page.locator('#password').fill(credentials.password);
  await page.locator('#kc-login').click();
  await page.waitForURL('http://localhost:8000/?workspace=operations');
  await page.getByRole('heading', { name: 'Local Engineer', exact: true }).waitFor();
  const identity = await (await page.request.get('/api/auth/me')).json();
  assert.equal(identity.authenticated, true);
  assert.deepEqual(identity.person.grants, []);
  const sources = await page.request.get('/api/operations/sources');
  assert.equal(sources.status(), 200);
  assert.deepEqual((await sources.json()).sources, []);
  const badLogout = await page.request.post('/api/auth/logout', { data: {}, headers: { 'X-CSRF-Token': 'incorrect' } });
  assert.equal(badLogout.status(), 403);
  await page.screenshot({ path: 'artifacts/identity-workspace.png', fullPage: true });
  await page.getByRole('button', { name: 'Sign out of application', exact: true }).click();
  await page.getByRole('link', { name: 'Sign in with organization', exact: true }).waitFor();
  assert.equal((await (await page.request.get('/api/auth/me')).json()).authenticated, false);
  assert.equal((await page.request.get('/api/operations/sources')).status(), 401);
  assert.deepEqual(errors, []);
  const receipt = { provider: 'Actual local Keycloak profile', protocol: 'Authorization code, PKCE S256, signed RS256 ID token',
    browser_login: 'passed', default_no_grants: 'passed', scoped_empty_sources: 'passed', csrf_denial: 'passed',
    browser_logout: 'passed', post_logout_denial: 'passed', browser_errors: errors,
    physical_source: 'Not commissioned; no device or source grant created', recorded_at: new Date().toISOString() };
  await writeFile('artifacts/identity-verification.json', JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt));
} finally { await browser.close(); }
