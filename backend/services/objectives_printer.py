"""
Simple module to extract and print objectives from lesson plans.

This module helps teachers print objectives from their lesson plans,
either from JSON files or from the database (if lesson_json is stored).

Public API: extract_subject_from_unit_lesson, ObjectivesPrinter,
print_objectives_from_file, print_objectives_from_plan.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.objectives import (
    docx_renderer,
    extraction,
    formatting,
    font_calculation,
    printing,
    subject_parsing,
)


def extract_subject_from_unit_lesson(unit_lesson: str) -> str:
    """
    Extract the actual subject from the unit_lesson text.

    This function parses patterns like:
    - "Unit 3 Lesson 9: MEASURE TO FIND THE AREA" -> "Math"
    - "Math Chapter 5: MULTIPLICATION FACTS" -> "Math"
    - "ELA Unit 2: READING COMPREHENSION" -> "ELA"
    - "Science Lab: PLANT GROWTH" -> "Science"

    Args:
        unit_lesson: The unit/lesson text from the lesson plan

    Returns:
        Detected subject name or "Unknown" if not found
    """
    return subject_parsing.extract_subject_from_unit_lesson(unit_lesson)


class ObjectivesPrinter:
    """Extract and format objectives from lesson plans for printing."""

    DAY_NAMES = extraction.DAY_NAMES

    def __init__(self) -> None:
        pass

    def load_from_json_file(self, json_path: str) -> Dict[str, Any]:
        """Load lesson plan from JSON file."""
        json_file = Path(json_path)
        if not json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_file, "r", encoding="utf-8") as f:
            lesson_json = json.load(f)

        return lesson_json

    def load_from_database(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load lesson plan from database."""
        from backend.database import get_db

        db = get_db()
        plan = db.get_weekly_plan(plan_id)

        if not plan:
            return None

        lesson_json = plan.get("lesson_json")

        if isinstance(lesson_json, str):
            return json.loads(lesson_json)
        elif isinstance(lesson_json, dict):
            return lesson_json

        return None

    def extract_objectives(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all objectives from lesson plan."""
        return extraction.extract_objectives(lesson_json)

    def format_for_print(
        self, objectives: List[Dict[str, Any]], format_type: str = "text"
    ) -> str:
        """Format objectives for printing."""
        return formatting.format_for_print(objectives, format_type)

    def save_to_file(
        self,
        objectives: List[Dict[str, Any]],
        output_path: str,
        format_type: str = "text",
    ) -> str:
        """Save formatted objectives to file."""
        return printing.save_to_file(objectives, output_path, format_type)

    def print_objectives(
        self,
        source: str,
        source_type: str = "file",
        output_path: Optional[str] = None,
        format_type: str = "text",
    ) -> str:
        """Main method to extract and print objectives."""
        if source_type == "database":
            lesson_json = self.load_from_database(source)
            if not lesson_json:
                raise ValueError(f"Plan not found in database: {source}")
        else:
            lesson_json = self.load_from_json_file(source)

        objectives = self.extract_objectives(lesson_json)

        if not objectives:
            return "No objectives found in lesson plan."

        formatted = self.format_for_print(objectives, format_type)

        if output_path:
            self.save_to_file(objectives, output_path, format_type)

        return formatted

    def calculate_font_size(
        self,
        text: str,
        available_width: float,
        available_height: float,
        base_font_size: int,
        min_font_size: int,
        max_font_size: int,
    ) -> int:
        """Calculate optimal font size to maximize text fill in available space."""
        return font_calculation.calculate_font_size(
            text,
            available_width,
            available_height,
            base_font_size,
            min_font_size,
            max_font_size,
        )

    def calculate_font_size_to_fill_height(
        self,
        text: str,
        available_width: float,
        target_height: float,
        min_font_size: int,
        max_font_size: int,
        char_width_ratio: float = 0.6,
        line_height_ratio: float = 1.3,
    ) -> int:
        """Calculate maximum font size that fits within target height."""
        return font_calculation.calculate_font_size_to_fill_height(
            text,
            available_width,
            target_height,
            min_font_size,
            max_font_size,
            char_width_ratio,
            line_height_ratio,
        )

    def generate_docx(
        self,
        lesson_json: Dict[str, Any],
        output_path: str,
        user_name: Optional[str] = None,
        week_of: Optional[str] = None,
    ) -> str:
        """Generate DOCX file with objectives, one lesson per page."""
        return docx_renderer.generate_docx(
            lesson_json, output_path, user_name, week_of
        )


def print_objectives_from_file(
    json_path: str, output_path: Optional[str] = None
) -> str:
    """Convenience function to print objectives from JSON file."""
    printer = ObjectivesPrinter()
    return printer.print_objectives(
        json_path, source_type="file", output_path=output_path
    )


def print_objectives_from_plan(plan_id: str, output_path: Optional[str] = None) -> str:
    """Convenience function to print objectives from database plan."""
    printer = ObjectivesPrinter()
    return printer.print_objectives(
        plan_id, source_type="database", output_path=output_path
    )
