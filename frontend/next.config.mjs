/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production';
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').origin;
const siteIsHttps = (process.env.NEXT_PUBLIC_SITE_URL || '').startsWith('https://');

// Content-Security-Policy for the public, statically rendered site: scripts, styles and fonts from this site
// only; data calls and images may also come from the API. 'unsafe-inline' is needed for Next.js's inline
// bootstrap scripts on static pages (nonces require per-request rendering); 'unsafe-eval' only in development.
// Sign-in, password reset, workspace and admin pages get a stricter per-request nonce policy from proxy.js.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: ${apiOrigin}`,
  "font-src 'self'",
  `connect-src 'self' ${apiOrigin}${isDev ? ' ws: wss:' : ''}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join('; ');

const NONCE_PAGES = 'login|forgot-password|reset-password|workspace|admin';

const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), browsing-topics=()' },
  { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
  // HSTS only when the site is actually served over HTTPS
  ...(siteIsHttps ? [{ key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' }] : []),
];

const nextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  images: {
    // AVIF first, WebP fallback; next/image negotiates per browser
    formats: ['image/avif', 'image/webp'],
    qualities: [75, 85],
  },
  async headers() {
    // Next.js already serves /_next/static with immutable, year-long caching in production
    return [
      { source: '/:path*', headers: securityHeaders },
      { source: `/((?!${NONCE_PAGES}).*)`, headers: [{ key: 'Content-Security-Policy', value: csp }] },
    ];
  },
};

export default nextConfig;
