'use client';

import { useState } from 'react';
import { Copy, KeyRound, Loader2, Trash2, UserPlus } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { fetchBackend, jsonRequest } from '@/lib/api';
import { AdminState, useAdminData } from './AdminFrame';

export default function UsersPage() {
  const { user: me } = useAuth();
  const { data, loading, error, reload } = useAdminData('/admin/users');
  const [form, setForm] = useState({ name: '', email: '', role: 'member' });
  const [secret, setSecret] = useState(null);
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
      setSecret({ email: result.user.email, password: result.temporary_password });
      setForm({ name: '', email: '', role: 'member' });
    }
  };

  const resetPassword = async (u) => {
    if (!window.confirm(`Generate a new temporary password for ${u.email}? Their sessions will be signed out.`)) return;
    const result = await act(() => fetchBackend(`/admin/users/${u.id}/reset-password`, jsonRequest('POST', {})));
    if (result) setSecret({ email: u.email, password: result.temporary_password });
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
            {busy ? <Loader2 size={16} className="spin" /> : <UserPlus size={16} />} Create user
          </button>
        </form>
        <p className="admin-note">A temporary password is generated and shown once. The user must change it at first sign-in.</p>
        {secret && (
          <div className="secret-box" role="status">
            <KeyRound size={16} aria-hidden="true" />
            <span>Temporary password for <strong>{secret.email}</strong>:</span>
            <code>{secret.password}</code>
            <button className="action-button update" onClick={() => navigator.clipboard.writeText(secret.password)}>
              <Copy size={14} /> Copy
            </button>
            <button className="legal-link" onClick={() => setSecret(null)}>Done</button>
          </div>
        )}
        {message && <p className={`form-msg ${message.ok ? 'ok' : 'err'}`} role="status">{message.text}</p>}
      </section>

      <section className="upload-card">
        <h2 className="legal-card-title">Users {data && `(${data.users.length})`}</h2>
        <AdminState loading={loading && !data} error={error} />
        {data && (
          <div className="legal-table-wrap">
            <table className="legal-table admin-table">
              <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last sign-in</th><th>Events (30d)</th><th /></tr></thead>
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
                      <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}</td>
                      <td>{u.events_30d}</td>
                      <td>
                        <div className="admin-actions">
                          <button className="action-button update" onClick={() => resetPassword(u)}>Reset password</button>
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
