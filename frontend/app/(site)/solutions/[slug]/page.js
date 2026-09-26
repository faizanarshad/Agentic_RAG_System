import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowRight, BadgeCheck, CircleAlert } from 'lucide-react';
import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import ProductFrame from '@/components/site/ProductFrame';
import { solutions, workflow } from '@/lib/content';
import { site } from '@/lib/site';
import { serviceSchema } from '@/lib/structured-data';

export const dynamicParams = false;

export function generateStaticParams() {
  return Object.keys(solutions).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }) {
  const { slug } = await params;
  const solution = solutions[slug];
  if (!solution) return {};
  const path = `/solutions/${slug}`;
  return {
    title: solution.metaTitle,
    description: solution.metaDescription,
    alternates: { canonical: path },
    openGraph: { url: path, title: `${solution.metaTitle} | ${site.name}`, description: solution.metaDescription },
  };
}

export default async function SolutionPage({ params }) {
  const { slug } = await params;
  const solution = solutions[slug];
  if (!solution) notFound();
  const path = `/solutions/${slug}`;

  return (
    <>
      <JsonLd
        data={serviceSchema({ path, name: solution.metaTitle, description: solution.metaDescription, serviceType: solution.serviceType })}
      />

      <section className="section--ink blueprint hero" aria-labelledby="solution-title">
        <div className="container hero__grid">
          <div className="hero__copy">
            <Breadcrumbs items={[{ name: 'Solutions', path: '/solutions' }, { name: solution.name, path }]} />
            <p className="eyebrow">{solution.kicker}</p>
            <h1 id="solution-title" className="display">{solution.title}</h1>
            <p className="lede">{solution.lede}</p>
            <div className="btn-row">
              <a className="btn btn--primary" href={`/workspace/${slug}`}>
                Open the {solution.name.toLowerCase()} workspace <ArrowRight size={17} aria-hidden="true" />
              </a>
              <Link className="btn btn--ghost" href="/contact">Ask a question</Link>
            </div>
          </div>
          <ProductFrame image={solution.image} label={`workspace / ${slug}`} eager />
        </div>
      </section>

      <section className="section" aria-labelledby="capabilities-title">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Capabilities</p>
            <h2 id="capabilities-title" className="h2">What the {solution.name.toLowerCase()} agents do</h2>
          </div>
          <div className="grid-3">
            {solution.capabilities.map((c) => (
              <article key={c.title} className="card">
                <h3 className="h3">{c.title}</h3>
                <p>{c.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section--ink blueprint" aria-labelledby="solution-workflow">
        <div className="container">
          <div className="section-head">
            <p className="eyebrow">Workflow</p>
            <h2 id="solution-workflow" className="h2">Every document follows the same verified path</h2>
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

      <section className="section" aria-labelledby="outputs-title">
        <div className="container grid-2">
          <div className="card">
            <p className="eyebrow">Deliverables</p>
            <h2 id="outputs-title" className="h3">What you get</h2>
            <ul className="check-list">
              {solution.outputs.map((o) => (
                <li key={o}><BadgeCheck size={18} aria-hidden="true" />{o}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <p className="eyebrow">Good to know</p>
            <h2 className="h3">Limits we are open about</h2>
            <p><CircleAlert size={18} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 6 }} />{solution.limits}</p>
          </div>
        </div>
      </section>

      <section className="section section--surface" aria-labelledby="solution-cta">
        <div className="container cta-band__inner">
          <h2 id="solution-cta" className="h2">Try it on a real {slug === 'engineering' ? 'drawing' : 'document'}</h2>
          <div className="btn-row">
            <a className="btn btn--primary" href={`/workspace/${slug}`}>
              Open the workspace <ArrowRight size={17} aria-hidden="true" />
            </a>
            <Link className="btn btn--ghost" href="/contact">Contact us</Link>
          </div>
        </div>
      </section>
    </>
  );
}
