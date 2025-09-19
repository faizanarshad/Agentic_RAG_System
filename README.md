# 🤖 Agentic RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system built with FastAPI, React, and modern AI technologies. This system allows you to upload documents, generate embeddings, and ask questions about your content using advanced language models.

## 🏗️ Architecture

```
Agentic_RAG_System/
├── backend/                 # FastAPI backend service
│   ├── api/                # API routes and endpoints
│   ├── core/               # Core configuration and settings
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions and logging
│   ├── sample_documents/   # Test PDF documents
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
│   └── TESTING_GUIDE.md    # Comprehensive testing guide
├── scripts/                # Utility scripts
│   └── create_test_pdfs.py # PDF generation script
└── README.md              # This file
```

## ✨ Features

- Document ingestion (PDF → chunks → embeddings)
- RAG pipeline with OpenAI + Pinecone
- FastAPI endpoints for chat and files
- React UI with Upload/Chat/Status tabs
- Delete and Replace (Update) file vectors from UI

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

### Frontend
```
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## 🧪 Test

- Use Upload tab to add PDFs from `backend/sample_documents/`
- Ask questions in Chat
- Manage vectors with Replace/Delete buttons after upload completes
- Status tab shows Vector DB and LLM health

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
- `POST /files/add_file` – upload/process PDF
- `PUT /files/update_file/{file_id}` – replace vectors with a new PDF
- `DELETE /files/delete_file/{file_id}` – remove vectors by file
- `GET /files/health` – RAG service health (LLM + Vector DB)

## 📖 Docs

- See `docs/TESTING_GUIDE.md` for detailed testing scenarios and datasets.