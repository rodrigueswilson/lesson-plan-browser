"""SSOT coverage for Grade 2 Science canonical module merge map."""

from tools.db.g2_science_canonical_ssot import (
    g2_science_modules,
    validate_ssot_covers_monolithic_ingest,
)


def test_g2_science_twenty_lessons_six_modules():
    mods = g2_science_modules()
    assert len(mods) == 6
    n = sum(len(m.lessons) for m in mods)
    assert n == 20


def test_ssot_covers_parser_rows_1_to_65_skipping_9():
    validate_ssot_covers_monolithic_ingest(expect_rows=65)
