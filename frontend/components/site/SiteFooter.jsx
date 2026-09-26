import Link from 'next/link';
import { Brand } from './Logo';
import { site } from '@/lib/site';
import { solutionList } from '@/lib/content';

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="site-footer__grid">
          <div className="site-footer__brand">
            <Link href="/" className="brand" aria-label="AIDocumentAgent home">
              <Brand />
            </Link>
            <p>{site.tagline}</p>
          </div>
          <div>
            <h2>Solutions</h2>
            <ul>
              {solutionList.map((s) => (
                <li key={s.slug}>
                  <Link href={`/solutions/${s.slug}`}>{s.name}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2>Company</h2>
            <ul>
              <li><Link href="/about">About</Link></li>
              <li><Link href="/blog">Blog</Link></li>
              <li><Link href="/contact">Contact</Link></li>
              {site.contactEmail && (
                <li><a href={`mailto:${site.contactEmail}`}>{site.contactEmail}</a></li>
              )}
            </ul>
          </div>
          <div>
            <h2>Product</h2>
            <ul>
              <li><a href="/workspace">Open workspace</a></li>
              <li><a href="/login">Sign in</a></li>
              <li><a href="/workspace/engineering">Drawing review</a></li>
              <li><a href="/workspace/legal">Legal synthesis</a></li>
            </ul>
          </div>
        </div>
        <div className="site-footer__base">
          <span>© {new Date().getFullYear()} {site.name}. All rights reserved.</span>
          <span>AI-assisted analysis supports, and does not replace, qualified professional review.</span>
        </div>
      </div>
    </footer>
  );
}
