"""Value-level redaction of personal health identifiers before medical text leaves the server.

Column-name filtering (csv_processor) misses identifiers inside free text, e.g. a phone number in clinical notes.
These patterns cover the HIPAA Safe Harbor identifiers that have a recognisable format. Names in free text cannot
be found reliably by pattern, so for regulated data use a de-identified dataset or a locally hosted model
(OPENAI_BASE_URL) as well.
"""

import re
from typing import Tuple

_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

_RULES = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("URL", re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE)),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("MRN", re.compile(r"\b(?:mrn|medical record(?: number| no\.?)?|patient id|member id)\s*[:#]?\s*[A-Z0-9-]{4,}\b",
                       re.IGNORECASE)),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("ZIP", re.compile(r"\b\d{5}-\d{4}\b")),
    # Full dates keep only the year (Safe Harbor allows the year)
    ("DATE", re.compile(r"\b(?:\d{1,2}[/.-]\d{1,2}[/.-](\d{4}|\d{2})|(\d{4})-\d{2}-\d{2})\b")),
    ("DATE", re.compile(rf"\b(?:\d{{1,2}}\s+{_MONTHS}\s+(\d{{4}})|{_MONTHS}\s+\d{{1,2}},?\s+(\d{{4}}))\b", re.IGNORECASE)),
]


def _date_replacement(match: "re.Match") -> str:
    year = next((g for g in match.groups() if g), None)
    return f"[DATE {year}]" if year and len(year) == 4 else "[DATE]"


def redact(text: str) -> Tuple[str, int]:
    """Return the text with identifiers replaced by [TYPE] placeholders, and the number replaced."""
    if not text:
        return text, 0
    total = 0
    for label, pattern in _RULES:
        replacement = _date_replacement if label == "DATE" else f"[{label}]"
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total


def redact_text(text: str) -> str:
    return redact(text)[0]
