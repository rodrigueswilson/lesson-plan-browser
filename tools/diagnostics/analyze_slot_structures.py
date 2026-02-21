"""
Diagnostic script to analyze slot structures in source DOCX files.
Identifies slot numbering inconsistencies and documents actual slot layouts.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.docx_parser import DOCXParser, validate_slot_structure


def analyze_document_slots(file_path: Path) -> Dict[str, Any]:
    """
    Analyze slot structure of a DOCX document.

    Returns:
        Dictionary with slot analysis including:
        - total_slots: Number of slots in document
        - slot_details: List of slot metadata
        - table_count: Total number of tables
        - has_signature: Whether signature table exists
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}", "file_path": str(file_path)}

    try:
        parser = DOCXParser(str(file_path))
        doc = parser.doc

        total_tables = len(doc.tables)

        # Check for signature table
        has_signature = False
        if total_tables > 0:
            last_table = doc.tables[-1]
            if last_table.rows and last_table.rows[0].cells:
                first_cell = last_table.rows[0].cells[0].text.strip().lower()
                if "signature" in first_cell or "required signatures" in first_cell:
                    has_signature = True

        # Calculate available slots
        if has_signature:
            available_slots = (total_tables - 1) // 2
        else:
            available_slots = total_tables // 2

        slot_details = []

        for slot_num in range(1, available_slots + 1):
            try:
                table_start, table_end = validate_slot_structure(doc, slot_num)
                meta_table = doc.tables[table_start]

                # Extract metadata
                slot_metadata = {
                    "slot_number": slot_num,
                    "table_start": table_start,
                    "table_end": table_end,
                    "subject": None,
                    "teacher": None,
                    "homeroom": None,
                    "grade": None,
                    "week_of": None,
                }

                for row in meta_table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        cell_lower = cell_text.lower()

                        if "subject:" in cell_lower:
                            slot_metadata["subject"] = cell_text.split(":", 1)[
                                -1
                            ].strip()
                        if "name:" in cell_lower or "teacher:" in cell_lower:
                            slot_metadata["teacher"] = cell_text.split(":", 1)[
                                -1
                            ].strip()
                        if "homeroom:" in cell_lower:
                            slot_metadata["homeroom"] = cell_text.split(":", 1)[
                                -1
                            ].strip()
                        if "grade:" in cell_lower:
                            slot_metadata["grade"] = cell_text.split(":", 1)[-1].strip()
                        if "week" in cell_lower and "of" in cell_lower:
                            slot_metadata["week_of"] = (
                                cell_text.split(":", 1)[-1].strip()
                                if ":" in cell_text
                                else cell_text
                            )

                slot_details.append(slot_metadata)

            except ValueError as e:
                slot_details.append({"slot_number": slot_num, "error": str(e)})

        return {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "total_tables": total_tables,
            "has_signature": has_signature,
            "available_slots": available_slots,
            "slot_details": slot_details,
        }

    except Exception as e:
        return {
            "error": str(e),
            "file_path": str(file_path),
            "file_name": file_path.name,
        }


def analyze_week_folder(week_folder_path: Path) -> Dict[str, Any]:
    """
    Analyze all DOCX files in a week folder.

    Args:
        week_folder_path: Path to week folder

    Returns:
        Dictionary with analysis of all documents
    """
    if not week_folder_path.exists():
        return {
            "error": f"Week folder not found: {week_folder_path}",
            "week_folder": str(week_folder_path),
        }

    docx_files = list(week_folder_path.glob("*.docx"))

    results = {
        "week_folder": str(week_folder_path),
        "total_files": len(docx_files),
        "documents": [],
    }

    for docx_file in sorted(docx_files):
        analysis = analyze_document_slots(docx_file)
        results["documents"].append(analysis)

    return results


def compare_with_user_slots(
    document_analysis: Dict[str, Any], user_slots: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare document slot structure with user's slot configuration.

    Args:
        document_analysis: Result from analyze_document_slots()
        user_slots: List of user slot configurations

    Returns:
        Comparison results showing mismatches
    """
    if "error" in document_analysis:
        return {"error": "Cannot compare - document analysis failed"}

    mismatches = []
    matches = []

    for user_slot in user_slots:
        requested_slot = user_slot.get("slot_number")
        requested_subject = user_slot.get("subject")
        teacher_pattern = (
            user_slot.get("primary_teacher_file_pattern")
            or user_slot.get("primary_teacher_name")
            or f"{user_slot.get('primary_teacher_first_name', '')} {user_slot.get('primary_teacher_last_name', '')}".strip()
        )

        # Try to find matching slot in document
        found_slot = None
        for slot_detail in document_analysis.get("slot_details", []):
            if slot_detail.get("error"):
                continue

            slot_subject = slot_detail.get("subject", "").lower()
            slot_teacher = slot_detail.get("teacher", "").lower()

            # Check if subject matches
            subject_match = False
            if requested_subject:
                req_subj_lower = requested_subject.lower()
                if req_subj_lower in slot_subject or slot_subject in req_subj_lower:
                    subject_match = True
                # Handle combined subjects like "ELA/SS"
                if "/" in req_subj_lower:
                    tokens = req_subj_lower.split("/")
                    if any(token.strip() in slot_subject for token in tokens):
                        subject_match = True

            # Check if teacher matches (if pattern provided)
            teacher_match = True
            if teacher_pattern:
                teacher_pattern_lower = teacher_pattern.lower()
                if teacher_pattern_lower not in slot_teacher:
                    teacher_match = False

            if subject_match and teacher_match:
                found_slot = slot_detail.get("slot_number")
                break

        if found_slot:
            if found_slot != requested_slot:
                mismatches.append(
                    {
                        "requested_slot": requested_slot,
                        "actual_slot": found_slot,
                        "subject": requested_subject,
                        "teacher_pattern": teacher_pattern,
                        "document_slot_subject": next(
                            (
                                s.get("subject")
                                for s in document_analysis.get("slot_details", [])
                                if s.get("slot_number") == found_slot
                            ),
                            None,
                        ),
                    }
                )
            else:
                matches.append(
                    {
                        "slot": requested_slot,
                        "subject": requested_subject,
                        "teacher_pattern": teacher_pattern,
                    }
                )

    return {
        "document": document_analysis.get("file_name"),
        "total_user_slots": len(user_slots),
        "matches": matches,
        "mismatches": mismatches,
        "match_count": len(matches),
        "mismatch_count": len(mismatches),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze slot structures in DOCX files"
    )
    parser.add_argument("--file", type=str, help="Path to single DOCX file to analyze")
    parser.add_argument(
        "--folder", type=str, help="Path to week folder to analyze all DOCX files"
    )
    parser.add_argument("--output", type=str, help="Output JSON file path")

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        result = analyze_document_slots(file_path)
        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

    elif args.folder:
        folder_path = Path(args.folder)
        result = analyze_week_folder(folder_path)
        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

    else:
        print("Please provide either --file or --folder argument")
        parser.print_help()
