import Link from 'next/link';
import { Brand } from '@/components/site/Logo';
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm';

export const metadata = {
  title: 'Reset your password',
  description: 'Request a password reset link for your AIDocumentAgent account.',
  robots: { index: false, follow: false },
  alternates: { canonical: '/forgot-password' },
};

export default function ForgotPasswordPage() {
  return (
    <main id="main" className="auth-page section--ink blueprint">
      <div className="auth-card">
        <Link href="/" className="brand auth-brand" aria-label="AIDocumentAgent home">
          <Brand />
        </Link>
        <h1 className="h3">Reset your password</h1>
        <p className="muted">Enter your account email and we will send you a link to choose a new password.</p>
        <ForgotPasswordForm />
        <p className="auth-foot">
          Remembered it? <Link className="text-link" href="/login">Back to sign in</Link>
        </p>
      </div>
    </main>
  );
}
