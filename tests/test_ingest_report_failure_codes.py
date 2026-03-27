"""Failure taxonomy helpers on ingest reports."""

import pytest

from tools.scraper.ingest_failure_codes import (
    KNOWN_FAILURE_CODES,
    apply_ingest_failure_code,
    failure_code_for_data_integrity_issue,
)


def _empty_report():
    return {
        "primary_failure_code": None,
        "secondary_failure_codes": [],
        "warnings": [],
    }


def test_apply_primary_then_secondary():
    r = _empty_report()
    apply_ingest_failure_code(r, "ANCHOR_MISS")
    apply_ingest_failure_code(r, "EMPTY_FIELD")
    assert r["primary_failure_code"] == "ANCHOR_MISS"
    assert r["secondary_failure_codes"] == ["EMPTY_FIELD"]


def test_apply_duplicate_secondary_noop():
    r = _empty_report()
    apply_ingest_failure_code(r, "SCHEMA_GATE")
    apply_ingest_failure_code(r, "SCHEMA_GATE")
    assert r["secondary_failure_codes"] == []


def test_unknown_code_raises():
    r = _empty_report()
    with pytest.raises(ValueError):
        apply_ingest_failure_code(r, "NOT_A_CODE")


def test_data_integrity_mapping():
    assert failure_code_for_data_integrity_issue("standards.description may x") == "BOUNDARY_LEAK"
    assert "standards_structured" in "lessons lack standards_structured"
    assert (
        failure_code_for_data_integrity_issue("lessons lack standards_structured")
        == "EMPTY_FIELD"
    )
    assert failure_code_for_data_integrity_issue("narrative_html soft check") == "SCHEMA_GATE"


def test_known_codes_match_taxonomy_v0():
    assert "ANCHOR_MISS" in KNOWN_FAILURE_CODES
    assert "UNKNOWN" in KNOWN_FAILURE_CODES
    assert len(KNOWN_FAILURE_CODES) == 8
