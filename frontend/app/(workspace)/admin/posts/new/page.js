import { Suspense } from 'react';
import PostEditor from '@/components/admin/PostEditor';

export const metadata = { title: 'New post' };

export default function Page() {
  return (
    <Suspense fallback={<div className="ws-loading">Loading…</div>}>
      <PostEditor />
    </Suspense>
  );
}
