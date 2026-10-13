"""Manual STROBE / CONSORT reporting-checklist assessments.

The input represents reviewer judgments; no manuscript NLP or methodological quality
inference is performed. The catalogue lives in web/checklists.json, shared with the UI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CATALOGUE = Path(__file__).resolve().parent / "web" / "checklists.json"
STATUSES = frozenset({"unassessed", "reported", "partial", "missing", "na"})
FORMAT = "reporting-checklist-review-v1"


def load_catalogue() -> dict[str, Any]:
    """Load the same versioned item catalogue consumed by the static application."""
    with CATALOGUE.open(encoding="utf-8") as handle:
        return json.load(handle)


def blank_review(guideline: str, manuscript: str = "") -> dict[str, Any]:
    catalogue = load_catalogue()
    if guideline not in catalogue:
        raise ValueError(f"Unknown guideline: {guideline}")
    if not isinstance(manuscript, str) or len(manuscript) > 120:
        raise ValueError("Manuscript label must be at most 120 characters")
    framework = catalogue[guideline]
    return {
        "format": FORMAT,
        "guideline": guideline,
        "version": framework["version"],
        "manuscript": manuscript,
        "items": [
            {"id": spec["id"], "title": spec["title"], "status": "unassessed", "location": "", "notes": ""}
            for spec in framework["items"]
        ],
    }


def summarize_review(review: dict[str, Any]) -> dict[str, Any]:
    """Validate a review and count statuses; do not claim a quality/compliance score."""
    if not isinstance(review, dict) or review.get("format") != FORMAT:
        raise ValueError("Unsupported review format")
    catalogue = load_catalogue()
    guideline = review.get("guideline")
    if not isinstance(guideline, str) or guideline not in catalogue:
        raise ValueError("Unknown guideline")
    framework = catalogue[guideline]
    if review.get("version") != framework["version"]:
        raise ValueError("Guideline version mismatch")
    label = review.get("manuscript")
    if not isinstance(label, str) or len(label) > 120:
        raise ValueError("Invalid manuscript label")
    items = review.get("items")
    expected = {spec["id"] for spec in framework["items"]}
    if not isinstance(items, list) or len(items) != len(expected):
        raise ValueError("Expected one entry per checklist item")
    seen: set[str] = set()
    counts = {key: 0 for key in ("reported", "partial", "missing", "na", "unassessed")}
    na_without_rationale: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Invalid item")
        key = item.get("id")
        if not isinstance(key, str) or key not in expected or key in seen:
            raise ValueError("Unknown or duplicate checklist item")
        seen.add(key)
        status = item.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError(f"Invalid item status for {key}")
        for field, maximum in (("location", 160), ("notes", 2000)):
            value = item.get(field)
            if not isinstance(value, str) or len(value) > maximum:
                raise ValueError(f"Invalid {field} for {key}")
        counts[status] += 1
        if status == "na" and not item["notes"].strip():
            na_without_rationale.append(key)
    total = len(expected)
    return {
        "guideline": guideline,
        "version": framework["version"],
        "manuscript": label,
        "total_items": total,
        "assessed_items": total - counts["unassessed"],
        "applicable_items_reviewed": counts["reported"] + counts["partial"] + counts["missing"],
        "counts": counts,
        "na_without_rationale": na_without_rationale,
        "interpretation": "Descriptive reviewer judgments only; not a methodological quality or risk-of-bias score.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual STROBE / CONSORT reporting checklist review")
    subparsers = parser.add_subparsers(dest="command", required=True)
    blank = subparsers.add_parser("template", help="Write an editable review template")
    blank.add_argument("--guideline", choices=["strobe", "consort"], required=True)
    blank.add_argument("--manuscript", default="")
    blank.add_argument("--output", required=True, type=Path)
    summ = subparsers.add_parser("summary", help="Validate and summarize an exported review")
    summ.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            result = blank_review(args.guideline, args.manuscript)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"Template written: {args.output}")
        else:
            review = json.loads(args.input.read_text(encoding="utf-8"))
            print(json.dumps(summarize_review(review), indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
