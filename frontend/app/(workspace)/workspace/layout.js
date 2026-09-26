import WorkspaceShell from '@/components/workspace/WorkspaceShell';
import '../../styles/workspace.css';

// The application itself is not a landing page: keep it out of search results
export const metadata = {
  title: { default: 'Workspace', template: '%s Workspace | AIDocumentAgent' },
  robots: { index: false, follow: false },
};

export default function WorkspaceLayout({ children }) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
