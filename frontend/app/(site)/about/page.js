import Link from 'next/link';
import { ArrowRight, Eye, ListChecks, ShieldCheck, UserCheck } from 'lucide-react';
import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import { defaultShareImage } from '@/lib/metadata';
import { techStack } from '@/lib/content';
import { site } from '@/lib/site';
import { webPageSchema } from '@/lib/structured-data';

const description =
  'Why AIDocumentAgent exists, the principles behind it and how its agents are built: specialist extraction, deterministic checks and verification you can audit.';

export const metadata = {
  title: 'About',
  description,
  alternates: { canonical: '/about' },
  openGraph: { url: '/about', title: `About ${site.name}`, description, images: [defaultShareImage] },
};

const PRINCIPLES = [
  { icon: Eye, title: 'Show the evidence', body: 'Every finding carries a location, every answer its sources. If you cannot trace it, we have not finished.' },
  { icon: ListChecks, title: 'Rules where rules work', body: 'Title blocks, revisions, units and datums are checked by deterministic code, not left to a model’s judgement.' },
  { icon: ShieldCheck, title: 'Assume the model can be wrong', body: 'Claims are re-verified on zoomed crops, numbers are fact-checked against sources, and verdicts cannot be more lenient than findings.' },
  { icon: UserCheck, title: 'People approve', body: 'The agents prepare, check and draft. Qualified engineers, lawyers and clinicians make the decisions.' },
];

const ARCHITECTURE = [
  { layer: 'Ingestion', detail: 'PyMuPDF renders every sheet and reads vector text; ezdxf reads CAD entities; scanned pages are transcribed by a vision model.' },
  { layer: 'Agents', detail: 'LangGraph workflows chain specialist agents: extraction, verification, consistency checking, review, synthesis and drafting.' },
  { layer: 'Checks', detail: 'Deterministic rule engines for drawings, revision audits and numeric fact-checking run alongside the models.' },
  { layer: 'Retrieval', detail: 'Pinecone vector search with domain namespaces and metadata filters grounds answers in your own documents.' },
  { layer: 'Delivery', detail: 'A FastAPI back end and this Next.js front end, with exports to Word and Markdown.' },
];

export default function AboutPage() {
  return (
    <>
      <JsonLd data={webPageSchema('AboutPage', { path: '/about', name: `About ${site.name}`, description })} />

      <section className="section--ink blueprint page-hero" aria-labelledby="about-title">
        <div className="container page-hero__inner">
          <Breadcrumbs items={[{ name: 'About', path: '/about' }]} />
          <p className="eyebrow">About</p>
          <h1 id="about-title" className="display">Precision work deserves precise tools</h1>
          <p className="lede">
            {site.name} builds AI agents for documents where a missed detail is expensive: a tolerance on a drawing, an
            uncapped liability in a contract, a threshold in a clinical guideline.
          </p>
        </div>
      </section>

      <section className="section" aria-labelledby="mission-title">
        <div className="container split">
          <div className="split__copy">
            <p className="eyebrow">Why we exist</p>
            <h2 id="mission-title" className="h2">Review is the bottleneck. Guesswork is not the answer.</h2>
          </div>
          <div className="prose">
            <p>
              Engineering, legal and clinical teams spend a large share of their time reading documents closely: checking a
              drawing before release, comparing revisions, extracting obligations from a contract portfolio, finding the
              relevant passage in a guideline.
            </p>
            <p>
              General-purpose chatbots can summarise, but they cannot show their work and they fail quietly. We built
              {' '}<strong>{site.name}</strong> so that the output of every agent can be checked: findings point to a location,
              answers cite their sources, and anything the system could not verify is flagged rather than filled in.
            </p>
            <p>
              The result is a workspace that does the first pass of review and documentation, and hands a qualified person a
              clear, auditable list of what needs their attention.
            </p>
          </div>
        </div>
      </section>

      <section className="section section--surface" aria-labelledby="principles-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Principles</p>
            <h2 id="principles-title" className="h2">What we will not compromise on</h2>
          </div>
          <div className="grid-2">
            {PRINCIPLES.map(({ icon: Icon, title, body }) => (
              <article key={title} className="card">
                <span className="card__icon"><Icon size={22} aria-hidden="true" /></span>
                <h3 className="h3">{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="architecture-title">
        <div className="container split">
          <div className="split__copy">
            <p className="eyebrow">How it is built</p>
            <h2 id="architecture-title" className="h2">An architecture designed for verification</h2>
            <p className="lede">Open, well-understood components, arranged so that every step can be inspected.</p>
            <ul className="check-list" aria-label="Technology">
              {techStack.map((t) => (
                <li key={t}><ShieldCheck size={16} aria-hidden="true" />{t}</li>
              ))}
            </ul>
          </div>
          <ol className="architecture">
            {ARCHITECTURE.map((a) => (
              <li key={a.layer}>
                <strong>{a.layer}</strong>
                <span>{a.detail}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section section--surface" aria-labelledby="responsible-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Responsible use</p>
            <h2 id="responsible-title" className="h2">Clear about what AI should and should not decide</h2>
          </div>
          <div className="prose">
            <p>
              {site.name} supports professional review. It does not approve drawings for release, give legal advice or make
              clinical decisions. Model readings can vary between runs, which is why deterministic checks and targeted
              re-verification are part of every workflow, and why every result is presented for human confirmation.
            </p>
            <p>
              Documents are processed by the back end you operate and by the configured AI model provider. Before using the
              workspace with confidential or regulated data, review that provider’s terms and your own data-handling
              requirements.
            </p>
          </div>
        </div>
      </section>

      <section className="section section--ink blueprint" aria-labelledby="about-cta">
        <div className="container cta-band__inner">
          <h2 id="about-cta" className="h2">See it on your own documents</h2>
          <p className="lede">Tell us what you review today and we will show you what the agents catch.</p>
          <div className="btn-row">
            <Link className="btn btn--primary" href="/contact">
              Contact us <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <a className="btn btn--ghost" href="/workspace">Open the workspace</a>
          </div>
        </div>
      </section>
    </>
  );
}
