'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import { API_BASE } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';
import { ActivityRow } from './OverviewPage';

const PAGE = 50;

export default function ActivityPage() {
  const [filters, setFilters] = useState({ action: '', workspace: '' });
  const [page, setPage] = useState(0);
  const query = new URLSearchParams({ limit: PAGE, offset: page * PAGE });
  if (filters.action) query.set('action', filters.action);
  if (filters.workspace) query.set('workspace', filters.workspace);
  const { data, loading, error } = useAdminData(`/admin/activity?${query}`);
  const csv = new URLSearchParams();
  if (filters.action) csv.set('action', filters.action);
  if (filters.workspace) csv.set('workspace', filters.workspace);
  const setFilter = (field) => (e) => { setPage(0); setFilters({ ...filters, [field]: e.target.value }); };

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Activity log</h2>
        <div className="admin-toolbar__actions admin-toolbar">
          <select aria-label="Filter by workspace" value={filters.workspace} onChange={setFilter('workspace')}>
            <option value="">All areas</option>
            {['engineering', 'legal', 'medical', 'auth', 'admin', 'website'].map((w) => <option key={w} value={w}>{w}</option>)}
          </select>
          <select aria-label="Filter by action" value={filters.action} onChange={setFilter('action')}>
            <option value="">All actions</option>
            {(data?.actions || []).map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <a className="action-button update" href={`${API_BASE}/admin/activity.csv?${csv}`}><Download size={14} /> Export CSV</a>
        </div>
      </div>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <section className="upload-card">
          <p className="legal-muted small">{data.total.toLocaleString()} event(s)</p>
          <div className="legal-table-wrap">
            <table className="legal-table admin-table">
              <thead><tr><th>When</th><th>User</th><th>Action</th><th>Workspace</th></tr></thead>
              <tbody>{data.events.map((e) => <ActivityRow key={e.id} event={e} />)}</tbody>
            </table>
          </div>
          <div className="admin-toolbar" style={{ marginTop: 12 }}>
            <button className="action-button update" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
            <span className="legal-muted small">Page {page + 1} of {Math.max(1, Math.ceil(data.total / PAGE))}</span>
            <button className="action-button update" disabled={(page + 1) * PAGE >= data.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </section>
      )}
    </>
  );
}
