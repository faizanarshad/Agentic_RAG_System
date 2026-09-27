import Link from 'next/link';
import { ArrowRight, FileSearch, FileStack, Quote, Ruler, ShieldCheck } from 'lucide-react';
import CapabilitySlider from '@/components/site/CapabilitySlider';
import TaskFinder from '@/components/site/TaskFinder';
import Carousel from '@/components/site/Carousel';
import Marquee from '@/components/site/Marquee';
import ProductFrame from '@/components/site/ProductFrame';
import JsonLd from '@/components/site/JsonLd';
import { benchmarks, faqs, findings, guardrails, images, solutionList, techStack, workflow } from '@/lib/content';
import { site } from '@/lib/site';
import { faqSchema, organizationSchema, softwareSchema, websiteSchema } from '@/lib/structured-data';

export const metadata = {
  title: { absolute: 'AIDocumentAgent: AI review for drawings, legal and clinical files' },
  description:
    'AI agents that review engineering drawings, synthesise legal documents and answer clinical questions from your files, with cited, verifiable results.',
  alternates: { canonical: '/' },
};

// Every capability across the workspaces, numbered in order
const capabilities = solutionList
  .flatMap((s) => s.capabilities.map((c) => ({ ...c, slug: s.slug, workspace: s.name })))
  .map((c, i) => ({ ...c, number: i + 1 }));
const workspaces = solutionList.map((s) => ({ slug: s.slug, name: s.name }));

const BENEFITS = [
  { icon: ShieldCheck, text: 'Verified findings' },
  { icon: Ruler, text: 'ISO & ASME drawing checks' },
  { icon: FileStack, text: 'PDF, DXF, scans & Word' },
  { icon: Quote, text: 'Cited answers' },
];

// Hero product tour: one annotated screenshot per workspace
const showcase = [
  {
    name: 'Engineering',
    image: images.engineeringReview,
    label: 'workspace / engineering / review',
    callouts: [
      { position: 'b', tone: 'critical', tag: 'Critical', text: 'Overall length 120 vs 125 across views' },
      { position: 'a', tone: 'verify', tag: 'Verified', text: 'Datum C: no symbol found on a zoomed re-check' },
    ],
  },
  {
    name: 'Legal',
    image: images.legalSynthesis,
    label: 'workspace / legal / corpus',
    callouts: [
      { position: 'b', tone: 'critical', tag: 'High risk', text: 'Uncapped liability in 3 of 100 documents' },
      { position: 'a', tone: 'verify', tag: 'Cited', text: 'Every synthesis claim links to its source' },
    ],
  },
  {
    name: 'Medical',
    image: images.medicalChat,
    label: 'workspace / medical / chat',
    callouts: [
      { position: 'b', tone: 'verify', tag: 'Sourced', text: 'Answer grounded in 5 retrieved passages' },
      { position: 'a', tone: 'verify', tag: 'Redacted', text: 'Phone numbers and IDs removed before indexing' },
    ],
  },
];

export default function HomePage() {
  return (
    <>
      <JsonLd data={[organizationSchema(), websiteSchema(), softwareSchema(), faqSchema(faqs)]} />
      <div className="home">

      {/* Hero */}
      <section className="section--ink blueprint hero" aria-labelledby="hero-title">
        <div className="container hero__grid">
          <div className="hero__copy">
            <p className="eyebrow">Document intelligence, verified</p>
            <h1 id="hero-title" className="display">
              AI agents that <span className="accent-text">check the details</span> in your documents
            </h1>
            <p className="lede">
              AIDocumentAgent reviews engineering drawings, synthesises legal document collections and answers clinical
              questions from your own files. Every finding is located, every answer is sourced, and every gap is flagged.
            </p>
            <div className="btn-row">
              <a className="btn btn--primary" href="/workspace">
                Open the workspace <ArrowRight size={17} aria-hidden="true" />
              </a>
              <Link className="btn btn--ghost" href="/contact">
                Talk to us
              </Link>
            </div>
            <ul className="hero__benefits" role="list">
              {BENEFITS.map(({ icon: Icon, text }) => (
                <li key={text}><span className="hero__benefit-icon"><Icon size={15} aria-hidden="true" /></span>{text}</li>
              ))}
            </ul>
          </div>
          <Carousel
            variant="fade"
            label="Product tour"
            tabs={showcase.map((s) => s.name)}
            interval={6500}
            tone="ink"
            className="hero-showcase"
          >
            {showcase.map((s, i) => (
              <ProductFrame key={s.name} image={s.image} label={s.label} eager={i === 0} scan callouts={s.callouts} />
            ))}
          </Carousel>
        </div>
      </section>

      {/* Start a task (overlaps the hero) */}
      <div className="container task-finder-wrap">
        <TaskFinder />
      </div>

      {/* Technology */}
      <Marquee label="Built with" items={techStack} />

      {/* Solutions */}
      <section className="section" aria-labelledby="solutions-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Three workspaces, {capabilities.length} capabilities</p>
            <h2 id="solutions-title" className="h2">Specialist agents for the documents that carry the most risk</h2>
            <p className="lede">
              Each workspace pairs domain-specific extraction with the same verification pipeline, so results are consistent
              whether you are releasing a drawing, reviewing a contract portfolio or checking a clinical guideline.
            </p>
          </div>
          <CapabilitySlider capabilities={capabilities} workspaces={workspaces} />
        </div>
      </section>

      {/* Workflow */}
      <section className="section section--ink blueprint" aria-labelledby="workflow-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">How it works</p>
            <h2 id="workflow-title" className="h2">From raw files to reviewed, documented results</h2>
            <p className="lede">
              Agentic workflows built with LangGraph route every document through extraction, verification and delivery,
              with a specialist agent at each step.
            </p>
          </div>
          <ol className="steps" role="list">
            {workflow.map((w) => (
              <li key={w.step} className="step">
                <span className="step__num">{w.step}</span>
                <h3>{w.title}</h3>
                <p>{w.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Guardrails */}
      <section className="section" aria-labelledby="guardrails-title">
        <div className="container split">
          <div className="split__copy">
            <p className="eyebrow">Verification, not guesswork</p>
            <h2 id="guardrails-title" className="h2">Built to be checked, so you can trust what it reports</h2>
            <p className="lede">
              Language models are powerful and fallible. AIDocumentAgent wraps them in guardrails that make results
              traceable and failures visible.
            </p>
            <Link className="text-link" href="/about">
              How we build <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
          <div>
            {guardrails.map((g) => (
              <div key={g.title} className="guardrail">
                <ShieldCheck size={22} aria-hidden="true" />
                <h3 className="h3">{g.title}</h3>
                <p>{g.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benchmarks */}
      <section className="section section--surface" aria-labelledby="results-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Measured, not claimed</p>
            <h2 id="results-title" className="h2">Results from our own test suites</h2>
          </div>
          <dl className="metrics">
            {benchmarks.map((b) => (
              <div key={b.label} className="metric">
                <dt className="metric__label">{b.label}</dt>
                <dd className="metric__value">{b.value}</dd>
                <dd className="metric__detail">{b.detail}</dd>
              </div>
            ))}
          </dl>
          <p className="footnote">
            Internal evaluations on synthetic test data with planted errors and known answers. Your documents will differ;
            we recommend a pilot on a representative sample.
          </p>
        </div>
      </section>

      {/* Findings slider */}
      <section className="section section--ink blueprint" aria-labelledby="findings-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">From our test runs</p>
            <h2 id="findings-title" className="h2">What the agents actually find</h2>
            <p className="lede">Real findings from runs on our synthetic test documents, with planted errors and known answers.</p>
          </div>
          <Carousel label="Example findings" interval={5500} tone="ink">
            {findings.map((f) => (
              <figure key={f.title} className="finding">
                <div className="finding__top">
                  <span className={`finding__tag finding__tag--${f.tone}`}>{f.tag}</span>
                  <span className="finding__workspace">{f.workspace}</span>
                </div>
                <p className="finding__title">{f.title}</p>
                <p className="finding__detail">{f.detail}</p>
                <figcaption className="finding__source">{f.source}</figcaption>
              </figure>
            ))}
          </Carousel>
        </div>
      </section>

      {/* FAQ */}
      <section className="section section--surface" aria-labelledby="faq-title">
        <div className="container">
          <div className="section-head section-head--center">
            <p className="eyebrow">Questions</p>
            <h2 id="faq-title" className="h2">Frequently asked questions</h2>
          </div>
          <div className="faq">
            {faqs.map((f) => (
              <details key={f.question}>
                <summary>{f.question}</summary>
                <p>{f.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section section--ink blueprint" aria-labelledby="cta-title">
        <div className="container cta-band__inner">
          <FileSearch size={36} aria-hidden="true" className="accent-text" />
          <h2 id="cta-title" className="h2">Put your hardest documents to the test</h2>
          <p className="lede">Start with a drawing, a contract folder or a clinical guideline and see what the agents find.</p>
          <div className="btn-row">
            <a className="btn btn--primary" href="/workspace">
              Open the workspace <ArrowRight size={17} aria-hidden="true" />
            </a>
            <Link className="btn btn--ghost" href="/contact">
              Book a walkthrough
            </Link>
          </div>
        </div>
      </section>
      </div>
    </>
  );
}
