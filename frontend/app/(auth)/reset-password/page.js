import Link from 'next/link';
import { Brand } from '@/components/site/Logo';
import ResetPasswordForm from '@/components/auth/ResetPasswordForm';

export const metadata = {
  title: 'Choose a password',
  description: 'Choose a new password for your AIDocumentAgent account.',
  robots: { index: false, follow: false },
  alternates: { canonical: '/reset-password' },
  // The link's token must never leak to other sites through the Referer header
  referrer: 'no-referrer',
};

export default function ResetPasswordPage() {
  return (
    <main id="main" className="auth-page section--ink blueprint">
      <div className="auth-card">
        <Link href="/" className="brand auth-brand" aria-label="AIDocumentAgent home">
          <Brand />
        </Link>
        <ResetPasswordForm />
        <p className="auth-foot">
          <Link className="text-link" href="/login">Back to sign in</Link>
        </p>
      </div>
    </main>
  );
}
