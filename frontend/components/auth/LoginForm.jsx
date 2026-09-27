'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { CircleAlert, CircleCheck, Eye, EyeOff, KeyRound, Loader2, LogIn, ShieldCheck } from 'lucide-react';
import { fetchBackend, jsonRequest } from '@/lib/api';

// Only allow redirects to paths inside this site (prevents open redirects)
function safeNext(value) {
  return value && value.startsWith('/') && !value.startsWith('//') && !value.startsWith('/login') ? value : '/workspace';
}

export default function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get('next'));
  const justReset = params.get('reset') === '1';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [mfaToken, setMfaToken] = useState(null);
  const [code, setCode] = useState('');
  const [useRecovery, setUseRecovery] = useState(false);

  const finish = (user) => router.replace(user.must_change_password ? '/workspace/account?required=1' : next);

  // Already signed in: go straight to the workspace
  useEffect(() => {
    fetchBackend('/auth/me').then(() => router.replace(next)).catch(() => {});
  }, [next, router]);

  const submit = async (event) => {
    event.preventDefault();
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const data = await fetchBackend('/auth/login', jsonRequest('POST', { email: email.trim(), password }));
      if (data.mfa_required) {
        setMfaToken(data.mfa_token);
        setBusy(false);
        return;
      }
      finish(data.user);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  };

  const submitCode = async (event) => {
    event.preventDefault();
    if (!code.trim()) return setError(useRecovery ? 'Enter a recovery code.' : 'Enter the 6-digit code.');
    setBusy(true);
    setError('');
    try {
      const data = await fetchBackend('/auth/login/mfa', jsonRequest('POST', { mfa_token: mfaToken, code: code.trim() }));
      finish(data.user);
    } catch (e) {
      setError(e.message);
      setBusy(false);
      if (/expired|sign in again/i.test(e.message)) {
        setMfaToken(null);
        setCode('');
      }
    }
  };

  if (mfaToken) {
    return (
      <form className="auth-form" onSubmit={submitCode} noValidate>
        <p className="mfa-intro">
          <ShieldCheck size={18} aria-hidden="true" />
          {useRecovery ? 'Enter one of your recovery codes.' : 'Enter the 6-digit code from your authenticator app.'}
        </p>
        <div className="field">
          <label htmlFor="login-code">{useRecovery ? 'Recovery code' : 'Authentication code'}</label>
          <input id="login-code" value={code} onChange={(e) => setCode(e.target.value)} autoFocus required
            autoComplete="one-time-code" inputMode={useRecovery ? 'text' : 'numeric'}
            pattern={useRecovery ? undefined : '[0-9 ]*'} maxLength={useRecovery ? 12 : 7}
            placeholder={useRecovery ? 'xxxx-xxxx' : '123 456'} className="mfa-code" />
        </div>
        <div aria-live="assertive">
          {error && <p className="form-status form-status--error"><CircleAlert size={18} aria-hidden="true" />{error}</p>}
        </div>
        <button className="btn btn--primary auth-submit" type="submit" disabled={busy}>
          {busy ? <Loader2 size={17} aria-hidden="true" /> : <KeyRound size={17} aria-hidden="true" />}
          {busy ? 'Verifying…' : 'Verify and sign in'}
        </button>
        <button type="button" className="text-link auth-alt" onClick={() => { setUseRecovery(!useRecovery); setCode(''); setError(''); }}>
          {useRecovery ? 'Use my authenticator app instead' : 'Lost your phone? Use a recovery code'}
        </button>
      </form>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit} noValidate>
      {justReset && (
        <p className="form-status form-status--success" role="status">
          <CircleCheck size={18} aria-hidden="true" />Password saved. Sign in with your new password.
        </p>
      )}
      <div className="field">
        <label htmlFor="login-email">Email</label>
        <input id="login-email" type="email" autoComplete="username" inputMode="email" value={email}
          onChange={(e) => setEmail(e.target.value)} required autoFocus />
      </div>
      <div className="field">
        <div className="field-label-row">
          <label htmlFor="login-password">Password</label>
          <Link className="text-link small-link" href="/forgot-password">Forgot password?</Link>
        </div>
        <div className="password-field">
          <input id="login-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password"
            value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button type="button" onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}>
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
      </div>
      <div aria-live="assertive">
        {error && <p className="form-status form-status--error"><CircleAlert size={18} aria-hidden="true" />{error}</p>}
      </div>
      <button className="btn btn--primary auth-submit" type="submit" disabled={busy}>
        {busy ? <Loader2 size={17} aria-hidden="true" /> : <LogIn size={17} aria-hidden="true" />}
        {busy ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  );
}
