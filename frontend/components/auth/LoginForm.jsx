'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CircleAlert, Eye, EyeOff, Loader2, LogIn } from 'lucide-react';
import { fetchBackend, jsonRequest } from '@/lib/api';

// Only allow redirects to paths inside this site (prevents open redirects)
function safeNext(value) {
  return value && value.startsWith('/') && !value.startsWith('//') && !value.startsWith('/login') ? value : '/workspace';
}

export default function LoginForm() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get('next'));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

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
      router.replace(data.user.must_change_password ? '/workspace/account?required=1' : next);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={submit} noValidate>
      <div className="field">
        <label htmlFor="login-email">Email</label>
        <input id="login-email" type="email" autoComplete="username" inputMode="email" value={email}
          onChange={(e) => setEmail(e.target.value)} required autoFocus />
      </div>
      <div className="field">
        <label htmlFor="login-password">Password</label>
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
