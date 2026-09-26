import Link from 'next/link';
import { Brand } from './Logo';
import SiteNav from './SiteNav';

export default function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link href="/" className="brand" aria-label="AIDocumentAgent home">
          <Brand />
        </Link>
        <SiteNav />
      </div>
    </header>
  );
}
