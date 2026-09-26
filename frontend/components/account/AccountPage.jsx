'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { AlertTriangle, CheckCircle, KeyRound, Loader2, Monitor, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { fetchBackend, jsonRequest } from '@/lib/api';

const MIN_LENGTH = 10;

function describeDevice(userAgent = '') {
  const browser = /Edg\//.test(userAgent) ? 'Edge' : /Chrome\//.test(userAgent) ? 'Chrome'
    : /Firefox\//.test(userAgent) ? 'Firefox' : /Safari\//.test(userAgent) ? 'Safari' : 'Browser';
  const os = /Windows/.test(userAgent) ? 'Windows' : /Mac OS X/.test(userAgent) ? 'macOS'
    : /Android/.test(userAgent) ? 'Android' : /iPhone|iPad/.test(userAgent) ? 'iOS' : /Linux/.test(userAgent) ? 'Linux' : '';
  return os ? `${browser} on ${os}` : browser;
}

export default function AccountPage() {
  const router = useRouter();
  const required = useSearchParams().get('required') === '1';
  const { user, reload } = useAuth();
  const [form, setForm] = useState({ current: '', next: '', confirm: '' });
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [sessions, setSessions] = useState([]);

  const loadSessions = useCallback(async () => {
    try {
      setSessions((await fetchBackend('/auth/sessions')).sessions);
    } catch {
      // Non-critical
    }
  }, []);

  useEffect(() => {
    // Fetch on mount; state is only set after the request resolves
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadSessions();
  }, [loadSessions]);

  const submit = async (event) => {
    event.preventDefault();
    if (form.next.length < MIN_LENGTH) return setStatus({ ok: false, text: `Use at least ${MIN_LENGTH} characters.` });
    if (form.next !== form.confirm) return setStatus({ ok: false, text: 'The new passwords do not match.' });
    setBusy(true);
    setStatus(null);
    try {
      const data = await fetchBackend('/auth/change-password',
        jsonRequest('POST', { current_password: form.current, new_password: form.next }));
      setForm({ current: '', next: '', confirm: '' });
      setStatus({
        ok: true,
        text: `Password updated.${data.other_sessions_signed_out ? ` ${data.other_sessions_signed_out} other session(s) were signed out.` : ''}`,
      });
      await reload();
      loadSessions();
      if (required) router.replace('/workspace');
    } catch (e) {
      setStatus({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };

  const revokeOthers = async () => {
    try {
      const data = await fetchBackend('/auth/sessions/revoke-others', jsonRequest('POST', {}));
      setStatus({ ok: true, text: `Signed out ${data.signed_out} other session(s).` });
      loadSessions();
    } catch (e) {
      setStatus({ ok: false, text: e.message });
    }
  };

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div className="ws-overview">
      <div className="ws-overview__inner account">
        <div>
          <h1 className="legal-page-title">Account</h1>
          <p className="legal-muted">{user?.name} · {user?.email} · <span className="ws-role-inline">{user?.role}</span></p>
        </div>

        {required && (
          <div className="legal-note eng-missing-box" role="alert">
            <AlertTriangle size={18} aria-hidden="true" />
            <span>You are using a temporary password. Choose a new password to continue.</span>
          </div>
        )}

        <section className="upload-card" aria-labelledby="password-title">
          <h2 id="password-title" className="legal-card-title"><KeyRound size={16} aria-hidden="true" /> Change password</h2>
          <form className="account-form" onSubmit={submit}>
            <input type="email" autoComplete="username" value={user?.email || ''} readOnly hidden />
            <label>
              <span>Current password</span>
              <input type="password" autoComplete="current-password" value={form.current} onChange={update('current')} required />
            </label>
            <label>
              <span>New password <em>(at least {MIN_LENGTH} characters)</em></span>
              <input type="password" autoComplete="new-password" value={form.next} onChange={update('next')} required minLength={MIN_LENGTH} />
            </label>
            <label>
              <span>Confirm new password</span>
              <input type="password" autoComplete="new-password" value={form.confirm} onChange={update('confirm')} required />
            </label>
            {status && (
              <p className={`form-msg ${status.ok ? 'ok' : 'err'}`} role="status">
                {status.ok ? <CheckCircle size={16} aria-hidden="true" /> : <AlertTriangle size={16} aria-hidden="true" />} {status.text}
              </p>
            )}
            <div>
              <button className="upload-button" type="submit" disabled={busy}>
                {busy ? <Loader2 size={16} className="spin" /> : <ShieldCheck size={16} />} Update password
              </button>
            </div>
          </form>
        </section>

        <section className="upload-card" aria-labelledby="sessions-title">
          <div className="medical-files-header">
            <h2 id="sessions-title" className="legal-card-title"><Monitor size={16} aria-hidden="true" /> Active sessions</h2>
            {sessions.length > 1 && (
              <button className="action-button delete" onClick={revokeOthers}>Sign out other sessions</button>
            )}
          </div>
          <table className="legal-table">
            <thead><tr><th>Device</th><th>IP address</th><th>Signed in</th><th>Last active</th></tr></thead>
            <tbody>
              {sessions.map((s, i) => (
                <tr key={i}>
                  <td>{describeDevice(s.user_agent)} {s.current && <span className="legal-badge risk-low">This device</span>}</td>
                  <td className="nowrap">{s.ip}</td>
                  <td className="nowrap">{new Date(s.created_at).toLocaleString()}</td>
                  <td className="nowrap">{new Date(s.last_seen_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
