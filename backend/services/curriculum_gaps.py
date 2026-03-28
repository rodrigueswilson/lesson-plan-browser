"""
Gap detection: Google Doc links in original_lesson_plans vs scraped_registry.json.

Used by tools/scraper/gap_detect_db.py and GET /api/curriculum/gaps.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Tuple


def normalize_grade(grade_str: Any) -> str:
    if not grade_str:
        return "Uncategorized_Grade"
    grade_str = str(grade_str).lower().strip()
    if grade_str in ("k", "kindergarten"):
        return "Kindergarten"
    match = re.search(r"(\d+)", grade_str)
    if match:
        return f"Grade {match.group(1)}"
    return "Uncategorized_Grade"


def normalize_subject(subject_str: Any) -> str:
    if not subject_str:
        return "Uncategorized_Subject"
    subject_str = str(subject_str).upper().strip()
    if "/" in subject_str:
        return subject_str.split("/")[0]
    return subject_str


def extract_metadata(text: str) -> List[Dict[str, str]]:
    """Extract Unit, Lesson, and Google Doc links from markdown/plain text."""
    md_links = re.findall(
        r"\[([^\]]+)\]\((https?://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)[^)]*)\)",
        text,
    )
    bare_links = re.findall(
        r"(?<!\()https?://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)",
        text,
    )
    results: List[Dict[str, str]] = []
    unit_match = re.search(r"Unit\s*[:#]?\s*(\d+|[A-Z])", text, re.I)
    lesson_match = re.search(r"Lesson\s*[:#]?\s*(\d+)", text, re.I)
    unit = unit_match.group(1) if unit_match else "Unknown"
    lesson = lesson_match.group(1) if lesson_match else "Unknown"
    for title, _url, doc_id in md_links:
        results.append({"id": doc_id, "title": title, "unit": unit, "lesson": lesson})
    processed_ids = {r["id"] for r in results}
    for doc_id in bare_links:
        if doc_id not in processed_ids:
            results.append(
                {"id": doc_id, "title": "Untitled", "unit": unit, "lesson": lesson}
            )
    return results


def load_scraped_doc_ids(registry_path: str) -> set[str]:
    scraped_ids: set[str] = set()
    if not os.path.isfile(registry_path):
        return scraped_ids
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
    for grade in registry.values():
        if not isinstance(grade, dict):
            continue
        for subject in grade.values():
            if not isinstance(subject, dict):
                continue
            for unit in subject.values():
                if isinstance(unit, dict):
                    for doc_id in unit.keys():
                        scraped_ids.add(str(doc_id))
    return scraped_ids


def compute_planned_and_gaps(
    db_path: str,
    registry_path: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], int, int]:
    """
    Returns (planned_tree, gaps_tree, total_doc_refs, gap_doc_refs_count).
    Shapes: grade -> subject -> unit -> lesson -> {doc_id: title}
    """
    scraped_ids = load_scraped_doc_ids(registry_path)
    planned: Dict[str, Any] = {}
    gaps: Dict[str, Any] = {}
    total_found = 0
    new_gaps = 0

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT grade, subject, full_text FROM original_lesson_plans WHERE full_text IS NOT NULL"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    for g_raw, s_raw, text in rows:
        grade = normalize_grade(g_raw)
        subject = normalize_subject(s_raw)
        docs = extract_metadata(text or "")
        if not docs:
            continue
        if grade not in planned:
            planned[grade] = {}
        if subject not in planned[grade]:
            planned[grade][subject] = {}
        for doc in docs:
            doc_id = doc["id"]
            unit = f"Unit {doc['unit']}"
            lesson = f"Lesson {doc['lesson']}"
            title = doc["title"]
            if unit not in planned[grade][subject]:
                planned[grade][subject][unit] = {}
            if lesson not in planned[grade][subject][unit]:
                planned[grade][subject][unit][lesson] = {}
            planned[grade][subject][unit][lesson][doc_id] = title
            total_found += 1
            if doc_id not in scraped_ids:
                if grade not in gaps:
                    gaps[grade] = {}
                if subject not in gaps[grade]:
                    gaps[grade][subject] = {}
                if unit not in gaps[grade][subject]:
                    gaps[grade][subject][unit] = {}
                if lesson not in gaps[grade][subject][unit]:
                    gaps[grade][subject][unit][lesson] = {}
                gaps[grade][subject][unit][lesson][doc_id] = title
                new_gaps += 1

    return planned, gaps, total_found, new_gaps


def gap_summary_lines(gaps: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for grade in sorted(gaps.keys()):
        for subject in sorted(gaps[grade].keys()):
            unique_ids: set[str] = set()
            units: List[str] = []
            for unit_name, lessons in gaps[grade][subject].items():
                units.append(unit_name)
                for lesson_data in lessons.values():
                    for doc_id in lesson_data.keys():
                        unique_ids.add(doc_id)
            unique_units = sorted(set(units))
            key_units_str = ", ".join(unique_units[:5])
            if len(unique_units) > 5:
                key_units_str += "..."
            lines.append(
                f"{grade:<15} | {subject:<20} | {len(unique_ids):<12} | {key_units_str}"
            )
    return lines
