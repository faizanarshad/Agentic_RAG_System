import 'server-only';

// Server-side reads of public content. Cached and refreshed every 60 s, and immediately when the
// API calls /api/revalidate after a change. Failures degrade to empty content so the site still builds.
const API = (process.env.API_INTERNAL_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '');

async function getJson(path, tags) {
  try {
    const response = await fetch(`${API}${path}`, { next: { revalidate: 60, tags } });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getPublishedPosts() {
  const data = await getJson('/public/posts?limit=100', ['posts']);
  return data?.posts || [];
}

export async function getPost(slug) {
  if (!/^[a-z0-9-]{1,90}$/.test(slug)) return null;
  return getJson(`/public/posts/${slug}`, ['posts']);
}

export async function getSiteSettings() {
  return (
    (await getJson('/public/settings', ['settings'])) || {
      announcement: { enabled: false },
      contact_form_enabled: true,
    }
  );
}

export const uploadUrl = (name) =>
  `${(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '')}/public/uploads/${name}`;
