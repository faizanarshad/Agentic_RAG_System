'use client';

import { useState } from 'react';
import { Copy, Link2, Loader2, MailCheck, Trash2, UserPlus } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { fetchBackend, jsonRequest } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';

export default function UsersPage() {
  const { user: me } = useAuth();
  const { data, loading, error, reload } = useAdminData('/admin/users');
  const [form, setForm] = useState({ name: '', email: '', role: 'member' });
  // {email, kind: 'invite' | 'reset', link?} – a link is only returned when it could not be emailed
  const [issued, setIssued] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  const act = async (fn, success) => {
    setMessage(null);
    try {
      const result = await fn();
      if (success) setMessage({ ok: true, text: success });
      await reload();
      return result;
    } catch (e) {
      setMessage({ ok: false, text: e.message });
      return null;
    }
  };

  const createUser = async (event) => {
    event.preventDefault();
    setBusy(true);
    const result = await act(() => fetchBackend('/admin/users', jsonRequest('POST', form)));
    setBusy(false);
    if (result) {
      setIssued({ email: result.user.email, kind: 'invite', link: result.link });
      setForm({ name: '', email: '', role: 'member' });
    }
  };

  const resetPassword = async (u) => {
    if (!window.confirm(`Send ${u.email} a password reset link? Their current password stops working and their sessions are signed out.`)) return;
    const result = await act(() => fetchBackend(`/admin/users/${u.id}/reset-password`, jsonRequest('POST', {})));
    if (result) setIssued({ email: u.email, kind: 'reset', link: result.link });
  };

  const patch = (u, body, text) => act(() => fetchBackend(`/admin/users/${u.id}`, jsonRequest('PATCH', body)), text);

  const remove = (u) => {
    if (!window.confirm(`Delete ${u.email}? This cannot be undone.`)) return;
    act(() => fetchBackend(`/admin/users/${u.id}`, { method: 'DELETE' }), `${u.email} deleted.`);
  };

  return (
    <>
      <section className="upload-card">
        <h2 className="legal-card-title"><UserPlus size={16} aria-hidden="true" /> Invite a user</h2>
        <form className="admin-form" onSubmit={createUser}>
          <label><span>Name</span><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
          <label><span>Email</span><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
          <label>
            <span>Role</span>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button className="upload-button" type="submit" disabled={busy}>
            {busy ? <Loader2 size={16} className="spin" /> : <UserPlus size={16} />} Send invitation
          </button>
        </form>
        <p className="admin-note">
          The user receives a single-use link to choose their own password (valid 72 hours). Nobody else ever sees it.
        </p>
        {issued && (issued.link ? (
          <div className="secret-box" role="status">
            <Link2 size={16} aria-hidden="true" />
            <span>
              Email is not configured, so send this {issued.kind === 'invite' ? 'invitation' : 'reset'} link
              to <strong>{issued.email}</strong> yourself. It works once.
            </span>
            <code className="secret-link">{issued.link}</code>
            <button className="action-button update" onClick={() => navigator.clipboard.writeText(issued.link)}>
              <Copy size={14} /> Copy
            </button>
            <button className="legal-link" onClick={() => setIssued(null)}>Done</button>
          </div>
        ) : (
          <div className="secret-box" role="status">
            <MailCheck size={16} aria-hidden="true" />
            <span>{issued.kind === 'invite' ? 'Invitation' : 'Reset link'} emailed to <strong>{issued.email}</strong>.</span>
            <button className="legal-link" onClick={() => setIssued(null)}>Done</button>
          </div>
        ))}
        {message && <p className={`form-msg ${message.ok ? 'ok' : 'err'}`} role="status">{message.text}</p>}
      </section>

      <section className="upload-card">
        <h2 className="legal-card-title">Users {data && `(${data.users.length})`}</h2>
        <AdminState loading={loading && !data} error={error} />
        {data && (
          <div className="legal-table-wrap">
            <table className="legal-table admin-table">
              <thead><tr><th>User</th><th>Role</th><th>Status</th><th>2FA</th><th>Last sign-in</th><th>Events (30d)</th><th /></tr></thead>
              <tbody>
                {data.users.map((u) => {
                  const self = u.id === me?.id;
                  return (
                    <tr key={u.id}>
                      <td>
                        <div className="legal-doc-title">{u.name}{self && ' (you)'}</div>
                        <div className="legal-muted small">{u.email}</div>
                      </td>
                      <td>
                        <select aria-label={`Role for ${u.email}`} value={u.role} disabled={self}
                          onChange={(e) => patch(u, { role: e.target.value }, `${u.email} is now ${e.target.value}.`)}>
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td>
                        <span className={`legal-badge ${u.status === 'active' ? 'risk-low' : 'neutral'}`}>{u.status}</span>
                        {u.must_change_password ? <span className="legal-badge risk-medium" style={{ marginLeft: 6 }}>temp password</span> : null}
                      </td>
                      <td>
                        <span className={`status-pill status-pill--${u.totp_enabled ? 'published' : 'draft'}`}>{u.totp_enabled ? 'On' : 'Off'}</span>
                      </td>
                      <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}</td>
                      <td>{u.events_30d}</td>
                      <td>
                        <div className="admin-actions">
                          <button className="action-button update" onClick={() => resetPassword(u)}>Reset password</button>
                          {u.totp_enabled ? (
                            <button className="action-button update" onClick={() => {
                              if (window.confirm(`Turn off two-factor authentication for ${u.email}? Use this only if they lost their phone and recovery codes.`)) {
                                act(() => fetchBackend(`/admin/users/${u.id}/reset-2fa`, jsonRequest('POST', {})), `2FA reset for ${u.email}.`);
                              }
                            }}>Reset 2FA</button>
                          ) : null}
                          {!self && (u.status === 'active' ? (
                            <button className="action-button update" onClick={() => patch(u, { status: 'disabled' }, `${u.email} disabled.`)}>Disable</button>
                          ) : (
                            <button className="action-button update" onClick={() => patch(u, { status: 'active' }, `${u.email} enabled.`)}>Enable</button>
                          ))}
                          {!self && (
                            <button className="action-button delete" onClick={() => remove(u)} aria-label={`Delete ${u.email}`}><Trash2 size={14} /></button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
