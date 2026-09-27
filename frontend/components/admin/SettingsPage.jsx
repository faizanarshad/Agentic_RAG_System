'use client';

import { useEffect, useState } from 'react';
import { Loader2, Megaphone, Save, SlidersHorizontal } from 'lucide-react';
import { fetchBackend, jsonRequest } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';

function Switch({ checked, onChange, label }) {
  return (
    <span className="switch">
      <input type="checkbox" role="switch" checked={checked} onChange={(e) => onChange(e.target.checked)} aria-label={label} />
      <span aria-hidden="true" />
    </span>
  );
}

export default function SettingsPage() {
  const { data, loading, error } = useAdminData('/admin/settings');
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Initialise the editable copy once the settings arrive
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (data) setForm(data);
  }, [data]);

  const setAnnouncement = (field, value) =>
    setForm((f) => ({ ...f, announcement: { ...f.announcement, [field]: value } }));

  const save = async () => {
    setSaving(true);
    setMessage(null);
    try {
      setForm(await fetchBackend('/admin/settings', jsonRequest('PUT', form)));
      setMessage({ ok: true, text: 'Settings saved. The public site updates within a minute.' });
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className="admin-toolbar">
        <h2 className="legal-card-title">Site settings</h2>
        <button className="upload-button" onClick={save} disabled={!form || saving}>
          {saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Save settings
        </button>
      </div>
      {message && <p className={`form-msg ${message.ok ? 'ok' : 'err'}`} role="status">{message.text}</p>}
      <AdminState loading={loading && !data} error={error} />
      {form && (
        <div className="admin-grid">
          <section className="upload-card">
            <h3 className="legal-card-title"><Megaphone size={16} aria-hidden="true" /> Announcement bar</h3>
            <div className="switch-row">
              <div><strong>Show announcement</strong><p>A slim bar above the header on every public page.</p></div>
              <Switch checked={form.announcement.enabled} onChange={(v) => setAnnouncement('enabled', v)} label="Show announcement" />
            </div>
            <div className="editor__main" style={{ gap: 12, marginTop: 12 }}>
              <label className="editor-field">
                <span>Message</span>
                <input value={form.announcement.text} maxLength={160} onChange={(e) => setAnnouncement('text', e.target.value)}
                  placeholder="New: revision audits for engineering drawings" />
              </label>
              <div className="admin-grid" style={{ gap: 12 }}>
                <label className="editor-field">
                  <span>Link text</span>
                  <input value={form.announcement.link_text} maxLength={40} onChange={(e) => setAnnouncement('link_text', e.target.value)} placeholder="Read more" />
                </label>
                <label className="editor-field">
                  <span>Link URL</span>
                  <input value={form.announcement.link_url} maxLength={300} onChange={(e) => setAnnouncement('link_url', e.target.value)} placeholder="/blog/… or https://…" />
                </label>
              </div>
              <label className="editor-field">
                <span>Style</span>
                <select value={form.announcement.tone} onChange={(e) => setAnnouncement('tone', e.target.value)}>
                  <option value="info">Brand (indigo)</option>
                  <option value="success">Success (teal)</option>
                  <option value="warning">Notice (amber)</option>
                </select>
              </label>
              <div className={`announcement-preview announcement-preview--${form.announcement.tone}`} aria-label="Preview">
                {form.announcement.text || 'Your announcement preview'}
                {form.announcement.link_text && <strong> {form.announcement.link_text} →</strong>}
              </div>
            </div>
          </section>

          <section className="upload-card">
            <h3 className="legal-card-title"><SlidersHorizontal size={16} aria-hidden="true" /> Website features</h3>
            <div className="switch-row">
              <div><strong>Contact form</strong><p>When off, the contact page shows a notice and the API rejects new messages.</p></div>
              <Switch checked={form.contact_form_enabled} onChange={(v) => setForm({ ...form, contact_form_enabled: v })} label="Contact form" />
            </div>
            <div className="switch-row">
              <div><strong>Website analytics</strong><p>Cookie-less page-view counting. When off, no page views are recorded.</p></div>
              <Switch checked={form.analytics_enabled} onChange={(v) => setForm({ ...form, analytics_enabled: v })} label="Website analytics" />
            </div>
          </section>
        </div>
      )}
    </>
  );
}
