"""
Tests for lesson_json string sanitization (NULL and control character removal).
"""

import pytest

from backend.llm.sanitize_lesson_json import sanitize_lesson_json_strings


def test_sanitize_removes_null_and_control_chars():
    """Strings with NULL and control characters are sanitized; valid Unicode preserved."""
    lesson = {
        "metadata": {"week_of": "03-09", "teacher_name": "Jos\x00\x01\x02e"},
        "days": {
            "monday": {
                "slots": [
                    {
                        "vocabulary_cognates": [
                            {"english": "evidence", "portuguese": "evid\x00eancia"},
                            {"english": "choice", "portuguese": "escolha"},
                        ],
                        "sentence_frames": [
                            {"english": "This is\x01 a test.", "portuguese": "Isto \x00e9 um teste."},
                        ],
                    }
                ]
            }
        },
    }
    result = sanitize_lesson_json_strings(lesson)
    assert "\x00" not in result["metadata"]["teacher_name"]
    assert result["metadata"]["teacher_name"] == "Jose"
    assert "\x00" not in result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"]
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"] == "evideancia"
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][1]["portuguese"] == "escolha"
    assert "\x01" not in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["english"]
    assert result["days"]["monday"]["slots"][0]["sentence_frames"][0]["english"] == "This is a test."
    assert "\x00" not in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["portuguese"]
    assert result["days"]["monday"]["slots"][0]["sentence_frames"][0]["portuguese"] == "Isto e9 um teste."


def test_sanitize_preserves_valid_unicode_and_apostrophes():
    """Valid Unicode (accented chars) and apostrophes are unchanged."""
    lesson = {
        "metadata": {"teacher_name": "Jos\xe9 Garc\xeda"},
        "days": {
            "monday": {
                "slots": [
                    {
                        "vocabulary_cognates": [
                            {"english": "evidence", "portuguese": "evid\xeancia"},
                            {"english": "character", "portuguese": "car\xe1ter"},
                        ],
                        "sentence_frames": [
                            {"english": "It's a runt.", "portuguese": "Isto \xe9 o menor da ninhada."},
                        ],
                    }
                ]
            }
        },
    }
    result = sanitize_lesson_json_strings(lesson)
    assert result["metadata"]["teacher_name"] == "Jos\xe9 Garc\xeda"
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"] == "evid\xeancia"
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][1]["portuguese"] == "car\xe1ter"
    assert "It's" in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["english"]
    assert "\xe9" in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["portuguese"]


def test_sanitize_preserves_tab_newline_cr():
    """Tab, newline, and carriage return are preserved."""
    lesson = {"metadata": {"note": "line1\t\n\r\nline2"}}
    result = sanitize_lesson_json_strings(lesson)
    assert result["metadata"]["note"] == "line1\t\n\r\nline2"


def test_sanitize_empty_and_none_safe():
    """Empty dict and empty structure are handled without error."""
    assert sanitize_lesson_json_strings({}) == {}
    assert sanitize_lesson_json_strings({"days": {}}) == {"days": {}}
    assert sanitize_lesson_json_strings({"days": {"monday": {"slots": []}}}) == {
        "days": {"monday": {"slots": []}}
    }


def test_sanitize_evidencia_with_null_becomes_evideancia():
    """Regression: evid\\u0000eancia becomes evideancia (NULL removed)."""
    lesson = {
        "days": {
            "monday": {
                "slots": [{"vocabulary_cognates": [{"english": "evidence", "portuguese": "evid\u0000eancia"}]}]
            }
        }
    }
    result = sanitize_lesson_json_strings(lesson)
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"] == "evideancia"
    assert "\u0000" not in result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"]


def test_repair_script_logic_applies_known_fixes():
    """Repair script repair_lesson_json_encoding applies known bad->correct fixes."""
    import sys
    from pathlib import Path
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from repair_wilson_w11_encoding import repair_lesson_json_encoding

    lesson = {
        "days": {
            "monday": {
                "slots": [
                    {
                        "vocabulary_cognates": [
                            {"english": "evidence", "portuguese": "evid\u0000eancia"},
                            {"english": "character", "portuguese": "care1ter"},
                        ],
                        "sentence_frames": [
                            {"english": "Text", "portuguese": "Isto e9 o menor da ninhada porque ___."},
                        ],
                    }
                ]
            }
        }
    }
    result = repair_lesson_json_encoding(lesson)
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][0]["portuguese"] == "evidência"
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"][1]["portuguese"] == "carácter"
    assert "Isto é" in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["portuguese"]
    assert "ninhada" in result["days"]["monday"]["slots"][0]["sentence_frames"][0]["portuguese"]
    assert "\u0000" not in str(result)
