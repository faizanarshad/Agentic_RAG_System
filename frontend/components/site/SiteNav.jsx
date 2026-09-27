'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowRight, Menu } from 'lucide-react';
import { navigation } from '@/lib/site';

// Desktop links plus a <details>-based mobile menu: it opens without JavaScript and only
// needs JS to close itself after navigation.
export default function SiteNav() {
  const pathname = usePathname();
  const menuRef = useRef(null);

  useEffect(() => {
    if (menuRef.current) menuRef.current.open = false;
  }, [pathname]);

  const current = (href) => (pathname === href || pathname.startsWith(`${href}/`) ? 'page' : undefined);

  return (
    <>
      <nav className="site-nav" aria-label="Main">
        {navigation.map((item) => (
          <Link key={item.href} href={item.href} aria-current={current(item.href)}>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="site-header__actions">
        {/* Plain <a>: the workspace is a separate app shell with its own stylesheet */}
        <a className="site-signin btn--desktop" href="/login">Sign in</a>
        <a className="btn btn--primary btn--desktop" href="/workspace">
          Open workspace <ArrowRight size={16} aria-hidden="true" />
        </a>
        <details className="menu-toggle" ref={menuRef}>
          <summary aria-label="Open menu">
            <Menu size={20} aria-hidden="true" />
          </summary>
          <nav className="menu-panel" aria-label="Mobile">
            {navigation.map((item) => (
              <Link key={item.href} href={item.href} aria-current={current(item.href)}>
                {item.label}
              </Link>
            ))}
            <a href="/login">Sign in</a>
            <a className="btn btn--primary" href="/workspace">
              Open workspace <ArrowRight size={16} aria-hidden="true" />
            </a>
          </nav>
        </details>
      </div>
    </>
  );
}
