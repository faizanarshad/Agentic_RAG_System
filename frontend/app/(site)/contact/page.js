import { Clock, Mail, ShieldCheck } from 'lucide-react';
import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import ContactForm from '@/components/site/ContactForm';
import { site } from '@/lib/site';
import { webPageSchema } from '@/lib/structured-data';

const description =
  'Contact the AIDocumentAgent team about drawing review, legal document synthesis, clinical document Q&A, pilots and integrations.';

export const metadata = {
  title: 'Contact',
  description,
  alternates: { canonical: '/contact' },
  openGraph: { url: '/contact', title: `Contact ${site.name}`, description },
};

export default function ContactPage() {
  return (
    <>
      <JsonLd data={webPageSchema('ContactPage', { path: '/contact', name: `Contact ${site.name}`, description })} />

      <section className="section--ink blueprint page-hero" aria-labelledby="contact-title">
        <div className="container page-hero__inner">
          <Breadcrumbs items={[{ name: 'Contact', path: '/contact' }]} />
          <p className="eyebrow">Contact</p>
          <h1 id="contact-title" className="display">Let’s look at your documents</h1>
          <p className="lede">
            Tell us what you review, compare or document today. We will reply with how the agents would handle it and the
            best way to run a pilot.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container contact-grid">
          <ContactForm />
          <aside aria-label="Contact information">
            <div className="aside-card">
              <h2 className="h3"><Clock size={18} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />What happens next</h2>
              <ol>
                <li>We read your message and reply by email, usually within two working days.</li>
                <li>If useful, we arrange a short call to understand your documents and review process.</li>
                <li>We suggest a pilot on a representative sample and agree how results will be measured.</li>
              </ol>
            </div>
            <div className="aside-card">
              <h2 className="h3"><ShieldCheck size={18} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />Before you send files</h2>
              <p className="muted">
                Please do not attach confidential drawings, contracts or patient data to this form. Describe them instead, and
                we will agree a secure way to share samples.
              </p>
            </div>
            {site.contactEmail && (
              <div className="aside-card">
                <h2 className="h3"><Mail size={18} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />Email</h2>
                <a className="text-link" href={`mailto:${site.contactEmail}`}>{site.contactEmail}</a>
              </div>
            )}
          </aside>
        </div>
      </section>
    </>
  );
}
