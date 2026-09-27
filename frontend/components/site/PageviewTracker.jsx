'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { API_BASE } from '@/lib/api';

// Cookie-less page-view beacon. text/plain keeps it a "simple" cross-origin request (no preflight),
// sendBeacon never blocks rendering, and browsers that send Do Not Track are not counted.
export default function PageviewTracker() {
  const pathname = usePathname();
  const firstView = useRef(true);

  useEffect(() => {
    if (navigator.doNotTrack === '1' || window.doNotTrack === '1') return;
    const payload = JSON.stringify({
      path: pathname,
      // Only the landing page has a meaningful external referrer
      referrer: firstView.current ? document.referrer : '',
    });
    firstView.current = false;
    const url = `${API_BASE}/analytics/pageview`;
    const blob = new Blob([payload], { type: 'text/plain' });
    if (!(navigator.sendBeacon && navigator.sendBeacon(url, blob))) {
      fetch(url, { method: 'POST', body: payload, keepalive: true, headers: { 'Content-Type': 'text/plain' } }).catch(() => {});
    }
  }, [pathname]);

  return null;
}
