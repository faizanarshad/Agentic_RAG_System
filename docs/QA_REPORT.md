# QA and Risk Report

**Scope:** AIDocumentAgent website (Next.js), workspace and admin panel, and the FastAPI back end.
**Date:** 27 September 2026 · **Environment:** local development (macOS), production build for performance checks.

## Summary

| Area | Result |
|---|---|
| Backend API tests | **113 passed**, 0 failed (`backend/tests`, pytest, Python 3.12) |
| End-to-end tests (desktop + mobile) | **60 passed**, 0 failed (`frontend/e2e`, Playwright; 2 signed-in tests need `E2E_EMAIL`/`E2E_PASSWORD`) |
| Accessibility (axe-core, WCAG 2.1 A/AA) | **0 serious or critical violations** on 11 pages × 2 devices |
| npm dependencies | **0 known vulnerabilities** (`npm audit`) |
| Python dependencies | **0 known vulnerabilities** (`pip-audit`; was 67 on Python 3.9) |
| Agent accuracy (`scripts/evaluate_agents.py`) | Legal: classification **96%**, governing law **99%**, risk direction **94%** (100 documents). Engineering: **11/11** seeded issues found |
| Secrets in git history | **None found** (scan of all commits for API-key patterns) |
| Lighthouse (mobile, production build) | Accessibility, best practices, SEO **100**; performance 86–97; CLS 0 |

**Risk register:** all 14 risks addressed. 12 are resolved. R4 (prompt injection) and R5 (third-party processing) are
reduced as far as the technology allows, and their remaining exposure is described under *Residual risks*.

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

# Agent accuracy against the synthetic answer keys (reads stored results; --run re-analyses, uses the API)
backend/venv/bin/python scripts/evaluate_agents.py --min-score 0.8

# Backups
cd backend && venv/bin/python manage.py backup        # also automatic every 24 h
venv/bin/python manage.py restore <archive>           # stop the API first
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
| `test_isolation.py` | Members cannot read, retry, delete, ask about or export other members' legal documents, batches, drawings, page images, comparisons or generated documents (404, not 403, so IDs are not confirmed). Lists show only their own records; admins see everything. Pinecone filters carry the owner. Shared templates can only be changed or deleted by their creator. Medical files can only be deleted by their uploader. |
| `test_account_links.py` | Invitations and resets: single use, expiry, forged tokens rejected, stored only as digests. A weak password does not burn the link. A reset signs out every session and the old password stops working. Forgot-password responses are identical for real and unknown emails, and are rate limited. |
| `test_hardening.py` | AES-GCM encryption of 2FA secrets (random nonce, legacy values readable). Uploads whose content does not match the extension are rejected. Rate limits live in the database. X-Forwarded-For is ignored unless it comes from a trusted proxy. Production settings validation. Prompt-injection detection (and no false positives on ordinary legal wording). Document fences cannot be closed from inside. PHI redaction keeps clinical values. Backup permissions, rotation, key exclusion and refusal of corrupt archives. |
| `test_security.py` | PBKDF2 (600k iterations) with unique salts. Strong temporary passwords. API security headers. `no-store` on auth responses. Errors do not leak internals. |

### End-to-end (`frontend/e2e`)

| File | What it proves |
|---|---|
| `site.spec.js` | Every public page:<br>• returns 200, with exactly one `<h1>`;<br>• title ≤ 70 characters, description 50–170, correct canonical URL, `og:image`, `lang`;<br>• valid JSON-LD, alt text on every image;<br>• no horizontal overflow, no console errors.<br>Also: no broken internal links; valid robots.txt and sitemap (every URL returns 200, no private URLs); proper 404 with `noindex`. |
| `security.spec.js` | Website security headers (CSP, frame, nosniff, referrer, permissions). Sign-in, password, workspace and admin pages get a fresh nonce CSP on every response with no `unsafe-inline` scripts, and still work. App, admin and login are `noindex`. Protected pages redirect to sign-in with the return path. Unsafe redirect targets refused. Generic error on bad credentials. Forgot-password does not reveal accounts; bad reset links are handled and the token is removed from the address bar. The API rejects anonymous requests. |
| `a11y.spec.js` | axe-core WCAG 2.1 A/AA on every public page, sign-in, forgot-password and reset-password; serious or critical violations fail the run. |
| `auth.spec.js` | Signed-in journey: sign in, open each workspace and the account page, sign out, protected again (runs when test credentials are provided). |

---

## Issues fixed in the first QA pass

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

## Risk register: resolution

| # | Risk (as found) | Status | What was done |
|---|---|---|---|
| R1 | Python 3.9 (end of life); 67 dependency advisories unfixable on it | **Resolved** | Rebuilt on Python 3.12. Upgraded to LangChain/LangGraph 1.x, FastAPI 0.14x, Pillow 12, PyMuPDF 1.28, OpenAI SDK 3.x. Replaced PyPDF2 with `pypdf`. `pip-audit`: 0. |
| R2 | Insecure production configuration possible; client IP spoofable behind a proxy | **Resolved** | With `ENVIRONMENT=production` the API refuses to start unless: cookies are secure; origins and `PUBLIC_SITE_URL` are HTTPS; the revalidation secret is 32+ characters; trusted proxies and the encryption key are set; debug is off. `X-Forwarded-For` is honoured only from `TRUSTED_PROXIES`. |
| R3 | No data isolation between users | **Resolved** | Every legal document, batch, drawing, comparison, generated document and medical file records its owner. Members see and act only on their own records, and anyone else's returns 404. Vector searches are filtered by owner. Admins see everything. Existing data was assigned to the first administrator. Templates are shared, but only their creator or an admin can change or delete them. |
| R4 | Prompt injection through uploaded documents | **Mitigated (residual)** | Every agent's system prompt marks document text as untrusted data. Document text is fenced, and the fences cannot be forged from inside. A detector flags text aimed at an AI, such as "ignore previous instructions", hidden characters or "rate this as low risk". Legal documents get a high-severity risk item and can never be rated low-risk; drawings get a major finding. The agents have no tools with side effects. See *Residual risks*. |
| R5 | Document content sent to OpenAI; identifier removal was column-name only | **Mitigated (residual)** | `OPENAI_BASE_URL` points every agent at Azure OpenAI (your tenant) or a self-hosted model, so documents need not leave your infrastructure. Medical uploads have emails, phone numbers, SSNs, MRNs, card numbers, IPs, ZIP+4 codes and full dates redacted at value level before embedding or sending. Clinical values are kept. |
| R6 | Uploads parsed without validation or scanning | **Resolved** | Magic-byte check that the content matches the extension. DOCX zip-bomb limit. Decompression-bomb pixel limit. PDF page limit. ClamAV scanning when installed (`VIRUS_SCAN=required` fails closed). Size limits on every upload path. |
| R7 | Contact and analytics rate limits in memory | **Resolved** | Stored in the database: they survive restarts and are shared by every instance. |
| R8 | CSP allowed `'unsafe-inline'` scripts | **Resolved** where it matters | Sign-in, password, workspace and admin pages use a per-request nonce with `'strict-dynamic'`, so injected scripts cannot run. The public marketing pages keep a static policy so they stay CDN-cacheable; they display only sanitised, admin-authored content and handle no accounts or documents. |
| R9 | TOTP secrets unencrypted | **Resolved** | AES-256-GCM at rest. The key comes from `DATA_ENCRYPTION_KEY` (or an owner-only key file); existing secrets were migrated at start-up. |
| R10 | No backups | **Resolved** | Automatic backups every 24 h, with 14 kept. Databases are copied with SQLite's online backup API; uploads are included. Archives have owner-only permissions and exclude the key. `manage.py backup / list-backups / restore`: restores are integrity-checked and keep the previous data for rollback. A full restore was tested. |
| R11 | Paid OpenAI health call every 30 s | **Resolved** | Health uses the free model-lookup endpoint, cached for 60 s. |
| R12 | `backend/venv/` tracked in git | **Resolved** | Removed from the index and ignored. |
| R13 | No email; temporary passwords shared manually; no self-service reset | **Resolved** | Invitations and "Forgot password?" use single-use links. Links expire (72 h for invitations, 60 min for resets), are stored as digests, travel in the URL fragment and are emailed over TLS. Admins never see or set passwords. Without SMTP configured, the admin sees the link to pass on. |
| R14 | Model output varies; no regression measurement | **Resolved** | `scripts/evaluate_agents.py` scores the agents against the synthetic answer keys and exits non-zero below a threshold. Run it before a model or prompt change. |

### Residual risks

These cannot be fully eliminated by any application today; they are reduced and documented:

- **Prompt injection (R4).** No known technique makes a language model completely immune to instructions hidden in
  its input. Defences are layered:
  - detection and flagging;
  - untrusted-data prompts;
  - deterministic rule checks that run independently of the model;
  - no agent tools with side effects.

  A successful injection can therefore at worst distort the analysis of the document that contains it, and that
  document is usually flagged. Keep a person accountable for decisions (the UI states that AI output is advisory).
- **Third-party processing (R5).** With the default OpenAI endpoint, document text is processed by OpenAI under
  their API terms (API data is not used for training by default). For regulated data:
  - point `OPENAI_BASE_URL` at Azure OpenAI or a self-hosted model;
  - sign the relevant data-processing agreement or BAA.

  Pattern redaction cannot reliably find names in free text, so use de-identified datasets where possible.
- **Model accuracy (R14).** Scores are high but not 100%. For example, settlement agreements are sometimes filed as
  contracts. Keep using `evaluate_agents.py` to measure.

### Production checklist

1. Serve both sites over HTTPS.
2. Set `ENVIRONMENT=production`. The API then lists anything unsafe and refuses to start until it is fixed.
3. Set `DATA_ENCRYPTION_KEY` from a secret manager, and store it separately from the backups.
4. Configure SMTP (`SMTP_HOST`, `SMTP_FROM`, credentials) so that invitations and resets are emailed.
5. Copy `backend/backups/` off the server regularly (for example to object storage).
6. Optionally set `VIRUS_SCAN=required` with ClamAV installed, and `OPENAI_BASE_URL` for in-tenant processing.

---

## Manual checks performed

- **2FA journey in a real browser:**
  - enrol by QR code; 10 recovery codes issued; status shows On;
  - a wrong code is rejected;
  - sign-in succeeds with an authenticator code, and separately with a recovery code;
  - afterwards 9 codes remain, and the admin Users list shows 2FA as On.
- **On-demand revalidation (production build):** a published change shows on the first page load; a wrong secret is rejected (401).
- **Backup and restore:** a backup was restored into a scratch environment. A deleted user came back, and their encrypted 2FA secret still decrypted with the carried-over key.
- **Nonce CSP:** every script tag on `/login` carries that response's nonce; public pages keep the static policy.
- **Isolation:** after the test run, the real database still contained only the owner's account and no test data.
