'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { CircleAlert, Eye, EyeOff, KeyRound, Loader2 } from 'lucide-react';
import { fetchBackend, jsonRequest } from '@/lib/api';

// The token arrives in the URL fragment (#token=...), which browsers never send to servers or other sites
function readToken() {
  const match = window.location.hash.match(/token=([A-Za-z0-9_-]+)/);
  return match ? match[1] : '';
}

export default function ResetPasswordForm() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [link, setLink] = useState(null); // null = checking; {valid, purpose, email}
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const value = readToken();
    // Remove the token from the address bar and history as soon as it has been read
    window.history.replaceState(null, '', window.location.pathname);
    const check = value
      ? fetchBackend('/auth/reset-password/check', jsonRequest('POST', { token: value }))
      : Promise.resolve({ valid: false });
    check
      .then((result) => {
        setToken(value);
        setLink(result);
      })
      .catch(() => setLink({ valid: false }));
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    if (password !== confirm) return setError('The two passwords do not match.');
    setBusy(true);
    setError('');
    try {
      await fetchBackend('/auth/reset-password', jsonRequest('POST', { token, password }));
      router.replace('/login?reset=1');
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  };

  if (link === null) {
    return <p className="muted"><Loader2 size={16} className="spin" aria-hidden="true" /> Checking your link…</p>;
  }

  if (!link.valid) {
    return (
      <>
        <h1 className="h3">This link has expired</h1>
        <p className="muted">Links work once and expire after a short time. Request a new one to continue.</p>
        <Link className="btn btn--primary auth-submit" href="/forgot-password">Request a new link</Link>
      </>
    );
  }

  const invite = link.purpose === 'invite';
  return (
    <>
      <h1 className="h3">{invite ? 'Welcome! Choose your password' : 'Choose a new password'}</h1>
      <p className="muted">For <strong>{link.email}</strong>. Use at least 10 characters.</p>
      <form className="auth-form" onSubmit={submit} noValidate>
        <input type="email" autoComplete="username" value={link.email} readOnly hidden />
        <div className="field">
          <label htmlFor="reset-password">New password</label>
          <div className="password-field">
            <input id="reset-password" type={show ? 'text' : 'password'} autoComplete="new-password" minLength={10}
              value={password} onChange={(e) => setPassword(e.target.value)} required autoFocus />
            <button type="button" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'}>
              {show ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>
        <div className="field">
          <label htmlFor="reset-confirm">Confirm password</label>
          <input id="reset-confirm" type={show ? 'text' : 'password'} autoComplete="new-password"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
        </div>
        <div aria-live="assertive">
          {error && <p className="form-status form-status--error"><CircleAlert size={18} aria-hidden="true" />{error}</p>}
        </div>
        <button className="btn btn--primary auth-submit" type="submit" disabled={busy}>
          {busy ? <Loader2 size={17} aria-hidden="true" /> : <KeyRound size={17} aria-hidden="true" />}
          {busy ? 'Saving…' : invite ? 'Create password' : 'Save new password'}
        </button>
      </form>
    </>
  );
}
