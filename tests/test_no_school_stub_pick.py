"""Day stub selection for no_school_days overlay (assessment vs calendar closure)."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.batch_processor_pkg.no_school_stub_pick import day_stub_for_no_school_list_entry
from tools.docx_parser.instructional_day import (
    NON_INSTRUCTIONAL_UNIT_LESSON,
    _day_text_for_instructional_inference,
    infer_instructional_weekdays_from_table_content,
)
from tools.docx_parser.no_school import is_day_no_school


def test_primary_notes_no_school_does_not_flag_calendar_closure():
    path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "instructional_inference"
        / "no_school_in_notes_only.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    mon = data["table_content"]["Monday"]
    primary = _day_text_for_instructional_inference(mon)
    assert "Main idea" in primary
    assert "No School" in " ".join(str(v) for v in mon.values())
    assert not is_day_no_school(primary)


def test_assessment_primary_gets_non_instructional_stub():
    processor = MagicMock()
    processor._no_school_day_stub.return_value = {"unit_lesson": "No School"}
    table = {"Monday": {"Unit/Lesson": "NJ-SLA reading block", "Notes": ""}}
    st = day_stub_for_no_school_list_entry(processor, "Monday", table)
    assert st["unit_lesson"] == NON_INSTRUCTIONAL_UNIT_LESSON


def test_calendar_closure_primary_keeps_no_school_stub():
    processor = MagicMock()
    processor._no_school_day_stub.return_value = {"unit_lesson": "No School"}
    table = {
        "Monday": {"Unit/Lesson": "No School — holiday", "Notes": ""},
    }
    st = day_stub_for_no_school_list_entry(processor, "Monday", table)
    assert st["unit_lesson"] == "No School"
    processor._no_school_day_stub.assert_called()


@pytest.mark.unit
def test_infer_week_not_cleared_by_non_instructional_boilerplate_in_notes():
    path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "instructional_inference"
        / "boilerplate_non_instructional_in_cells.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    tc = data["table_content"]
    assert infer_instructional_weekdays_from_table_content(tc) == [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
    ]
