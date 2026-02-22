"""
Slot structure validation for DOCX lesson plan documents.
"""

import string
from typing import Tuple


def validate_slot_structure(doc, slot_number: int) -> Tuple[int, int]:
    """
    Validate document structure for slot extraction.

    Ensures document has expected table layout (metadata + daily plans per slot + signature).
    Fails loudly with detailed error messages for unexpected structures.

    Args:
        doc: Document object (from python-docx)
        slot_number: Requested slot number (1-indexed)

    Raises:
        ValueError: If structure is invalid with detailed message

    Returns:
        tuple: (table_start, table_end) indices for the slot (0-indexed)
    """
    from backend.telemetry import logger

    table_count = len(doc.tables)

    if table_count == 0:
        raise ValueError("Document has no tables")

    # Check for signature table (last table) - optional validation
    last_table = doc.tables[-1]
    has_signature = False

    if last_table.rows and last_table.rows[0].cells:
        first_cell = last_table.rows[0].cells[0].text.strip().lower()
        if "signature" in first_cell or "required signatures" in first_cell:
            has_signature = True

    # Calculate available slots (excluding signature if present)
    if has_signature:
        available_slots = (table_count - 1) // 2
    else:
        # No signature table - all tables are slot tables
        available_slots = table_count // 2
        logger.warning(
            "no_signature_table",
            extra={
                "table_count": table_count,
                "available_slots": available_slots,
                "last_table_first_cell": last_table.rows[0].cells[0].text.strip() if last_table.rows and last_table.rows[0].cells else "empty",
            },
        )

    # Validate table count matches expected pattern
    if has_signature:
        expected_table_count = (available_slots * 2) + 1
        if table_count != expected_table_count:
            valid_counts = [2 * n + 1 for n in range(1, 11)]
            valid_examples = ", ".join(
                f"{c} ({(c - 1) // 2} slot{'s' if (c - 1) // 2 > 1 else ''})"
                for c in valid_counts[:5]
            )
            raise ValueError(
                f"Unexpected table count: {table_count}. "
                f"Expected {expected_table_count} for {available_slots} slots. "
                f"Examples of valid counts: {valid_examples}."
            )
    else:
        expected_table_count = available_slots * 2
        if table_count != expected_table_count:
            raise ValueError(
                f"Unexpected table count: {table_count}. "
                f"Expected {expected_table_count} (even number) for {available_slots} slots "
                f"without signature table. Each slot requires 2 tables (metadata + daily plan)."
            )

    # Validate requested slot exists
    if slot_number < 1:
        raise ValueError(f"Slot number must be >= 1, got {slot_number}")

    if slot_number > available_slots:
        raise ValueError(
            f"Slot {slot_number} requested but only {available_slots} slots available. "
            f"Document has {table_count} tables."
        )

    # Calculate table indices for this slot
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1

    # Validate metadata table (relaxed: case-insensitive, whitespace-tolerant)
    meta_table = doc.tables[table_start]
    if not meta_table.rows or not meta_table.rows[0].cells:
        raise ValueError(
            f"Slot {slot_number} metadata table (index {table_start}) is empty"
        )

    first_cell = meta_table.rows[0].cells[0].text.strip().lower()
    metadata_indicators = ["name", "teacher"]
    has_metadata_indicator = any(
        indicator in first_cell for indicator in metadata_indicators
    )

    if not has_metadata_indicator:
        raise ValueError(
            f"Slot {slot_number} table {table_start} doesn't look like metadata table. "
            f"Expected 'Name:', 'Teacher:', or similar but got: '{meta_table.rows[0].cells[0].text.strip()[:50]}'"
        )

    # Validate daily plans table (relaxed: check all cells, strip punctuation)
    daily_table = doc.tables[table_end]
    if not daily_table.rows or not daily_table.rows[0].cells:
        raise ValueError(
            f"Slot {slot_number} daily plans table (index {table_end}) is empty"
        )

    first_row_text = " ".join(cell.text.strip() for cell in daily_table.rows[0].cells)
    first_row_clean = first_row_text.translate(
        str.maketrans("", "", string.punctuation)
    ).upper()

    weekdays = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    has_weekday = any(day in first_row_clean for day in weekdays)

    metadata_indicators_row = ["UNIT", "LESSON", "MODULE", "SUBJECT", "OBJECTIVE"]
    has_metadata_indicator = any(
        indicator in first_row_clean for indicator in metadata_indicators_row
    )

    if not has_weekday:
        if has_metadata_indicator:
            logger.warning(
                "daily_plans_table_looks_like_metadata",
                extra={
                    "slot_number": slot_number,
                    "table_index": table_end,
                    "first_row": first_row_text[:200],
                    "note": "Table appears to contain metadata instead of daily plans. Proceeding anyway."
                }
            )
        else:
            raise ValueError(
                f"Slot {slot_number} table {table_end} doesn't look like daily plans table. "
                f"Expected weekday headers but got: '{first_row_text[:100]}'"
            )

    logger.info(
        "slot_structure_validated",
        extra={
            "slot_number": slot_number,
            "table_start": table_start,
            "table_end": table_end,
            "total_tables": table_count,
            "available_slots": available_slots,
        },
    )

    return table_start, table_end
