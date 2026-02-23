"""
Format helpers for table/cell content.

Provides: format_objective, format_anticipatory_set, format_tailored_instruction,
format_misconceptions, format_assessment, format_homework,
filter_valid_vocabulary_pairs, filter_valid_sentence_frames.
"""

from typing import Dict, List, Optional


def format_objective(renderer, objective: Dict) -> str:
    """Format objective section."""
    if not objective:
        return ""

    if renderer.is_originals:
        return objective.get("content_objective") or objective.get("student_goal") or ""

    parts = []
    if "content_objective" in objective:
        parts.append(f"**Content:** {objective['content_objective']}")
    if "student_goal" in objective:
        parts.append(f"**Student Goal:** {objective['student_goal']}")
    if "wida_objective" in objective:
        parts.append(f"**WIDA/Bilingual:** {objective['wida_objective']}")
    return "\n\n".join(parts)


def format_anticipatory_set(renderer, anticipatory: Dict) -> str:
    """Format anticipatory set section."""
    if not anticipatory:
        return ""

    if renderer.is_originals:
        return anticipatory.get("original_content") or ""

    parts = []
    if "original_content" in anticipatory:
        parts.append(anticipatory["original_content"])
    if "bilingual_bridge" in anticipatory:
        parts.append(f"\n**Bilingual Bridge:** {anticipatory['bilingual_bridge']}")
    return "\n".join(parts)


def filter_valid_vocabulary_pairs(
    renderer, vocabulary_cognates: List[Dict]
) -> List[Dict]:
    """Filter vocabulary pairs to only include valid ones with both english and portuguese."""
    return [
        pair
        for pair in vocabulary_cognates
        if isinstance(pair, dict)
        and str(pair.get("english", "")).strip()
        and str(pair.get("portuguese", "")).strip()
    ]


def filter_valid_sentence_frames(renderer, sentence_frames: List[Dict]) -> List[Dict]:
    """Filter sentence frames to only include well-formed ones."""
    return [
        frame
        for frame in sentence_frames
        if isinstance(frame, dict)
        and str(frame.get("english", "")).strip()
        and str(frame.get("portuguese", "")).strip()
        and str(frame.get("proficiency_level", "")).strip()
    ]


def format_tailored_instruction(
    renderer,
    instruction: Dict,
    vocabulary_cognates: Optional[List[Dict]] = None,
    sentence_frames: Optional[List[Dict]] = None,
) -> str:
    """Format tailored instruction section."""
    if not instruction:
        return ""

    if renderer.is_originals:
        return instruction.get("original_content") or ""

    parts = []

    if "original_content" in instruction:
        parts.append(instruction["original_content"])

    if "co_teaching_model" in instruction:
        co_teaching = instruction["co_teaching_model"]
        parts.append(
            f"\n**Co-Teaching Model:** {co_teaching.get('model_name', '')}"
        )
        if "phase_plan" in co_teaching:
            parts.append("\n**Phase Plan:**")
            for phase in co_teaching["phase_plan"]:
                phase_name = phase.get("phase_name", "")
                minutes = phase.get("minutes", "")
                parts.append(f"- **{phase_name}** ({minutes} min)")
                if "bilingual_teacher_role" in phase:
                    parts.append(
                        f"  - Bilingual: {phase['bilingual_teacher_role']}"
                    )
                if "primary_teacher_role" in phase:
                    parts.append(f"  - Primary: {phase['primary_teacher_role']}")

    ell_support = instruction.get("ell_support") or []
    if ell_support:
        parts.append("\n**ELL Support:**")
        for strategy in ell_support:
            strategy_name = strategy.get("strategy_name", "")
            implementation = strategy.get("implementation", "")
            levels = strategy.get("proficiency_levels", "")
            parts.append(f"- **{strategy_name}** ({levels}): {implementation}")

    if vocabulary_cognates:
        valid_pairs = filter_valid_vocabulary_pairs(renderer, vocabulary_cognates)
        if valid_pairs:
            parts.append("\n**Vocabulary / Cognate Awareness:**")
            for pair in valid_pairs:
                english = str(pair.get("english", "")).strip()
                portuguese = str(pair.get("portuguese", "")).strip()
                parts.append(f"- **{english}** -> *{portuguese}*")

    if sentence_frames:
        valid_frames = filter_valid_sentence_frames(renderer, sentence_frames)
        if valid_frames:
            parts.append("\n**Sentence Frames / Stems / Questions:**")
            level_order = [
                ("levels_1_2", "Levels 1-2"),
                ("levels_3_4", "Levels 3-4"),
                ("levels_5_6", "Levels 5-6"),
            ]
            for level_key, level_label in level_order:
                frames_for_level = [
                    f
                    for f in valid_frames
                    if f.get("proficiency_level") == level_key
                ]
                if not frames_for_level:
                    continue
                parts.append(f"\n- **{level_label}:**")
                for frame in frames_for_level:
                    english = str(frame.get("english", "")).strip()
                    portuguese = str(frame.get("portuguese", "")).strip()
                    language_function = str(
                        frame.get("language_function", "")
                    ).strip()
                    parts.append(f"  - PT: *{portuguese}*")
                    if language_function:
                        parts.append(
                            f"    EN: **{english}** (function: {language_function})"
                        )
                    else:
                        parts.append(f"    EN: **{english}**")

    if "materials" in instruction and instruction["materials"]:
        parts.append("\n**Materials:** " + ", ".join(instruction["materials"]))

    return "\n".join(parts)


def format_misconceptions(renderer, misconceptions: Dict) -> str:
    """Format misconceptions section."""
    if not misconceptions:
        return ""

    if renderer.is_originals:
        return misconceptions.get("original_content") or ""

    parts = []
    if "original_content" in misconceptions:
        parts.append(misconceptions["original_content"])
    if "linguistic_note" in misconceptions:
        ling = misconceptions["linguistic_note"]
        if "note" in ling:
            parts.append(f"\n**Linguistic Note:** {ling['note']}")
        if "prevention_tip" in ling:
            parts.append(f"**Prevention:** {ling['prevention_tip']}")
    return "\n".join(parts)


def format_assessment(renderer, assessment: Dict) -> str:
    """Format assessment section."""
    if not assessment:
        return ""

    if renderer.is_originals:
        return assessment.get("primary_assessment") or ""

    parts = []
    if "primary_assessment" in assessment:
        parts.append(f"**Assessment:** {assessment['primary_assessment']}")
    if "bilingual_overlay" in assessment:
        overlay = assessment["bilingual_overlay"]
        if "instrument" in overlay:
            parts.append(f"\n**Instrument:** {overlay['instrument']}")
        if "supports_by_level" in overlay:
            parts.append("\n**Supports by Level:**")
            supports = overlay["supports_by_level"]
            if "levels_1_2" in supports:
                parts.append(f"- **Levels 1-2:** {supports['levels_1_2']}")
            if "levels_3_4" in supports:
                parts.append(f"- **Levels 3-4:** {supports['levels_3_4']}")
            if "levels_5_6" in supports:
                parts.append(f"- **Levels 5-6:** {supports['levels_5_6']}")
    return "\n".join(parts)


def format_homework(renderer, homework: Dict) -> str:
    """Format homework section."""
    if not homework:
        return ""

    if renderer.is_originals:
        return homework.get("original_content") or ""

    parts = []
    if "original_content" in homework and homework["original_content"]:
        parts.append(homework["original_content"])
    if "family_connection" in homework:
        parts.append(f"\n**Family Connection:** {homework['family_connection']}")
    return "\n".join(parts)
