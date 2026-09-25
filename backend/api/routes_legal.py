"""API routes for legal document intelligence and corpus synthesis."""

import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from core.config import settings
from services.legal_agent_service import LegalAgentService
from services.legal_prompts import DOC_TYPES
from utils.logger import logger

router = APIRouter(prefix="/legal", tags=["legal"])

# Initialize legal service lazily. Sync routes run in a threadpool, so creation is locked:
# a second instance would start its own workers and re-process every unfinished document.
legal_service = None
legal_service_lock = threading.Lock()

def get_legal_service() -> LegalAgentService:
    global legal_service
    with legal_service_lock:
        if legal_service is None:
            legal_service = LegalAgentService()
    return legal_service


RISK_LEVELS = ("low", "medium", "high")


class AskRequest(BaseModel):
    """Request model for legal question answering."""
    question: str
    file_id: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for semantic search over legal passages."""
    query: str
    doc_type: Optional[str] = None
    overall_risk: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=50)


class SynthesizeRequest(BaseModel):
    """Request model for cross-document synthesis."""
    question: str
    doc_type: Optional[str] = None
    overall_risk: Optional[str] = None
    max_documents: int = Field(default=15, ge=1, le=40)


def _validate_filters(doc_type: Optional[str], overall_risk: Optional[str]) -> None:
    if doc_type and doc_type not in DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"doc_type must be one of {DOC_TYPES}")
    if overall_risk and overall_risk not in RISK_LEVELS:
        raise HTTPException(status_code=400, detail=f"overall_risk must be one of {list(RISK_LEVELS)}")


def _service_error(action: str, error: Exception) -> HTTPException:
    logger.error(f"Error during legal {action}: {str(error)}")
    return HTTPException(status_code=500, detail=f"Failed to {action}: {str(error)}")


@router.post("/batches")
def create_batch(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Upload up to LEGAL_MAX_BATCH_DOCS documents and queue them for background analysis."""
    if len(files) > settings.LEGAL_MAX_BATCH_DOCS:
        raise HTTPException(
            status_code=400,
            detail=f"At most {settings.LEGAL_MAX_BATCH_DOCS} documents per batch (received {len(files)})",
        )
    try:
        payload = [(file.filename or "document", file.file.read()) for file in files]
        result = get_legal_service().ingest_files(payload)
    except Exception as e:
        raise _service_error("queue documents", e)
    if result["batch"] is None:
        raise HTTPException(status_code=400, detail={"message": "No valid documents", "rejected": result["rejected"]})
    return result


@router.get("/batches/latest")
def latest_batch() -> Dict[str, Any]:
    """Return progress for the most recent batch, if any."""
    service = get_legal_service()
    batch_id = service.store.latest_batch_id()
    return {"batch": service.store.get_batch(batch_id) if batch_id else None}


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str) -> Dict[str, Any]:
    """Return progress for a batch."""
    batch = get_legal_service().store.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/documents")
def list_documents(
    doc_type: Optional[str] = None,
    overall_risk: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List analyzed documents with filters and pagination."""
    _validate_filters(doc_type, overall_risk)
    return get_legal_service().store.list_documents(doc_type, overall_risk, status, search, limit, offset)


@router.get("/documents/{doc_id}")
def get_document(doc_id: str) -> Dict[str, Any]:
    """Return a document's full analysis: classification, extraction, risks and summary."""
    document = get_legal_service().store.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/documents/{doc_id}/retry")
def retry_document(doc_id: str) -> Dict[str, Any]:
    """Re-run the analysis pipeline for a document (e.g. after a failure)."""
    if not get_legal_service().retry_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"file_id": doc_id, "message": "Document queued for re-analysis"}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> Dict[str, Any]:
    """Delete a document, its analysis and its vectors."""
    try:
        deleted = get_legal_service().delete_document(doc_id)
    except Exception as e:
        raise _service_error("delete document", e)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"file_id": doc_id, "message": "Document deleted"}


@router.get("/corpus/stats")
def corpus_stats() -> Dict[str, Any]:
    """Aggregate statistics across every analyzed document."""
    try:
        return get_legal_service().corpus_stats()
    except Exception as e:
        raise _service_error("compute corpus statistics", e)


@router.post("/ask")
def ask(request: AskRequest) -> Dict[str, Any]:
    """Answer a question about one document (file_id) or the whole corpus, with citations."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        return get_legal_service().ask(request.question.strip(), request.file_id)
    except Exception as e:
        raise _service_error("answer question", e)


@router.post("/search")
def search(request: SearchRequest) -> Dict[str, Any]:
    """Semantic search over passages of analyzed legal documents."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    _validate_filters(request.doc_type, request.overall_risk)
    try:
        results = get_legal_service().search(
            request.query.strip(), request.doc_type, request.overall_risk, request.top_k
        )
    except Exception as e:
        raise _service_error("search", e)
    return {"query": request.query, "results": results}


@router.post("/synthesize")
def synthesize(request: SynthesizeRequest) -> Dict[str, Any]:
    """Run the plan -> retrieve -> map -> reduce agent to synthesize insights across documents."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    _validate_filters(request.doc_type, request.overall_risk)
    try:
        return get_legal_service().synthesize(
            request.question.strip(), request.doc_type, request.overall_risk, request.max_documents
        )
    except Exception as e:
        raise _service_error("synthesize", e)
