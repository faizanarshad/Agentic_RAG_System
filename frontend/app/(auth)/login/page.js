import { Suspense } from 'react';
import Link from 'next/link';
import { Brand } from '@/components/site/Logo';
import LoginForm from '@/components/auth/LoginForm';

export const metadata = {
  title: 'Sign in',
  description: 'Sign in to the AIDocumentAgent workspace.',
  robots: { index: false, follow: false },
  alternates: { canonical: '/login' },
};

export default function LoginPage() {
  return (
    <main id="main" className="auth-page section--ink blueprint">
      <div className="auth-card">
        <Link href="/" className="brand auth-brand" aria-label="AIDocumentAgent home">
          <Brand />
        </Link>
        <h1 className="h3">Sign in to your workspace</h1>
        <p className="muted">Use your account email and password.</p>
        <Suspense fallback={<div className="auth-form-placeholder" />}>
          <LoginForm />
        </Suspense>
        <p className="auth-foot">
          No account yet? <Link className="text-link" href="/contact">Request access</Link>
        </p>
      </div>
    </main>
  );
}
