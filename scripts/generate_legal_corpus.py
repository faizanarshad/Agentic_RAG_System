"""
Generate a corpus of fictional legal documents for testing the Legal Synthesis page.

Every document is synthetic: invented parties, courts and case numbers, marked as synthetic
in its header. Output: datasets/legal_corpus/ (.txt, text PDFs, and image-only "scanned" PDFs
that exercise the OCR path) plus manifest.json.

Usage (from the repo root):
    backend/venv/bin/python scripts/generate_legal_corpus.py --count 100
"""

import argparse
import json
import os
import random
import re
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor

import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import OpenAI

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

OUTPUT_DIR = os.path.join(REPO_ROOT, "datasets", "legal_corpus")

# (doc_type, subtype, share of corpus)
DOCUMENT_MIX = [
    ("contract", "Mutual Non-Disclosure Agreement", 8),
    ("contract", "Master Services Agreement", 7),
    ("contract", "SaaS Subscription Agreement", 6),
    ("contract", "Commercial Lease Agreement", 5),
    ("contract", "Employment Agreement", 5),
    ("contract", "Software License Agreement", 4),
    ("contract", "Supply Agreement", 5),
    ("court_filing", "Complaint for Breach of Contract", 6),
    ("court_filing", "Motion to Dismiss", 5),
    ("court_filing", "Motion for Summary Judgment", 4),
    ("court_filing", "Answer and Affirmative Defenses", 5),
    ("case_file", "Court Opinion and Order", 6),
    ("case_file", "Litigation Matter Summary", 5),
    ("case_file", "Settlement Agreement and Release", 4),
    ("compliance_record", "GDPR Data Protection Audit Report", 5),
    ("compliance_record", "HIPAA Security Risk Assessment", 4),
    ("compliance_record", "SOX Internal Controls Review", 3),
    ("compliance_record", "AML/KYC Compliance Review", 3),
    ("compliance_record", "Data Breach Incident Report", 3),
    ("other_legal", "Durable Power of Attorney", 2),
]

RISK_TRAITS = {
    "contract": [
        "uncapped liability for one party", "automatic renewal with a 90-day notice window",
        "no termination for convenience", "one-sided indemnification", "vague payment milestones",
        "broad non-compete lasting 3 years", "IP assignment of all work product including pre-existing IP",
        "balanced, well-drafted terms with a mutual liability cap", "missing data protection clause",
        "late payment penalty of 2% per month",
    ],
    "court_filing": [
        "a response deadline in the next 60 days", "claims for fraud and breach of fiduciary duty",
        "a statute of limitations defense", "a request for injunctive relief", "damages of over $5 million",
    ],
    "case_file": [
        "a judgment against the defendant with damages awarded", "a pending appeal",
        "a confidential settlement with a non-disparagement clause", "a dismissal without prejudice",
    ],
    "compliance_record": [
        "three critical findings with remediation deadlines", "a clean audit with minor observations",
        "overdue remediation from a prior audit", "a potential regulatory fine", "a vendor-risk gap",
    ],
    "other_legal": ["broad financial powers", "a springing power effective on incapacity"],
}

JURISDICTIONS = [
    "State of Delaware", "State of New York", "State of California", "State of Texas",
    "England and Wales", "State of Illinois", "Province of Ontario", "State of Washington",
]

PROMPT = """Write a realistic but entirely FICTIONAL {subtype} ({doc_type}).
Requirements:
- Invent all names (companies, people, courts' case numbers); never use real companies or real people.
- Governing law / jurisdiction: {jurisdiction}.
- Include the following characteristic: {trait}.
- Use realistic legal structure: title, numbered sections or paragraphs, defined terms, dates in 2025-2027,
  monetary amounts, obligations with deadlines, and signature or certification blocks where appropriate.
- Length: 900-1500 words. Plain text only, no markdown.
Begin with the document title on the first line."""

SYNTHETIC_BANNER = "SYNTHETIC DOCUMENT - fictional content generated for testing. Not a real legal document.\n\n"


def build_specs(count: int, seed: int) -> list:
    rng = random.Random(seed)
    weighted = [item for item in DOCUMENT_MIX for _ in range(item[2])]
    specs = []
    for i in range(count):
        doc_type, subtype, _ = weighted[i % len(weighted)] if count >= len(weighted) else rng.choice(weighted)
        specs.append({
            "index": i + 1,
            "doc_type": doc_type,
            "subtype": subtype,
            "jurisdiction": rng.choice(JURISDICTIONS),
            "trait": rng.choice(RISK_TRAITS[doc_type]),
        })
    rng.shuffle(specs)
    # Most as text; some as text PDFs and some as image-only scans to exercise PDF parsing and OCR
    for position, spec in enumerate(specs):
        spec["format"] = "scanned_pdf" if position < 5 else "pdf" if position < 15 else "txt"
    return specs


def generate_text(client: OpenAI, model: str, spec: dict) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT.format(**spec)}],
        temperature=0.9,
        max_tokens=3000,
    )
    return SYNTHETIC_BANNER + (response.choices[0].message.content or "").strip()


def build_text_pdf(text: str) -> "fitz.Document":
    """Lay out wrapped text line by line (insert_textbox silently drops text that overflows)."""
    wrapped = []
    for paragraph in text.splitlines():
        wrapped.extend(textwrap.wrap(paragraph, width=100) or [""])
    pdf = fitz.open()
    lines_per_page = 62
    for start in range(0, len(wrapped), lines_per_page):
        page = pdf.new_page(width=612, height=792)
        y = 60
        for line in wrapped[start:start + lines_per_page]:
            page.insert_text((54, y), line, fontsize=9)
            y += 11
    return pdf


def write_text_pdf(text: str, path: str) -> None:
    pdf = build_text_pdf(text)
    pdf.save(path)
    pdf.close()


def write_scanned_pdf(text: str, path: str) -> None:
    """Render a text PDF to images and rebuild it from those images only (no text layer)."""
    source = build_text_pdf(text)
    scanned = fitz.open()
    for page in source:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        new_page = scanned.new_page(width=page.rect.width, height=page.rect.height)
        # Embed as compressed PNG; inserting the raw pixmap stores it uncompressed (~20 MB per file)
        new_page.insert_image(new_page.rect, stream=pixmap.tobytes("png"))
    scanned.save(path)
    source.close()
    scanned.close()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--model", default=os.getenv("LEGAL_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set (expected in backend/.env)")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    client = OpenAI(max_retries=5)
    specs = build_specs(args.count, args.seed)

    def produce(spec: dict) -> dict:
        extension = "txt" if spec["format"] == "txt" else "pdf"
        filename = f"{spec['index']:03d}_{slugify(spec['subtype'])}.{extension}"
        path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(path):
            text = generate_text(client, args.model, spec)
            if spec["format"] == "txt":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            elif spec["format"] == "pdf":
                write_text_pdf(text, path)
            else:
                write_scanned_pdf(text, path)
        print(f"  {filename}", flush=True)
        return {**spec, "filename": filename}

    print(f"Generating {len(specs)} synthetic legal documents into {OUTPUT_DIR}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        manifest = list(pool.map(produce, specs))

    with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f:
        json.dump(sorted(manifest, key=lambda item: item["index"]), f, indent=2)
    print(f"Done. Wrote {len(manifest)} documents and manifest.json")


if __name__ == "__main__":
    main()
