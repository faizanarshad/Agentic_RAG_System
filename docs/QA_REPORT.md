# QA and Risk Report

**Scope:** AIDocumentAgent website (Next.js), workspace and admin panel, and the FastAPI back end.
**Date:** 27 September 2026 · **Environment:** local development (macOS), production build for performance checks.

## Summary

| Area | Result |
|---|---|
| Backend API tests | **76 passed**, 0 failed (`backend/tests`, pytest) |
| End-to-end tests (desktop + mobile) | **54 passed**, 0 failed (`frontend/e2e`, Playwright; 2 signed-in tests need `E2E_EMAIL`/`E2E_PASSWORD`) |
| Accessibility (axe-core, WCAG 2.1 A/AA) | **0 serious or critical violations** on 9 pages × 2 devices |
| npm dependencies | **0 known vulnerabilities** (`npm audit`) |
| Python dependencies | **67 advisories in 20 packages**. None can be fixed on Python 3.9 (see R1) |
| Secrets in git history | **None found** (scan of all commits for API-key patterns) |
| Lighthouse (mobile, production build) | Accessibility, best practices, SEO **100**; performance 86–97; CLS 0 |

**Fixed in this pass:** 7 issues (details below).
**Open risks:** 2 high (Python runtime, production configuration), 4 medium, 8 low.

---

## How to run QA

```bash
# Back end: API tests (isolated temporary data, no OpenAI/Pinecone calls)
cd backend && venv/bin/python -m pytest

# Front end: lint, production build, end-to-end suite (site and API must be running)
cd frontend
npx playwright install chromium        # once
npm run qa                              # lint + build + Playwright
# or only the browser tests; PW_CHANNEL=chrome uses an installed Chrome
PW_CHANNEL=chrome npm run test:e2e
# optional signed-in journey
E2E_EMAIL=member@example.com E2E_PASSWORD=... npm run test:e2e

# Dependency audits
cd frontend && npm audit
cd backend && venv/bin/pip-audit -r requirements.txt
```

Continuous integration: `.github/workflows/qa.yml` runs the backend tests, lint, build and the end-to-end suite on every push and pull request, and uploads the Playwright report when a run fails.

---

## Automated coverage

### Backend (`backend/tests`)

| File | What it proves |
|---|---|
| `test_auth.py` | HttpOnly + SameSite session cookie. Identical errors for wrong password and unknown email (no account enumeration). Lockout after 5 failures. Disabled users blocked. Session tokens stored only as digests. Logout invalidates. Password rules. Password change signs out other sessions. Temporary-password flag cleared. |
| `test_two_factor.py` | RFC 4226 test vectors. Enrolment needs a valid code. Login requires the second factor, with no session before it. Codes cannot be replayed. Recovery codes work once and are stored hashed. Challenge locks after 5 wrong codes. Disabling needs password + code. Admin reset works. |
| `test_access_control.py` | 16 endpoints reject anonymous users (401). Members cannot reach 10 admin endpoints (403). Foreign-origin POST blocked (CSRF). CORS allows only the configured origin. Duplicate users rejected. Admins cannot delete themselves. The last admin cannot be demoted. Disabling signs the user out. |
| `test_content.py` | 7 XSS payloads stripped from posts. H1 reserved for titles. Drafts and scheduled posts are not public. Public API hides source and author IDs. Unique slugs. Invalid input rejected. Uploads re-encoded to WebP. Non-images rejected. Upload path traversal blocked. Unsafe announcement links rejected. |
| `test_contact_analytics.py` | Contact validation. Honeypot silently discarded. Rate limit (5/hour). Form can be paused. Page views ignore bots and private areas. No IP address stored. Own-site referrers dropped. CSV exports neutralise formula injection. |
| `test_security.py` | PBKDF2 (600k iterations) with unique salts. Strong temporary passwords. API security headers. `no-store` on auth responses. Errors do not leak internals. |

### End-to-end (`frontend/e2e`)

| File | What it proves |
|---|---|
| `site.spec.js` | Every public page:<br>• returns 200, with exactly one `<h1>`;<br>• title ≤ 70 characters, description 50–170, correct canonical URL, `og:image`, `lang`;<br>• valid JSON-LD, alt text on every image;<br>• no horizontal overflow, no console errors.<br>Also: no broken internal links; valid robots.txt and sitemap (every URL returns 200, no private URLs); proper 404 with `noindex`. |
| `security.spec.js` | Website security headers (CSP, frame, nosniff, referrer, permissions). App, admin and login are `noindex`. Protected pages redirect to sign-in with the return path. Unsafe redirect targets refused. Generic error on bad credentials. The API rejects anonymous requests. |
| `a11y.spec.js` | axe-core WCAG 2.1 A/AA on every public page and the sign-in page; serious or critical violations fail the run. |
| `auth.spec.js` | Signed-in journey: sign in, open each workspace and the account page, sign out, protected again (runs when test credentials are provided). |

---

## Issues fixed in this pass

| # | Issue | Severity | Fix |
|---|---|---|---|
| F1 | Website had no Content-Security-Policy, and no HSTS for HTTPS deployments | Medium | CSP limits scripts, styles and fonts to the site and data calls and images to the API. Framing blocked. `object-src 'none'`. HSTS sent automatically when the site URL is HTTPS. COOP added. |
| F2 | API responses had no security headers and advertised `server: uvicorn` | Low | `nosniff`, `X-Frame-Options: DENY`, `no-referrer`, CORP on all responses. `Cache-Control: no-store` on `/auth` and `/admin`. Server banner removed. |
| F3 | No two-factor authentication | Medium | TOTP 2FA with QR enrolment, replay protection, 10 hashed single-use recovery codes, per-challenge attempt limit, admin reset, and a 2FA column in Users. |
| F4 | No share image (`og:image`) on /solutions, /about, /contact, /blog: pages that set their own Open Graph data dropped the inherited image | Low (SEO) | Explicit default share image on those pages and on blog posts without a cover. |
| F5 | Home title 82 characters and Engineering description 171 characters (truncated in search results) | Low (SEO) | Shortened to 65 and 156 characters. |
| F6 | The "signed-in users" live count could include expired sessions or deleted users | Low | Counts only unexpired sessions of existing, active users. |
| F7 | `.gitignore` excluded every `test_*.py`, so a test suite would never have been committed | Low (process) | Exception for `backend/tests/` and `frontend/e2e/`; test artefacts ignored. |

---

## Open risks

### High

**R1. Back end runs on Python 3.9, which is end of life, and 67 dependency advisories are unfixable on it.**
`pip-audit` reports 67 advisories across 20 packages, including:
- Pillow (18), aiohttp (14), python-multipart (6), Starlette (5);
- LangChain / LangGraph / LangSmith;
- PyMuPDF, PyPDF2, requests, urllib3.

For every one, the newest release that installs on Python 3.9 is the vulnerable version; the fixes need Python 3.10+. Several are in file parsing (Pillow, PyMuPDF, PyPDF2), which processes untrusted uploads.

*Recommendation:*
1. Rebuild the venv on Python 3.12 (available on this machine).
2. Upgrade to LangChain/LangGraph 1.x and update the `langchain.schema` / text-splitter imports.
3. Replace the deprecated PyPDF2 with `pypdf`.
4. Re-run `pytest` and `pip-audit`.

**R2. Production configuration is security-critical.** Defaults are for local HTTP. Before going live:
- serve over HTTPS and set `COOKIE_SECURE=True`;
- set `FRONTEND_ORIGINS` and `NEXT_PUBLIC_SITE_URL` to the real origins;
- set the same `REVALIDATE_SECRET` on both servers;
- put the API behind a reverse proxy that forwards the real client IP.

Without that last step, sign-in throttling and analytics see the proxy's IP: one attacker could lock out everyone, or throttling could be ineffective.

*Recommendation:* a deployment checklist and an environment check at start-up that refuses to run with insecure settings in production mode.

### Medium

| # | Risk | Recommendation |
|---|---|---|
| R3 | **No data isolation between users.** Every signed-in member sees every uploaded drawing, legal document and generated document. | Add owner/team scoping to the workspace stores and APIs before onboarding separate clients or teams. |
| R4 | **Prompt injection through uploaded documents.** Text inside a document (for example hidden instructions in a contract) can influence model output, such as suppressing findings. Deterministic rule checks and cross-checks reduce but do not remove the risk. | Adversarial test documents in the evaluation suite; treat AI output as advisory (already stated in the UI); keep human approval. |
| R5 | **Third-party processing.** Document content is sent to OpenAI. Medical identifier removal is column-name based only. | Review provider terms and data-processing agreements; add formal de-identification before regulated data is used. |
| R6 | **Uploads are parsed without malware scanning or sandboxing** (PDF, DXF, images, DOCX). Combined with R1, parser vulnerabilities are a realistic attack path. | Upgrade parsers (R1); scan uploads (e.g. ClamAV); run parsing in an isolated worker with resource limits. |

### Low

| # | Risk | Recommendation |
|---|---|---|
| R7 | Contact and analytics rate limits are in memory: they reset on restart and aren't shared across instances. (Sign-in throttling is stored in the database.) | Move to Redis or the database when running more than one instance. |
| R8 | CSP allows `'unsafe-inline'` scripts, needed for statically rendered Next.js pages. XSS protection relies on server-side sanitisation (tested). | Nonce-based CSP if pages move to dynamic rendering. |
| R9 | TOTP secrets are stored unencrypted in SQLite (the data folder is git-ignored and not web-accessible). | Encrypt at rest with a key held outside the database (KMS or environment secret). |
| R10 | SQLite on a single server; no automated backups. | Scheduled backups of `backend/data/`; PostgreSQL for high availability or multiple instances. |
| R11 | The workspace Status panel makes a paid OpenAI "health" call every 30 seconds while open. | Cache the health result, or use a free models-list call. |
| R12 | 26 files under `backend/venv/` are still tracked in git. | `git rm -r --cached backend/venv` and keep it ignored. |
| R13 | No email delivery: temporary passwords are shared manually and there's no self-service reset. | Transactional email for invitations and password reset. |
| R14 | Model output varies between runs (drawing extraction, risk scores). | Rule checks and verification already mitigate; add regression runs against the synthetic answer keys to CI. |

---

## Manual checks performed

- **2FA journey in a real browser:**
  - enrol by QR code; 10 recovery codes issued; status shows On;
  - a wrong code is rejected;
  - sign-in succeeds with an authenticator code, and separately with a recovery code;
  - afterwards 9 codes remain, and the admin Users list shows 2FA as On.
- **On-demand revalidation (production build):** a published change shows on the first page load; a wrong secret is rejected (401).
- **Isolation:** after the test run, the real database still contained only the owner's account and no test data.
