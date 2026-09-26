'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Activity, BarChart3, Coins, Globe, Inbox, Server, Users } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { fetchBackend } from '@/lib/api';

const NAV = [
  { href: '/admin', label: 'Overview', icon: BarChart3 },
  { href: '/admin/traffic', label: 'Traffic', icon: Globe },
  { href: '/admin/usage', label: 'Usage & cost', icon: Coins },
  { href: '/admin/users', label: 'Users', icon: Users },
  { href: '/admin/messages', label: 'Messages', icon: Inbox },
  { href: '/admin/activity', label: 'Activity', icon: Activity },
  { href: '/admin/system', label: 'System', icon: Server },
];

/** Loads an admin endpoint; re-fetches when the path changes. */
export function useAdminData(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const load = useCallback(async () => {
    try {
      setState({ data: await fetchBackend(path), error: null, loading: false });
    } catch (e) {
      setState({ data: null, error: e.message, loading: false });
    }
  }, [path]);
  useEffect(() => {
    // Fetch when the endpoint changes; state is only set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);
  return { ...state, reload: load };
}

export function RangePicker({ days, onChange }) {
  return (
    <label className="admin-range">
      <span className="visually-hidden">Date range</span>
      <select value={days} onChange={(e) => onChange(Number(e.target.value))}>
        <option value={7}>Last 7 days</option>
        <option value={30}>Last 30 days</option>
        <option value={90}>Last 90 days</option>
      </select>
    </label>
  );
}

export function AdminState({ loading, error }) {
  if (loading) return <div className="ws-loading" role="status">Loading…</div>;
  if (error) return <p className="legal-error">{error}</p>;
  return null;
}

export default function AdminFrame({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (user && !isAdmin) router.replace('/workspace');
  }, [user, isAdmin, router]);

  if (!isAdmin) return <div className="ws-loading" role="status">Checking access…</div>;

  return (
    <div className="ws-overview">
      <div className="ws-overview__inner admin">
        <div className="legal-header">
          <div>
            <h1 className="legal-page-title">Admin</h1>
            <p className="legal-muted">Analytics, users, messages and system health.</p>
          </div>
        </div>
        <nav className="admin-nav" aria-label="Admin sections">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} className={`nav-button ${pathname === href ? 'active' : ''}`}
              aria-current={pathname === href ? 'page' : undefined}>
              <Icon size={15} aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>
        {children}
      </div>
    </div>
  );
}
