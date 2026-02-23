"""
Builds the JSON schema example for LLM prompts (single-slot day structure).
Used by prompt_builder.build_schema_example.
"""

import json
from typing import Any, Dict, List, Optional


def build_schema_example(
    week_of: str,
    grade: str,
    subject: str,
    teacher_name: Optional[str],
    homeroom: Optional[str],
) -> str:
    """Build schema example JSON string (single-slot structure only)."""

    def create_day(
        unit_lesson: str,
        *,
        wida_objective: str = "Students will explain [content] through [selected domains based on activities], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains]).",
        student_goal: str = "I will [domain actions based on lesson activities] about [content].",
        anticipatory_bridge: str = "...",
        co_teaching_model: Optional[Dict[str, Any]] = None,
        ell_support: Optional[List[Dict[str, Any]]] = None,
        special_needs_support: Optional[List[str]] = None,
        materials: Optional[List[str]] = None,
        linguistic_note: Optional[Dict[str, Any]] = None,
        bilingual_overlay: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "unit_lesson": unit_lesson,
            "objective": {
                "content_objective": "Students will...",
                "student_goal": student_goal,
                "wida_objective": wida_objective,
            },
            "anticipatory_set": {
                "original_content": "...",
                "bilingual_bridge": anticipatory_bridge,
            },
            "tailored_instruction": {
                "original_content": "...",
                "co_teaching_model": co_teaching_model or {},
                "ell_support": ell_support or [],
                "special_needs_support": special_needs_support or [],
                "materials": materials or [],
            },
            "misconceptions": {
                "original_content": "...",
                "linguistic_note": linguistic_note or {},
            },
            "assessment": {
                "primary_assessment": "...",
                "bilingual_overlay": bilingual_overlay or {},
            },
            "homework": {"original_content": "...", "family_connection": "..."},
        }

    day_definitions = [
        (
            "monday",
            {
                "unit_lesson": "Unit One Lesson One",
                "wida_objective": "Students will explain the water cycle through listening to explanations, reading diagrams, speaking with partners, and writing paragraphs, using visual supports and sentence frames appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Listening/Reading/Speaking/Writing).",
                "student_goal": "I will listen to explanations, read diagrams, speak with my partner, and write about the water cycle.",
                "anticipatory_bridge": "Preview key cognates: word/palavra...",
                "co_teaching_model": {
                    "model_name": "Station Teaching",
                    "rationale": "...",
                    "wida_context": "...",
                    "phase_plan": [
                        {
                            "phase_name": "Warmup",
                            "minutes": 5,
                            "bilingual_teacher_role": "...",
                            "primary_teacher_role": "...",
                        }
                    ],
                    "implementation_notes": ["..."],
                },
                "ell_support": [
                    {
                        "strategy_id": "cognate_awareness",
                        "strategy_name": "Cognate Awareness",
                        "implementation": "...",
                        "proficiency_levels": "Levels 2-5",
                    }
                ],
                "special_needs_support": ["..."],
                "materials": ["..."],
                "linguistic_note": {
                    "pattern_id": "subject_pronoun_omission",
                    "note": "...",
                    "prevention_tip": "...",
                },
                "bilingual_overlay": {
                    "instrument": "...",
                    "wida_mapping": "...",
                    "supports_by_level": {
                        "levels_1_2": "...",
                        "levels_3_4": "...",
                        "levels_5_6": "...",
                    },
                    "scoring_lens": "...",
                    "constraints_honored": "...",
                },
            },
        ),
        (
            "tuesday",
            {
                "unit_lesson": "Unit One Lesson Two",
                "co_teaching_model": {
                    "model_name": "Station Teaching",
                    "rationale": "...",
                    "wida_context": "...",
                    "phase_plan": [],
                    "implementation_notes": [],
                },
                "linguistic_note": {
                    "pattern_id": "...",
                    "note": "...",
                    "prevention_tip": "...",
                },
                "bilingual_overlay": {
                    "instrument": "...",
                    "wida_mapping": "...",
                    "supports_by_level": {},
                    "scoring_lens": "...",
                    "constraints_honored": "...",
                },
            },
        ),
        ("wednesday", {"unit_lesson": "Unit One Lesson Three"}),
        ("thursday", {"unit_lesson": "Unit One Lesson Four"}),
        ("friday", {"unit_lesson": "Unit One Lesson Five"}),
    ]

    example = {
        "metadata": {"week_of": week_of, "grade": grade, "subject": subject},
        "days": {
            day: create_day(**definition) for day, definition in day_definitions
        },
    }

    if teacher_name:
        example["metadata"]["teacher_name"] = teacher_name
    if homeroom:
        example["metadata"]["homeroom"] = homeroom

    return json.dumps(example, indent=2)
