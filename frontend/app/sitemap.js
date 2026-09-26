import { absoluteUrl } from '@/lib/site';
import { solutionList } from '@/lib/content';
import { getPublishedPosts } from '@/lib/content-api';

// Public, indexable pages only (the workspace app is noindex and disallowed in robots.txt)
export const revalidate = 3600;

export default async function sitemap() {
  const lastModified = new Date();
  const posts = await getPublishedPosts();
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
    { url: absoluteUrl('/blog'), lastModified, changeFrequency: 'weekly', priority: 0.8 },
    ...posts.map((p) => ({
      url: absoluteUrl(`/blog/${p.slug}`),
      lastModified: new Date(p.updated_at),
      changeFrequency: 'monthly',
      priority: 0.7,
    })),
  ];
}
