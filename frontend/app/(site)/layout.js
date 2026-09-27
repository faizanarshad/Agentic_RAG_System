import SiteHeader from '@/components/site/SiteHeader';
import SiteFooter from '@/components/site/SiteFooter';
import PageviewTracker from '@/components/site/PageviewTracker';
import AnnouncementBar from '@/components/site/AnnouncementBar';
import SiteMotion from '@/components/site/SiteMotion';

export default function SiteLayout({ children }) {
  return (
    <>
      <div className="scroll-progress" aria-hidden="true" />
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <AnnouncementBar />
      <SiteHeader />
      <main id="main">{children}</main>
      <SiteFooter />
      <PageviewTracker />
      <SiteMotion />
    </>
  );
}
