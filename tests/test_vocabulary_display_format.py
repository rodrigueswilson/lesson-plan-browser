"""Tests for vocabulary pair display formatting (arrow separator)."""

from backend.utils.vocabulary_display_format import (
    VOCAB_PAIR_SEP,
    format_vocab_markdown_bullet,
    format_vocab_plain_bullet,
)


def test_vocab_pair_sep_is_unicode_arrow():
    assert VOCAB_PAIR_SEP == " \u2192 "
    assert "->" not in VOCAB_PAIR_SEP


def test_format_vocab_markdown_bullet_uses_arrow_not_ascii():
    line = format_vocab_markdown_bullet("water", "água")
    assert "\u2192" in line
    assert "->" not in line
    assert line == "- **water** \u2192 *água*"


def test_format_vocab_plain_bullet_uses_arrow_not_ascii():
    line = format_vocab_plain_bullet("map", "mapa")
    assert "\u2192" in line
    assert "->" not in line
    assert line == "- map \u2192 mapa"
