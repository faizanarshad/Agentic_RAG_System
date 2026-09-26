const { test, expect } = require('@playwright/test');
const { PUBLIC_PAGES } = require('./pages');

// Every public page: renders, one h1, SEO metadata, valid structured data, no console errors, fits the screen
for (const path of PUBLIC_PAGES) {
  test(`page ${path} passes content and SEO checks`, async ({ page, baseURL }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

    const response = await page.goto(path, { waitUntil: 'networkidle' });
    expect(response.status(), 'HTTP status').toBe(200);

    await expect(page.locator('h1'), 'exactly one h1').toHaveCount(1);
    const title = await page.title();
    expect(title.length, 'title length').toBeGreaterThan(10);
    expect(title.length, 'title length').toBeLessThanOrEqual(70);
    const description = await page.getAttribute('meta[name="description"]', 'content');
    expect(description?.length || 0, 'meta description').toBeGreaterThan(50);
    expect(description.length, 'meta description ≤ 170').toBeLessThanOrEqual(170);
    const canonical = await page.getAttribute('link[rel="canonical"]', 'href');
    expect(canonical, 'canonical URL').toBeTruthy();
    expect(new URL(canonical).pathname.replace(/\/$/, '') || '/').toBe(path.replace(/\/$/, '') || '/');
    expect(await page.getAttribute('meta[property="og:image"]', 'content'), 'og:image').toBeTruthy();
    expect(await page.getAttribute('html', 'lang')).toBe('en');

    const jsonLd = await page.locator('script[type="application/ld+json"]').allTextContents();
    expect(jsonLd.length, 'structured data present').toBeGreaterThan(0);
    for (const block of jsonLd) {
      const data = JSON.parse(block);
      for (const item of Array.isArray(data) ? data : [data]) {
        expect(item['@context']).toBe('https://schema.org');
        expect(item['@type']).toBeTruthy();
      }
    }

    const missingAlt = await page.locator('img:not([alt])').count();
    expect(missingAlt, 'images without alt').toBe(0);

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, 'horizontal overflow (px)').toBeLessThanOrEqual(1);

    expect(errors, 'console errors').toEqual([]);
  });
}

test('internal links resolve (no broken links)', async ({ page, request }) => {
  const seen = new Set();
  const broken = [];
  for (const path of PUBLIC_PAGES) {
    await page.goto(path);
    const hrefs = await page.locator('a[href^="/"]').evaluateAll((as) => as.map((a) => a.getAttribute('href')));
    for (const href of hrefs) {
      const url = href.split('#')[0];
      if (!url || seen.has(url)) continue;
      seen.add(url);
      const response = await request.get(url, { maxRedirects: 5 });
      if (response.status() >= 400) broken.push(`${url} → ${response.status()} (from ${path})`);
    }
  }
  expect(broken, 'broken internal links').toEqual([]);
  expect(seen.size).toBeGreaterThan(10);
});

test('robots.txt and sitemap.xml are valid', async ({ request }) => {
  const robots = await (await request.get('/robots.txt')).text();
  expect(robots).toContain('Disallow: /workspace');
  expect(robots).toMatch(/Sitemap: https?:\/\/.+\/sitemap\.xml/);

  const sitemap = await (await request.get('/sitemap.xml')).text();
  const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  expect(urls.length).toBeGreaterThanOrEqual(PUBLIC_PAGES.length);
  for (const url of urls) {
    const status = (await request.get(new URL(url).pathname)).status();
    expect(status, url).toBe(200);
  }
  expect(urls.some((u) => u.includes('/workspace') || u.includes('/admin') || u.includes('/login'))).toBe(false);
});

test('404 page is served for unknown URLs and not indexed', async ({ page }) => {
  const response = await page.goto('/this-page-does-not-exist');
  expect(response.status()).toBe(404);
  expect(await page.getAttribute('meta[name="robots"]', 'content')).toContain('noindex');
});
