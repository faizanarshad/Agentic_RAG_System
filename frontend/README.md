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
- `app/(auth)/login/` – sign-in page
- `app/(workspace)/workspace/` – the application (sign-in required, client-rendered, `noindex`, own stylesheet)
- `app/(workspace)/admin/` – admin panel (admin role): overview, traffic, usage & cost, users, messages, activity, system
- `app/sitemap.js`, `app/robots.js`, `app/manifest.js`, `app/opengraph-image.js`, `app/icon.svg`, `app/apple-icon.js` – SEO and icons
- `components/site/` – header, footer, breadcrumbs, JSON-LD, product frames, contact form
- `components/workspace/` – Engineering, Legal, Medical and Status workspaces
- `components/auth/` – `AuthProvider` (session check, redirects) and the login form
- `components/admin/` – admin pages and dependency-free SVG charts (hover tooltip, keyboard navigation, table view)
- `lib/site.js` – brand, URLs and contact details; `lib/content.js` – page copy; `lib/structured-data.js` – schema.org helpers
- `assets/` – product screenshots (statically imported, served as AVIF/WebP by `next/image`)

## SEO checklist

- Set `NEXT_PUBLIC_SITE_URL` to the production origin before building; canonical URLs, the sitemap and structured data use it.
- Each public page exports its own title, description, canonical URL and Open Graph data.
- Structured data: Organization, WebSite, SoftwareApplication and FAQPage (home), Service (solution pages), AboutPage, ContactPage, CollectionPage and BreadcrumbList.
- `/workspace`, `/admin` and `/login` are `noindex, nofollow`; `/workspace` is disallowed in `robots.txt`.

## Authentication

The API sets an HttpOnly session cookie; every request from `lib/api.js` uses `credentials: 'include'`. A 401 from any workspace call fires an event that sends the user to `/login?next=…`. Authorisation is enforced by the API; the client guard only decides what to render.

## Analytics

`components/site/PageviewTracker.jsx` sends a cookie-less `text/plain` beacon to `/analytics/pageview` on each public page view (skipped when Do Not Track is on).
