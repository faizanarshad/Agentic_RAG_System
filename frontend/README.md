# AIDocumentAgent website and workspace (Next.js, JavaScript)

Public marketing site (Home, Solutions, About, Contact) plus the AIDocumentAgent workspace
(Engineering, Legal, Medical). Built with the Next.js App Router in JavaScript.

## Run

```bash
cp .env.example .env.local   # then edit the values
npm install
npm run dev                  # http://localhost:3001
```

Production:

```bash
npm run build
npm start                    # http://localhost:3001
```

The workspaces and contact form need the FastAPI back end (`../backend`, port 8000).

## Structure

- `app/(site)/` – statically rendered public pages with shared header and footer
- `app/(workspace)/workspace/` – the application (client-rendered, `noindex`, own stylesheet)
- `app/sitemap.js`, `app/robots.js`, `app/manifest.js`, `app/opengraph-image.js`, `app/icon.svg`, `app/apple-icon.js` – SEO and icons
- `components/site/` – header, footer, breadcrumbs, JSON-LD, product frames, contact form
- `components/workspace/` – Engineering, Legal, Medical and Status workspaces
- `lib/site.js` – brand, URLs and contact details; `lib/content.js` – page copy; `lib/structured-data.js` – schema.org helpers
- `assets/` – product screenshots (statically imported, served as AVIF/WebP by `next/image`)

## SEO checklist

- Set `NEXT_PUBLIC_SITE_URL` to the production origin before building; canonical URLs, the sitemap and structured data use it.
- Each public page exports its own title, description, canonical URL and Open Graph data.
- Structured data: Organization, WebSite, SoftwareApplication and FAQPage (home), Service (solution pages), AboutPage, ContactPage, CollectionPage and BreadcrumbList.
- `/workspace` is `noindex, nofollow` and disallowed in `robots.txt`.
