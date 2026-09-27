'use client';

import { CheckCircle, XCircle } from 'lucide-react';
import { AdminState, useAdminData } from './AdminFrame';
import { BarList } from './charts';

export default function SystemPage() {
  const { data, loading, error } = useAdminData('/admin/system');
  return (
    <>
      <h2 className="legal-card-title">System</h2>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <div className="admin-grid">
          <section className="upload-card">
            <h3 className="legal-card-title">Vector database</h3>
            <p>
              <span className={`legal-badge ${data.vector_db.ok ? 'risk-low' : 'risk-high'}`}>
                {data.vector_db.ok ? <CheckCircle size={12} aria-hidden="true" /> : <XCircle size={12} aria-hidden="true" />}
                {data.vector_db.ok ? 'Connected' : 'Unavailable'}
              </span>
            </p>
            {data.vector_db.ok ? (
              <BarList items={Object.entries(data.vector_db.namespaces)} formatLabel={(n) => `Namespace: ${n}`} />
            ) : <p className="legal-error">{data.vector_db.error}</p>}
          </section>
          <section className="upload-card">
            <h3 className="legal-card-title">Storage (MB)</h3>
            <BarList items={Object.entries(data.storage_mb)} formatValue={(v) => `${v} MB`} />
          </section>
          <section className="upload-card">
            <h3 className="legal-card-title">Models</h3>
            <dl className="kv">
              {Object.entries(data.models).map(([k, v]) => (<div key={k} style={{ display: 'contents' }}><dt>{k}</dt><dd><code>{v}</code></dd></div>))}
            </dl>
          </section>
          <section className="upload-card">
            <h3 className="legal-card-title">Security settings</h3>
            <dl className="kv">
              <dt>Secure cookies (HTTPS)</dt><dd>{data.security.cookie_secure ? 'On' : 'Off (enable in production)'}</dd>
              <dt>Session lifetime</dt><dd>{data.security.session_ttl_hours} hours</dd>
              <dt>Allowed origins</dt><dd>{data.security.allowed_origins.join(', ')}</dd>
              <dt>Website analytics</dt><dd>{data.security.analytics_enabled ? 'Enabled' : 'Disabled'}</dd>
            </dl>
          </section>
        </div>
      )}
    </>
  );
}
