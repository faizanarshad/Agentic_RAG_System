'use client';

import { useId, useState } from 'react';
import { ArrowRight, Ruler, Scale, Stethoscope } from 'lucide-react';

// "Where do you want to start?" picker: choose a workspace and a task, then jump straight to that
// workspace tab (/workspace/<slug>?view=<tab>). The default link and popular links work without JavaScript.
const WORKSPACES = [
  {
    slug: 'engineering',
    name: 'Engineering',
    icon: Ruler,
    tasks: [
      { view: 'review', label: 'Review a drawing against ISO or ASME' },
      { view: 'compare', label: 'Compare two revisions' },
      { view: 'templates', label: 'Edit a documentation template' },
      { view: 'documents', label: 'Open generated documents' },
    ],
  },
  {
    slug: 'legal',
    name: 'Legal',
    icon: Scale,
    tasks: [
      { view: 'overview', label: 'Analyse a batch of legal documents' },
      { view: 'synthesize', label: 'Synthesise insights across documents' },
      { view: 'ask', label: 'Ask or search the whole collection' },
      { view: 'documents', label: 'Browse the document register' },
    ],
  },
  {
    slug: 'medical',
    name: 'Medical',
    icon: Stethoscope,
    tasks: [
      { view: 'chat', label: 'Ask a clinical question' },
      { view: 'upload', label: 'Upload guidelines, papers or datasets' },
    ],
  },
];

const POPULAR = [
  { href: '/workspace/engineering?view=review', label: 'Review a drawing' },
  { href: '/workspace/engineering?view=compare', label: 'Compare revisions' },
  { href: '/workspace/legal?view=synthesize', label: 'Synthesise contracts' },
  { href: '/workspace/medical?view=chat', label: 'Ask a clinical question' },
];

export default function TaskFinder() {
  const id = useId();
  const [workspace, setWorkspace] = useState(WORKSPACES[0]);
  const [task, setTask] = useState(WORKSPACES[0].tasks[0].view);

  const choose = (w) => {
    setWorkspace(w);
    setTask(w.tasks[0].view);
  };

  return (
    <div className="task-finder">
      <div className="task-finder__card">
        <div className="task-finder__field">
          <span className="task-finder__label" id={`${id}-ws`}>Workspace</span>
          <div className="task-finder__segments" role="group" aria-labelledby={`${id}-ws`}>
            {WORKSPACES.map((w, i) => {
              const Icon = w.icon;
              const checked = w.slug === workspace.slug;
              return (
                <button key={w.slug} type="button" aria-pressed={checked}
                  className="task-finder__segment" onClick={() => choose(w)}>
                  <span className="task-finder__num" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
                  <Icon size={16} aria-hidden="true" />
                  {w.name}
                </button>
              );
            })}
          </div>
        </div>
        <div className="task-finder__field task-finder__field--grow">
          <label className="task-finder__label" htmlFor={`${id}-task`}>Task</label>
          <select id={`${id}-task`} className="task-finder__select" value={task} onChange={(e) => setTask(e.target.value)}>
            {workspace.tasks.map((t) => <option key={t.view} value={t.view}>{t.label}</option>)}
          </select>
        </div>
        {/* Plain <a>: the workspace is a separate app shell with its own stylesheet */}
        <a className="btn btn--primary task-finder__go" href={`/workspace/${workspace.slug}?view=${task}`}>
          Start <ArrowRight size={17} aria-hidden="true" />
        </a>
      </div>
      <nav className="task-finder__popular" aria-label="Popular tasks">
        <span>Popular:</span>
        {POPULAR.map((p) => <a key={p.href} href={p.href}>{p.label}</a>)}
      </nav>
    </div>
  );
}
