import { Inter, JetBrains_Mono } from 'next/font/google';
import { site } from '@/lib/site';
import './globals.css';

// Self-hosted at build time by next/font: no external font requests, no layout shift
const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const mono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono-face',
  display: 'swap',
  weight: ['400', '500', '600'],
});

export const metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: `${site.name} | AI agents for technical, legal and clinical documents`,
    template: `%s | ${site.name}`,
  },
  description: site.description,
  applicationName: site.name,
  keywords: [
    'AI document agent',
    'engineering drawing review',
    'drawing checker',
    'GD&T review',
    'revision control',
    'technical documentation',
    'legal document analysis',
    'contract analysis AI',
    'document synthesis',
    'clinical document Q&A',
    'RAG',
  ],
  authors: [{ name: site.name, url: site.url }],
  creator: site.name,
  publisher: site.name,
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: site.name,
    locale: site.locale,
    url: '/',
    title: site.name,
    description: site.description,
  },
  twitter: {
    card: 'summary_large_image',
    title: site.name,
    description: site.description,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, 'max-image-preview': 'large', 'max-snippet': -1 },
  },
  formatDetection: { telephone: false, email: false, address: false },
};

export const viewport = {
  themeColor: site.themeColor,
  colorScheme: 'light',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`} data-scroll-behavior="smooth">
      <body>{children}</body>
    </html>
  );
}
