"""API routes for the engineering drawing & documentation agent."""

import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from services.engineering_agent_service import EngineeringAgentService, normalize_template
from services.engineering_prompts import STANDARDS
from utils.logger import logger

router = APIRouter(prefix="/engineering", tags=["engineering"])

# Initialize the service lazily; sync routes run in a threadpool, so creation is locked
engineering_service = None
engineering_service_lock = threading.Lock()

def get_engineering_service() -> EngineeringAgentService:
    global engineering_service
    with engineering_service_lock:
        if engineering_service is None:
            engineering_service = EngineeringAgentService()
    return engineering_service


class ReviewRequest(BaseModel):
    """Request model for re-running a drawing review."""
    standard: str = "ISO"


class AskRequest(BaseModel):
    """Request model for questions about a drawing."""
    question: str
    history: List[Dict[str, str]] = []


class CompareRequest(BaseModel):
    """Request model for comparing two drawings or documents."""
    a_id: str
    b_id: str


class TemplateField(BaseModel):
    name: str
    type: str = "text"
    required: bool = True


class TemplateSection(BaseModel):
    title: str
    guidance: str = ""
    fields: List[TemplateField] = []


class TemplateModel(BaseModel):
    """A documentation template."""
    name: str
    description: str = ""
    category: str = "custom"
    sections: List[TemplateSection]


class GenerateRequest(BaseModel):
    """Request model for generating a document from a template."""
    template_id: str
    drawing_ids: List[str] = []
    comparison_ids: List[str] = []
    instructions: str = ""


class DocumentUpdate(BaseModel):
    """Edits to a generated document."""
    title: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None


def _validate_standard(standard: str) -> None:
    if standard not in STANDARDS:
        raise HTTPException(status_code=400, detail=f"standard must be one of {list(STANDARDS)}")


def _service_error(action: str, error: Exception) -> HTTPException:
    logger.error(f"Error during engineering {action}: {str(error)}")
    return HTTPException(status_code=500, detail=f"Failed to {action}: {str(error)}")


# ----- drawings -----

@router.get("/standards")
def list_standards() -> Dict[str, Any]:
    """Drawing standards the reviewer can check against."""
    return {key: {"label": value["label"], "checklist": value["checklist"]} for key, value in STANDARDS.items()}


@router.post("/drawings")
def upload_drawing(file: UploadFile = File(...), standard: str = Form("ISO")) -> Dict[str, Any]:
    """Upload a drawing (PDF, PNG/JPG/TIFF or DXF) and run the full review."""
    _validate_standard(standard)
    try:
        return get_engineering_service().review_upload(file.filename or "drawing", file.file.read(), standard)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("review drawing", e)


@router.get("/drawings")
def list_drawings() -> Dict[str, Any]:
    return {"drawings": get_engineering_service().store.list_drawings()}


@router.get("/drawings/{drawing_id}")
def get_drawing(drawing_id: str) -> Dict[str, Any]:
    drawing = get_engineering_service().get_drawing(drawing_id)
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return drawing


@router.get("/drawings/{drawing_id}/pages/{page_number}")
def get_page_image(drawing_id: str, page_number: int) -> FileResponse:
    """Rendered PNG of one sheet."""
    path = get_engineering_service().page_image_path(drawing_id, page_number)
    if path is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(path, media_type="image/png")


@router.post("/drawings/{drawing_id}/review")
def rerun_review(drawing_id: str, request: ReviewRequest) -> Dict[str, Any]:
    """Re-run the review, e.g. against a different standard."""
    _validate_standard(request.standard)
    try:
        return get_engineering_service().run_review(drawing_id, request.standard)
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found")
    except Exception as e:
        raise _service_error("review drawing", e)


@router.post("/drawings/{drawing_id}/ask")
def ask_drawing(drawing_id: str, request: AskRequest) -> Dict[str, Any]:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        return get_engineering_service().ask(drawing_id, request.question.strip(), request.history)
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found or not processed")
    except Exception as e:
        raise _service_error("answer question", e)


@router.delete("/drawings/{drawing_id}")
def delete_drawing(drawing_id: str) -> Dict[str, Any]:
    if not get_engineering_service().delete_drawing(drawing_id):
        raise HTTPException(status_code=404, detail="Drawing not found")
    return {"id": drawing_id, "message": "Drawing deleted"}


# ----- comparisons -----

@router.post("/compare")
def compare(request: CompareRequest) -> Dict[str, Any]:
    """Compare two reviewed drawings/documents (A = baseline, B = new)."""
    if request.a_id == request.b_id:
        raise HTTPException(status_code=400, detail="Choose two different drawings")
    try:
        return get_engineering_service().compare(request.a_id, request.b_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("compare", e)


@router.get("/comparisons")
def list_comparisons() -> Dict[str, Any]:
    return {"comparisons": get_engineering_service().store.list_comparisons()}


# ----- templates -----

@router.get("/templates")
def list_templates() -> Dict[str, Any]:
    return {"templates": get_engineering_service().store.list_templates()}


@router.post("/templates")
def create_template(template: TemplateModel) -> Dict[str, Any]:
    service = get_engineering_service()
    try:
        template_id = service.store.create_template(normalize_template(template.dict()))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return service.store.get_template(template_id)


@router.post("/templates/import")
def import_template(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Create a template from an existing DOCX, PDF, TXT or MD document."""
    service = get_engineering_service()
    try:
        template_id = service.import_template(file.filename or "template", file.file.read())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("import template", e)
    return service.store.get_template(template_id)


@router.put("/templates/{template_id}")
def update_template(template_id: str, template: TemplateModel) -> Dict[str, Any]:
    """Save edits to a template. Built-in templates are copied instead of modified."""
    service = get_engineering_service()
    existing = service.store.get_template(template_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        normalized = normalize_template(template.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if existing["builtin"]:
        if normalized["name"] == existing["name"]:
            normalized["name"] = f"{existing['name']} (custom)"
        template_id = service.store.create_template(normalized)
    else:
        service.store.update_template(template_id, normalized)
    return service.store.get_template(template_id)


@router.post("/templates/{template_id}/review")
def review_template(template_id: str) -> Dict[str, Any]:
    """AI critique of a template with a proposed improved version."""
    try:
        return get_engineering_service().review_template(template_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        raise _service_error("review template", e)


@router.delete("/templates/{template_id}")
def delete_template(template_id: str) -> Dict[str, Any]:
    service = get_engineering_service()
    template = service.store.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if template["builtin"]:
        raise HTTPException(status_code=400, detail="Built-in templates cannot be deleted")
    service.store.delete_template(template_id)
    return {"id": template_id, "message": "Template deleted"}


# ----- generated documents -----

@router.post("/documents/generate")
def generate_document(request: GenerateRequest) -> Dict[str, Any]:
    """Fill a template from reviewed drawings and comparisons."""
    try:
        return get_engineering_service().generate_document(
            request.template_id, request.drawing_ids, request.comparison_ids, request.instructions
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("generate document", e)


@router.get("/documents")
def list_documents() -> Dict[str, Any]:
    return {"documents": get_engineering_service().store.list_documents()}


@router.get("/documents/{document_id}")
def get_document(document_id: str) -> Dict[str, Any]:
    document = get_engineering_service().store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/documents/{document_id}")
def update_document(document_id: str, update: DocumentUpdate) -> Dict[str, Any]:
    service = get_engineering_service()
    if service.store.get_document(document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    fields = {k: v for k, v in update.dict().items() if v is not None}
    if fields:
        service.store.update_document(document_id, **fields)
    return service.store.get_document(document_id)


@router.delete("/documents/{document_id}")
def delete_document(document_id: str) -> Dict[str, Any]:
    service = get_engineering_service()
    if service.store.get_document(document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    service.store.delete_document(document_id)
    return {"id": document_id, "message": "Document deleted"}


@router.get("/documents/{document_id}/export")
def export_document(document_id: str, format: str = "docx") -> Response:
    """Download a generated document as DOCX or Markdown."""
    service = get_engineering_service()
    document = service.store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in document["title"]).strip() or "document"
    if format == "md":
        return PlainTextResponse(
            service.export_markdown(document_id),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
        )
    if format != "docx":
        raise HTTPException(status_code=400, detail="format must be 'docx' or 'md'")
    return Response(
        service.export_docx(document_id),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.docx"'},
    )
