"""
Frozen JSON checks for LLM-shaped lesson output (strategy pack ids).

Set RUN_LLM_GOLDEN=1 to enable. No live API calls.
"""

import json
import os
from pathlib import Path

import pytest

from backend.llm.strategy_pack_context import validate_ell_support_strategy_ids

_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_FIXTURES = sorted(
    (_ROOT / "tests/fixtures/llm_golden").glob("*.json"),
    key=lambda p: p.name,
)


@pytest.mark.skipif(
    os.environ.get("RUN_LLM_GOLDEN") != "1",
    reason="Set RUN_LLM_GOLDEN=1 to run golden JSON regression checks",
)
@pytest.mark.parametrize("fixture_path", _GOLDEN_FIXTURES, ids=lambda p: p.stem)
def test_golden_ell_support_strategy_ids(fixture_path: Path):
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    ok, err, bad = validate_ell_support_strategy_ids(data)
    assert ok, f"{fixture_path.name}: {err} unknown={bad}"

    for day_name, day in (data.get("days") or {}).items():
        if not isinstance(day, dict):
            continue
        ti = day.get("tailored_instruction")
        if not isinstance(ti, dict):
            continue
        ell = ti.get("ell_support")
        if not isinstance(ell, list):
            continue
        for item in ell:
            assert isinstance(item, dict)
            assert "implementation" in item
            assert len(str(item.get("implementation") or "")) > 0, (
                f"{fixture_path.name} {day_name}: empty implementation"
            )
