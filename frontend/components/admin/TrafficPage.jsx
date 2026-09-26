'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import { API_BASE } from '@/lib/api';
import { AdminState, RangePicker, useAdminData } from './AdminFrame';
import { BarList, StatTile, TimeSeriesChart } from './charts';

export default function TrafficPage() {
  const [days, setDays] = useState(30);
  const { data, loading, error } = useAdminData(`/admin/traffic?days=${days}`);
  const perVisitor = data && data.totals.visitors ? (data.totals.page_views / data.totals.visitors).toFixed(1) : '—';

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Website traffic</h2>
        <div className="admin-toolbar__actions">
          <RangePicker days={days} onChange={setDays} />
          <a className="action-button update" href={`${API_BASE}/admin/traffic.csv?days=${days}`}><Download size={14} /> Export CSV</a>
        </div>
      </div>
      <p className="admin-note">
        First-party and cookie-less: visitors are counted with an anonymous identifier that changes daily, IP addresses are
        never stored, bots are excluded and browsers sending Do Not Track are not counted.
      </p>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <>
          <div className="legal-tiles">
            <StatTile label="Page views" value={data.totals.page_views.toLocaleString()} delta={data.deltas.page_views} sub={`last ${days} days`} />
            <StatTile label="Unique visitors" value={data.totals.visitors.toLocaleString()} delta={data.deltas.visitors} sub="counted per day (IDs reset daily)" />
            <StatTile label="Views per visitor" value={perVisitor} />
            <StatTile label="Conversion rate" value={data.deltas.conversion_rate.current === null ? '—' : `${data.deltas.conversion_rate.current}%`}
              sub={`${data.deltas.messages.current} contact message(s)`} />
          </div>
          <div className="admin-grid">
            <section className="upload-card">
              <h3 className="legal-card-title">Page views per day</h3>
              <TimeSeriesChart series={data.series.page_views} label="Page views" />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Unique visitors per day</h3>
              <TimeSeriesChart series={data.series.visitors} label="Unique visitors" />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Contact conversions per day</h3>
              <TimeSeriesChart series={data.conversions} label="Contact messages" />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Landing pages</h3>
              <BarList items={data.landing_pages} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Top blog posts</h3>
              <BarList items={data.top_posts} empty="No post views yet" />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Top pages</h3>
              <BarList items={data.top_pages} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Referrers</h3>
              <BarList items={data.referrers} />
            </section>
            <section className="upload-card">
              <h3 className="legal-card-title">Devices</h3>
              <BarList items={data.devices} formatLabel={(d) => d.replace(/^\w/, (c) => c.toUpperCase())} />
            </section>
          </div>
        </>
      )}
    </>
  );
}
