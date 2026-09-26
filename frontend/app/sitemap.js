import { absoluteUrl } from '@/lib/site';
import { solutionList } from '@/lib/content';

// Public, indexable pages only (the workspace app is noindex and disallowed in robots.txt)
export default function sitemap() {
  const lastModified = new Date();
  return [
    { url: absoluteUrl('/'), lastModified, changeFrequency: 'weekly', priority: 1 },
    { url: absoluteUrl('/solutions'), lastModified, changeFrequency: 'monthly', priority: 0.9 },
    ...solutionList.map((s) => ({
      url: absoluteUrl(`/solutions/${s.slug}`),
      lastModified,
      changeFrequency: 'monthly',
      priority: 0.9,
    })),
    { url: absoluteUrl('/about'), lastModified, changeFrequency: 'monthly', priority: 0.7 },
    { url: absoluteUrl('/contact'), lastModified, changeFrequency: 'yearly', priority: 0.6 },
  ];
}
