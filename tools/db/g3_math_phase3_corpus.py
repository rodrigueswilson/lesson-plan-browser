"""
Canonical Phase 3 Grade 3 Math ingest targets.

SSOT path: reference_docs/scraped_registry.json -> "Grade 3" -> "Math".

Each unit_id uses the stable convention Math_3_U{number}_{doc_id_prefix} where
doc_id_prefix is the first eight characters of the Google Doc file id (same as
prior wave ingest_reports in this repo).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class G3MathUnitSpec:
    registry_key: str
    doc_id: str
    unit_id: str
    unit_number: int
    title: str


# Full multi-lesson teacher-guide units in scope for Phase 3 corpus completion.
G3_MATH_PHASE3_UNITS: Tuple[G3MathUnitSpec, ...] = (
    G3MathUnitSpec(
        registry_key="Unit 1_Introducing_Multiplication",
        doc_id="13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg",
        unit_id="Math_3_U1_13jAzcMR",
        unit_number=1,
        title="Grade 3 Unit 1: Introducing Multiplication",
    ),
    G3MathUnitSpec(
        registry_key="Unit 2_Area_and_Multiplication",
        doc_id="1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE",
        unit_id="Math_3_U2_1hBoK4uk",
        unit_number=2,
        title="Grade 3 Unit 2: Area and Multiplication",
    ),
    G3MathUnitSpec(
        registry_key="Unit 3_Extending_Operations_to_Fractions",
        doc_id="1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4",
        unit_id="Math_3_U3_1W1IBU71",
        unit_number=3,
        title="Grade 3 Unit 3: Extending Operations to Fractions",
    ),
    G3MathUnitSpec(
        registry_key="Unit 4_Relating_Multiplication_to_Division",
        doc_id="1VUoecGCd8fLAarsUTOgOMktXUFhZjJm_97wuAdH6QMs",
        unit_id="Math_3_U4_1VUoecGC",
        unit_number=4,
        title="Grade 3 Unit 4: Relating Multiplication to Division",
    ),
    G3MathUnitSpec(
        registry_key="Unit 5_Fractions_as_Number",
        doc_id="1LEDv2I_UuMnUiEH44IxLSXOVb846UD1uqlMwnD-B1mg",
        unit_id="Math_3_U5_1LEDv2I_",
        unit_number=5,
        title="Grade 3 Unit 5: Fractions as Number",
    ),
    G3MathUnitSpec(
        registry_key="Unit 6_Measuring_Length_Time_Liquid_Volume_and_Weight",
        doc_id="1VozISaYFa5MWb5AqDLYVQ0ynWpFJHc4HDZK3k2tYbHE",
        unit_id="Math_3_U6_1VozISaY",
        unit_number=6,
        title="Grade 3 Unit 6: Measuring Length, Time, Liquid Volume and Weight",
    ),
    G3MathUnitSpec(
        registry_key="Unit 7_Two-Dimensional_Shapes_and_Perimeter",
        doc_id="1W0aGPyiUTW7ASQd-x2eGjwW_--e9G_GYil_3SrXrC_8",
        unit_id="Math_3_U7_1W0aGPyi",
        unit_number=7,
        title="Grade 3 Unit 7: Two-Dimensional Shapes and Perimeter",
    ),
    G3MathUnitSpec(
        registry_key="Unit 8_Putting_It_All_Together",
        doc_id="1gFC5KEGeuEw3QxQVQWgf6zKS3DnFrhMZVK5QtB_HFto",
        unit_id="Math_3_U8_1gFC5KEG",
        unit_number=8,
        title="Grade 3 Unit 8: Putting It All Together",
    ),
)

# Documented exclusions (still present under Grade 3 -> Math in the registry).
G3_MATH_PHASE3_REGISTRY_EXCLUSIONS: Tuple[Tuple[str, str], ...] = (
    (
        "Grade_3_Benchmark_2_Blueprint",
        "Benchmark blueprint; not a multi-lesson teacher guide tab.",
    ),
    (
        "Grade_3_Benchmark_3_Blueprint",
        "Benchmark blueprint; not a multi-lesson teacher guide tab.",
    ),
    (
        "Grade_3_Benchmark_4_Blueprint",
        "Benchmark blueprint; not a multi-lesson teacher guide tab.",
    ),
    (
        "Grade_3_Mathematics_Curriculum_Guide",
        "Program-level curriculum guide; not a per-unit lesson guide for ingest_to_curriculum.",
    ),
)
