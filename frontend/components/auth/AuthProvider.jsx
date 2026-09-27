'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { AUTH_REQUIRED_EVENT, fetchBackend, jsonRequest } from '@/lib/api';

const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * Loads the signed-in user and guards the application routes.
 * The API enforces authorisation on every request; this only decides what to render.
 */
export default function AuthProvider({ children, requireAdmin = false }) {
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState({ status: 'loading', user: null });

  const loadUser = useCallback(async () => {
    try {
      const data = await fetchBackend('/auth/me');
      setState({ status: 'ready', user: data.user });
    } catch {
      setState({ status: 'signed-out', user: null });
    }
  }, []);

  useEffect(() => {
    // Fetch on mount; state is only set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    const onExpired = () => setState({ status: 'signed-out', user: null });
    window.addEventListener(AUTH_REQUIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, onExpired);
  }, []);

  useEffect(() => {
    if (state.status === 'signed-out') {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    } else if (state.status === 'ready' && state.user.must_change_password && pathname !== '/workspace/account') {
      router.replace('/workspace/account?required=1');
    } else if (state.status === 'ready' && requireAdmin && state.user.role !== 'admin') {
      router.replace('/workspace');
    }
  }, [state, pathname, requireAdmin, router]);

  const logout = useCallback(async () => {
    try {
      await fetchBackend('/auth/logout', jsonRequest('POST', {}));
    } finally {
      // Full page load on purpose: clears all in-memory app state and swaps to the site stylesheet
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign('/login');
    }
  }, []);

  const allowed =
    state.status === 'ready' &&
    (!state.user.must_change_password || pathname === '/workspace/account') &&
    (!requireAdmin || state.user.role === 'admin');

  return (
    <AuthContext.Provider value={{ user: state.user, reload: loadUser, logout }}>
      {allowed ? children : <div className="ws-loading" role="status">Checking your session…</div>}
    </AuthContext.Provider>
  );
}
