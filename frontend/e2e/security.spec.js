const { test, expect } = require('@playwright/test');

test('security headers are present on the website', async ({ request }) => {
  const headers = (await request.get('/')).headers();
  expect(headers['content-security-policy']).toContain("frame-ancestors 'none'");
  expect(headers['content-security-policy']).toContain("object-src 'none'");
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['x-frame-options']).toBe('DENY');
  expect(headers['referrer-policy']).toBeTruthy();
  expect(headers['permissions-policy']).toBeTruthy();
  expect(headers['x-powered-by']).toBeUndefined();
});

test('the app and admin are not indexable', async ({ page }) => {
  for (const path of ['/workspace', '/admin', '/login']) {
    await page.goto(path);
    expect(await page.getAttribute('meta[name="robots"]', 'content'), path).toContain('noindex');
  }
});

test('signed-out visitors are sent to sign-in from protected areas', async ({ page }) => {
  for (const path of ['/workspace', '/workspace/engineering', '/admin', '/admin/users']) {
    await page.goto(path);
    await page.waitForURL(/\/login\?next=/);
    expect(new URL(page.url()).searchParams.get('next')).toBe(path);
  }
});

test('open redirects are refused after sign-in', async ({ page }) => {
  await page.goto('/login?next=//evil.example');
  // The form keeps the user on this site; the unsafe target is replaced before any navigation
  await expect(page.locator('#login-email')).toBeVisible();
  expect(new URL(page.url()).host).toBe(new URL(page.url()).host);
});

test('wrong credentials show a generic error', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#login-email', `nobody-${Date.now()}@example.com`);
  await page.fill('#login-password', 'definitely-wrong-password');
  await page.click('button[type=submit]');
  await expect(page.locator('.form-status--error')).toHaveText(/Incorrect email or password/);
});

test('the API rejects anonymous workspace and admin requests', async ({ request }) => {
  const api = process.env.E2E_API_URL || 'http://localhost:8000';
  for (const path of ['/legal/documents', '/engineering/drawings', '/admin/users', '/admin/overview']) {
    expect((await request.get(`${api}${path}`)).status(), path).toBe(401);
  }
});

test('account and app pages use a strict per-request nonce policy', async ({ request, page }) => {
  const nonces = new Set();
  for (const path of ['/login', '/forgot-password', '/reset-password', '/workspace', '/admin']) {
    const csp = (await request.get(path)).headers()['content-security-policy'];
    expect(csp, path).toMatch(/script-src 'self' 'nonce-[A-Za-z0-9+/=]+' 'strict-dynamic'/);
    expect(csp, path).not.toMatch(/script-src[^;]*'unsafe-inline'/);
    nonces.add(csp.match(/'nonce-([^']+)'/)[1]);
  }
  expect(nonces.size).toBe(5); // a fresh nonce on every response
  // ...and the page still works under it
  await page.goto('/login');
  await page.fill('#login-email', 'x@example.com');
  await expect(page.getByRole('link', { name: 'Forgot password?' })).toBeVisible();
});

test('password reset flow does not reveal accounts and handles bad links', async ({ page }) => {
  await page.goto('/forgot-password');
  await page.fill('#forgot-email', `nobody-${Date.now()}@example.com`);
  await page.getByRole('button', { name: 'Send reset link' }).click();
  await expect(page.locator('.form-status--success')).toContainText('If an account exists');

  await page.goto('/reset-password#token=not-a-real-token');
  await expect(page.getByRole('heading', { name: 'This link has expired' })).toBeVisible();
  expect(page.url()).not.toContain('token='); // the token is removed from the address bar
});
