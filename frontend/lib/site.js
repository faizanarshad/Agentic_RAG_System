// Single source of truth for brand, URLs and contact details.
// NEXT_PUBLIC_SITE_URL must be set to the production origin before deploying: it drives
// canonical URLs, the sitemap, robots.txt, Open Graph URLs and structured data.
export const site = {
  name: 'AIDocumentAgent',
  shortName: 'AIDocumentAgent',
  tagline: 'AI agents that read, check and document your technical, legal and clinical files.',
  description:
    'AIDocumentAgent reviews engineering drawings, synthesises legal document collections and answers clinical questions from your own files, with citations, automated checks and flags for anything it cannot verify.',
  url: (process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3001').replace(/\/$/, ''),
  contactEmail: process.env.NEXT_PUBLIC_CONTACT_EMAIL || '',
  locale: 'en_GB',
  themeColor: '#0b1220',
};

export const navigation = [
  { href: '/solutions/engineering', label: 'Engineering' },
  { href: '/solutions/legal', label: 'Legal' },
  { href: '/solutions/medical', label: 'Medical' },
  { href: '/blog', label: 'Blog' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
];

export const absoluteUrl = (path = '/') => `${site.url}${path === '/' ? '' : path}`;
