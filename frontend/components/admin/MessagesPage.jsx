'use client';

import { useState } from 'react';
import { Download, Mail, MailOpen, Trash2 } from 'lucide-react';
import { API_BASE, fetchBackend, jsonRequest } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';
import { BarList } from './charts';

export default function MessagesPage() {
  const [status, setStatus] = useState('all');
  const { data, loading, error, reload } = useAdminData(`/admin/messages?status=${status}`);

  const setRead = async (m, read) => {
    await fetchBackend(`/admin/messages/${m.id}`, jsonRequest('PATCH', { read }));
    reload();
  };

  const remove = async (m) => {
    if (!window.confirm(`Delete the message from ${m.email}?`)) return;
    await fetchBackend(`/admin/messages/${m.id}`, { method: 'DELETE' });
    reload();
  };

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Contact messages</h2>
        <div className="admin-toolbar__actions">
          <label className="admin-range">
            <span className="visually-hidden">Filter</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All messages</option>
              <option value="unread">Unread</option>
              <option value="read">Read</option>
            </select>
          </label>
          <a className="action-button update" href={`${API_BASE}/admin/messages.csv`}><Download size={14} /> Export CSV</a>
        </div>
      </div>
      <AdminState loading={loading && !data} error={error} />
      {data && (
        <div className="admin-grid">
          <section className="upload-card">
            <h3 className="legal-card-title">{data.total} message(s) · {data.stats.unread} unread</h3>
            {data.messages.length === 0 && <p className="legal-empty-note">No messages.</p>}
            {data.messages.map((m) => (
              <article key={m.id} className={`message-card ${m.read_at ? '' : 'unread'}`}>
                <div className="message-card__head">
                  <span className="message-card__from">{m.name} · <a className="legal-link" href={`mailto:${m.email}`}>{m.email}</a></span>
                  <span className="legal-muted small">{new Date(m.created_at).toLocaleString()}</span>
                </div>
                <div className="legal-muted small">{m.company || 'No company'} · {m.topic}</div>
                <p>{m.message}</p>
                <div className="admin-actions">
                  {m.read_at ? (
                    <button className="action-button update" onClick={() => setRead(m, false)}><Mail size={14} /> Mark unread</button>
                  ) : (
                    <button className="action-button update" onClick={() => setRead(m, true)}><MailOpen size={14} /> Mark read</button>
                  )}
                  <a className="action-button update" href={`mailto:${m.email}?subject=${encodeURIComponent('Re: your AIDocumentAgent enquiry')}`}>Reply</a>
                  <button className="action-button delete" onClick={() => remove(m)} aria-label="Delete message"><Trash2 size={14} /></button>
                </div>
              </article>
            ))}
          </section>
          <section className="upload-card">
            <h3 className="legal-card-title">By topic</h3>
            <BarList items={data.stats.by_topic} />
          </section>
        </div>
      )}
    </>
  );
}
