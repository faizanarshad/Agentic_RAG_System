import Link from 'next/link';
import { Ruler, Scale, Stethoscope } from 'lucide-react';
import { StatusLoader } from '@/components/workspace/loaders';

export const metadata = { title: 'Overview' };

const WORKSPACES = [
  { href: '/workspace/engineering', icon: Ruler, title: 'Engineering', body: 'Review drawings against ISO or ASME, compare revisions and generate ECNs, FAI reports and specifications.' },
  { href: '/workspace/legal', icon: Scale, title: 'Legal', body: 'Analyse up to 100 contracts, filings and compliance records per batch and synthesise insights across them.' },
  { href: '/workspace/medical', icon: Stethoscope, title: 'Medical', body: 'Upload clinical guidelines, literature and datasets and ask questions answered from them.' },
];

export default function WorkspaceOverview() {
  return (
    <div className="ws-overview">
      <div className="ws-overview__inner">
        <div>
          <h1 className="legal-page-title">Workspace</h1>
          <p className="legal-muted">Choose a workspace. Everything you upload stays in your own back end.</p>
        </div>
        <div className="ws-cards">
          {WORKSPACES.map(({ href, icon: Icon, title, body }) => (
            <Link key={href} href={href} className="ws-card">
              <Icon size={22} aria-hidden="true" />
              <h2 className="legal-card-title">{title}</h2>
              <p>{body}</p>
            </Link>
          ))}
        </div>
        <StatusLoader />
      </div>
    </div>
  );
}
