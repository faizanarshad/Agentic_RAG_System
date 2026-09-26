import Link from 'next/link';
import SiteHeader from '@/components/site/SiteHeader';
import SiteFooter from '@/components/site/SiteFooter';

export const metadata = { title: 'Page not found', robots: { index: false } };

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="section not-found">
        <div className="container">
          <p className="eyebrow">Error 404</p>
          <h1 className="display">This page is not on the drawing</h1>
          <p className="lede" style={{ marginInline: 'auto', marginBlock: '20px 28px' }}>
            The page you were looking for does not exist or has moved.
          </p>
          <div className="btn-row" style={{ justifyContent: 'center' }}>
            <Link className="btn btn--primary" href="/">Back to home</Link>
            <Link className="btn btn--ghost" href="/contact">Contact us</Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
