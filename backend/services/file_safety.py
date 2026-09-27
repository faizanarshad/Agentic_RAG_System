"""Upload safety: file contents must match the claimed type, size/complexity limits, optional virus scan."""

import io
import os
import shutil
import subprocess
import warnings
import zipfile
from typing import Iterable

from PIL import Image

from utils.logger import logger

# Refuse decompression bombs: images above ~60 megapixels raise instead of allocating gigabytes
Image.MAX_IMAGE_PIXELS = 60_000_000
warnings.simplefilter("error", Image.DecompressionBombWarning)

MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "1000"))
VIRUS_SCAN = os.getenv("VIRUS_SCAN", "auto").lower()   # auto | required | off
CLAMAV_COMMAND = os.getenv("CLAMAV_COMMAND", "")


class UnsafeFileError(ValueError):
    """Raised when an upload fails a safety check; the message is safe to show to the user."""


def _looks_like_text(content: bytes) -> bool:
    sample = content[:65536]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            sample.decode("latin-1")
            return True
        except UnicodeDecodeError:
            return False


def _matches(extension: str, content: bytes) -> bool:
    head = content[:16]
    if extension == ".pdf":
        return b"%PDF-" in content[:1024]
    if extension == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8\xff")
    if extension in (".tif", ".tiff"):
        return head.startswith((b"II*\x00", b"MM\x00*"))
    if extension == ".gif":
        return head.startswith((b"GIF87a", b"GIF89a"))
    if extension == ".webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if extension == ".docx":
        if not head.startswith(b"PK\x03\x04"):
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = archive.namelist()
                total = sum(info.file_size for info in archive.infolist())
            # Zip bombs: refuse archives that would expand beyond 200 MB
            return "word/document.xml" in names and total < 200 * 1024 * 1024
        except zipfile.BadZipFile:
            return False
    if extension == ".dxf":
        text = content[:200000].decode("utf-8", errors="ignore").upper()
        return _looks_like_text(content) and "SECTION" in text and ("ENTITIES" in text or "HEADER" in text)
    if extension in (".txt", ".md", ".csv"):
        return _looks_like_text(content)
    return False


def check_pdf_pages(content: bytes) -> None:
    import pymupdf as fitz

    try:
        with fitz.open(stream=content, filetype="pdf") as pdf:
            if pdf.page_count > MAX_PDF_PAGES:
                raise UnsafeFileError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")
    except UnsafeFileError:
        raise
    except Exception:
        raise UnsafeFileError("The PDF could not be opened; it may be damaged.")


def _scanner() -> str:
    if CLAMAV_COMMAND:
        return CLAMAV_COMMAND
    return shutil.which("clamdscan") or shutil.which("clamscan") or ""


def virus_scan(content: bytes, filename: str) -> None:
    if VIRUS_SCAN == "off":
        return
    scanner = _scanner()
    if not scanner:
        if VIRUS_SCAN == "required":
            raise UnsafeFileError("Uploads are temporarily unavailable: the virus scanner is not running.")
        return
    try:
        result = subprocess.run([scanner, "--no-summary", "-"], input=content, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.error(f"Virus scan failed for {filename}: {e}")
        if VIRUS_SCAN == "required":
            raise UnsafeFileError("The file could not be scanned for viruses. Please try again.")
        return
    if result.returncode == 1:
        logger.warning(f"Virus detected in upload {filename}: {result.stdout.decode(errors='ignore').strip()}")
        raise UnsafeFileError("The file was rejected by the virus scanner.")
    if result.returncode != 0 and VIRUS_SCAN == "required":
        raise UnsafeFileError("The file could not be scanned for viruses. Please try again.")


def validate_upload(filename: str, content: bytes, allowed: Iterable[str]) -> str:
    """Run all checks; returns the normalised extension or raises UnsafeFileError."""
    extension = os.path.splitext(filename or "")[1].lower()
    if extension not in set(allowed):
        raise UnsafeFileError(f"File type '{extension or 'unknown'}' is not allowed.")
    if not content:
        raise UnsafeFileError("The file is empty.")
    if not _matches(extension, content):
        raise UnsafeFileError(f"The file's contents do not match its '{extension}' extension.")
    if extension == ".pdf":
        check_pdf_pages(content)
    virus_scan(content, filename)
    return extension
