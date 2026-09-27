"""
Generate fictional engineering drawings with planted errors for testing the Engineering page.

Outputs (datasets/engineering_samples/):
  bracket_EP-1001_revA.pdf  vector part drawing; planted errors: missing material, conflicting overall
                            length (120 vs 125), GD&T frame referencing undefined datum C, inch value on a
                            millimetre drawing, missing checker/approver
  bracket_EP-1001_revB.pdf  revision B: hole Ø8.5→Ø9.0 and thickness 10→12 changed, but the revision table
                            only records "added material specification" (unrecorded changes)
  flange_FL-2040.dxf        DXF with block-attribute title block; planted errors: bore dimension text
                            overridden to Ø50 while geometry is Ø48, title block says INCHES but file is mm
  answer_key.json           the planted errors, for checking the agent's findings

Usage (from the repo root):
    backend/venv/bin/python scripts/generate_engineering_samples.py
"""

import json
import math
import os

import ezdxf
import fitz  # PyMuPDF

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, "datasets", "engineering_samples")

A3 = (1190, 842)  # landscape, points
MM = 3.2          # points per model millimetre in the views
BLACK = (0, 0, 0)
THIN, MEDIUM, THICK = 0.4, 0.7, 1.4


# ---------------------------------------------------------------------- PDF drawing helpers

def text(page, x, y, value, size=8, bold=False):
    page.insert_text((x, y), value, fontsize=size, fontname="hebo" if bold else "helv")


def arrow(page, tip, direction):
    dx, dy = direction
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    size, spread = 6, 2.2
    left = (tip[0] - ux * size - uy * spread, tip[1] - uy * size + ux * spread)
    right = (tip[0] - ux * size + uy * spread, tip[1] - uy * size - ux * spread)
    page.draw_polyline([left, tip, right], color=BLACK, fill=BLACK, width=THIN, closePath=True)


def dim_horizontal(page, x1, x2, y_feature, y_dim, label):
    for x in (x1, x2):
        page.draw_line((x, y_feature), (x, y_dim + (3 if y_dim < y_feature else -3)), color=BLACK, width=THIN)
    page.draw_line((x1, y_dim), (x2, y_dim), color=BLACK, width=THIN)
    arrow(page, (x1, y_dim), (-1, 0))
    arrow(page, (x2, y_dim), (1, 0))
    width = fitz.get_text_length(label, fontsize=8)
    text(page, (x1 + x2) / 2 - width / 2, y_dim - 3, label)


def dim_vertical(page, y1, y2, x_feature, x_dim, label):
    for y in (y1, y2):
        page.draw_line((x_feature, y), (x_dim + (3 if x_dim < x_feature else -3), y), color=BLACK, width=THIN)
    page.draw_line((x_dim, y1), (x_dim, y2), color=BLACK, width=THIN)
    arrow(page, (x_dim, y1), (0, -1))
    arrow(page, (x_dim, y2), (0, 1))
    page.insert_text((x_dim - 4, (y1 + y2) / 2 + 8), label, fontsize=8, fontname="helv", rotate=90)


def leader(page, start, end, label):
    page.draw_line(start, end, color=BLACK, width=THIN)
    arrow(page, start, (start[0] - end[0], start[1] - end[1]))
    page.draw_line(end, (end[0] + 8, end[1]), color=BLACK, width=THIN)
    text(page, end[0] + 10, end[1] + 3, label)


def centre_mark(page, x, y, size=6):
    page.draw_line((x - size, y), (x + size, y), color=BLACK, width=THIN, dashes="[4 2] 0")
    page.draw_line((x, y - size), (x, y + size), color=BLACK, width=THIN, dashes="[4 2] 0")


def feature_control_frame(page, x, y, cells):
    """Position tolerance frame: symbol cell drawn graphically, then text cells."""
    height, x0 = 14, x
    page.draw_rect(fitz.Rect(x0, y, x0 + 16, y + height), color=BLACK, width=THIN)
    cx, cy = x0 + 8, y + height / 2
    page.draw_circle((cx, cy), 3.5, color=BLACK, width=THIN)
    page.draw_line((cx - 6, cy), (cx + 6, cy), color=BLACK, width=THIN)
    page.draw_line((cx, cy - 6), (cx, cy + 6), color=BLACK, width=THIN)
    x0 += 16
    for cell in cells:
        width = fitz.get_text_length(cell, fontsize=8) + 8
        page.draw_rect(fitz.Rect(x0, y, x0 + width, y + height), color=BLACK, width=THIN)
        text(page, x0 + 4, y + 10, cell)
        x0 += width


def datum_symbol(page, x, y, letter):
    page.draw_rect(fitz.Rect(x - 7, y, x + 7, y + 14), color=BLACK, width=THIN)
    text(page, x - 3, y + 10, letter, bold=True)
    page.draw_line((x, y + 14), (x, y + 22), color=BLACK, width=THIN)
    page.draw_polyline([(x - 4, y + 22), (x + 4, y + 22), (x, y + 28)], color=BLACK, fill=BLACK,
                       width=THIN, closePath=True)


def title_block(page, fields):
    x0, y0, x1, y1 = 700, 640, 1170, 822
    page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=BLACK, width=THICK)
    rows = [
        [("COMPANY", fields["company"], 470)],
        [("TITLE", fields["title"], 300), ("DWG NO", fields["dwg_no"], 110), ("REV", fields["rev"], 60)],
        [("MATERIAL", fields["material"], 235), ("FINISH", fields["finish"], 235)],
        [("SCALE", fields["scale"], 90), ("UNITS", fields["units"], 90), ("SIZE", "A3", 70),
         ("SHEET", "1 OF 1", 90), ("PROJECTION", "FIRST ANGLE", 130)],
        [("GENERAL TOLERANCES", fields["tolerance"], 470)],
        [("DRAWN", fields["drawn"], 120), ("DATE", fields["date"], 110), ("CHECKED", fields["checked"], 120),
         ("APPROVED", fields["approved"], 120)],
    ]
    row_height = (y1 - y0) / len(rows)
    for r, row in enumerate(rows):
        x, top = x0, y0 + r * row_height
        for label, value, width in row:
            page.draw_rect(fitz.Rect(x, top, x + width, top + row_height), color=BLACK, width=THIN)
            text(page, x + 3, top + 9, label, size=5.5)
            text(page, x + 3, top + row_height - 6, value, size=9, bold=True)
            x += width
    # First-angle projection symbol inside the PROJECTION cell
    px, py = 1105, y0 + 3 * row_height + 16
    page.draw_circle((px, py), 5, color=BLACK, width=THIN)
    page.draw_circle((px, py), 2.5, color=BLACK, width=THIN)
    page.draw_polyline([(px + 12, py - 5), (px + 26, py - 8), (px + 26, py + 8), (px + 12, py + 5)],
                       color=BLACK, width=THIN, closePath=True)


def revision_table(page, rows):
    x0, y0 = 760, 24
    widths = [40, 230, 80, 60]
    headers = ["REV", "DESCRIPTION", "DATE", "APPROVED"]
    for r, row in enumerate([headers] + rows):
        x = x0
        for width, value in zip(widths, row):
            page.draw_rect(fitz.Rect(x, y0 + r * 16, x + width, y0 + (r + 1) * 16), color=BLACK, width=THIN)
            text(page, x + 3, y0 + r * 16 + 11, value, size=7, bold=(r == 0))
            x += width


def draw_bracket(path, revision):
    """Mounting bracket 120 x 80 plate with 4 holes and a central bore; revision A or B."""
    hole = "8.5" if revision == "A" else "9.0"
    thickness = 10 if revision == "A" else 12
    document = fitz.open()
    page = document.new_page(width=A3[0], height=A3[1])
    page.draw_rect(fitz.Rect(12, 12, A3[0] - 12, A3[1] - 12), color=BLACK, width=THICK)
    text(page, 24, 30, "SYNTHETIC SAMPLE DRAWING - FICTIONAL, FOR SOFTWARE TESTING", size=7)

    # Front view (plate 120 x 80)
    fx, fy = 140, 180
    w, h = 120 * MM, 80 * MM
    page.draw_rect(fitz.Rect(fx, fy, fx + w, fy + h), color=BLACK, width=THICK)
    text(page, fx, fy + h + 60, "FRONT VIEW", size=9, bold=True)
    for hx, hy in ((10, 10), (110, 10), (10, 70), (110, 70)):
        cx, cy = fx + hx * MM, fy + hy * MM
        page.draw_circle((cx, cy), float(hole) / 2 * MM, color=BLACK, width=MEDIUM)
        centre_mark(page, cx, cy, 12)
    bx, by = fx + 60 * MM, fy + 40 * MM
    page.draw_circle((bx, by), 15 * MM, color=BLACK, width=MEDIUM)
    centre_mark(page, bx, by, 60)

    dim_horizontal(page, fx, fx + w, fy, fy - 45, "120")
    dim_horizontal(page, fx + 10 * MM, fx + 110 * MM, fy, fy - 22, "100")
    dim_horizontal(page, fx, fx + 10 * MM, fy + h, fy + h + 22, "10")
    dim_vertical(page, fy, fy + h, fx, fx - 45, "80")
    dim_vertical(page, fy + 10 * MM, fy + 70 * MM, fx, fx - 22, "60")
    dim_vertical(page, fy + h - 10 * MM, fy + h, fx + w, fx + w + 22, "10")
    leader(page, (fx + 110 * MM + 3, fy + 10 * MM - 3), (fx + w + 30, fy - 30), f"4X Ø{hole} THRU")
    leader(page, (bx + 10 * MM, by - 11 * MM), (fx + w + 30, fy + 60), "Ø30 H7")
    feature_control_frame(page, fx + w + 40, fy - 22, ["Ø0.2", "A", "B", "C"])  # datum C is never defined
    datum_symbol(page, fx - 70, fy + h / 2 - 14, "B")

    # Side view (thickness), to the right of the front view (first-angle: left view on the right)
    sx = fx + w + 150
    page.draw_rect(fitz.Rect(sx, fy, sx + thickness * MM, fy + h), color=BLACK, width=THICK)
    text(page, sx - 20, fy + h + 60, "SIDE VIEW", size=9, bold=True)
    dim_horizontal(page, sx, sx + thickness * MM, fy + h, fy + h + 22, str(thickness))
    datum_symbol(page, sx + thickness * MM + 20, fy + 30, "A")

    # Top view (below the front view): overall length dimensioned as 125, conflicting with 120
    ty = fy + h + 110
    page.draw_rect(fitz.Rect(fx, ty, fx + w, ty + thickness * MM), color=BLACK, width=THICK)
    page.draw_line((fx + 60 * MM - 15 * MM, ty), (fx + 60 * MM - 15 * MM, ty + thickness * MM),
                   color=BLACK, width=THIN, dashes="[3 2] 0")
    page.draw_line((fx + 60 * MM + 15 * MM, ty), (fx + 60 * MM + 15 * MM, ty + thickness * MM),
                   color=BLACK, width=THIN, dashes="[3 2] 0")
    dim_horizontal(page, fx, fx + w, ty + thickness * MM, ty + thickness * MM + 28, "125")
    text(page, fx, ty + thickness * MM + 62, "TOP VIEW", size=9, bold=True)

    notes = [
        "NOTES:",
        "1. BREAK ALL SHARP EDGES 0.2 X 45°.",
        "2. DEBURR ALL HOLES.",
        "3. CORNER RADIUS R0.12 in ON ALL OUTER CORNERS.",  # inch value on a millimetre drawing
        "4. ALL DIMENSIONS IN MILLIMETERS UNLESS OTHERWISE SPECIFIED.",
    ]
    for i, note in enumerate(notes):
        text(page, 40, 700 + i * 13, note, size=8, bold=(i == 0))

    title_block(page, {
        "company": "FICTIONAL DYNAMICS LTD",
        "title": "MOUNTING BRACKET",
        "dwg_no": "EP-1001",
        "rev": revision,
        "material": "" if revision == "A" else "AL 6061-T6",
        "finish": "ANODIZE CLEAR",
        "scale": "1:2",
        "units": "mm",
        "tolerance": "ISO 2768-mK",
        "drawn": "J. RIVERA",
        "date": "2026-03-14" if revision == "A" else "2026-05-02",
        "checked": "",
        "approved": "",
    })
    rows = [["A", "INITIAL RELEASE", "2026-03-14", "J.R."]]
    if revision == "B":
        rows.append(["B", "ADDED MATERIAL SPECIFICATION", "2026-05-02", "J.R."])
    revision_table(page, rows)
    document.save(path)
    document.close()


def draw_flange_dxf(path):
    document = ezdxf.new(setup=True)
    document.header["$INSUNITS"] = 4  # millimetres
    msp = document.modelspace()

    msp.add_circle((0, 0), 60)                     # Ø120 outer diameter
    msp.add_circle((0, 0), 24)                     # Ø48 bore
    msp.add_circle((0, 0), 45, dxfattribs={"linetype": "CENTER"})  # Ø90 bolt circle
    for i in range(6):
        angle = math.radians(60 * i)
        msp.add_circle((45 * math.cos(angle), 45 * math.sin(angle)), 5)  # 6X Ø10

    msp.add_linear_dim(base=(0, 75), p1=(-60, 0), p2=(60, 0)).render()
    # Bore dimension text overridden to Ø50 although the geometry is Ø48
    msp.add_diameter_dim(center=(0, 0), radius=24, angle=30, text="%%c50").render()
    msp.add_diameter_dim(center=(0, 0), radius=45, angle=150, text="%%c90 BC").render()
    msp.add_text("6X %%c10 THRU EQ SP", height=3.5).set_placement((48, -58))

    block = document.blocks.new("TITLEBLOCK")
    block.add_lwpolyline([(0, 0), (140, 0), (140, 42), (0, 42)], close=True)
    tags = ["TITLE", "DWG_NO", "REV", "MATERIAL", "UNITS", "SCALE", "PROJECTION", "TOLERANCE", "DRAWN", "DATE"]
    for i, tag in enumerate(tags):
        x, y = (4 if i < 5 else 74), 36 - (i % 5) * 8
        block.add_text(f"{tag}:", height=2.2).set_placement((x, y))
        block.add_attdef(tag, (x + 24, y), dxfattribs={"height": 2.5})
    msp.add_blockref("TITLEBLOCK", (70, -110)).add_auto_attribs({
        "TITLE": "PIPE FLANGE DN40",
        "DWG_NO": "FL-2040",
        "REV": "A",
        "MATERIAL": "STEEL S235JR",
        "UNITS": "INCHES",  # file units are millimetres
        "SCALE": "1:1",
        "PROJECTION": "FIRST ANGLE",
        "TOLERANCE": "ISO 2768-m",
        "DRAWN": "A. OKAFOR",
        "DATE": "2026-04-20",
    })
    msp.add_mtext(
        "SYNTHETIC SAMPLE - FICTIONAL\\PNOTES:\\P1. REMOVE ALL BURRS.\\P2. FACE FINISH Ra 3.2.",
        dxfattribs={"char_height": 3},
    ).set_location((-110, -80))
    document.saveas(path)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    draw_bracket(os.path.join(OUTPUT_DIR, "bracket_EP-1001_revA.pdf"), "A")
    draw_bracket(os.path.join(OUTPUT_DIR, "bracket_EP-1001_revB.pdf"), "B")
    draw_flange_dxf(os.path.join(OUTPUT_DIR, "flange_FL-2040.dxf"))
    answer_key = {
        "bracket_EP-1001_revA.pdf": [
            "Material missing from title block",
            "Overall length dimensioned 120 (front view) and 125 (top view)",
            "Position tolerance references datum C, which is not defined (only A and B)",
            "Note 3 uses inches (R0.12 in) on a millimetre drawing",
            "Checked by / approved by empty",
        ],
        "bracket_EP-1001_revB.pdf vs revA": [
            "Hole diameter changed Ø8.5 -> Ø9.0 (not recorded in revision table)",
            "Thickness changed 10 -> 12 (not recorded in revision table)",
            "Material added AL 6061-T6 (recorded)",
            "Revision A -> B, date changed",
        ],
        "flange_FL-2040.dxf": [
            "Bore dimension text overridden to Ø50 but geometry measures Ø48",
            "Title block units INCHES but DXF units are millimetres",
        ],
    }
    with open(os.path.join(OUTPUT_DIR, "answer_key.json"), "w") as f:
        json.dump(answer_key, f, indent=2)
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
