"""Score the legal and engineering agents against the synthetic datasets' answer keys.

Model output varies between runs and model versions; this turns "does it still work?" into numbers you can
track. It reads results already stored by the app (no API cost), or analyses the samples first with --run.

    backend/venv/bin/python scripts/evaluate_agents.py                  # score stored results
    backend/venv/bin/python scripts/evaluate_agents.py --run            # (re)analyse samples first (uses the API)
    backend/venv/bin/python scripts/evaluate_agents.py --json report.json --min-score 0.8

Exits with status 1 when any score is below --min-score, so it can gate a release or a model upgrade.
"""

import argparse
import json
import os
import re
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(REPO_ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

LEGAL_DIR = os.path.join(REPO_ROOT, "datasets", "legal_corpus")
ENGINEERING_DIR = os.path.join(REPO_ROOT, "datasets", "engineering_samples")

# Seeded traits that should push a document's risk up, or keep it down
HIGH_TRAITS = ("uncapped liability", "one-sided indemnification", "damages of over", "fraud", "three critical",
               "regulatory fine", "overdue remediation", "judgment against", "IP assignment of all")
LOW_TRAITS = ("balanced, well-drafted", "clean audit")

def NUM(value: str) -> str:
    """A number not embedded in a longer number (\\b fails after symbols such as the diameter sign)."""
    return rf"(?<![\d.]){value}(?![\d])"


# Each expected engineering issue: every pattern must appear in one finding (or in the comparison output)
ENGINEERING_EXPECTED = {
    "bracket_EP-1001_revA.pdf": [
        ("Material missing from title block", [r"material"]),
        ("Overall length 120 vs 125", [NUM("120"), NUM("125")]),
        ("Undefined datum C", [r"datum\s*[\"'‘“]?C\b"]),
        ("Inch value on a millimetre drawing", [r"inch|\bin\b|R0\.12"]),
        ("Checked / approved empty", [r"checked|approv"]),
    ],
    "comparison": [
        ("Hole diameter 8.5 -> 9.0 unrecorded", [r"8\.5", NUM(r"9(\.0)?")]),
        ("Thickness 10 -> 12 unrecorded", [NUM("10"), NUM("12")]),
        ("Material AL 6061-T6 added", [r"6061"]),
        ("Revision A -> B", [r"revision|\brev\b"]),
    ],
    "flange_FL-2040.dxf": [
        ("Bore text 50 vs geometry 48", [NUM("50"), NUM("48")]),
        ("Units: inches vs millimetres", [r"inch", r"mill|\bmm\b"]),
    ],
}


def _norm(value) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(value or "").lower()).replace("  ", " ").strip()


def evaluate_legal(run: bool) -> dict:
    from services.legal_store import LegalStore

    manifest = {item["filename"]: item for item in json.load(open(os.path.join(LEGAL_DIR, "manifest.json")))}
    store = LegalStore()
    if run:
        from services.legal_agent_service import LegalAgentService
        service = LegalAgentService()
        files = [(name, open(os.path.join(LEGAL_DIR, name), "rb").read()) for name in manifest]
        service.ingest_files(files)
        print(f"Queued {len(files)} legal documents; waiting for analysis…")
        while store.status_counts().get("queued", 0) + store.status_counts().get("processing", 0):
            time.sleep(10)

    # Latest completed analysis per filename
    latest = {}
    for doc in store.list_documents(status="completed", limit=100000)["documents"]:
        if doc["filename"] in manifest and doc["filename"] not in latest:
            latest[doc["filename"]] = doc
    if not latest:
        return {"evaluated": 0, "note": "No analysed corpus documents found; run with --run"}

    type_hits = law_hits = law_total = risk_hits = risk_total = 0
    misses = []
    for filename, doc in latest.items():
        expected = manifest[filename]
        if doc.get("doc_type") == expected["doc_type"]:
            type_hits += 1
        else:
            misses.append(f"{filename}: type {doc.get('doc_type')} (expected {expected['doc_type']})")
        if doc.get("governing_law"):
            law_total += 1
            place = _norm(expected["jurisdiction"]).replace("state of ", "").replace("province of ", "")
            if place in _norm(doc["governing_law"]):
                law_hits += 1
            else:
                misses.append(f"{filename}: governing law '{doc['governing_law']}' (expected {expected['jurisdiction']})")
        trait = expected["trait"]
        if any(t.lower() in trait.lower() for t in HIGH_TRAITS):
            risk_total += 1
            ok = doc.get("overall_risk") in ("medium", "high")
        elif any(t.lower() in trait.lower() for t in LOW_TRAITS):
            risk_total += 1
            ok = doc.get("overall_risk") in ("low", "medium")
        else:
            continue
        risk_hits += ok
        if not ok:
            misses.append(f"{filename}: risk {doc.get('overall_risk')} for trait '{trait}'")

    return {
        "evaluated": len(latest),
        "classification_accuracy": round(type_hits / len(latest), 3),
        "governing_law_accuracy": round(law_hits / law_total, 3) if law_total else None,
        "risk_direction_accuracy": round(risk_hits / risk_total, 3) if risk_total else None,
        "misses": misses[:40],
    }


def _matched(patterns, texts) -> bool:
    return any(all(re.search(p, text, re.IGNORECASE) for p in patterns) for text in texts)


def evaluate_engineering(run: bool) -> dict:
    from services.engineering_agent_service import EngineeringAgentService

    service = EngineeringAgentService()
    store = service.store
    if run:
        for name in ("bracket_EP-1001_revA.pdf", "bracket_EP-1001_revB.pdf", "flange_FL-2040.dxf"):
            print(f"Reviewing {name}…")
            service.review_upload(name, open(os.path.join(ENGINEERING_DIR, name), "rb").read(), "ISO")

    latest = {}
    for drawing in store.list_drawings():  # newest first
        if drawing["status"] == "completed" or drawing.get("verdict"):
            latest.setdefault(drawing["filename"], drawing["id"])
    if run and "bracket_EP-1001_revA.pdf" in latest and "bracket_EP-1001_revB.pdf" in latest:
        print("Comparing revA -> revB…")
        service.compare(latest["bracket_EP-1001_revA.pdf"], latest["bracket_EP-1001_revB.pdf"])

    results, found, total = {}, 0, 0
    for key, expected in ENGINEERING_EXPECTED.items():
        if key == "comparison":
            ids = (latest.get("bracket_EP-1001_revA.pdf"), latest.get("bracket_EP-1001_revB.pdf"))
            comparison = next((c for c in store.list_comparisons() if (c["a_id"], c["b_id"]) == ids), None)
            texts = [json.dumps(item, ensure_ascii=False) for item in (comparison or {}).get("result", {}).get("changes", [])]
            texts += [json.dumps((comparison or {}).get("result", {}).get("revision_control", ""), ensure_ascii=False)]
            available = comparison is not None
        else:
            drawing = store.get_drawing(latest[key]) if key in latest else None
            findings = ((drawing or {}).get("review") or {}).get("findings") or []
            texts = [" ".join(str(f.get(k, "")) for k in ("title", "description", "location")) for f in findings]
            available = drawing is not None
        if not available:
            results[key] = {"note": "not reviewed yet; run with --run"}
            continue
        detail = {label: _matched(patterns, texts) for label, patterns in expected}
        found += sum(detail.values())
        total += len(detail)
        results[key] = detail

    return {"issue_recall": round(found / total, 3) if total else None, "found": found, "expected": total,
            "detail": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="store_true", help="analyse the sample datasets first (uses the API)")
    parser.add_argument("--only", choices=("legal", "engineering"))
    parser.add_argument("--json", help="write the report to this file")
    parser.add_argument("--min-score", type=float, default=0.8, help="fail when any score is below this")
    args = parser.parse_args()

    report = {}
    if args.only in (None, "legal"):
        report["legal"] = evaluate_legal(args.run)
    if args.only in (None, "engineering"):
        report["engineering"] = evaluate_engineering(args.run)

    print(json.dumps(report, indent=2))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)

    scores = {f"{area}.{k}": v for area, values in report.items() for k, v in values.items()
              if isinstance(v, float)}
    failing = {k: v for k, v in scores.items() if v < args.min_score}
    if failing:
        print(f"\nBelow {args.min_score}: " + ", ".join(f"{k}={v}" for k, v in failing.items()))
        sys.exit(1)
    print(f"\nAll scores ≥ {args.min_score}: " + ", ".join(f"{k}={v}" for k, v in scores.items()))


if __name__ == "__main__":
    main()
