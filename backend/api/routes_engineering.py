"""API routes for the engineering drawing & documentation agent."""

import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from api.deps import can_access, current_owner_id, owner_scope
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


def _owned(request: Request, kind: str, record_id: str) -> Dict[str, Any]:
    """Fetch a drawing, comparison or document the caller may see; anyone else's is reported as not found."""
    store = get_engineering_service().store
    getter = {"drawing": store.get_drawing, "comparison": store.get_comparison, "document": store.get_document}[kind]
    record = getter(record_id)
    if not can_access(record, owner_scope(request)):
        raise HTTPException(status_code=404, detail=f"{kind.capitalize()} not found")
    return record


def _can_edit_template(request: Request, template: Dict[str, Any]) -> bool:
    """Templates are shared for use; only their creator or an administrator may change or delete them."""
    scope = owner_scope(request)
    return not template["builtin"] and (scope is None or template.get("owner_id") == scope)


# ----- drawings -----

@router.get("/standards")
def list_standards() -> Dict[str, Any]:
    """Drawing standards the reviewer can check against."""
    return {key: {"label": value["label"], "checklist": value["checklist"]} for key, value in STANDARDS.items()}


@router.post("/drawings")
def upload_drawing(request: Request, file: UploadFile = File(...), standard: str = Form("ISO")) -> Dict[str, Any]:
    """Upload a drawing (PDF, PNG/JPG/TIFF or DXF) and run the full review."""
    _validate_standard(standard)
    try:
        return get_engineering_service().review_upload(
            file.filename or "drawing", file.file.read(), standard, owner_id=current_owner_id(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("review drawing", e)


@router.get("/drawings")
def list_drawings(request: Request) -> Dict[str, Any]:
    return {"drawings": get_engineering_service().store.list_drawings(owner_scope(request))}


@router.get("/drawings/{drawing_id}")
def get_drawing(request: Request, drawing_id: str) -> Dict[str, Any]:
    _owned(request, "drawing", drawing_id)
    drawing = get_engineering_service().get_drawing(drawing_id)
    if drawing is None:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return drawing


@router.get("/drawings/{drawing_id}/pages/{page_number}")
def get_page_image(request: Request, drawing_id: str, page_number: int) -> FileResponse:
    """Rendered PNG of one sheet."""
    _owned(request, "drawing", drawing_id)
    path = get_engineering_service().page_image_path(drawing_id, page_number)
    if path is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(path, media_type="image/png")


@router.post("/drawings/{drawing_id}/review")
def rerun_review(drawing_id: str, body: ReviewRequest, request: Request) -> Dict[str, Any]:
    """Re-run the review, e.g. against a different standard."""
    _validate_standard(body.standard)
    _owned(request, "drawing", drawing_id)
    try:
        return get_engineering_service().run_review(drawing_id, body.standard)
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found")
    except Exception as e:
        raise _service_error("review drawing", e)


@router.post("/drawings/{drawing_id}/ask")
def ask_drawing(drawing_id: str, body: AskRequest, request: Request) -> Dict[str, Any]:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    _owned(request, "drawing", drawing_id)
    try:
        return get_engineering_service().ask(drawing_id, body.question.strip(), body.history)
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found or not processed")
    except Exception as e:
        raise _service_error("answer question", e)


@router.delete("/drawings/{drawing_id}")
def delete_drawing(request: Request, drawing_id: str) -> Dict[str, Any]:
    _owned(request, "drawing", drawing_id)
    if not get_engineering_service().delete_drawing(drawing_id):
        raise HTTPException(status_code=404, detail="Drawing not found")
    return {"id": drawing_id, "message": "Drawing deleted"}


# ----- comparisons -----

@router.post("/compare")
def compare(body: CompareRequest, request: Request) -> Dict[str, Any]:
    """Compare two reviewed drawings/documents (A = baseline, B = new)."""
    if body.a_id == body.b_id:
        raise HTTPException(status_code=400, detail="Choose two different drawings")
    _owned(request, "drawing", body.a_id)
    _owned(request, "drawing", body.b_id)
    try:
        return get_engineering_service().compare(body.a_id, body.b_id, owner_id=current_owner_id(request))
    except KeyError:
        raise HTTPException(status_code=404, detail="Drawing not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("compare", e)


@router.get("/comparisons")
def list_comparisons(request: Request) -> Dict[str, Any]:
    return {"comparisons": get_engineering_service().store.list_comparisons(owner_scope(request))}


# ----- templates -----

@router.get("/templates")
def list_templates() -> Dict[str, Any]:
    return {"templates": get_engineering_service().store.list_templates()}


@router.post("/templates")
def create_template(template: TemplateModel, request: Request) -> Dict[str, Any]:
    service = get_engineering_service()
    try:
        template_id = service.store.create_template(normalize_template(template.dict()), current_owner_id(request))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return service.store.get_template(template_id)


@router.post("/templates/import")
def import_template(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """Create a template from an existing DOCX, PDF, TXT or MD document."""
    service = get_engineering_service()
    try:
        template_id = service.import_template(
            file.filename or "template", file.file.read(), owner_id=current_owner_id(request)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("import template", e)
    return service.store.get_template(template_id)


@router.put("/templates/{template_id}")
def update_template(template_id: str, template: TemplateModel, request: Request) -> Dict[str, Any]:
    """Save edits to a template. Built-in and other people's templates are copied instead of modified."""
    service = get_engineering_service()
    existing = service.store.get_template(template_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        normalized = normalize_template(template.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not _can_edit_template(request, existing):
        if normalized["name"] == existing["name"]:
            normalized["name"] = f"{existing['name']} (custom)"
        template_id = service.store.create_template(normalized, current_owner_id(request))
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
def delete_template(request: Request, template_id: str) -> Dict[str, Any]:
    service = get_engineering_service()
    template = service.store.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if template["builtin"]:
        raise HTTPException(status_code=400, detail="Built-in templates cannot be deleted")
    if not _can_edit_template(request, template):
        raise HTTPException(status_code=403, detail="Only the template's creator or an administrator can delete it")
    service.store.delete_template(template_id)
    return {"id": template_id, "message": "Template deleted"}


# ----- generated documents -----

@router.post("/documents/generate")
def generate_document(body: GenerateRequest, request: Request) -> Dict[str, Any]:
    """Fill a template from reviewed drawings and comparisons."""
    for drawing_id in body.drawing_ids:
        _owned(request, "drawing", drawing_id)
    for comparison_id in body.comparison_ids:
        _owned(request, "comparison", comparison_id)
    try:
        return get_engineering_service().generate_document(
            body.template_id, body.drawing_ids, body.comparison_ids, body.instructions,
            owner_id=current_owner_id(request),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _service_error("generate document", e)


@router.get("/documents")
def list_documents(request: Request) -> Dict[str, Any]:
    return {"documents": get_engineering_service().store.list_documents(owner_scope(request))}


@router.get("/documents/{document_id}")
def get_document(request: Request, document_id: str) -> Dict[str, Any]:
    return _owned(request, "document", document_id)


@router.put("/documents/{document_id}")
def update_document(document_id: str, update: DocumentUpdate, request: Request) -> Dict[str, Any]:
    service = get_engineering_service()
    _owned(request, "document", document_id)
    fields = {k: v for k, v in update.dict().items() if v is not None}
    if fields:
        service.store.update_document(document_id, **fields)
    return service.store.get_document(document_id)


@router.delete("/documents/{document_id}")
def delete_document(request: Request, document_id: str) -> Dict[str, Any]:
    service = get_engineering_service()
    _owned(request, "document", document_id)
    service.store.delete_document(document_id)
    return {"id": document_id, "message": "Document deleted"}


@router.get("/documents/{document_id}/export")
def export_document(request: Request, document_id: str, format: str = "docx") -> Response:
    """Download a generated document as DOCX or Markdown."""
    service = get_engineering_service()
    document = _owned(request, "document", document_id)
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
