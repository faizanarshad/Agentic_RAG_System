'use client';

import { useState } from 'react';
import { CircleAlert, CircleCheck, Loader2, Mail } from 'lucide-react';
import { fetchBackend, jsonRequest } from '@/lib/api';

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    if (!email.trim()) return setError('Enter your email address.');
    setBusy(true);
    setError('');
    try {
      const data = await fetchBackend('/auth/forgot-password', jsonRequest('POST', { email: email.trim() }));
      setSent(data.message);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <p className="form-status form-status--success" role="status">
        <CircleCheck size={18} aria-hidden="true" />{sent}
      </p>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit} noValidate>
      <div className="field">
        <label htmlFor="forgot-email">Email</label>
        <input id="forgot-email" type="email" autoComplete="username" inputMode="email" value={email}
          onChange={(e) => setEmail(e.target.value)} required autoFocus />
      </div>
      <div aria-live="assertive">
        {error && <p className="form-status form-status--error"><CircleAlert size={18} aria-hidden="true" />{error}</p>}
      </div>
      <button className="btn btn--primary auth-submit" type="submit" disabled={busy}>
        {busy ? <Loader2 size={17} aria-hidden="true" /> : <Mail size={17} aria-hidden="true" />}
        {busy ? 'Sending…' : 'Send reset link'}
      </button>
    </form>
  );
}
