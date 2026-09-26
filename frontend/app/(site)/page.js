import Link from 'next/link';
import { ArrowRight, BadgeCheck, CircleCheck, FileSearch, Ruler, Scale, ShieldCheck, Stethoscope } from 'lucide-react';
import ProductFrame from '@/components/site/ProductFrame';
import JsonLd from '@/components/site/JsonLd';
import { benchmarks, faqs, guardrails, images, solutionList, techStack, workflow } from '@/lib/content';
import { site } from '@/lib/site';
import { faqSchema, organizationSchema, softwareSchema, websiteSchema } from '@/lib/structured-data';

export const metadata = {
  title: { absolute: 'AIDocumentAgent: AI review for drawings, legal and clinical files' },
  description:
    'AI agents that review engineering drawings, synthesise legal documents and answer clinical questions from your files, with cited, verifiable results.',
  alternates: { canonical: '/' },
};

const SOLUTION_ICONS = { engineering: Ruler, legal: Scale, medical: Stethoscope };

export default function HomePage() {
  return (
    <>
      <JsonLd data={[organizationSchema(), websiteSchema(), softwareSchema(), faqSchema(faqs)]} />

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
            <div className="hero__meta">
              <span><CircleCheck size={14} aria-hidden="true" /> ISO &amp; ASME drawing checks</span>
              <span><CircleCheck size={14} aria-hidden="true" /> PDF, DXF, scans &amp; Word</span>
              <span><CircleCheck size={14} aria-hidden="true" /> Cited answers</span>
            </div>
          </div>
          <ProductFrame
            image={images.engineeringReview}
            label="workspace / engineering / review"
            eager
            callouts={[
              { position: 'b', tone: 'critical', tag: 'Critical', text: 'Overall length 120 vs 125 across views' },
              { position: 'a', tone: 'verify', tag: 'Verified', text: 'Datum C: no symbol found on a zoomed re-check' },
            ]}
          />
        </div>
      </section>

      {/* Technology */}
      <div className="stack-strip" role="note" aria-label="Built with">
        <span className="stack-strip__label">Built with</span>
        {techStack.map((t) => (
          <span key={t} className="stack-strip__item">{t}</span>
        ))}
      </div>

      {/* Solutions */}
      <section className="section" aria-labelledby="solutions-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Three workspaces, one engine</p>
            <h2 id="solutions-title" className="h2">Specialist agents for the documents that carry the most risk</h2>
            <p className="lede">
              Each workspace pairs domain-specific extraction with the same verification pipeline, so results are consistent
              whether you are releasing a drawing, reviewing a contract portfolio or checking a clinical guideline.
            </p>
          </div>
          <div className="grid-3">
            {solutionList.map((s) => {
              const Icon = SOLUTION_ICONS[s.slug];
              return (
                <article key={s.slug} className="card card--link">
                  <span className="card__icon"><Icon size={22} aria-hidden="true" /></span>
                  <p className="card__kicker">{s.kicker}</p>
                  <h3 className="h3">{s.name}</h3>
                  <p>{s.lede}</p>
                  <Link className="text-link card__link" href={`/solutions/${s.slug}`}>
                    Explore {s.name.toLowerCase()} <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                </article>
              );
            })}
          </div>
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

      {/* Engineering spotlight */}
      <section className="section" aria-labelledby="spotlight-title">
        <div className="container split split--reverse">
          <div className="split__copy">
            <p className="eyebrow">Change control</p>
            <h2 id="spotlight-title" className="h2">Catch the changes nobody recorded</h2>
            <p className="lede">
              Compare two revisions and every substantive change is audited against the new revision-table entries. Changes
              that were made but never recorded are called out, and an ECN can be drafted from the comparison in one step.
            </p>
            <ul className="check-list">
              <li><BadgeCheck size={18} aria-hidden="true" />Form, fit and function impact for every change</li>
              <li><BadgeCheck size={18} aria-hidden="true" />Revision increment checked automatically</li>
              <li><BadgeCheck size={18} aria-hidden="true" />ECN, FAI and review records exported to Word</li>
            </ul>
            <Link className="text-link" href="/solutions/engineering">
              See the engineering workspace <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
          <ProductFrame image={images.engineeringCompare} label="workspace / engineering / compare" light />
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
    </>
  );
}
