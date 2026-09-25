"""Built-in engineering documentation templates, seeded into the store on first run."""

from typing import Any, Dict, List


def _field(name: str, type_: str = "text", required: bool = True) -> Dict[str, Any]:
    return {"name": name, "type": type_, "required": required}


BUILTIN_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "builtin-ecn",
        "name": "Engineering Change Notice (ECN)",
        "category": "change_management",
        "description": "Documents a change to a released drawing: what changed, why, impact and approvals.",
        "sections": [
            {"title": "Change Identification", "guidance": "Identify the affected drawing and the revision transition.",
             "fields": [_field("ECN number"), _field("Drawing number"), _field("Drawing title"),
                        _field("Current revision"), _field("New revision"), _field("Date", "date")]},
            {"title": "Description of Change", "guidance": "List every change, quoting old and new values. Include zone or view where possible.",
             "fields": [_field("Changes", "table"), _field("Reason for change", "longtext")]},
            {"title": "Impact Assessment", "guidance": "State whether form, fit or function is affected and the effect on stock, tooling, inspection and related documents.",
             "fields": [_field("Form/fit/function impact", "longtext"), _field("Affected documents and parts", "longtext"),
                        _field("Disposition of existing stock", "text", False), _field("Effectivity", "text")]},
            {"title": "Approvals", "guidance": "Engineering, quality and manufacturing sign-off.",
             "fields": [_field("Originator"), _field("Engineering approval"), _field("Quality approval"),
                        _field("Manufacturing approval", "text", False)]},
        ],
    },
    {
        "id": "builtin-fai",
        "name": "First Article Inspection Report (AS9102-style)",
        "category": "quality",
        "description": "Records verification of every drawing characteristic on the first production article.",
        "sections": [
            {"title": "Part Information", "guidance": "Identify the part and drawing exactly as in the title block.",
             "fields": [_field("Part number"), _field("Part name"), _field("Drawing number"), _field("Drawing revision"),
                        _field("Material"), _field("Serial / lot number"), _field("Inspection date", "date")]},
            {"title": "Characteristic Accountability", "guidance": "One row per ballooned characteristic: number, requirement (nominal and tolerance), measured result, pass/fail. Include notes and GD&T requirements.",
             "fields": [_field("Characteristics", "table")]},
            {"title": "Material and Special Processes", "guidance": "Material certifications and special processes (heat treat, plating, NDT).",
             "fields": [_field("Material specification"), _field("Special processes", "longtext", False),
                        _field("Certificates of conformance", "text", False)]},
            {"title": "Result and Approval", "guidance": "Overall result and any nonconformances.",
             "fields": [_field("Overall result"), _field("Nonconformances", "longtext", False),
                        _field("Inspector"), _field("Approval")]},
        ],
    },
    {
        "id": "builtin-review",
        "name": "Drawing Review Record",
        "category": "review",
        "description": "Formal record of a drawing check before release, with findings and disposition.",
        "sections": [
            {"title": "Drawing Under Review", "guidance": "Identify the drawing and the standard it was checked against.",
             "fields": [_field("Drawing number"), _field("Title"), _field("Revision"), _field("Standard applied"),
                        _field("Review date", "date")]},
            {"title": "Findings", "guidance": "List each finding with severity, location and required action.",
             "fields": [_field("Findings", "table"), _field("Summary", "longtext")]},
            {"title": "Disposition", "guidance": "Approved, approved with comments, or rejected, with conditions.",
             "fields": [_field("Verdict"), _field("Conditions for release", "longtext", False),
                        _field("Checker"), _field("Approver", "text", False)]},
        ],
    },
    {
        "id": "builtin-release",
        "name": "Drawing Release & Transmittal Note",
        "category": "release",
        "description": "Transmits released drawings to manufacturing or a supplier.",
        "sections": [
            {"title": "Transmittal", "guidance": "Who is sending what to whom and why.",
             "fields": [_field("Transmittal number"), _field("Date", "date"), _field("From"), _field("To"),
                        _field("Purpose of issue")]},
            {"title": "Documents Released", "guidance": "One row per drawing: number, title, revision, sheets, format.",
             "fields": [_field("Documents", "table")]},
            {"title": "Notes and Acknowledgement", "guidance": "Special instructions and receipt acknowledgement.",
             "fields": [_field("Special instructions", "longtext", False), _field("Released by"),
                        _field("Received by", "text", False)]},
        ],
    },
    {
        "id": "builtin-spec",
        "name": "Component Technical Specification",
        "category": "specification",
        "description": "Technical specification accompanying a part drawing: requirements, materials, testing.",
        "sections": [
            {"title": "Scope", "guidance": "What the component is, where it is used, and the governing drawing.",
             "fields": [_field("Component"), _field("Drawing reference"), _field("Scope", "longtext")]},
            {"title": "Requirements", "guidance": "Dimensional, material, finish and functional requirements drawn from the drawing.",
             "fields": [_field("Material and finish", "longtext"), _field("Critical dimensions and tolerances", "table"),
                        _field("Functional requirements", "longtext", False)]},
            {"title": "Verification", "guidance": "How each requirement is inspected or tested.",
             "fields": [_field("Inspection methods", "table"), _field("Acceptance criteria", "longtext")]},
            {"title": "Referenced Standards", "guidance": "Drawing and tolerancing standards, material specifications.",
             "fields": [_field("Standards", "longtext")]},
        ],
    },
]
