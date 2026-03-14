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
                            {"english": "Use word", "portuguese": "Este trae7o e a conspirae7e3o."},
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
    assert "Este traço" in result["days"]["monday"]["slots"][0]["sentence_frames"][1]["portuguese"]
    assert "conspiração" in result["days"]["monday"]["slots"][0]["sentence_frames"][1]["portuguese"]
    assert "\u0000" not in str(result)


def test_repair_script_does_not_modify_english_fields():
    """Repair applies Portuguese fixes only to portuguese/bilingual_bridge/family_connection; English unchanged."""
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
                        "objective": {
                            "content_objective": "Students will analyze evidence.",
                            "student_goal": "I will use evidence and practice reading and speaking (reading, speaking).",
                            "wida_objective": "ELD-SS.6-8.Explain.Reading/Writing.",
                        },
                        "vocabulary_cognates": [
                            {"english": "evidence", "portuguese": "evidência"},
                            {"english": "reading", "portuguese": "leitura"},
                        ],
                        "sentence_frames": [
                            {"english": "I see ___", "portuguese": "Eu vejo ___"},
                        ],
                        "anticipatory_set": {
                            "original_content": "Preview the lesson.",
                            "bilingual_bridge": "Discuss: Como as leis ajudam?",
                        },
                        "homework": {
                            "original_content": "Read page 5.",
                            "family_connection": "Pergunte em casa: Como foi o dia?",
                        },
                    }
                ]
            }
        }
    }
    result = repair_lesson_json_encoding(lesson)
    slot = result["days"]["monday"]["slots"][0]
    assert slot["objective"]["student_goal"] == "I will use evidence and practice reading and speaking (reading, speaking)."
    assert slot["vocabulary_cognates"][0]["english"] == "evidence"
    assert slot["vocabulary_cognates"][1]["english"] == "reading"
    assert slot["sentence_frames"][0]["english"] == "I see ___"
    assert slot["anticipatory_set"]["original_content"] == "Preview the lesson."
    assert slot["homework"]["original_content"] == "Read page 5."
    assert slot["vocabulary_cognates"][0]["portuguese"] == "evidência"
    assert slot["sentence_frames"][0]["portuguese"] == "Eu vejo ___"
    assert "Como" in slot["anticipatory_set"]["bilingual_bridge"]
    assert "Pergunte" in slot["homework"]["family_connection"]


def test_repair_script_reverts_ea_in_english_fields():
    """Repair reverts accidental ê in English (hear, learns, fear) in all string fields."""
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
                        "sentence_frames": [
                            {"english": "I see ___, I hêr ___, I feel ___.", "portuguese": "Eu vejo ___."},
                        ],
                        "objective": {
                            "student_goal": "When Wilbur lêrns his fate, he feels ___ (reading).",
                            "wida_objective": "The narrative demonstrates Wilburs fêr because ___.",
                        },
                    }
                ]
            }
        }
    }
    result = repair_lesson_json_encoding(lesson)
    slot = result["days"]["monday"]["slots"][0]
    assert "I hear ___" in slot["sentence_frames"][0]["english"]
    assert "hêr" not in slot["sentence_frames"][0]["english"]
    assert "learns" in slot["objective"]["student_goal"]
    assert "lêrns" not in slot["objective"]["student_goal"]
    assert "fear" in slot["objective"]["wida_objective"]
    assert "fêr" not in slot["objective"]["wida_objective"]


def test_repair_script_fixes_english_hears_reacts_and_portuguese_reage_ve():
    """Repair fixes hêrs->hears, rêcts->reacts (English) and rêge->reage, vea->vê (Portuguese only)."""
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
                        "objective": {
                            "student_goal": "I will describe what Wilbur sees and hêrs (reading).",
                            "wida_objective": "Explain how he rêcts (ELD-LA.Explain.Reacts).",
                        },
                        "sentence_frames": [
                            {
                                "english": "I see ___, I hêr ___, I feel ___.",
                                "portuguese": "Eu vou descrever o que Wilbur vea e ouve e explicar como ele rêge.",
                            },
                        ],
                    }
                ]
            }
        }
    }
    result = repair_lesson_json_encoding(lesson)
    slot = result["days"]["monday"]["slots"][0]
    assert "hears" in slot["objective"]["student_goal"]
    assert "hêrs" not in slot["objective"]["student_goal"]
    assert "reacts" in slot["objective"]["wida_objective"]
    assert "rêcts" not in slot["objective"]["wida_objective"]
    assert slot["sentence_frames"][0]["english"] == "I see ___, I hear ___, I feel ___."
    assert "vê" in slot["sentence_frames"][0]["portuguese"]
    assert "vea" not in slot["sentence_frames"][0]["portuguese"]
    assert "reage" in slot["sentence_frames"][0]["portuguese"]
    assert "rêge" not in slot["sentence_frames"][0]["portuguese"]


def test_repair_script_fixes_mio_reacao_reding():
    """Repair fixes Rêding->reading (EN), rêção->reação (PT). mío->medo applied in script for DB repair."""
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
                        "objective": {"student_goal": "I will practice Rêding (reading)."},
                        "sentence_frames": [
                            {
                                "english": "I see ___",
                                "portuguese": "Ele sente m\u00edo e depois r\u00ea\u00e7\u00e3o.",
                            },
                        ],
                    }
                ]
            }
        }
    }
    result = repair_lesson_json_encoding(lesson)
    slot = result["days"]["monday"]["slots"][0]
    assert "reading" in slot["objective"]["student_goal"]
    assert "Rêding" not in slot["objective"]["student_goal"]
    pt = slot["sentence_frames"][0]["portuguese"]
    assert "reação" in pt
    assert "rêção" not in pt
