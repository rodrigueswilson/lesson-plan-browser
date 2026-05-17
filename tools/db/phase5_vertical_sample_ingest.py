"""
Build DOCX from local Docs API JSON snapshots and ingest Phase 5 vertical samples (no OAuth).

Skips Math G4/G5 matrix rows when no *_originals/*.json exists with a matching documentId
(see PHASE_5_SAMPLE_MATRIX.md; those still need Drive export or a new API snapshot).

Usage (repo root):
  python tools/db/phase5_vertical_sample_ingest.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PY = sys.executable
_GDOC = _REPO_ROOT / "tools" / "scraper" / "gdoc_tab_to_docx.py"
_INGEST = _REPO_ROOT / "tools" / "db" / "ingest_wave_unit.py"
_WORK = _REPO_ROOT / "reference_docs" / "scraped" / "phase5_ingest_work"


def _run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(_REPO_ROOT))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def _merge_docx(parts: list[Path], out: Path) -> None:
    """Concatenate DOCX bodies (page break between parts). Requires python-docx."""
    from docx import Document

    merged = Document(str(parts[0]))
    for p in parts[1:]:
        nxt = Document(str(p))
        merged.add_page_break()
        for el in nxt.element.body:
            merged.element.body.append(el)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.save(str(out))


def _ingest_merged_ela_tabs(
    label: str,
    json_path: Path,
    tab_titles: list[str],
    merged_out: Path,
    ingest_argv_tail: list[str],
) -> None:
    """Export each tab to a temp docx, merge (Front Matter + unit tab), then ingest."""
    print(f"\n=== {label} (merged tabs) ===", flush=True)
    tmp_parts: list[Path] = []
    for i, tt in enumerate(tab_titles):
        p = _WORK / f"_tmp_merge_{merged_out.stem}_{i}.docx"
        _run(
            [
                _PY,
                str(_GDOC),
                "--json-path",
                str(json_path),
                "--tab-title",
                tt,
                "--out",
                str(p),
            ]
        )
        tmp_parts.append(p)
    _merge_docx(tmp_parts, merged_out)
    _run([_PY, str(_INGEST), *ingest_argv_tail, "--docx", str(merged_out)])


def main() -> int:
    _WORK.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, list[str], list[str]]] = [
        (
            "ELA G4 compendium (Grade 4 Unit 1 tab)",
            [
                _PY,
                str(_GDOC),
                "--json-path",
                str(
                    _REPO_ROOT
                    / "reference_docs/scraped/K_8_ELA_Pacing_Guide_SY_25_26/Tab_1/04___Fourth_Grade_Unit_Description_and_Summary_of_Key_Learning/originals/04___Fourth_Grade_Unit_Description_and_Summary_of_Key_Learning.json"
                ),
                "--tab-title",
                "Grade 4 Unit 1",
                "--out",
                str(_WORK / "ELA_4_Grade4_Unit1.docx"),
            ],
            [
                _PY,
                str(_INGEST),
                "--unit-id",
                "ELA_4_compendium_sample",
                "--grade",
                "4",
                "--subject",
                "ELA",
                "--unit-number",
                "1",
                "--title",
                "Grade 4 ELA: Unit 1 (from compendium tab)",
                "--doc-id",
                "1jeeDNSMhT4k_-kMzR65EszWgKkCznHOn0KMVtdp4ofs",
                "--docx",
                str(_WORK / "ELA_4_Grade4_Unit1.docx"),
                "--parser-version",
                "phase5@local_json_tab",
            ],
        ),
        (
            "ELA G5 compendium (Grade 5 Unit 1 tab)",
            [
                _PY,
                str(_GDOC),
                "--json-path",
                str(
                    _REPO_ROOT
                    / "reference_docs/scraped/K_8_ELA_Pacing_Guide_SY_25_26/Tab_1/05___Fifth_Grade_Unit_Description_and_Summary_of_Key_Learning/originals/05___Fifth_Grade_Unit_Description_and_Summary_of_Key_Learning.json"
                ),
                "--tab-title",
                "Grade 5 Unit 1",
                "--out",
                str(_WORK / "ELA_5_Grade5_Unit1.docx"),
            ],
            [
                _PY,
                str(_INGEST),
                "--unit-id",
                "ELA_5_compendium_sample",
                "--grade",
                "5",
                "--subject",
                "ELA",
                "--unit-number",
                "1",
                "--title",
                "Grade 5 ELA: Unit 1 (from compendium tab)",
                "--doc-id",
                "1vRv3y0geSVJBGOHfgtplWNygz4nfwSE4RwAM1GbZQWY",
                "--docx",
                str(_WORK / "ELA_5_Grade5_Unit1.docx"),
                "--parser-version",
                "phase5@local_json_tab",
            ],
        ),
        (
            "Math G8 Unit 8 (PythagoreanTheorem)",
            [
                _PY,
                str(_GDOC),
                "--json-path",
                str(
                    _REPO_ROOT
                    / "reference_docs/scraped/Unit_1__Adding__Subtracting_and_Working_With_Data/Tab_1/Unit_1__Adding__Subtracting_and_Working_With_Data/Tab_1/Unit_3__Measuring_Length/Tab_1/Unit_3__Adding_and_Subtracting_Within_20/Tab_1/Unit_5__Arithmetic_in_Base_Ten/Unit_5__Arithmetic_in_Base_Ten/Unit_5__Rational_Number_Arithmetic/Unit_5__Rational_Number_Arithmetic/Unit_7__Exponents_and_Scientific_Notation/Unit_7__Exponents_and_Scientific_Notation/Unit_1__Area_and_Surface_Area/Unit_1__Area_and_Surface_Area/Unit_6__More_Decimal_and_Fraction_Operations/Tab_1/Unit_5__Place_Value_Patterns_and_Decimal_Operations/Tab_1/Unit_7__Rational_Numbers/Unit_7__Rational_Numbers/Unit_7__Shapes_on_the_Coordinate_Plane/Tab_1/Unit_3__Unit_Rates_and_Percentages/Unit_3__Unit_Rates_and_Percentages/Unit_2__Introducing_Proportional_Relationships/Unit_2__Introducing_Proportional_Relationships/Unit_3__Linear_Relationships/Unit_3__Linear_Relationships/Unit_5__Functions_and_Volume/Unit_5__Functions_and_Volume/Unit_2__Linear_Equations_and_Systems/Tab_1/Unit_4__Linear_Equations_and_Linear_Systems/Unit_4__Linear_Equations_and_Linear_Systems/Unit_4__Linear_Inequalities_and_Systems/Tab_1/Unit_8__Pythagorean_Theorem_and_Irrational_Numbers/originals/Unit_8__Pythagorean_Theorem_and_Irrational_Numbers.json"
                ),
                "--tab-id",
                "t.0",
                "--out",
                str(_WORK / "Math_8_U8.docx"),
            ],
            [
                _PY,
                str(_INGEST),
                "--unit-id",
                "Math_8_U8_sample",
                "--grade",
                "8",
                "--subject",
                "Math",
                "--unit-number",
                "8",
                "--title",
                "Unit 8: Pythagorean Theorem and Irrational Numbers",
                "--doc-id",
                "1BBR66X-WrHrPdHs8OFUhFtEaCQ-uvQeVIDQaJwes1GU",
                "--docx",
                str(_WORK / "Math_8_U8.docx"),
                "--parser-version",
                "phase5@local_json_tab",
            ],
        ),
    ]

    for label, gdoc_cmd, ingest_cmd in jobs:
        print(f"\n=== {label} ===", flush=True)
        _run(gdoc_cmd)
        _run(ingest_cmd)

    g6_json = (
        _REPO_ROOT
        / "reference_docs/scraped/K_8_ELA_Pacing_Guide_SY_25_26/Tab_1/Grade_6_ELA_Unit_1_The_Hero_s_Journey__Percy_Jackson/originals/Grade_6_ELA_Unit_1_The_Hero_s_Journey__Percy_Jackson.json"
    )
    _ingest_merged_ela_tabs(
        "ELA G6 Unit 1 (Percy / Hero journey)",
        g6_json,
        ["Front Matter", "Grade 6 Unit 1"],
        _WORK / "ELA_6_merged.docx",
        [
            "--unit-id",
            "ELA_6_U1_sample",
            "--grade",
            "6",
            "--subject",
            "ELA",
            "--unit-number",
            "1",
            "--title",
            "Grade 6 ELA Unit 1: The Hero's Journey (Percy Jackson)",
            "--doc-id",
            "1iVNkWwfzOsu9p7zJsCHqrlWFFQ-p33GsmjqUXP1nFfY",
            "--parser-version",
            "phase5@local_json_merged_tabs",
        ],
    )
    g8_json = (
        _REPO_ROOT
        / "reference_docs/scraped/K_8_ELA_Pacing_Guide_SY_25_26/Tab_1/Grade_8_ELA_Unit_1_The_Road_to_Success__Make_Lemonade/originals/Grade_8_ELA_Unit_1_The_Road_to_Success__Make_Lemonade.json"
    )
    _ingest_merged_ela_tabs(
        "ELA G8 Unit 1 (Make Lemonade)",
        g8_json,
        ["Front Matter", "Grade 8 Unit 1"],
        _WORK / "ELA_8_merged.docx",
        [
            "--unit-id",
            "ELA_8_U1_sample",
            "--grade",
            "8",
            "--subject",
            "ELA",
            "--unit-number",
            "1",
            "--title",
            "Grade 8 ELA Unit 1: The Road to Success: Make Lemonade",
            "--doc-id",
            "1ordR_c50CNntMjqavOQR9JHgfzklI2CUprYDjgfOdOU",
            "--parser-version",
            "phase5@local_json_merged_tabs",
        ],
    )

    print(
        "\nDone. Math G4/G5 matrix rows (1aMiqyg… / 1S9fRcM1…): no local Docs API JSON "
        "with matching documentId; ingest with OAuth + ingest_wave_unit when ready.\n",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
