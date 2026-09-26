import { timingSafeEqual } from 'node:crypto';
import { revalidatePath, revalidateTag } from 'next/cache';

const ALLOWED_TAGS = new Set(['posts', 'settings']);

function authorised(request) {
  const secret = process.env.REVALIDATE_SECRET || '';
  const given = request.headers.get('x-revalidate-secret') || '';
  if (!secret || given.length !== secret.length) return false;
  return timingSafeEqual(Buffer.from(given), Buffer.from(secret));
}

// Called by the API after posts or settings change, so pages refresh without waiting for the 60 s window
export async function POST(request) {
  if (!authorised(request)) {
    return Response.json({ ok: false }, { status: 401 });
  }
  const body = await request.json().catch(() => ({}));
  const tags = (body.tags || []).filter((t) => ALLOWED_TAGS.has(t));
  const paths = (body.paths || []).filter((p) => typeof p === 'string' && /^\/[a-z0-9\-/]*$/.test(p));
  // { expire: 0 }: an admin who just published expects the next page load to show the change,
  // so stale content is never served (stale-while-revalidate would show the old version once)
  tags.forEach((tag) => revalidateTag(tag, { expire: 0 }));
  paths.forEach((path) => revalidatePath(path));
  return Response.json({ ok: true, tags, paths });
}
