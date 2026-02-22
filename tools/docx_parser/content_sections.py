"""
Subject and section content extraction for DOCX parsing.
"""

import re
from typing import Any, Callable, Dict, List, Optional


def find_subject_sections(doc, tables: List, get_full_text: Callable[[], str]) -> Dict[str, Any]:
    """Find different subject sections in the document."""
    sections = {}
    for i, table in enumerate(doc.tables):
        if len(table.rows) == 1:
            for cell in table.rows[0].cells:
                text = cell.text.strip()
                if "Subject:" in text:
                    subject = text.replace("Subject:", "").strip()
                    sections[subject] = {
                        "type": "table",
                        "header_table": i,
                        "lesson_table": i + 1 if i + 1 < len(doc.tables) else None,
                    }
                    break

    if not sections:
        full_text = get_full_text()
        subjects = ["math", "science", "ela", "english", "social studies", "history"]
        for subject in subjects:
            pattern = rf"\b{subject}\b"
            if re.search(pattern, full_text, re.IGNORECASE):
                sections[subject.lower()] = {"type": "text", "found": True}
    return sections


def extract_by_heading(
    paragraphs: List[str], heading_text: str, case_sensitive: bool = False
) -> List[str]:
    """Extract content following a specific heading."""
    content = []
    found_heading = False
    for para in paragraphs:
        if not case_sensitive:
            match = heading_text.lower() in para.lower()
        else:
            match = heading_text in para
        if match and len(para) < 100:
            found_heading = True
            continue
        if found_heading:
            if len(para) < 50 and para.isupper():
                break
            content.append(para)
    return content


def extract_table_by_header(tables: List[List[List[str]]], header_text: str) -> Optional[List[List[str]]]:
    """Extract table that contains specific header text."""
    for table in tables:
        if not table:
            continue
        first_row = table[0]
        for cell in first_row:
            if header_text.lower() in cell.lower():
                return table
    return None


def extract_table_lesson(doc, table_index: int, get_cell_text_fn: Callable) -> Dict[str, Any]:
    """Extract lesson content from a table (Davies' format)."""
    if table_index >= len(doc.tables):
        return {}
    table = doc.tables[table_index]
    content = {}
    days = []
    for cell in table.rows[0].cells[1:]:
        day = cell.text.strip()
        if day:
            days.append(day)
    for row in table.rows[1:]:
        row_label = row.cells[0].text.strip()
        if not row_label:
            continue
        for i, day in enumerate(days):
            if day not in content:
                content[day] = {}
            cell = row.cells[i + 1]
            cell_text = get_cell_text_fn(cell)
            if cell_text:
                content[day][row_label] = cell_text
    return content


def extract_objectives(content: List[str]) -> List[str]:
    """Extract learning objectives from content."""
    objectives = []
    in_objectives = False
    keywords_start = ["objective", "goal", "learning target", "swbat", "students will"]
    keywords_stop = ["activity", "procedure", "assessment", "material"]
    for para in content:
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords_start):
            in_objectives = True
            if ":" in para:
                obj_text = para.split(":", 1)[1].strip()
                if obj_text:
                    objectives.append(obj_text)
            continue
        if in_objectives:
            if any(kw in para_lower for kw in keywords_stop):
                in_objectives = False
            else:
                objectives.append(para)
    return objectives


def extract_activities(content: List[str]) -> List[str]:
    """Extract learning activities from content."""
    activities = []
    in_activities = False
    keywords_start = ["activity", "activities", "procedure", "lesson", "instruction"]
    keywords_stop = ["assessment", "material", "homework", "closure"]
    for para in content:
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords_start):
            in_activities = True
            if ":" in para:
                act_text = para.split(":", 1)[1].strip()
                if act_text:
                    activities.append(act_text)
            continue
        if in_activities:
            if any(kw in para_lower for kw in keywords_stop):
                in_activities = False
            else:
                activities.append(para)
    return activities


def extract_assessments(content: List[str]) -> List[str]:
    """Extract assessments from content."""
    assessments = []
    in_assessments = False
    keywords_start = ["assessment", "evaluate", "check for understanding", "exit ticket"]
    keywords_stop = ["material", "homework", "closure", "extension"]
    for para in content:
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords_start):
            in_assessments = True
            if ":" in para:
                assess_text = para.split(":", 1)[1].strip()
                if assess_text:
                    assessments.append(assess_text)
            continue
        if in_assessments:
            if any(kw in para_lower for kw in keywords_stop):
                in_assessments = False
            else:
                assessments.append(para)
    return assessments


def extract_materials(content: List[str]) -> List[str]:
    """Extract materials/resources from content."""
    materials = []
    in_materials = False
    keywords_start = ["material", "resource", "supplies", "equipment"]
    keywords_stop = ["objective", "activity", "procedure", "assessment"]
    for para in content:
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords_start):
            in_materials = True
            if ":" in para:
                mat_text = para.split(":", 1)[1].strip()
                if mat_text:
                    materials.append(mat_text)
            continue
        if in_materials:
            if any(kw in para_lower for kw in keywords_stop):
                in_materials = False
            else:
                materials.append(para)
    return materials


def extract_subject_content(
    doc,
    tables: List,
    paragraphs: List[str],
    subject: str,
    get_full_text: Callable,
    is_day_no_school: Callable[[str], bool],
    extract_table_lesson_fn: Callable,
    get_cell_text_fn: Callable,
    strip_urls: bool = True,
) -> Dict[str, Any]:
    """Extract content for a specific subject. extract_table_lesson_fn(table_index) returns dict of day -> {label -> text}."""
    sections = find_subject_sections(doc, tables, get_full_text)
    subject_mappings = {
        "language arts": ["ela", "english", "reading", "literacy"],
        "math": ["mathematics", "math"],
        "science": ["science", "sci", "science/health"],
        "social studies": ["ss", "social studies", "history"],
        "ela": ["ela", "english", "language arts", "reading"],
        "ela/ss": ["ela/ss", "language arts/social studies"],
    }
    subject_lower = subject.lower()
    possible_names = [subject_lower]
    for canonical, aliases in subject_mappings.items():
        if subject_lower in aliases or subject_lower == canonical:
            possible_names.extend(aliases)
            break

    for key, info in sections.items():
        key_lower = key.lower()
        if any(name in key_lower for name in possible_names):
            if info.get("type") == "table" and info.get("lesson_table") is not None:
                table_content = extract_table_lesson_fn(info["lesson_table"])
                full_text_parts = []
                no_school_days = []
                for day, day_content in table_content.items():
                    day_text = " ".join(day_content.values())
                    if is_day_no_school(day_text):
                        no_school_days.append(day)
                        full_text_parts.append(f"\n{day.upper()}")
                        full_text_parts.append("Unit/Lesson: No School")
                        for label, text in day_content.items():
                            label_lower = label.lower()
                            if "unit" not in label_lower and "lesson" not in label_lower:
                                full_text_parts.append(f"{label} {text}")
                            elif text.strip() and text.strip().lower() != "no school":
                                full_text_parts.append(f"{label} {text}")
                    else:
                        full_text_parts.append(f"\n{day.upper()}")
                        for label, text in day_content.items():
                            full_text_parts.append(f"{label} {text}")
                return {
                    "subject": key,
                    "full_text": "\n".join(full_text_parts),
                    "table_content": table_content,
                    "no_school_days": no_school_days,
                    "found": True,
                    "format": "table",
                }
            elif info.get("type") == "text":
                full_text = get_full_text(strip_urls=strip_urls)
                content = [p.strip() for p in full_text.split("\n") if p.strip()]
                return {
                    "subject": subject,
                    "full_text": full_text,
                    "found": True,
                    "format": "text",
                    "objectives": extract_objectives(content),
                    "activities": extract_activities(content),
                    "assessments": extract_assessments(content),
                    "materials": extract_materials(content),
                }

    full_text = get_full_text(strip_urls=strip_urls)
    content = [p.strip() for p in full_text.split("\n") if p.strip()]
    return {
        "subject": subject,
        "full_text": full_text,
        "found": False,
        "format": "unknown",
        "objectives": extract_objectives(content),
        "activities": extract_activities(content),
        "assessments": extract_assessments(content),
        "materials": extract_materials(content),
    }


def list_available_subjects(sections: Dict[str, Any]) -> List[str]:
    """List all potential subjects found in the document."""
    return list(sections.keys())
