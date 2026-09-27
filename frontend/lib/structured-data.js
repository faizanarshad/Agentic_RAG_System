import { absoluteUrl, site } from './site';

const organizationId = `${site.url}/#organization`;

export const organizationSchema = () => ({
  '@context': 'https://schema.org',
  '@type': 'Organization',
  '@id': organizationId,
  name: site.name,
  url: site.url,
  logo: absoluteUrl('/icon.svg'),
  description: site.description,
  ...(site.contactEmail && {
    email: site.contactEmail,
    contactPoint: [{ '@type': 'ContactPoint', contactType: 'customer support', email: site.contactEmail }],
  }),
});

export const websiteSchema = () => ({
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  '@id': `${site.url}/#website`,
  name: site.name,
  url: site.url,
  publisher: { '@id': organizationId },
  inLanguage: 'en',
});

export const softwareSchema = () => ({
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: site.name,
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  url: site.url,
  description: site.description,
  publisher: { '@id': organizationId },
  featureList: [
    'Engineering drawing review against ISO and ASME standards',
    'Drawing revision comparison with revision-control audit',
    'Template-based technical documentation with Word export',
    'Legal document classification, extraction and risk analysis',
    'Cross-document legal synthesis with citations',
    'Clinical question answering over uploaded documents',
  ],
});

export const breadcrumbSchema = (items) => ({
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: items.map((item, index) => ({
    '@type': 'ListItem',
    position: index + 1,
    name: item.name,
    item: absoluteUrl(item.path),
  })),
});

export const faqSchema = (faqs) => ({
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqs.map((faq) => ({
    '@type': 'Question',
    name: faq.question,
    acceptedAnswer: { '@type': 'Answer', text: faq.answer },
  })),
});

export const webPageSchema = (type, { path, name, description }) => ({
  '@context': 'https://schema.org',
  '@type': type,
  '@id': `${absoluteUrl(path)}#webpage`,
  url: absoluteUrl(path),
  name,
  description,
  isPartOf: { '@id': `${site.url}/#website` },
  about: { '@id': organizationId },
});

export const serviceSchema = ({ path, name, description, serviceType }) => ({
  '@context': 'https://schema.org',
  '@type': 'Service',
  name,
  description,
  serviceType,
  url: absoluteUrl(path),
  provider: { '@id': organizationId },
  areaServed: 'Worldwide',
});
