"""Regression: category JSON ids, _index.json, and WIDA keys stay aligned."""

import pytest
import subprocess

pytestmark = pytest.mark.unit
import sys
from pathlib import Path


def test_verify_strategy_pack_ssot_script_exits_zero():
    root = Path(__file__).resolve().parent.parent
    script = root / "tools" / "verify_strategy_pack_ssot.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
