
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm.json_pre_validation import pre_validate_json
from tools.json_repair import repair_json


def test_samples():
    samples = [
        {
            "name": "Standard WIDA Error",
            "json": '{"wida_mapping": "Target WIDA "levels": 1-6"}',
        },
        {
            "name": "Multiple internal quotes",
            "json": '{"wida_mapping": "Explain "target" with "levels" 2-5"}',
        },
        {
            "name": "Trailing comma",
            "json": '{"key": "value",}',
        },
        {
            "name": "Unquoted property",
            "json": '{key: "value"}',
        },
        {
            "name": "Missing closing brace",
            "json": '{"key": "value"',
        },
        {
            "name": "Assessment stray quote before Time field",
            "json": (
                '{"assessment": {"primary_assessment": '
                '"Rubric: Claim (1), Organization (1). " Time": "30 minutes."}}'
            ),
        },
    ]

    for sample in samples:
        bad_json = sample["json"]

        valid, msg, result = pre_validate_json(bad_json)
        if not valid and result:
            fixed = result.get("fixed_string")
            if fixed:
                try:
                    json.loads(fixed)
                    continue
                except json.JSONDecodeError:
                    pass

        success, repaired, _msg = repair_json(bad_json)
        assert success, f"{sample['name']}: repair_json failed"
        json.loads(repaired)
