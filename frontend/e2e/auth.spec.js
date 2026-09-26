const { test, expect } = require('@playwright/test');

// Full sign-in journey. Needs a test account: E2E_EMAIL / E2E_PASSWORD (a member or admin without 2FA).
const email = process.env.E2E_EMAIL;
const password = process.env.E2E_PASSWORD;

test.describe('signed-in journey', () => {
  test.skip(!email || !password, 'Set E2E_EMAIL and E2E_PASSWORD to run the signed-in journey');

  test('sign in, open each workspace, sign out', async ({ page }) => {
    await page.goto('/login?next=/workspace/engineering');
    await page.fill('#login-email', email);
    await page.fill('#login-password', password);
    await page.click('button[type=submit]');
    // Match the path exactly: a glob would also match the starting URL /login?next=/workspace/engineering
    await page.waitForURL((url) => url.pathname === '/workspace/engineering');
    for (const path of ['/workspace/legal', '/workspace/medical', '/workspace/account']) {
      await page.goto(path);
      await expect(page.locator('.ws-header')).toBeVisible();
    }
    await page.locator('.ws-user summary').click();
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.waitForURL((url) => url.pathname === '/login');
    await page.goto('/workspace');
    await page.waitForURL(/\/login\?next=/);
  });
});
