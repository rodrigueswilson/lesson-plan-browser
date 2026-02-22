"""
Build and persist vocabulary/cognates and sentence-frames steps.
Uses same persist pattern as phase_steps (DB create or in-memory when table missing).
"""
import json
import uuid
from typing import Any, List

from backend.config import settings
from backend.schema import LessonStep
from backend.services.lesson_steps import phase_steps
from backend.telemetry import logger


def add_vocab_and_frames_steps(
    vocabulary_cognates: List[Any],
    day_sentence_frames: List[Any],
    tailored_instruction: dict,
    phase_plan_count: int,
    plan_id: str,
    day: str,
    slot: int,
    start_time_offset: int,
    db_for_plan: Any,
    generated_steps: List[LessonStep],
) -> int:
    """
    Add vocabulary/cognates step (if vocabulary_cognates) and sentence-frames step
    (if day_sentence_frames). Uses phase_steps.persist_step for both.
    Returns start_time_offset after the last added step.
    """
    if not vocabulary_cognates and not day_sentence_frames:
        logger.warning(
            "vocabulary_frames_missing",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot": slot,
                "warning": (
                    "No vocabulary_cognates or sentence_frames found in lesson_json. "
                    "Vocabulary/frames steps will not be created. "
                    "If this plan should have vocabulary/frames, check the source JSON "
                    "or use update_plan_supabase.py to fix the plan's lesson_json."
                ),
            },
        )

    logger.info(
        "vocabulary_cognates_check",
        extra={
            "plan_id": plan_id,
            "has_vocabulary_cognates": bool(vocabulary_cognates),
            "is_list": isinstance(vocabulary_cognates, list),
            "length": len(vocabulary_cognates)
            if isinstance(vocabulary_cognates, list)
            else 0,
        },
    )

    if vocabulary_cognates:
        lines = []
        for pair in vocabulary_cognates:
            if not isinstance(pair, dict):
                continue
            english = str(pair.get("english", "")).strip()
            portuguese = str(pair.get("portuguese", "")).strip()
            if not english or not portuguese:
                continue
            lines.append(f"- {english} -> {portuguese}")

        if lines:
            vocab_step_id = str(uuid.uuid4())
            vocab_step_number = phase_plan_count + 1
            ell_support = tailored_instruction.get("ell_support") or []
            vocab_strategy_text = ""
            if isinstance(ell_support, list):
                for s in ell_support:
                    if isinstance(s, dict):
                        strategy_id = s.get("strategy_id", "").lower()
                        strategy_name = str(s.get("strategy_name", "")).lower()
                        if (
                            strategy_id == "cognate_awareness"
                            or "cognate" in strategy_name
                        ):
                            vocab_strategy_text = s.get(
                                "implementation", ""
                            ) or s.get("implementation_steps", "")
                            if vocab_strategy_text:
                                if isinstance(vocab_strategy_text, list):
                                    vocab_strategy_text = "\n".join(
                                        vocab_strategy_text
                                    )
                                break
            display_content = "\n".join(lines)
            if vocab_strategy_text:
                display_content = f"{vocab_strategy_text}\n\n{display_content}"

            vocab_step = {
                "id": vocab_step_id,
                "lesson_plan_id": plan_id,
                "day_of_week": day.lower(),
                "slot_number": slot,
                "step_number": vocab_step_number,
                "step_name": "Vocabulary / Cognate Awareness",
                "duration_minutes": 5,
                "start_time_offset": start_time_offset,
                "content_type": "instruction",
                "display_content": display_content,
                "hidden_content": [],
                "sentence_frames": [],
                "materials_needed": [],
                "vocabulary_cognates": json.dumps(vocabulary_cognates)
                if settings.USE_SUPABASE
                else vocabulary_cognates,
            }
            phase_steps.persist_step(vocab_step, db_for_plan, generated_steps)
            start_time_offset += 5

    if day_sentence_frames:
        frames_step_id = str(uuid.uuid4())
        existing_steps = db_for_plan.get_lesson_steps(
            plan_id, day_of_week=day, slot_number=slot
        )
        next_step_number = (
            (existing_steps[-1].step_number + 1)
            if existing_steps
            else (phase_plan_count + 1)
        )
        ell_support = tailored_instruction.get("ell_support") or []
        frames_strategy_text = ""
        if isinstance(ell_support, list):
            for s in ell_support:
                if isinstance(s, dict):
                    strategy_id = s.get("strategy_id", "").lower()
                    strategy_name = str(s.get("strategy_name", "")).lower()
                    if (
                        strategy_id == "sentence_frames"
                        or "sentence frames" in strategy_name
                        or "sentence frame" in strategy_name
                    ):
                        frames_strategy_text = s.get(
                            "implementation", ""
                        ) or s.get("implementation_steps", "")
                        if frames_strategy_text:
                            if isinstance(frames_strategy_text, list):
                                frames_strategy_text = "\n".join(
                                    frames_strategy_text
                                )
                            break
        frames_display_parts = []
        if frames_strategy_text:
            frames_display_parts.append(frames_strategy_text)
        frames_display_parts.append("\nReference Frames:")
        for frame in day_sentence_frames:
            if isinstance(frame, dict):
                english = frame.get("english", "")
                if english:
                    frames_display_parts.append(f"- {english}")
        frames_display_content = (
            "\n\n".join(frames_display_parts)
            if frames_display_parts
            else frames_strategy_text
        )
        frames_step = {
            "id": frames_step_id,
            "lesson_plan_id": plan_id,
            "day_of_week": day.lower(),
            "slot_number": slot,
            "step_number": next_step_number,
            "step_name": "Sentence Frames / Stems / Questions",
            "duration_minutes": 5,
            "start_time_offset": start_time_offset,
            "content_type": "sentence_frames",
            "display_content": frames_display_content,
            "hidden_content": [],
            "sentence_frames": day_sentence_frames,
            "materials_needed": [],
        }
        phase_steps.persist_step(frames_step, db_for_plan, generated_steps)
        start_time_offset += 5

    return start_time_offset
