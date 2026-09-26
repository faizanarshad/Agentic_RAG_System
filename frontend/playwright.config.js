// End-to-end QA for the public website and the application's access control.
// Run against a running site: E2E_BASE_URL (default http://localhost:3001) with the API up.
const { defineConfig, devices } = require('@playwright/test');

const channel = process.env.PW_CHANNEL; // e.g. "chrome" to use an installed Chrome instead of bundled Chromium

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3001',
    trace: 'retain-on-failure',
    ...(channel ? { channel } : {}),
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], ...(channel ? { channel } : {}) } },
    { name: 'mobile', use: { ...devices['Pixel 7'], ...(channel ? { channel } : {}) } },
  ],
});
