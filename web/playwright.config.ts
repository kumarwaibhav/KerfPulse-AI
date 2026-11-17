import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  timeout: 60000,
  expect: { timeout: 10000 },
  reporter: 'list',
  outputDir: 'test-results',
  use: {
    baseURL: process.env.PDM_E2E_URL || 'http://127.0.0.1:8000',
    channel: 'chrome',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    viewport: { width: 1440, height: 1024 },
  },
});
