'use client';

import { useEffect, useSyncExternalStore } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutGrid, Moon, Ruler, Scale, Stethoscope, Sun } from 'lucide-react';
import { Brand } from '@/components/site/Logo';

const TABS = [
  { href: '/workspace', label: 'Overview', icon: LayoutGrid },
  { href: '/workspace/engineering', label: 'Engineering', icon: Ruler },
  { href: '/workspace/legal', label: 'Legal', icon: Scale },
  { href: '/workspace/medical', label: 'Medical', icon: Stethoscope },
];

// Theme preference lives in localStorage; useSyncExternalStore reads it without a
// server/client mismatch (the server snapshot is always "light").
const THEME_EVENT = 'aidocumentagent-theme';

function readTheme() {
  try {
    return localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

function subscribe(callback) {
  window.addEventListener('storage', callback);
  window.addEventListener(THEME_EVENT, callback);
  return () => {
    window.removeEventListener('storage', callback);
    window.removeEventListener(THEME_EVENT, callback);
  };
}

function saveTheme(theme) {
  try {
    localStorage.setItem('theme', theme);
  } catch {
    // Storage unavailable (private mode): the choice lasts for this page only
  }
  window.dispatchEvent(new Event(THEME_EVENT));
}

export default function WorkspaceShell({ children }) {
  const pathname = usePathname();
  const theme = useSyncExternalStore(subscribe, readTheme, () => 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="app">
      <header className="ws-header">
        <div className="ws-header__inner">
          <Link href="/workspace" className="ws-brand" aria-label="AIDocumentAgent workspace">
            <Brand />
            <small>Workspace</small>
          </Link>
          <nav className="ws-nav" aria-label="Workspaces">
            {TABS.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined}>
                <Icon size={15} aria-hidden="true" />
                {label}
              </Link>
            ))}
          </nav>
          <div className="ws-actions">
            {/* Full page load on purpose: the marketing site uses a different stylesheet */}
            {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
            <a className="ws-site-link" href="/">Back to site</a>
            <button
              type="button"
              className="theme-toggle"
              onClick={() => saveTheme(theme === 'light' ? 'dark' : 'light')}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
            </button>
          </div>
        </div>
      </header>
      <main className="main" id="main">{children}</main>
    </div>
  );
}
