"""Choose No School vs Non-instructional (assessment) day stub using primary table column text."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from tools.batch_processor_pkg.helpers import non_instructional_day_stub
from tools.docx_parser.instructional_day import (
    _day_text_for_instructional_inference,
    is_testing_or_assessment_day,
)
from tools.docx_parser.no_school import is_day_no_school


def day_stub_for_no_school_list_entry(
    processor: Any,
    day_key: str,
    table_content: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Pick stub when parser flagged this weekday in ``no_school_days``.

    Uses the same primary-column text as instructional inference so Notes cells
    cannot solo-trigger calendar closure. Assessment/testing primary lines get
    ``non_instructional_day_stub``; true calendar closure keeps No School.
    """
    if not table_content:
        return processor._no_school_day_stub()
    day_lower = day_key.lower().strip()
    day_content: Any = None
    for k, v in table_content.items():
        if str(k).lower().strip() == day_lower:
            day_content = v
            break
    if day_content is None:
        return processor._no_school_day_stub()
    primary = _day_text_for_instructional_inference(day_content)
    pt = (primary or "").strip()
    if pt and is_testing_or_assessment_day(pt) and not is_day_no_school(pt):
        return deepcopy(non_instructional_day_stub())
    return processor._no_school_day_stub()
