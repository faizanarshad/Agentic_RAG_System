# AIDocumentAgent

AI agents that read, check and document technical, legal and clinical files: engineering drawing review against ISO/ASME, legal document synthesis across whole collections, and clinical question answering over your own documents. FastAPI + LangGraph + Pinecone back end, Next.js (JavaScript) website and workspace.

## 🏗️ Architecture

```
Agentic_RAG_System/
├── backend/                 # FastAPI backend service
│   ├── api/                # API routes and endpoints
│   ├── core/               # Core configuration and settings
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions and logging
│   ├── sample_documents/   # Test PDF and CSV documents
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js (JavaScript) website + workspace
│   ├── app/                # App Router: public pages, /workspace app, SEO files
│   ├── components/         # Site and workspace components
│   ├── lib/                # Site config, content, structured data
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
│   └── TESTING_GUIDE.md    # Comprehensive testing guide
├── scripts/                # Utility scripts
│   └── create_test_pdfs.py # PDF generation script
└── README.md              # This file
```

## ✨ Features

- **Document Ingestion**: PDF and CSV files → chunks → embeddings
- **Medical CSV Support**: Automatic medical content detection and HIPAA-compliant PHI removal
- **RAG Pipeline**: OpenAI + Pinecone for intelligent document retrieval
- **FastAPI Endpoints**: RESTful APIs for chat and file management
- **Website**: Next.js marketing site with technical SEO (metadata, canonical URLs, sitemap, robots.txt, structured data, OG images) and the workspace app
- **File Management**: Upload, delete, and replace file vectors from UI
- **Medical Specialization**: Optimized for medical datasets and clinical documentation
- **Legal Data Synthesis**: Agentic analysis of contracts, court filings, case files and compliance records, with cross-document synthesis (see below)
- **Engineering Drawing Agent**: Reviews technical drawings (PDF, DXF, images) against ISO/ASME, compares revisions, and generates documentation from templates (see below)

## 🚀 Run

### Backend
```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Ensure `.env` in `backend/` is configured:
```
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_MODEL=gpt-3.5-turbo

PINECONE_API_KEY=pcsk-...
PINECONE_INDEX_NAME=rag-documents
# Region must match your Pinecone index host (e.g., ap-southeast-1)
PINECONE_ENVIRONMENT=ap-southeast-1
```

### Frontend (Next.js)
```
cd frontend
cp .env.example .env.local   # set NEXT_PUBLIC_SITE_URL before deploying
npm install
npm run dev
```

- Website: http://localhost:3001 (Home, Solutions, About, Contact)
- Workspace: http://localhost:3001/workspace (Engineering, Legal, Medical)
- API docs: http://localhost:8000/docs

See `frontend/README.md` for structure and the SEO checklist. Contact-form messages are stored in `backend/data/contact/messages.db`.

## 🧪 Test

- Use Upload tab to add PDFs or CSV files from `backend/sample_documents/`
- Ask questions in Chat
- Manage vectors with Replace/Delete buttons after upload completes
- Status tab shows Vector DB and LLM health

## ⚖️ Legal Data Synthesis

The **Legal** tab processes a corpus of legal documents (up to 100 per batch by default) and synthesizes insights across it.

**Per-document agent pipeline** (LangGraph, runs in background workers):

```
load (text / DOCX / OCR) → classify → extract → assess risk → summarize → index in Pinecone
                              └── non-legal documents skip extract and risk ──┘
```

- **OCR**: scanned PDF pages (and PNG/JPG/TIFF images) are rendered with PyMuPDF and transcribed by a vision-capable model.
- **Classification**: contract, court filing, case file, compliance record, other legal, non-legal (+ subtype and jurisdiction).
- **Extraction**: parties, key dates, type-specific fields (e.g. governing law, liability cap, case number, remediation deadline), key clauses, obligations and monetary amounts.
- **Risk analysis**: overall risk level and score, categorized risks with section references and recommendations, missing protections.
- **Indexing**: legal-aware chunking with a contextual header per chunk; vectors carry `domain=legal`, `doc_type`, `overall_risk` metadata so search can be filtered.

**Page views**

- **Overview** – batch upload (files or a whole folder) with live progress, corpus dashboard: document types, risk levels, risk categories, governing law, highest-risk documents, upcoming deadlines.
- **Documents** – filterable list; open any document for its summary, key terms, parties, risks, obligations, clauses, and to ask questions about it.
- **Synthesize** – cross-document research: a planning agent writes search queries → the most relevant documents are retrieved → an analysis agent reviews each document in parallel → a synthesis agent writes a report with themes, comparisons, risks, outliers and recommendations, citing documents (D1, D2 …).
- **Ask & Search** – cited Q&A and semantic passage search across the corpus. Questions about one short document read the whole document instead of retrieving chunks.

**Sample corpus.** Generate 100 fictional legal documents (85 TXT, 10 text PDFs, 5 image-only scanned PDFs) to try the page:

```
backend/venv/bin/python scripts/generate_legal_corpus.py --count 100
```

Files are written to `datasets/legal_corpus/`; upload that folder from the Legal tab. Every file is marked as synthetic.

**Configuration** (`backend/.env`, all optional):

| Variable | Default | Purpose |
|---|---|---|
| `LEGAL_MODEL` | `gpt-4.1-mini` | Model for OCR, classification, extraction, risk, Q&A and synthesis (needs JSON mode and image input) |
| `LEGAL_MAX_BATCH_DOCS` | `100` | Documents per upload batch; raise for larger corpora |
| `LEGAL_WORKERS` | `4` | Documents analyzed in parallel |
| `LEGAL_MAX_FILE_MB` | `25` | Maximum size per file |
| `LEGAL_OCR_MAX_PAGES` | `30` | OCR page limit per document (controls cost) |
| `LEGAL_FULL_TEXT_QA_CHARS` | `60000` | Single-document questions read the full text below this size |

Uploaded files and analyses are stored in `backend/data/legal/` (SQLite + originals), which is git-ignored. Unfinished documents resume automatically after a restart. Analysis costs roughly $0.01–0.02 per document with `gpt-4.1-mini`.

> AI-generated analysis is for research support only and is not legal advice.

## 📐 Engineering Drawing & Documentation Agent

The **Engineering** tab is an AI agent for checking engineering drawings and producing the documentation that accompanies them.

**Review workflow** (LangGraph):

```
load → extract → verify datums → rule checks → cross-view consistency → standards review → finalize
```

- **Load**: PDFs and images are rendered per sheet; DXF files are rendered with ezdxf and their exact CAD data is read (texts, title-block attributes, dimensions with measured values, units, layers). Vector PDFs contribute their positioned text layer.
- **Extract**: a vision model reads each sheet as a full image plus four zoomed tiles (small dimension text is unreadable at full-sheet resolution) and extracts the title block, views, dimensions, tolerances, GD&T, datums, notes, revision table and BOM.
- **Verify datums**: each claimed datum symbol is re-checked on a zoomed crop; unconfirmed claims are dropped (vision models sometimes "see" a datum the design would plausibly have).
- **Rule checks** (deterministic): title-block completeness, title-block revision vs revision table, unit mixing, tolerance coverage, GD&T references to undefined datums, conflicting dimensions, sheet numbering, and for DXF: dimension text overridden to hide a geometry mismatch, and CAD units vs title block.
- **Cross-view consistency**: a specialist agent compares every extent across views, datum references, dimension chains and callouts.
- **Standards review**: ISO (128, 129-1, 1101, 7200, 2768) or ASME (Y14.5, Y14.100, Y14.35) checklist; findings carry severity, location and a fix. The verdict can never be more lenient than the worst finding.

**Page views**

- **Review** – upload a drawing, see the sheet next to the verdict, findings, automated checks, checklist and extracted data; ask questions about the drawing.
- **Compare** – baseline vs new revision (or two related documents): every change with impact, plus a revision-control audit that checks each substantive change against the revision-table entries added in the new revision and lists unrecorded changes.
- **Templates** – built-in templates (Engineering Change Notice, First Article Inspection report, Drawing Review Record, Release & Transmittal, Component Technical Specification); edit sections and fields, get an AI review with a proposed improved version, or import a template from DOCX/PDF/TXT/MD.
- **Documents** – fill a template from reviewed drawings and comparisons (e.g. "Draft an ECN from this comparison"), edit, and export to Word or Markdown. Facts are copied from the sources; missing facts are left empty and flagged, drafted analysis is marked `[DRAFT]`, and any number not found in the sources is flagged for verification.

**Sample drawings** with planted errors (and an answer key):

```
backend/venv/bin/python scripts/generate_engineering_samples.py
```

Writes `datasets/engineering_samples/`: a bracket drawing (rev A) with five planted errors, its rev B with changes not recorded in the revision table, and a DXF flange with an overridden dimension and a units mismatch.

**Configuration** (`backend/.env`, optional): `ENGINEERING_MODEL` (default `gpt-4.1`, must support image input), `ENGINEERING_MAX_PAGES` (default 6 sheets per review), `ENGINEERING_MAX_FILE_MB` (default 50). A review costs roughly $0.05–0.15 and takes 30–60 seconds. Data is stored in `backend/data/engineering/` (git-ignored).

> AI-assisted checking supports, and does not replace, a qualified engineer's review and approval.

## 🔧 Troubleshooting

### Pinecone SSL / "Max retries exceeded ... SSLError(FileNotFoundError)"
- Create a fresh venv with modern Python (prefer 3.11+)
- Install HTTP stack with certs:
```
pip install --upgrade pip certifi requests "urllib3<2.2"
```
- We set `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE` to `certifi.where()` in `backend/core/config.py` automatically.
- Restart backend.

### Region mismatch
- If your Pinecone index host looks like `...aped...`, set `PINECONE_ENVIRONMENT=ap-southeast-1` (or the region where your index resides).
- `backend/services/vectordb_service.py` uses `PINECONE_ENVIRONMENT` for `ServerlessSpec`.

### Missing deps (e.g., `ModuleNotFoundError: langgraph`)
- Activate venv and run:
```
pip install -r requirements.txt
```

### Health shows Degraded
- Open http://localhost:8000/files/health and verify:
  - `vectordb: true` (Pinecone reachable and index OK)
  - `llm: true` (OpenAI reachable)
- Fix `.env` keys or region and restart.

## 📚 API Endpoints

- `POST /chat/` – query with RAG
- `GET /health` – basic API health
- `POST /files/add_file` – upload/process PDF or CSV files
- `POST /files/csv_info` – analyze CSV file before upload (medical content detection)
- `PUT /files/update_file/{file_id}` – replace vectors with a new PDF
- `DELETE /files/delete_file/{file_id}` – remove vectors by file
- `GET /files/health` – RAG service health (LLM + Vector DB)
- `POST /legal/batches` – upload legal documents (multipart `files`) and queue them for analysis
- `GET /legal/batches/latest`, `GET /legal/batches/{batch_id}` – batch progress
- `GET /legal/documents` – list documents (`doc_type`, `overall_risk`, `status`, `search`, `limit`, `offset`)
- `GET /legal/documents/{id}` – full analysis for one document
- `POST /legal/documents/{id}/retry`, `DELETE /legal/documents/{id}` – re-analyze or delete
- `GET /legal/corpus/stats` – corpus-wide statistics
- `POST /legal/ask` – cited Q&A (`question`, optional `file_id`)
- `POST /legal/search` – semantic passage search (`query`, optional `doc_type`, `overall_risk`, `top_k`)
- `POST /legal/synthesize` – cross-document synthesis report (`question`, optional `doc_type`, `overall_risk`, `max_documents`)
- `POST /contact` – store a website contact-form message (validated, honeypot, rate-limited)
- `POST /engineering/drawings` – upload and review a drawing (multipart `file`, `standard` = ISO|ASME)
- `GET /engineering/drawings`, `GET /engineering/drawings/{id}`, `GET /engineering/drawings/{id}/pages/{n}` – library, review detail, rendered sheet
- `POST /engineering/drawings/{id}/review`, `POST /engineering/drawings/{id}/ask`, `DELETE /engineering/drawings/{id}` – re-review, ask, delete
- `POST /engineering/compare` – compare two reviewed drawings (`a_id`, `b_id`)
- `GET/POST /engineering/templates`, `PUT/DELETE /engineering/templates/{id}`, `POST /engineering/templates/{id}/review`, `POST /engineering/templates/import` – templates
- `POST /engineering/documents/generate`, `GET/PUT/DELETE /engineering/documents/{id}`, `GET /engineering/documents/{id}/export?format=docx|md` – generated documents

## 📖 Docs

- See `docs/TESTING_GUIDE.md` for detailed testing scenarios and datasets.