import Link from 'next/link';
import { ArrowRight, Ruler, Scale, Stethoscope } from 'lucide-react';
import Breadcrumbs from '@/components/site/Breadcrumbs';
import JsonLd from '@/components/site/JsonLd';
import { defaultShareImage } from '@/lib/metadata';
import { solutionList } from '@/lib/content';
import { site } from '@/lib/site';
import { webPageSchema } from '@/lib/structured-data';

const description =
  'AI agents for engineering drawing review, legal document synthesis and clinical document Q&A, built on one verification pipeline.';

export const metadata = {
  title: 'Solutions',
  description,
  alternates: { canonical: '/solutions' },
  openGraph: { url: '/solutions', title: `Solutions | ${site.name}`, description, images: [defaultShareImage] },
};

const ICONS = { engineering: Ruler, legal: Scale, medical: Stethoscope };

export default function SolutionsPage() {
  return (
    <>
      <JsonLd data={webPageSchema('CollectionPage', { path: '/solutions', name: 'Solutions', description })} />
      <section className="section--ink blueprint page-hero" aria-labelledby="solutions-title">
        <div className="container page-hero__inner">
          <Breadcrumbs items={[{ name: 'Solutions', path: '/solutions' }]} />
          <p className="eyebrow">Solutions</p>
          <h1 id="solutions-title" className="display">One verification engine, three specialist workspaces</h1>
          <p className="lede">{description}</p>
        </div>
      </section>
      <section className="section">
        <div className="container grid-3">
          {solutionList.map((s) => {
            const Icon = ICONS[s.slug];
            return (
              <article key={s.slug} className="card card--link">
                <span className="card__icon"><Icon size={22} aria-hidden="true" /></span>
                <p className="card__kicker">{s.kicker}</p>
                <h2 className="h3">{s.title}</h2>
                <p>{s.lede}</p>
                <Link className="text-link card__link" href={`/solutions/${s.slug}`}>
                  Explore {s.name.toLowerCase()} <ArrowRight size={16} aria-hidden="true" />
                </Link>
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}
