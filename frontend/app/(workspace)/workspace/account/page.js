import { Suspense } from 'react';
import AccountPage from '@/components/account/AccountPage';

export const metadata = { title: 'Account' };

export default function Page() {
  return (
    <Suspense fallback={<div className="ws-loading">Loading…</div>}>
      <AccountPage />
    </Suspense>
  );
}
