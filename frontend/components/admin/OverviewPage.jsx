'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, CheckCircle, Inbox, Info, XCircle } from 'lucide-react';
import { AdminState, RangePicker, useAdminData } from './AdminFrame';
import { BarList, StatTile, TimeSeriesChart } from './charts';

const humanize = (v) => String(v).replace(/[._]/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
const VERDICT = {
  approved: { label: 'Approved', tone: 'risk-low', icon: CheckCircle },
  approved_with_comments: { label: 'With comments', tone: 'risk-medium', icon: AlertTriangle },
  rejected: { label: 'Rejected', tone: 'risk-high', icon: XCircle },
};

export function ActivityRow({ event }) {
  return (
    <tr>
      <td className="nowrap">{new Date(event.created_at).toLocaleString()}</td>
      <td>{event.user_name || <span className="legal-muted small">System / visitor</span>}</td>
      <td><code>{event.action}</code></td>
      <td>{event.workspace ? humanize(event.workspace) : '—'}</td>
    </tr>
  );
}

export default function OverviewPage() {
  const [days, setDays] = useState(30);
  const { data, loading, error } = useAdminData(`/admin/overview?days=${days}`);

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Overview</h2>
        <RangePicker days={days} onChange={setDays} />
      </div>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <>
          <div className="legal-tiles">
            <StatTile label="Workspace actions" value={data.kpis.actions.toLocaleString()} sub={`${data.kpis.signed_in_users} users signed in`} />
            <StatTile label="Website page views" value={data.kpis.page_views.toLocaleString()} sub={`${data.kpis.visitors} unique visitors`} />
            <StatTile label="Model cost (est.)" value={`$${data.kpis.llm_cost_usd.toFixed(2)}`} sub={`last ${days} days`} />
            <StatTile label="Unread messages" value={data.messages.unread} sub={`${data.messages.total} total`} />
          </div>

          <div className="admin-grid">
            <section className="upload-card">
              <h3 className="legal-card-title">Workspace actions per day</h3>
              <TimeSeriesChart series={data.series.actions} label="Workspace actions" />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Website page views per day</h3>
              <TimeSeriesChart series={data.series.page_views} label="Page views" />
            </section>

            <section className="upload-card">
              <h3 className="legal-card-title">Actions by workspace</h3>
              <BarList items={data.by_workspace} formatLabel={humanize} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Content</h3>
              <dl className="kv">
                <dt>Drawings reviewed</dt><dd>{data.content.drawings}</dd>
                <dt>Revision comparisons</dt><dd>{data.content.comparisons}</dd>
                <dt>Generated documents</dt><dd>{data.content.generated_documents}</dd>
                <dt>Templates</dt><dd>{data.content.templates}</dd>
                <dt>Legal documents</dt><dd>{data.content.legal_documents}</dd>
                <dt>Active users</dt><dd>{data.kpis.active_users} ({data.kpis.admins} admin)</dd>
                <dt>Failed sign-ins</dt><dd>{data.kpis.failed_logins}</dd>
              </dl>
              {Object.keys(data.content.drawing_verdicts || {}).length > 0 && (
                <div className="legal-drawer-actions" style={{ marginTop: 14 }}>
                  {Object.entries(data.content.drawing_verdicts).map(([verdict, count]) => {
                    const v = VERDICT[verdict] || { label: humanize(verdict), tone: 'neutral', icon: Info };
                    const Icon = v.icon;
                    return <span key={verdict} className={`legal-badge ${v.tone}`}><Icon size={12} aria-hidden="true" /> {v.label}: {count}</span>;
                  })}
                </div>
              )}
            </section>

            <section className="upload-card admin-span-2">
              <div className="admin-toolbar">
                <h3 className="legal-card-title">Recent activity</h3>
                <Link className="action-button update" href="/admin/activity">View all</Link>
              </div>
              {data.recent_activity.length === 0 ? (
                <p className="legal-empty-note">No activity yet.</p>
              ) : (
                <div className="legal-table-wrap">
                  <table className="legal-table admin-table">
                    <thead><tr><th>When</th><th>User</th><th>Action</th><th>Workspace</th></tr></thead>
                    <tbody>{data.recent_activity.map((e) => <ActivityRow key={e.id} event={e} />)}</tbody>
                  </table>
                </div>
              )}
            </section>

            {data.messages.unread > 0 && (
              <section className="upload-card admin-span-2">
                <p className="legal-note"><Inbox size={16} aria-hidden="true" /> {data.messages.unread} unread contact message(s). <Link className="legal-link" href="/admin/messages">Open inbox</Link></p>
              </section>
            )}
          </div>
        </>
      )}
    </>
  );
}
