'use client';

import { useState } from 'react';
import { CheckCircle, Copy, Download, KeyRound, Loader2, ShieldCheck, ShieldOff } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { fetchBackend, jsonRequest } from '@/lib/api';

function RecoveryCodes({ codes, onDone }) {
  const text = codes.join('\n');
  const download = () => {
    const url = URL.createObjectURL(new Blob([`AIDocumentAgent recovery codes\nEach code works once.\n\n${text}\n`], { type: 'text/plain' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'aidocumentagent-recovery-codes.txt' });
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="recovery" role="status">
      <p><strong>Save these recovery codes now.</strong> Each works once if you lose your phone. They will not be shown again.</p>
      <ul className="recovery__codes">{codes.map((c) => <li key={c}><code>{c}</code></li>)}</ul>
      <div className="admin-actions">
        <button className="action-button update" onClick={() => navigator.clipboard.writeText(text)}><Copy size={14} /> Copy</button>
        <button className="action-button update" onClick={download}><Download size={14} /> Download</button>
        <button className="upload-button" onClick={onDone}><CheckCircle size={16} /> I have saved them</button>
      </div>
    </div>
  );
}

export default function TwoFactorCard() {
  const { user, reload } = useAuth();
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [codes, setCodes] = useState(null);
  const [mode, setMode] = useState(null); // 'disable' | 'regenerate'
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  const run = async (fn) => {
    setBusy(true);
    setMessage(null);
    try {
      await fn();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };

  const start = () => run(async () => setSetup(await fetchBackend('/auth/2fa/setup', jsonRequest('POST', {}))));

  const confirm = (e) => {
    e.preventDefault();
    run(async () => {
      const data = await fetchBackend('/auth/2fa/enable', jsonRequest('POST', { code }));
      setCodes(data.recovery_codes);
      setSetup(null);
      setCode('');
      await reload();
    });
  };

  const disable = (e) => {
    e.preventDefault();
    run(async () => {
      await fetchBackend('/auth/2fa/disable', jsonRequest('POST', { password, code }));
      setMode(null);
      setPassword('');
      setCode('');
      setMessage({ ok: true, text: 'Two-factor authentication is off.' });
      await reload();
    });
  };

  const regenerate = (e) => {
    e.preventDefault();
    run(async () => {
      setCodes((await fetchBackend('/auth/2fa/recovery-codes', jsonRequest('POST', { password }))).recovery_codes);
      setMode(null);
      setPassword('');
      await reload();
    });
  };

  return (
    <section className="upload-card" aria-labelledby="mfa-title">
      <h2 id="mfa-title" className="legal-card-title">
        <ShieldCheck size={16} aria-hidden="true" /> Two-factor authentication
        <span className={`status-pill status-pill--${user?.totp_enabled ? 'published' : 'draft'}`}>{user?.totp_enabled ? 'On' : 'Off'}</span>
      </h2>

      {codes ? (
        <RecoveryCodes codes={codes} onDone={() => { setCodes(null); setMessage({ ok: true, text: 'Two-factor authentication is on.' }); }} />
      ) : user?.totp_enabled ? (
        <>
          <p className="legal-muted">
            Signing in asks for a code from your authenticator app. {user.recovery_codes_left} recovery code(s) left.
          </p>
          {!mode && (
            <div className="admin-actions" style={{ marginTop: 12 }}>
              <button className="action-button update" onClick={() => setMode('regenerate')}><KeyRound size={14} /> New recovery codes</button>
              <button className="action-button delete" onClick={() => setMode('disable')}><ShieldOff size={14} /> Turn off</button>
            </div>
          )}
          {mode && (
            <form className="account-form" onSubmit={mode === 'disable' ? disable : regenerate} style={{ marginTop: 12 }}>
              <label><span>Current password</span>
                <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </label>
              {mode === 'disable' && (
                <label><span>Authenticator or recovery code</span>
                  <input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="one-time-code" required />
                </label>
              )}
              <div className="admin-actions">
                <button className={mode === 'disable' ? 'action-button delete' : 'upload-button'} type="submit" disabled={busy}>
                  {busy && <Loader2 size={14} className="spin" />} {mode === 'disable' ? 'Turn off 2FA' : 'Generate new codes'}
                </button>
                <button type="button" className="legal-link" onClick={() => setMode(null)}>Cancel</button>
              </div>
            </form>
          )}
        </>
      ) : setup ? (
        <form className="mfa-setup" onSubmit={confirm}>
          <ol className="mfa-steps">
            <li>Open an authenticator app (Google Authenticator, Microsoft Authenticator, 1Password, Authy…).</li>
            <li>Scan this QR code, or enter the key manually.</li>
            <li>Type the 6-digit code the app shows.</li>
          </ol>
          <div className="mfa-setup__body">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="mfa-qr" src={`data:image/svg+xml;utf8,${encodeURIComponent(setup.qr_svg)}`} alt="QR code for your authenticator app" width={220} height={220} />
            <div className="account-form">
              <label><span>Manual key</span><code className="mfa-secret">{setup.secret.match(/.{1,4}/g).join(' ')}</code></label>
              <label><span>6-digit code</span>
                <input value={code} onChange={(e) => setCode(e.target.value)} inputMode="numeric" autoComplete="one-time-code" maxLength={7} required autoFocus />
              </label>
              <div className="admin-actions">
                <button className="upload-button" type="submit" disabled={busy}>{busy ? <Loader2 size={16} className="spin" /> : <ShieldCheck size={16} />} Turn on</button>
                <button type="button" className="legal-link" onClick={() => setSetup(null)}>Cancel</button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <>
          <p className="legal-muted">Add a second step at sign-in: a code from an app on your phone. Recommended for all admins.</p>
          <div style={{ marginTop: 12 }}>
            <button className="upload-button" onClick={start} disabled={busy}>{busy ? <Loader2 size={16} className="spin" /> : <ShieldCheck size={16} />} Set up two-factor authentication</button>
          </div>
        </>
      )}
      {message && <p className={`form-msg ${message.ok ? 'ok' : 'err'}`} role="status" style={{ marginTop: 12 }}>{message.text}</p>}
    </section>
  );
}
