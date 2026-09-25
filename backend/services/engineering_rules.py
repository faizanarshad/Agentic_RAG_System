"""Deterministic drawing checks that run before the LLM review."""

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

REQUIRED_TITLE_BLOCK_FIELDS = [
    ("title", "Title"),
    ("drawing_number", "Drawing number"),
    ("revision", "Revision"),
    ("scale", "Scale"),
    ("units", "Units"),
    ("material", "Material"),
    ("projection", "Projection method"),
    ("general_tolerance", "General tolerance"),
    ("drawn_by", "Drawn by"),
    ("date", "Date"),
]

INITIAL_REVISIONS = {"", "-", "0", "00", "A", "01", "1", "NC", "IR"}
INCH_PATTERN = re.compile(r'\d(?:\.\d+)?\s*(?:"|in\b|inch)', re.IGNORECASE)
MM_PATTERN = re.compile(r"\d(?:\.\d+)?\s*mm\b", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")
TOLERANCE_PATTERN = re.compile(r"±|\+/-|\+\d|-\d|[A-Za-z]\d{1,2}\b|\bMAX\b|\bMIN\b|\d\s*/\s*\d|\bREF\b|\(|\)", re.IGNORECASE)


def _check(rule_id: str, title: str, status: str, severity: str, detail: str,
           category: str, recommendation: str = "") -> Dict[str, Any]:
    return {
        "id": rule_id,
        "title": title,
        "status": status,  # pass | fail | not_applicable
        "severity": severity,
        "category": category,
        "detail": detail,
        "recommendation": recommendation,
    }


def run_rule_checks(extraction: Dict[str, Any], page_count: int, cad: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run all deterministic checks and return their results."""
    title_block = extraction.get("title_block") or {}
    dimensions = extraction.get("dimensions") or []
    is_assembly = "assembly" in (extraction.get("drawing_type") or "").lower()
    results = []

    # R1: title block completeness
    missing = [
        label for key, label in REQUIRED_TITLE_BLOCK_FIELDS
        if not (title_block.get(key) or "").strip() and not (key == "material" and is_assembly)
    ]
    results.append(_check(
        "R1", "Title block completeness",
        "fail" if missing else "pass",
        "major" if {"Drawing number", "Revision", "Material", "Units"} & set(missing) else "minor",
        f"Missing: {', '.join(missing)}" if missing else "All required title block fields are present.",
        "title_block",
        "Complete the missing title block fields before release." if missing else "",
    ))

    # R2: title block revision matches the latest revision table entry
    revision = (title_block.get("revision") or "").strip().upper()
    revision_rows = [r for r in extraction.get("revision_table") or [] if (r.get("revision") or "").strip()]
    if revision_rows:
        # Tables list newest first or last; order by (length, value) so "10" > "9" and "AA" > "Z"
        latest = max((r["revision"].strip().upper() for r in revision_rows), key=lambda rev: (len(rev), rev))
        mismatch = revision and revision != latest
        results.append(_check(
            "R2", "Revision consistency",
            "fail" if mismatch else "pass",
            "major",
            f"Title block shows revision '{revision}' but the revision table's latest entry is '{latest}'."
            if mismatch else f"Title block revision '{revision}' matches the revision table.",
            "revision_control",
            "Align the title block revision with the latest revision table entry." if mismatch else "",
        ))
    elif revision and revision not in INITIAL_REVISIONS:
        results.append(_check(
            "R2", "Revision consistency", "fail", "major",
            f"Title block shows revision '{revision}' but there is no revision table describing the changes.",
            "revision_control", "Add a revision table recording each change, date and approval.",
        ))
    else:
        results.append(_check("R2", "Revision consistency", "not_applicable", "info",
                              "Initial release or no revision information.", "revision_control"))

    # R3: unit consistency
    dimension_text = " ".join(str(d.get("value") or "") + " " + str(d.get("tolerance") or "") for d in dimensions)
    has_inch, has_mm = bool(INCH_PATTERN.search(dimension_text)), bool(MM_PATTERN.search(dimension_text))
    declared = (title_block.get("units") or "").lower()
    conflict = (has_inch and has_mm) or (has_inch and "mm" in declared) or (
        has_mm and ("inch" in declared or declared.strip() in {"in", '"'})
    )
    results.append(_check(
        "R3", "Unit consistency",
        "fail" if conflict else "pass",
        "major",
        f"Dimensions mix unit systems or contradict the declared units ('{title_block.get('units') or 'not stated'}')."
        if conflict else "No unit mixing detected in the dimensions.",
        "dimensioning",
        "Use one unit system throughout and state it in the title block." if conflict else "",
    ))

    # R4: tolerance coverage
    untoleranced = [
        d.get("value") for d in dimensions
        if not (d.get("tolerance") or "").strip() and not TOLERANCE_PATTERN.search(str(d.get("value") or ""))
    ]
    general_tolerance = (title_block.get("general_tolerance") or "").strip()
    if dimensions and untoleranced and not general_tolerance:
        results.append(_check(
            "R4", "Tolerance coverage", "fail", "major",
            f"{len(untoleranced)} of {len(dimensions)} dimensions have no tolerance and there is no general tolerance "
            f"note (e.g. {', '.join(str(v) for v in untoleranced[:5])}).",
            "tolerancing",
            "Add a general tolerance note (e.g. ISO 2768-mK or a title-block tolerance block) or individual tolerances.",
        ))
    else:
        results.append(_check(
            "R4", "Tolerance coverage", "pass" if dimensions else "not_applicable", "info",
            "Every dimension is covered by an individual or general tolerance." if dimensions else "No dimensions found.",
            "tolerancing",
        ))

    # R5: GD&T frames reference defined datums
    # Only datum feature symbols define datums; letters inside feature control frames are references
    defined = {
        str(d.get("letter") if isinstance(d, dict) else d).strip().upper()
        for d in extraction.get("datum_features") or extraction.get("datums") or [] if d
    }
    referenced = {d.strip().upper() for frame in extraction.get("gdt") or [] for d in frame.get("datums") or [] if d}
    undefined = sorted(referenced - defined)
    if referenced:
        results.append(_check(
            "R5", "Datum references",
            "fail" if undefined else "pass",
            "critical",
            f"Feature control frames reference undefined datum(s): {', '.join(undefined)}."
            if undefined else "All referenced datums are defined.",
            "gdt",
            "Add datum feature symbols for each referenced datum or correct the feature control frames." if undefined else "",
        ))
    else:
        results.append(_check("R5", "Datum references", "not_applicable", "info", "No GD&T frames found.", "gdt"))

    # R6: the same feature dimensioned with conflicting values
    by_feature = defaultdict(set)
    for d in dimensions:
        # feature_key names the physical extent consistently across views; fall back to the description
        feature = re.sub(r"\s+", " ", (d.get("feature_key") or d.get("feature") or "").strip().lower())
        if feature and d.get("value"):
            by_feature[feature].add(str(d["value"]).strip())
    conflicts = {feature: sorted(values) for feature, values in by_feature.items() if len(values) > 1}
    results.append(_check(
        "R6", "Conflicting dimensions",
        "fail" if conflicts else "pass",
        "critical",
        "; ".join(f"'{feature}' is dimensioned as {' and '.join(values)}" for feature, values in conflicts.items())
        if conflicts else "No feature is dimensioned with conflicting values.",
        "consistency",
        "Keep one controlling dimension per feature and remove or correct the conflicting one." if conflicts else "",
    ))

    # R7: sheet numbering matches the number of sheets supplied
    sheet = title_block.get("sheet") or ""
    match = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", sheet, re.IGNORECASE)
    if match and int(match.group(2)) != page_count:
        results.append(_check(
            "R7", "Sheet numbering", "fail", "minor",
            f"Title block says sheet '{sheet}' but the file contains {page_count} sheet(s).",
            "title_block", "Correct the sheet count or supply the missing sheets.",
        ))
    else:
        results.append(_check("R7", "Sheet numbering", "pass" if match else "not_applicable", "info",
                              f"Sheet '{sheet}'." if match else "No 'sheet X of Y' found.", "title_block"))

    if cad:
        results.extend(_cad_checks(cad, title_block))
    return results


def _cad_checks(cad: Dict[str, Any], title_block: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []

    # R8: dimension text overridden so it no longer matches the measured geometry
    mismatched = []
    for dim in cad.get("dimensions") or []:
        if not dim.get("text_overridden") or dim.get("measured") is None:
            continue
        numbers = NUMBER_PATTERN.findall(dim.get("displayed_text") or "")
        if numbers and all(abs(float(n) - dim["measured"]) > 0.01 for n in numbers):
            mismatched.append(f"shows '{dim['displayed_text']}' but geometry measures {dim['measured']}")
    results.append(_check(
        "R8", "CAD dimension overrides",
        "fail" if mismatched else "pass",
        "critical",
        "Overridden dimension text hides a geometry mismatch: " + "; ".join(mismatched[:6])
        if mismatched else "Displayed dimension values match the CAD geometry.",
        "dimensioning",
        "Remove the text override or correct the geometry so the model and the drawing agree." if mismatched else "",
    ))

    # R9: CAD file units agree with the title block
    cad_units = cad.get("units") or "unknown"
    declared = (title_block.get("units") or "").lower()
    disagree = cad_units in ("inches", "millimeters") and declared and (
        (cad_units == "inches" and "mm" in declared) or (cad_units == "millimeters" and "inch" in declared)
    )
    results.append(_check(
        "R9", "CAD units vs title block",
        "fail" if disagree else ("pass" if declared else "not_applicable"),
        "major",
        f"The DXF is drawn in {cad_units} but the title block states '{title_block.get('units')}'."
        if disagree else f"DXF units: {cad_units}.",
        "consistency",
        "Set the drawing units ($INSUNITS) to match the title block." if disagree else "",
    ))
    return results


def diff_extractions(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic differences between two extractions (supporting evidence for the compare agent)."""
    def dimension_set(extraction):
        return {
            f"{(d.get('feature') or '').strip()}: {d.get('value')}{(' ' + d['tolerance']) if d.get('tolerance') else ''}"
            for d in extraction.get("dimensions") or []
        }

    title_a, title_b = a.get("title_block") or {}, b.get("title_block") or {}
    title_changes = [
        {"field": key, "a": title_a.get(key), "b": title_b.get(key)}
        for key in sorted(set(title_a) | set(title_b))
        if (title_a.get(key) or None) != (title_b.get(key) or None)
    ]
    dims_a, dims_b = dimension_set(a), dimension_set(b)
    notes_a, notes_b = set(a.get("notes") or []), set(b.get("notes") or [])
    return {
        "title_block_changes": title_changes,
        "dimensions_only_in_a": sorted(dims_a - dims_b),
        "dimensions_only_in_b": sorted(dims_b - dims_a),
        "notes_only_in_a": sorted(notes_a - notes_b),
        "notes_only_in_b": sorted(notes_b - notes_a),
        "revision_table_a": a.get("revision_table") or [],
        "revision_table_b": b.get("revision_table") or [],
    }
