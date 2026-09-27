'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Ruler, Scale, Stethoscope } from 'lucide-react';
import Carousel from './Carousel';

const ICONS = { engineering: Ruler, legal: Scale, medical: Stethoscope };

// Numbered capability cards in a swipeable slider, filtered by workspace tabs
export default function CapabilitySlider({ capabilities, workspaces }) {
  const [filter, setFilter] = useState('all');
  const shown = filter === 'all' ? capabilities : capabilities.filter((c) => c.slug === filter);
  const tabs = [{ slug: 'all', name: 'All' }, ...workspaces];

  return (
    <>
      <div className="filter-tabs" role="group" aria-label="Filter capabilities by workspace">
        {tabs.map((t, i) => (
          <button key={t.slug} type="button" className="filter-tabs__tab" aria-pressed={filter === t.slug}
            onClick={() => setFilter(t.slug)}>
            {i > 0 && <span className="filter-tabs__num" aria-hidden="true">{String(i).padStart(2, '0')}</span>}
            {t.name}
            <span className="filter-tabs__count">
              {t.slug === 'all' ? capabilities.length : capabilities.filter((c) => c.slug === t.slug).length}
            </span>
          </button>
        ))}
      </div>
      {/* Remount on filter change so the slider starts from the first card */}
      <Carousel key={filter} label="Capabilities">
        {shown.map((c) => {
          const Icon = ICONS[c.slug];
          return (
            <article key={`${c.slug}-${c.title}`} className="card card--link capability">
              <div className="capability__top">
                <span className="capability__num" aria-hidden="true">{String(c.number).padStart(2, '0')}</span>
                <span className="capability__tag"><Icon size={14} aria-hidden="true" />{c.workspace}</span>
              </div>
              <h3 className="h3">{c.title}</h3>
              <p>{c.body}</p>
              <Link className="text-link card__link" href={`/solutions/${c.slug}`}>
                <span className="visually-hidden">{c.title}: </span>Explore {c.workspace.toLowerCase()}
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </article>
          );
        })}
      </Carousel>
    </>
  );
}
