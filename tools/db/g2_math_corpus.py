"""
Canonical Grade 2 Math ingest targets aligned with the district hub doc.

Hub (also in scraped_registry.json): **Grade 2 Mathematics Curriculum Guide**
(`1Wb_ty4UKX6uWOuSP71yFxkuC5XOyCp6l1pKdEN5HQfw`). Linked unit teacher guides are the nine
`G2MathUnitSpec` rows below.

SSOT for Doc ids: `reference_docs/scraped_registry.json` -> "Grade 2" -> "Math".

Each unit_id uses Math_2_U{number}_{doc_id_prefix} where doc_id_prefix is the first
eight characters of the Google Doc file id (same convention as g3_math_phase3_corpus).

To refresh linked ids from the hub (OAuth required):

  python tools/scraper/list_gdoc_links_in_document.py --doc-id 1Wb_ty4UKX6uWOuSP71yFxkuC5XOyCp6l1pKdEN5HQfw
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class G2MathUnitSpec:
    registry_key: str
    doc_id: str
    unit_id: str
    unit_number: int
    title: str


G2_MATH_UNITS: Tuple[G2MathUnitSpec, ...] = (
    G2MathUnitSpec(
        registry_key="Unit 1_Adding_Subtracting_and_Working_With_Data",
        doc_id="15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU",
        unit_id="Math_2_U1_15E1iQ_x",
        unit_number=1,
        title="Grade 2 Unit 1: Adding, Subtracting and Working With Data",
    ),
    G2MathUnitSpec(
        registry_key="Unit 2_Add_and_Subtract_Within_100",
        doc_id="1xETg0g5z_wnCqdrQX-ySheJFk3xI9aTC1WnKp-XIjdo",
        unit_id="Math_2_U2_1xETg0g5",
        unit_number=2,
        title="Grade 2 Unit 2: Add and Subtract Within 100",
    ),
    G2MathUnitSpec(
        registry_key="Unit 3_Measuring_Length",
        doc_id="1jS0EN5RQpawPPkDnTkUnbktDeqnLDjeojFHudRl5zGY",
        unit_id="Math_2_U3_1jS0EN5R",
        unit_number=3,
        title="Grade 2 Unit 3: Measuring Length",
    ),
    G2MathUnitSpec(
        registry_key="Unit 4_Addition_and_Subtraction_on_the_Number_Line",
        doc_id="1x8ll9eW0ZVYdBOKIdDfEPk1X_79X3dyOtq_zyByvpe4",
        unit_id="Math_2_U4_1x8ll9eW",
        unit_number=4,
        title="Grade 2 Unit 4: Addition and Subtraction on the Number Line",
    ),
    G2MathUnitSpec(
        registry_key="Unit 5_Numbers_to_1000",
        doc_id="1S9fRcM1-6futZzmOgOEg3eQ1hfRh8YpXHfjmyiPTu08",
        unit_id="Math_2_U5_1S9fRcM1",
        unit_number=5,
        title="Grade 2 Unit 5: Numbers to 1,000",
    ),
    G2MathUnitSpec(
        registry_key="Unit 6_Geometry_Time_and_Money",
        doc_id="1Sc97mZeXhUqDjDXsLcMW77JyCYiqHlTrAqjwvDSOcBA",
        unit_id="Math_2_U6_1Sc97mZe",
        unit_number=6,
        title="Grade 2 Unit 6: Geometry, Time and Money",
    ),
    G2MathUnitSpec(
        registry_key="Unit 7_Adding_and_Subtracting_within_1000",
        doc_id="1_ssfcJowFerv6F7wHH7bZlSwE0SLT7KWhJpsv5jvUI0",
        unit_id="Math_2_U7_1_ssfcJo",
        unit_number=7,
        title="Grade 2 Unit 7: Adding and Subtracting within 1,000",
    ),
    G2MathUnitSpec(
        registry_key="Unit 8_Equal_Groups",
        doc_id="1WAKGnW03wBBAl2jCxsUIkShN6Aaf-rvr4OCNnogNQNw",
        unit_id="Math_2_U8_1WAKGnW0",
        unit_number=8,
        title="Grade 2 Unit 8: Equal Groups",
    ),
    G2MathUnitSpec(
        registry_key="Unit 9_Putting_It_All_Together",
        doc_id="1WlshQ2M5dJzALUM2jGbNvcodERGkLY09G9FBN40uDCc",
        unit_id="Math_2_U9_1WlshQ2M",
        unit_number=9,
        title="Grade 2 Unit 9: Putting It All Together",
    ),
)

G2_MATH_REGISTRY_EXCLUSIONS: Tuple[Tuple[str, str], ...] = (
    (
        "Additional_Optional_Digitized_Texts_Grade_2Unit_Learning_About_North_America",
        "Supplemental texts; not the multi-lesson Math teacher-guide tab.",
    ),
    (
        "Grade_2_Benchmark_2_Blueprint",
        "Assessment blueprint; not a unit teacher guide.",
    ),
    (
        "Grade_2_Benchmark_3_Blueprint",
        "Assessment blueprint; not a unit teacher guide.",
    ),
    (
        "Grade_2_Benchmark_4_Blueprint",
        "Assessment blueprint; not a unit teacher guide.",
    ),
)
