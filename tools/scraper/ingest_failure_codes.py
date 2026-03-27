"""Failure taxonomy helpers for ingest reports (no docx / subject_config imports)."""

from __future__ import annotations

from typing import Any, Dict, List

# Keep in sync with docs/curriculum/FAILURE_TAXONOMY.md (v0 codes).
KNOWN_FAILURE_CODES: frozenset = frozenset(
    {
        "ANCHOR_MISS",
        "TABLE_GRID",
        "BOUNDARY_LEAK",
        "EXPORT_LOSS",
        "LINK_SKIP",
        "SCHEMA_GATE",
        "EMPTY_FIELD",
        "UNKNOWN",
    }
)


def apply_ingest_failure_code(report: Dict[str, Any], code: str) -> None:
    """Attach one taxonomy code: first sets primary_failure_code; further distinct codes go to secondaries."""
    if code not in KNOWN_FAILURE_CODES:
        raise ValueError(f"Unknown failure code {code!r}; see docs/curriculum/FAILURE_TAXONOMY.md")
    if report.get("primary_failure_code") is None:
        report["primary_failure_code"] = code
        return
    if report["primary_failure_code"] == code:
        return
    secondaries: List[str] = report.setdefault("secondary_failure_codes", [])
    if code not in secondaries:
        secondaries.append(code)


def failure_code_for_data_integrity_issue(line: str) -> str:
    """Map a line from verify_curriculum_data_integrity() to a taxonomy code."""
    if "procedure heading noise" in line or "standards.description" in line:
        return "BOUNDARY_LEAK"
    if "standards_structured" in line:
        return "EMPTY_FIELD"
    return "SCHEMA_GATE"
