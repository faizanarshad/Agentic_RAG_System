import Link from 'next/link';
import { getSiteSettings } from '@/lib/content-api';

export default async function AnnouncementBar() {
  const { announcement } = await getSiteSettings();
  if (!announcement?.enabled || !announcement.text) return null;
  const external = announcement.link_url?.startsWith('https://');
  return (
    <div className={`announcement announcement--${announcement.tone || 'info'}`} role="region" aria-label="Announcement">
      <div className="container announcement__inner">
        <span>{announcement.text}</span>
        {announcement.link_url && announcement.link_text && (
          external ? (
            <a href={announcement.link_url} rel="noopener noreferrer">{announcement.link_text} →</a>
          ) : (
            <Link href={announcement.link_url}>{announcement.link_text} →</Link>
          )
        )}
      </div>
    </div>
  );
}
