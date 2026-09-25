"""Load engineering drawings (PDF, raster images, DXF CAD files) into page images plus exact text."""

import base64
import io
import os
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
from PIL import Image

from core.config import settings
from utils.logger import logger


SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".dxf"}

# Long side of the stored page render; enough for the zoomed tiles sent to the vision model
RENDER_LONG_SIDE_PX = 3000

# DXF $INSUNITS codes
DXF_UNITS = {0: "unitless", 1: "inches", 2: "feet", 4: "millimeters", 5: "centimeters", 6: "meters"}


class EngineeringLoader:
    """Renders each sheet to PNG and extracts positioned text (PDF text layer or DXF entities)."""

    def load(self, file_path: str, filename: str, output_dir: str) -> Dict[str, Any]:
        """
        Load a drawing.

        Args:
            file_path: Path to the uploaded file
            filename: Original filename (used to detect the type)
            output_dir: Directory where page PNGs are written

        Returns:
            Dictionary with pages (image path, size, positioned text), source type and CAD data for DXF files
        """
        extension = os.path.splitext(filename)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{extension}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Loading engineering drawing {filename}")

        if extension == ".dxf":
            return self._load_dxf(file_path, output_dir)
        return self._load_pdf_or_image(file_path, output_dir, "pdf" if extension == ".pdf" else "image")

    def _load_pdf_or_image(self, file_path: str, output_dir: str, source_type: str) -> Dict[str, Any]:
        pages = []
        with fitz.open(file_path) as document:
            page_count = document.page_count
            for number, page in enumerate(document, start=1):
                if number > settings.ENGINEERING_MAX_PAGES:
                    logger.warning(f"Page limit reached; only the first {settings.ENGINEERING_MAX_PAGES} sheets are reviewed")
                    break
                zoom = RENDER_LONG_SIDE_PX / max(page.rect.width, page.rect.height)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                image_path = os.path.join(output_dir, f"page_{number}.png")
                pixmap.save(image_path)
                pages.append({
                    "number": number,
                    "image_path": image_path,
                    "width": pixmap.width,
                    "height": pixmap.height,
                    "text_blocks": self._positioned_text(page) if source_type == "pdf" else [],
                })
        return {"source_type": source_type, "page_count": page_count, "pages": pages, "cad": None}

    @staticmethod
    def _positioned_text(page: "fitz.Page") -> List[Dict[str, Any]]:
        """Text blocks with their position as a percentage of the sheet (x from left, y from top)."""
        width, height = page.rect.width, page.rect.height
        blocks = []
        for x0, y0, x1, y1, text, *_ in page.get_text("blocks"):
            text = " ".join(text.split())
            if text:
                blocks.append({
                    "text": text,
                    "x": round(100 * ((x0 + x1) / 2) / width),
                    "y": round(100 * ((y0 + y1) / 2) / height),
                })
        return blocks

    def _load_dxf(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        import ezdxf
        from ezdxf.addons.drawing import Frontend, RenderContext, config, layout, pymupdf

        document = ezdxf.readfile(file_path)
        modelspace = document.modelspace()
        cad = self._cad_entities(document, modelspace)

        backend = pymupdf.PyMuPdfBackend()
        render_config = config.Configuration(
            background_policy=config.BackgroundPolicy.WHITE,
            color_policy=config.ColorPolicy.BLACK,
        )
        Frontend(RenderContext(document), backend, config=render_config).draw_layout(modelspace)
        page_layout = layout.Page(0, 0, layout.Units.mm, margins=layout.Margins.all(5))
        png_bytes = backend.get_pixmap_bytes(page_layout, fmt="png", dpi=200)

        image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        scale = RENDER_LONG_SIDE_PX / max(image.size)
        if scale < 1:
            image = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
        image_path = os.path.join(output_dir, "page_1.png")
        image.save(image_path)

        text_blocks = [{"text": item["text"], "x": item["x"], "y": item["y"]} for item in cad.pop("positioned_text")]
        return {
            "source_type": "dxf",
            "page_count": 1,
            "pages": [{
                "number": 1,
                "image_path": image_path,
                "width": image.width,
                "height": image.height,
                "text_blocks": text_blocks,
            }],
            "cad": cad,
        }

    @staticmethod
    def _cad_entities(document, modelspace) -> Dict[str, Any]:
        """Exact CAD data: texts, block attributes (title blocks), dimensions with measured values, layers."""
        extents = _extents(modelspace)
        texts, dimensions, attributes = [], [], []

        def position(point) -> Dict[str, int]:
            if extents is None:
                return {"x": 0, "y": 0}
            (min_x, min_y), (max_x, max_y) = extents
            return {
                "x": round(100 * (point[0] - min_x) / max(max_x - min_x, 1e-9)),
                "y": round(100 * (max_y - point[1]) / max(max_y - min_y, 1e-9)),  # y from top, like PDFs
            }

        for entity in modelspace:
            kind = entity.dxftype()
            if kind == "TEXT":
                texts.append({"text": _dxf_plain(entity.dxf.text), "layer": entity.dxf.layer, **position(entity.dxf.insert)})
            elif kind == "MTEXT":
                texts.append({"text": entity.plain_text(), "layer": entity.dxf.layer, **position(entity.dxf.insert)})
            elif kind == "INSERT":
                for attrib in entity.attribs:
                    attributes.append({
                        "block": entity.dxf.name,
                        "tag": attrib.dxf.tag,
                        "value": _dxf_plain(attrib.dxf.text),
                        **position(attrib.dxf.insert),
                    })
            elif kind == "DIMENSION":
                try:
                    measured = round(entity.get_measurement(), 4)
                except Exception:
                    measured = None
                override = _dxf_plain(entity.dxf.get("text", ""))
                shown = override.replace("<>", str(measured)) if override and override != "<>" else str(measured)
                dimensions.append({
                    "measured": measured,
                    "displayed_text": shown,
                    "text_overridden": bool(override and override != "<>" and "<>" not in override),
                    "layer": entity.dxf.layer,
                    **position(entity.dxf.get("text_midpoint", entity.dxf.defpoint)),
                })

        positioned_text = [
            {"text": t["text"], "x": t["x"], "y": t["y"]} for t in texts if t["text"].strip()
        ] + [
            {"text": f"{a['tag']}: {a['value']}", "x": a["x"], "y": a["y"]} for a in attributes
        ] + [
            {"text": f"DIM {d['displayed_text']}", "x": d["x"], "y": d["y"]} for d in dimensions
        ]
        return {
            "units": DXF_UNITS.get(document.header.get("$INSUNITS", 0), "unknown"),
            "layers": sorted(layer.dxf.name for layer in document.layers),
            "texts": texts,
            "block_attributes": attributes,
            "dimensions": dimensions,
            "positioned_text": positioned_text,
        }


def _dxf_plain(value: str) -> str:
    """Replace DXF special-character codes (%%c diameter, %%d degree, %%p plus/minus)."""
    for code, char in (("%%c", "Ø"), ("%%C", "Ø"), ("%%d", "°"), ("%%D", "°"), ("%%p", "±"), ("%%P", "±")):
        value = value.replace(code, char)
    return value


def _extents(modelspace) -> Optional[tuple]:
    try:
        from ezdxf import bbox

        box = bbox.extents(modelspace)
        if box.has_data:
            return (box.extmin.x, box.extmin.y), (box.extmax.x, box.extmax.y)
    except Exception:
        pass
    return None


def page_images_for_vision(image_path: str) -> List[str]:
    """
    Return base64 PNGs for one sheet: the full sheet plus four overlapping quadrant tiles.

    The vision API downsizes each image so its short side is ~768 px, which makes small dimension
    text unreadable on a full sheet; the tiles give roughly twice the effective resolution.
    """
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    crops = [image]
    overlap_x, overlap_y = int(width * 0.05), int(height * 0.05)
    half_x, half_y = width // 2, height // 2
    for left, top in ((0, 0), (half_x, 0), (0, half_y), (half_x, half_y)):
        box = (
            max(left - overlap_x, 0),
            max(top - overlap_y, 0),
            min(left + half_x + overlap_x, width),
            min(top + half_y + overlap_y, height),
        )
        crops.append(image.crop(box))

    encoded = []
    for crop in crops:
        crop.thumbnail((2048, 2048))
        buffer = io.BytesIO()
        crop.save(buffer, format="PNG", optimize=True)
        encoded.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
    return encoded


def crop_for_vision(image_path: str, x_percent: float, y_percent: float, half_size_percent: float = 14) -> str:
    """Base64 PNG of a region around (x%, y%) of the sheet, for targeted verification."""
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    half = half_size_percent / 100 * max(width, height)
    cx, cy = x_percent / 100 * width, y_percent / 100 * height
    box = (int(max(cx - half, 0)), int(max(cy - half, 0)), int(min(cx + half, width)), int(min(cy + half, height)))
    crop = image.crop(box)
    crop.thumbnail((1536, 1536))
    buffer = io.BytesIO()
    crop.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def text_layer_summary(pages: List[Dict[str, Any]], limit_chars: int = 12000) -> str:
    """Positioned text for the prompt, e.g. '[p1 x=85% y=92%] DWG NO: EP-1001'."""
    lines = []
    for page in pages:
        for block in page["text_blocks"]:
            lines.append(f"[p{page['number']} x={block['x']}% y={block['y']}%] {block['text']}")
    text = "\n".join(lines)
    return text[:limit_chars] if text else "(no text layer: raster drawing, rely on the images)"
