import { absoluteUrl } from '@/lib/site';

export default function robots() {
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: ['/workspace'] }],
    sitemap: absoluteUrl('/sitemap.xml'),
  };
}
