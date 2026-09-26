/** @type {import('next').NextConfig} */
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), browsing-topics=()' },
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
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};

export default nextConfig;
