import AuthProvider from '@/components/auth/AuthProvider';
import WorkspaceShell from '@/components/workspace/WorkspaceShell';
import '../styles/workspace.css';

// The application (workspace and admin) requires sign-in and stays out of search results
export const metadata = {
  robots: { index: false, follow: false },
};

export default function AppLayout({ children }) {
  return (
    <AuthProvider>
      <WorkspaceShell>{children}</WorkspaceShell>
    </AuthProvider>
  );
}
