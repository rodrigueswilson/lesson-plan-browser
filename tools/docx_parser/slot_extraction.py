"""
Slot-based extraction (find slot by subject) for DOCX parsing.
"""

import string
from typing import Callable, Optional

from backend.telemetry import logger


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return text.translate(str.maketrans("", "", string.punctuation)).lower().strip()


def _tokenize_subject(text: str) -> list:
    tokens = []
    for sep in ["/", "-", "&", "and"]:
        if sep in text:
            tokens.extend(text.split(sep))
            break
    else:
        tokens = [text]
    return [_normalize_text(t) for t in tokens if t.strip()]


def find_slot_by_subject(
    doc,
    subject: str,
    teacher_name: Optional[str] = None,
    homeroom: Optional[str] = None,
    grade: Optional[str] = None,
    validate_slot_structure_fn: Optional[Callable] = None,
) -> int:
    """
    Find which slot contains the given subject by scanning metadata tables.

    Args:
        doc: Document object (from python-docx)
        subject: Subject name to find (e.g., "ELA/SS", "Math", "Science")
        teacher_name: Optional teacher name to disambiguate duplicate subjects
        homeroom: Optional homeroom to disambiguate duplicate subjects
        grade: Optional grade to disambiguate duplicate subjects
        validate_slot_structure_fn: Function(doc, slot_number) -> (table_start, table_end)

    Returns:
        Slot number (1-indexed) containing the subject

    Raises:
        ValueError: If subject not found in any slot
    """
    if validate_slot_structure_fn is None:
        from .structure import validate_slot_structure
        validate_slot_structure_fn = validate_slot_structure

    subject_normalized = _normalize_text(subject)
    subject_tokens = _tokenize_subject(subject)

    subject_mappings = {
        "ela": ["ela", "english", "language arts", "reading", "literacy"],
        "math": ["math", "mathematics"],
        "science": ["science", "sci"],
        "social studies": ["ss", "social studies", "history"],
        "ela/ss": ["ela/ss", "elass", "language arts/social studies", "language artssocial studies"],
    }

    possible_aliases = [subject_normalized]
    for canonical, aliases in subject_mappings.items():
        if subject_normalized in aliases or subject_normalized == _normalize_text(canonical):
            possible_aliases.extend([_normalize_text(a) for a in aliases])
            break

    teacher_normalized = _normalize_text(teacher_name) if teacher_name else None
    homeroom_normalized = _normalize_text(homeroom) if homeroom else None
    grade_normalized = _normalize_text(grade) if grade else None

    total_tables = len(doc.tables)
    has_signature = False
    if total_tables > 0:
        last_table = doc.tables[-1]
        if last_table.rows and last_table.rows[0].cells:
            first_cell = last_table.rows[0].cells[0].text.strip().lower()
            if "signature" in first_cell or "required signatures" in first_cell:
                has_signature = True

    available_slots = (total_tables - 1) // 2 if has_signature else total_tables // 2
    matches = []

    for slot_num in range(1, available_slots + 1):
        try:
            table_start, table_end = validate_slot_structure_fn(doc, slot_num)
            meta_table = doc.tables[table_start]
            slot_subject = slot_teacher = slot_homeroom = slot_grade = None

            for row in meta_table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    cell_lower = cell_text.lower()
                    if "subject:" in cell_lower:
                        slot_subject = cell_text.split(":", 1)[-1].strip()
                    if "name:" in cell_lower or "teacher:" in cell_lower:
                        slot_teacher = cell_text.split(":", 1)[-1].strip()
                    if "homeroom:" in cell_lower:
                        slot_homeroom = cell_text.split(":", 1)[-1].strip()
                    if "grade:" in cell_lower:
                        slot_grade = cell_text.split(":", 1)[-1].strip()

            if not slot_subject:
                continue

            subject_value_normalized = _normalize_text(slot_subject)
            subject_value_tokens = _tokenize_subject(slot_subject)
            matched = False
            matched_alias = None

            for alias in possible_aliases:
                if subject_value_normalized == alias:
                    matched = True
                    matched_alias = alias
                    logger.debug("subject_exact_match", extra={"slot": slot_num, "requested": subject, "metadata": slot_subject, "matched_alias": alias})
                    break

            if not matched and len(subject_tokens) > 1:
                if all(any(st == vt for vt in subject_value_tokens) for st in subject_tokens):
                    matched = True
                    matched_alias = "token_match"
                    logger.debug("subject_token_match", extra={"slot": slot_num, "requested_tokens": subject_tokens, "metadata_tokens": subject_value_tokens})

            if matched:
                matches.append({
                    "slot_num": slot_num,
                    "subject": slot_subject,
                    "teacher": slot_teacher,
                    "homeroom": slot_homeroom,
                    "grade": slot_grade,
                    "matched_alias": matched_alias,
                })
        except ValueError:
            continue

    if not matches and len(subject_tokens) > 1:
        logger.info("trying_flexible_subject_match", extra={"requested_subject": subject, "tokens": subject_tokens, "message": "No exact match found, trying individual tokens"})
        for slot_num in range(1, available_slots + 1):
            try:
                table_start, table_end = validate_slot_structure_fn(doc, slot_num)
                meta_table = doc.tables[table_start]
                slot_subject = slot_teacher = slot_homeroom = slot_grade = None
                for row in meta_table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        cell_lower = cell_text.lower()
                        if "subject:" in cell_lower:
                            slot_subject = cell_text.split(":", 1)[-1].strip()
                        if "name:" in cell_lower or "teacher:" in cell_lower:
                            slot_teacher = cell_text.split(":", 1)[-1].strip()
                        if "homeroom:" in cell_lower:
                            slot_homeroom = cell_text.split(":", 1)[-1].strip()
                        if "grade:" in cell_lower:
                            slot_grade = cell_text.split(":", 1)[-1].strip()
                if slot_subject:
                    subject_value_normalized = _normalize_text(slot_subject)
                    for token in subject_tokens:
                        if token == subject_value_normalized:
                            logger.info("flexible_subject_match_found", extra={"requested_subject": subject, "matched_token": token, "metadata_subject": slot_subject, "slot": slot_num})
                            matches.append({
                                "slot_num": slot_num,
                                "subject": slot_subject,
                                "teacher": slot_teacher,
                                "homeroom": slot_homeroom,
                                "grade": slot_grade,
                                "matched_alias": f"flexible_token_{token}",
                            })
                            break
            except ValueError:
                continue

    if not matches:
        raise ValueError(
            f"Subject '{subject}' not found in any slot. "
            f"Available slots: {available_slots}. "
            f"Scanned metadata tables but found no matching subject."
        )

    if len(matches) == 1:
        match = matches[0]
        logger.info("subject_slot_found", extra={"requested_subject": subject, "found_in_slot": match["slot_num"], "metadata_subject": match["subject"], "metadata_teacher": match["teacher"], "matched_via": match["matched_alias"]})
        return match["slot_num"]

    if teacher_normalized:
        for match in matches:
            if match["teacher"] and teacher_normalized in _normalize_text(match["teacher"]):
                logger.info("subject_slot_found_via_teacher", extra={"requested_subject": subject, "requested_teacher": teacher_name, "found_in_slot": match["slot_num"], "metadata_subject": match["subject"], "metadata_teacher": match["teacher"], "total_matches": len(matches)})
                return match["slot_num"]

    if homeroom_normalized:
        homeroom_matches = [m for m in matches if m["homeroom"] and homeroom_normalized == _normalize_text(m["homeroom"])]
        if len(homeroom_matches) == 1:
            match = homeroom_matches[0]
            logger.info("subject_slot_found_via_homeroom", extra={"requested_subject": subject, "requested_homeroom": homeroom, "found_in_slot": match["slot_num"], "metadata_subject": match["subject"], "metadata_homeroom": match["homeroom"], "total_matches": len(matches)})
            return match["slot_num"]
        elif len(homeroom_matches) > 1 and grade_normalized:
            grade_matches = [m for m in homeroom_matches if m["grade"] and grade_normalized == _normalize_text(m["grade"])]
            if len(grade_matches) == 1:
                match = grade_matches[0]
                logger.info("subject_slot_found_via_homeroom_grade", extra={"requested_subject": subject, "requested_homeroom": homeroom, "requested_grade": grade, "found_in_slot": match["slot_num"], "metadata_subject": match["subject"], "metadata_homeroom": match["homeroom"], "metadata_grade": match["grade"], "total_matches": len(matches)})
                return match["slot_num"]
            elif len(grade_matches) > 1:
                match = grade_matches[0]
                logger.warning("multiple_matches_after_homeroom_grade", extra={"requested_subject": subject, "requested_homeroom": homeroom, "requested_grade": grade, "total_matches": len(grade_matches), "selected_slot": match["slot_num"]})
                return match["slot_num"]

    match = matches[0]
    logger.warning("multiple_subject_matches", extra={
        "requested_subject": subject,
        "requested_teacher": teacher_name,
        "requested_homeroom": homeroom,
        "requested_grade": grade,
        "total_matches": len(matches),
        "matches": [{"slot": m["slot_num"], "teacher": m["teacher"], "homeroom": m["homeroom"], "grade": m.get("grade")} for m in matches],
        "selected_slot": match["slot_num"],
        "message": "Multiple slots match subject, returning first match",
    })
    return match["slot_num"]
