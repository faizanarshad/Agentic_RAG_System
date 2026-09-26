import AdminFrame from '@/components/admin/AdminFrame';

export const metadata = {
  title: { default: 'Admin', template: '%s · Admin | AIDocumentAgent' },
};

export default function AdminLayout({ children }) {
  return <AdminFrame>{children}</AdminFrame>;
}
