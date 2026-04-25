"""
Grade 2 Science canonical curriculum shape (writer / ADR-003 appendix).

The monolithic DOCX ingest produces ~65 parser lesson rows under one unit. This SSOT
describes **6 modules** and **20 teaching lessons** with irregular lesson counts per
module, and records which parser ``lesson_number`` rows (1..65) merge into each
canonical lesson.

Writer **day bands** stay inside ``science_li_sc_day_structured`` / relational segments
after merge (**concatenated in source order** from each parser ``lesson_number`` row listed
in ``source_parser_lesson_numbers``).

**Important:** Each monolithic parser row carries its own learning-intention grid, so **day
labels (e.g. "Day 1", "Days 2&3") often restart** at every concatenated block. The relational
table then has **more segment rows** than ``writer_day_count`` in this SSOT when a canonical
lesson merges multiple parser rows. That is expected for the current merge strategy, not
duplicate keys: ``science_lesson_day_segments`` enforces ``UNIQUE(lesson_id, segment_index)``.
Pedagogical "instructional days" for pacing remain the appendix / ``writer_day_count`` figures;
the segment list is a **loss-preserving stitch** of parser output until a future pass
deduplicates, renumbers, or tags segments by source row.

See: docs/scrapers/ADR-003-grade2-science-cluster-ssot-and-daily-projection.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class G2ScienceCanonicalLessonSpec:
    """One of 20 writer lessons."""

    lesson_in_module: int
    title: str
    writer_day_count: int
    source_parser_lesson_numbers: Tuple[int, ...]


@dataclass(frozen=True)
class G2ScienceModuleSpec:
    module_number: int
    unit_id: str
    unit_title: str
    lessons: Tuple[G2ScienceCanonicalLessonSpec, ...]


# Parser row 9 is a second "Solids" block tied to doc lesson 2; treat as duplicate of row 6.
_G2_SCIENCE_MODULES: Tuple[G2ScienceModuleSpec, ...] = (
    G2ScienceModuleSpec(
        module_number=1,
        unit_id="Science_2_Mod1_PropertiesOfMatter",
        unit_title="Grade 2 Science — Module 1: Properties of Matter",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Describe Matter",
                10,
                (1, 2, 3, 4, 5),
            ),
            G2ScienceCanonicalLessonSpec(2, "Solids", 9, (6,)),
            G2ScienceCanonicalLessonSpec(3, "Liquids and Gases", 10, (7,)),
            G2ScienceCanonicalLessonSpec(4, "Use Matter", 9, (8,)),
        ),
    ),
    G2ScienceModuleSpec(
        module_number=2,
        unit_id="Science_2_Mod2_ChangesToMatter",
        unit_title="Grade 2 Science — Module 2: Changes to Matter",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Put Matter Together",
                9,
                (10, 11, 12, 13, 14, 15, 16, 17, 18, 19),
            ),
            G2ScienceCanonicalLessonSpec(2, "Mixtures", 9, (20,)),
            G2ScienceCanonicalLessonSpec(
                3,
                "Temperature Changes Matter",
                10,
                (21, 22, 23, 24),
            ),
        ),
    ),
    G2ScienceModuleSpec(
        module_number=3,
        unit_id="Science_2_Mod3_PlantsAndTheirNeeds",
        unit_title="Grade 2 Science — Module 3: Plants and Their Needs",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Plants Need Water",
                10,
                (25, 26, 27, 28, 29, 30, 31, 32, 33),
            ),
            G2ScienceCanonicalLessonSpec(2, "Plants Need Light", 10, (34,)),
            G2ScienceCanonicalLessonSpec(3, "Plants Make More Plants", 10, (35,)),
        ),
    ),
    G2ScienceModuleSpec(
        module_number=4,
        unit_id="Science_2_Mod4_LivingThingsInHabitats",
        unit_title="Grade 2 Science — Module 4: Living Things in Habitats",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Habitats",
                10,
                (36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46),
            ),
            G2ScienceCanonicalLessonSpec(2, "Forest and Grasslands", 10, (47,)),
            G2ScienceCanonicalLessonSpec(3, "Water Habitats", 10, (48,)),
            G2ScienceCanonicalLessonSpec(4, "Hot and Cold Deserts", 10, (49,)),
        ),
    ),
    G2ScienceModuleSpec(
        module_number=5,
        unit_id="Science_2_Mod5_EarthSurfaceChanges",
        unit_title="Grade 2 Science — Module 5: Earth's Surface Changes",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Weathering and Erosion",
                10,
                (50, 51, 52, 53),
            ),
            G2ScienceCanonicalLessonSpec(
                2,
                "Quick Changes to Earth's Surface",
                10,
                (54,),
            ),
            G2ScienceCanonicalLessonSpec(3, "Slowing Earth's Changes", 10, (55,)),
        ),
    ),
    G2ScienceModuleSpec(
        module_number=6,
        unit_id="Science_2_Mod6_EarthSurface",
        unit_title="Grade 2 Science — Module 6: Earth's Surface",
        lessons=(
            G2ScienceCanonicalLessonSpec(
                1,
                "Describe Earth's Surface",
                9,
                (56, 57, 58, 59, 60, 61, 62),
            ),
            G2ScienceCanonicalLessonSpec(2, "Oceans", 10, (63,)),
            G2ScienceCanonicalLessonSpec(3, "Fresh Water", 10, (64, 65)),
        ),
    ),
)


def g2_science_modules() -> Tuple[G2ScienceModuleSpec, ...]:
    return _G2_SCIENCE_MODULES


def monolithic_science_unit_id() -> str:
    """Unit id produced by ``ingest_wave_unit`` for the Grade 2 Science root Doc."""
    return "Science_2_U1_1SNRc-NF"


def all_source_parser_numbers_used() -> List[int]:
    used: List[int] = []
    for m in _G2_SCIENCE_MODULES:
        for les in m.lessons:
            used.extend(les.source_parser_lesson_numbers)
    return used


def validate_ssot_covers_monolithic_ingest(*, expect_rows: int = 65) -> None:
    """Raises ValueError if mapping does not use each parser row 1..expect_rows exactly once (except skipped)."""
    used = sorted(all_source_parser_numbers_used())
    skipped = {9}
    expected = [n for n in range(1, expect_rows + 1) if n not in skipped]
    if used != expected:
        raise ValueError(
            f"SSOT parser row coverage mismatch: expected {expected!r} got {used!r}"
        )
