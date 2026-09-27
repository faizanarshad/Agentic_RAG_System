const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const { PUBLIC_PAGES } = require('./pages');

// WCAG 2.1 A/AA automated checks. Serious and critical violations fail the run.
// Reduced motion so contrast is measured on the settled page, not mid-way through a scroll reveal.
test.use({ reducedMotion: 'reduce' });

for (const path of [...PUBLIC_PAGES, '/login', '/forgot-password', '/reset-password']) {
  test(`accessibility: ${path}`, async ({ page }) => {
    await page.goto(path, { waitUntil: 'networkidle' });
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    const blocking = results.violations
      .filter((v) => ['serious', 'critical'].includes(v.impact))
      .map((v) => `${v.id} (${v.impact}): ${v.help} — ${v.nodes.length} element(s): ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`);
    expect(blocking, 'serious/critical accessibility violations').toEqual([]);
  });
}
