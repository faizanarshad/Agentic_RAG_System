import { Suspense } from 'react';
import PostEditor from '@/components/admin/PostEditor';

export const metadata = { title: 'Edit post' };

export default async function Page({ params }) {
  const { id } = await params;
  return (
    <Suspense fallback={<div className="ws-loading">Loading…</div>}>
      <PostEditor postId={id} />
    </Suspense>
  );
}
