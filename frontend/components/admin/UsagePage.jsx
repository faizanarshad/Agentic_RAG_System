'use client';

import { useState } from 'react';
import { AdminState, RangePicker, useAdminData } from './AdminFrame';
import { BarList, StatTile, TimeSeriesChart } from './charts';

const usd = (v) => `$${Number(v || 0).toFixed(v >= 1 ? 2 : 4)}`;
const compact = (v) => Intl.NumberFormat(undefined, { notation: 'compact' }).format(v || 0);

export default function UsagePage() {
  const [days, setDays] = useState(30);
  const { data, loading, error } = useAdminData(`/admin/usage?days=${days}`);

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Usage &amp; cost</h2>
        <RangePicker days={days} onChange={setDays} />
      </div>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <>
          <div className="legal-tiles">
            <StatTile label="Estimated model cost" value={usd(data.totals.cost_usd)} sub={`last ${days} days`} />
            <StatTile label="Model calls" value={data.totals.calls.toLocaleString()} />
            <StatTile label="Input tokens" value={compact(data.totals.prompt_tokens)} />
            <StatTile label="Output tokens" value={compact(data.totals.completion_tokens)} />
          </div>
          <div className="admin-grid">
            <section className="upload-card admin-span-2">
              <h3 className="legal-card-title">Estimated cost per day (USD)</h3>
              <TimeSeriesChart series={data.series.cost_usd} label="Cost (USD)" format={(v) => `$${v.toFixed(v >= 1 ? 2 : 3)}`} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Cost by feature</h3>
              <BarList items={data.by_feature} formatValue={usd} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Most used actions</h3>
              <BarList items={data.top_actions} />
            </section>
            <section className="upload-card admin-span-2">
              <h3 className="legal-card-title">By model</h3>
              {data.by_model.length === 0 ? <p className="legal-empty-note">No model calls recorded yet.</p> : (
                <div className="legal-table-wrap">
                  <table className="legal-table admin-table">
                    <thead><tr><th>Model</th><th>Calls</th><th>Input tokens</th><th>Output tokens</th><th>Est. cost</th></tr></thead>
                    <tbody>
                      {data.by_model.map((m) => (
                        <tr key={m.model}>
                          <td><code>{m.model}</code></td>
                          <td>{m.calls.toLocaleString()}</td>
                          <td>{m.prompt_tokens.toLocaleString()}</td>
                          <td>{m.completion_tokens.toLocaleString()}</td>
                          <td>{usd(m.cost_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="admin-note">{data.pricing_note}</p>
            </section>
            <section className="upload-card admin-span-2">
              <h3 className="legal-card-title">Actions per user</h3>
              <BarList items={data.by_user.map((u) => [`${u.name} (${u.email})`, u.actions])} />
            </section>
          </div>
        </>
      )}
    </>
  );
}
