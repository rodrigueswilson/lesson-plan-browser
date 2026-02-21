"""
Mock LLM Service for Testing
Returns valid lesson plan JSON without calling real LLM API
"""

import json
from typing import Callable, Dict, Any, Optional, Tuple
from pathlib import Path


class MockLLMService:
    """Mock LLM service that returns valid test data"""
    
    def __init__(self):
        """Initialize mock service"""
        # Load a valid example to use as template
        self.template = self._load_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Load valid lesson template"""
        template_path = Path("tests/fixtures/valid_lesson_minimal.json")
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback minimal template
        return {
            "metadata": {
                "week_of": "10/6-10/10",
                "grade": "6",
                "subject": "Science"
            },
            "days": {
                "monday": {"unit_lesson": "Mock Lesson"},
                "tuesday": {"unit_lesson": "TBD"},
                "wednesday": {"unit_lesson": "TBD"},
                "thursday": {"unit_lesson": "TBD"},
                "friday": {"unit_lesson": "TBD"}
            }
        }
    
    def transform_lesson(
        self,
        primary_content: str,
        grade: str,
        subject: str,
        week_of: str,
        teacher_name: Optional[str] = None,
        homeroom: Optional[str] = None,
        plan_id: Optional[str] = None,
        available_days: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Mock transformation - returns valid test data
        
        Args:
            primary_content: Primary teacher's lesson content
            grade: Grade level
            subject: Subject area
            week_of: Week date range
            teacher_name: Teacher name (optional)
            homeroom: Homeroom (optional)
            plan_id: Plan ID for performance tracking (optional)
            available_days: List of days that have content (optional)
        
        Returns:
            Tuple of (success, lesson_json, error_message)
        """
        # Create response based on template
        lesson_json = self.template.copy()
        
        # Update metadata
        lesson_json["metadata"]["week_of"] = week_of
        lesson_json["metadata"]["grade"] = grade
        lesson_json["metadata"]["subject"] = subject
        
        if teacher_name:
            lesson_json["metadata"]["teacher_name"] = teacher_name
        if homeroom:
            lesson_json["metadata"]["homeroom"] = homeroom
        
        # Add mock content to all days (copy Monday data to other days for testing)
        if "days" in lesson_json:
            # Extract first meaningful line as unit/lesson (skip day headers)
            lines = primary_content.strip().split('\n')
            unit_lesson = "Mock Lesson"
            for line in lines:
                line_clean = line.strip().upper()
                # Skip day headers and empty lines
                if line_clean and line_clean not in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
                    unit_lesson = line[:100]
                    break
            
            # Fill all days with the same data for testing
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                if day in lesson_json["days"]:
                    lesson_json["days"][day]["unit_lesson"] = f"{subject} - {unit_lesson}"
        
        return True, lesson_json, None


# Singleton instance
_mock_service: Optional[MockLLMService] = None


def get_mock_llm_service() -> MockLLMService:
    """Get or create mock LLM service instance"""
    global _mock_service
    
    if _mock_service is None:
        _mock_service = MockLLMService()
    
    return _mock_service
