"""Blog posts, image uploads and site settings (admin), plus the public read API."""

import io
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from core.config import settings
from services.content_store import get_content_store, render_markdown
from services.platform_store import get_platform_store
from services.site_revalidate import revalidate_site
from .deps import client_ip, require_admin

admin_router = APIRouter(prefix="/admin", tags=["admin-content"], dependencies=[Depends(require_admin)])
public_router = APIRouter(prefix="/public", tags=["public"])

UPLOAD_DIR = os.path.join(settings.PLATFORM_DATA_DIR, "uploads")
UPLOAD_NAME = re.compile(r"^[0-9a-f\-]{36}\.webp$")
STATUSES = ("draft", "published")


class PostPayload(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    slug: Optional[str] = Field(default=None, max_length=90)
    excerpt: str = Field(default="", max_length=320)
    content_md: str = Field(default="", max_length=200_000)
    cover_image: Optional[str] = None
    cover_alt: Optional[str] = Field(default=None, max_length=200)
    tags: List[str] = []
    status: str = "draft"
    seo_title: Optional[str] = Field(default=None, max_length=70)
    seo_description: Optional[str] = Field(default=None, max_length=170)
    published_at: Optional[str] = None


class PreviewPayload(BaseModel):
    content_md: str = Field(default="", max_length=200_000)


class AnnouncementSettings(BaseModel):
    enabled: bool = False
    text: str = Field(default="", max_length=160)
    link_text: str = Field(default="", max_length=40)
    link_url: str = Field(default="", max_length=300)
    tone: str = "info"


class SettingsPayload(BaseModel):
    announcement: Optional[AnnouncementSettings] = None
    contact_form_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None


def _validate_post(payload: PostPayload) -> Dict[str, Any]:
    if payload.status not in STATUSES:
        raise HTTPException(status_code=422, detail="Status must be draft or published.")
    if payload.published_at:
        try:
            datetime.fromisoformat(payload.published_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="Publish date must be an ISO date-time.")
    if payload.cover_image and not UPLOAD_NAME.match(payload.cover_image):
        raise HTTPException(status_code=422, detail="Cover image must be an uploaded image.")
    return payload.dict()


def _touch_site(post: Optional[Dict[str, Any]] = None) -> None:
    paths = ["/blog"] + ([f"/blog/{post['slug']}"] if post else [])
    revalidate_site(["posts"], paths)


# ---------------------------------------------------------------------- admin: posts

@admin_router.get("/posts")
def list_posts() -> Dict[str, Any]:
    return {"posts": get_content_store().list_posts_admin()}


@admin_router.get("/posts/{post_id}")
def get_post(post_id: str) -> Dict[str, Any]:
    post = get_content_store().get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post


@admin_router.post("/posts")
def create_post(payload: PostPayload, request: Request) -> Dict[str, Any]:
    post = get_content_store().save_post(_validate_post(payload), request.state.user["id"])
    get_platform_store().log_event("content.post_created", request.state.user["id"], "admin",
                                   {"slug": post["slug"], "status": post["status"]}, client_ip(request))
    _touch_site(post)
    return post


@admin_router.put("/posts/{post_id}")
def update_post(post_id: str, payload: PostPayload, request: Request) -> Dict[str, Any]:
    store = get_content_store()
    previous = store.get_post(post_id)
    if previous is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    post = store.save_post(_validate_post(payload), request.state.user["id"], post_id)
    action = "content.post_published" if previous["status"] != "published" and post["status"] == "published" \
        else "content.post_updated"
    get_platform_store().log_event(action, request.state.user["id"], "admin",
                                   {"slug": post["slug"], "status": post["status"]}, client_ip(request))
    _touch_site(post)
    if previous["slug"] != post["slug"]:
        revalidate_site(["posts"], [f"/blog/{previous['slug']}"])
    return post


@admin_router.delete("/posts/{post_id}")
def delete_post(post_id: str, request: Request) -> Dict[str, Any]:
    store = get_content_store()
    post = store.get_post(post_id)
    if post is None or not store.delete_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found.")
    get_platform_store().log_event("content.post_deleted", request.state.user["id"], "admin",
                                   {"slug": post["slug"]}, client_ip(request))
    _touch_site(post)
    return {"ok": True}


@admin_router.post("/posts/preview")
def preview(payload: PreviewPayload) -> Dict[str, str]:
    """Same renderer and sanitiser as publishing, so the preview matches the live page."""
    return {"html": render_markdown(payload.content_md)}


@admin_router.get("/posts/{post_id}/stats")
def post_stats(post_id: str) -> Dict[str, Any]:
    post = get_content_store().get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    from .routes_admin import _daily

    path = f"/blog/{post['slug']}"
    store = get_platform_store()
    return {
        "views": store.scalar("SELECT COUNT(*) FROM page_views WHERE path = ?", (path,)),
        "visitors": store.scalar("SELECT COUNT(DISTINCT visitor) FROM page_views WHERE path = ?", (path,)),
        "series": _daily("page_views", 30, where="AND path = ?", params=(path,)),
        "referrers": [[r["ref"], r["n"]] for r in store.query(
            "SELECT COALESCE(referrer, 'Direct / none') AS ref, COUNT(*) AS n FROM page_views WHERE path = ? "
            "GROUP BY ref ORDER BY n DESC LIMIT 8", (path,))],
    }


# ---------------------------------------------------------------------- admin: uploads

@admin_router.post("/uploads")
def upload_image(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accept an image, re-encode it as WebP (strips metadata and any embedded payload), max 2000 px."""
    content = file.file.read(settings.UPLOAD_MAX_MB * 1024 * 1024 + 1)
    if len(content) > settings.UPLOAD_MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Images must be under {settings.UPLOAD_MAX_MB} MB.")
    from services.file_safety import UnsafeFileError, validate_upload
    try:
        validate_upload(file.filename or "image", content, {".png", ".jpg", ".jpeg", ".webp", ".gif"})
    except UnsafeFileError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content))
        if image.format not in ("PNG", "JPEG", "WEBP", "GIF"):
            raise HTTPException(status_code=422, detail="Upload a PNG, JPEG, WebP or GIF image.")
        image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
        image.thumbnail((2000, 2000))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(status_code=422, detail="The file is not a valid image.")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = f"{uuid.uuid4()}.webp"
    image.save(os.path.join(UPLOAD_DIR, name), "WEBP", quality=82, method=6)
    get_platform_store().log_event("content.image_uploaded", request.state.user["id"], "admin", {"file": name},
                                   client_ip(request))
    return {"name": name, "url": f"/public/uploads/{name}", "width": image.width, "height": image.height}


# ---------------------------------------------------------------------- admin: settings

@admin_router.get("/settings")
def get_settings() -> Dict[str, Any]:
    return get_content_store().get_settings()


@admin_router.put("/settings")
def put_settings(payload: SettingsPayload, request: Request) -> Dict[str, Any]:
    values = {k: v for k, v in payload.dict().items() if v is not None}
    announcement = values.get("announcement")
    if announcement:
        if announcement["tone"] not in ("info", "success", "warning"):
            raise HTTPException(status_code=422, detail="Tone must be info, success or warning.")
        url = announcement["link_url"].strip()
        if url and not (url.startswith("/") and not url.startswith("//")) and not url.startswith("https://"):
            raise HTTPException(status_code=422, detail="Link must be a site path (/…) or an https:// URL.")
    updated = get_content_store().update_settings(values)
    get_platform_store().log_event("admin.settings_updated", request.state.user["id"], "admin",
                                   {"keys": sorted(values)}, client_ip(request))
    revalidate_site(["settings"], ["/"])
    return updated


# ---------------------------------------------------------------------- public (no auth)

@public_router.get("/posts")
def public_posts(tag: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return {"posts": get_content_store().list_published(tag, min(max(limit, 1), 100))}


@public_router.get("/posts/{slug}")
def public_post(slug: str) -> Dict[str, Any]:
    post = get_content_store().get_published(slug)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post


@public_router.get("/settings")
def public_settings() -> Dict[str, Any]:
    current = get_content_store().get_settings()
    return {"announcement": current["announcement"], "contact_form_enabled": current["contact_form_enabled"]}


@public_router.get("/uploads/{name}")
def uploaded_file(name: str) -> FileResponse:
    if not UPLOAD_NAME.match(name):
        raise HTTPException(status_code=404, detail="Not found.")
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found.")
    # Names are random UUIDs and files never change, so they can be cached for a year
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"})
