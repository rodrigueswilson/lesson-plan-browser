from typing import Dict, List, Optional
import re

class SubjectConfig:
    """
    Configuration for subject-specific parsing logic.
    Defines anchor headers and field mappings.
    """
    
    MATH = {
        "name": "Math",
        "anchors": {
            "learning_intentions": ["teacher-facing learning objective", "teacher objectives"],
            "purpose": ["lesson purpose"],
            "objectives_student": ["student-facing learning objective", "student objectives", "student goal"],
            "narrative_html": ["lesson narrative"],
            # Avoid bare "mlr" / "purpose": they match inside body lines (e.g. "MLR8…", "The purpose of this lesson…").
            "mlr": ["mathematical language routine", "routine(s)", "mathematical language routines"],
            "materials": ["materials", "materials needed", "required preparation", "material list"],
            "instructional_resources": ["supplemental resources", "formative assessment"],
            "procedure_html": [
                "daily tasks & procedure",
                "instructional steps",
                "activities",
                "procedure",
                "lesson delivery",
                "lesson activities",
                "warm-up",
                "cool-down",
                "activity synthesis",
            ],
            "vocabulary": ["vocabulary", "key terms"]
        },
        "patterns": {
            "lesson_title": re.compile(r"(?:LESSON\s+(\d+)|(\d+\.\d+\.\d+)\s+Teacher Guide)\s*[:\-]?\s*(.+)", re.IGNORECASE),
            "standards": re.compile(
                r"(?:NJSLS|NCTM)-MATH\.CONTENT\.[A-Z0-9\.\-]+|MP\d+|PR\d+",
                re.IGNORECASE,
            ),
        }
    }

    # NGSS / district science teacher guides: lesson headers often mirror ELA ("Lesson N:") or shout LESSON N.
    SCIENCE = {
        "name": "Science",
        "anchors": {
            "learning_intentions": [
                "learning objective",
                "learning objectives",
                "objectives",
                "essential question",
            ],
            "purpose": ["lesson purpose", "overview", "focus"],
            "objectives_student": [
                "student-facing",
                "students will",
                "i can",
                "success criteria",
            ],
            # Writer headings for phenomenon/setup live in procedure_html so openers are not
            # split away from THE LESSON IN ACTION (procedure_html was empty on some lessons).
            "narrative_html": [],
            "mlr": ["science and engineering practice", "sep ", "crosscutting"],
            "materials": ["materials", "materials needed", "prep", "safety"],
            "instructional_resources": ["resources", "supplemental", "formative"],
            "procedure_html": [
                "procedure",
                "instructional sequence",
                "explore",
                "elaborate",
                "engage",
                "explain",
                "evaluate",
                "activities",
                "lesson activities",
                # Newark-style Grade 2 Science teacher guide section boundaries (ADR-003).
                "the lesson in action",
                "do it now in science",
                "online learning activities",
                "lesson opening",
                "during the lesson",
                "lesson closing",
                "lesson narrative",
                "background",
                "phenomenon",
            ],
            "vocabulary": ["vocabulary", "key terms", "academic vocabulary"],
        },
        "patterns": {
            # Same capture layout as MATH: lesson number in group 1 OR 2, title in group 3.
            "lesson_title": re.compile(
                r"(?:(?:LESSON|Lesson)\s+(\d+)|(\d+\.\d+\.\d+)\s+Teacher Guide)\s*[:\-]?\s*(.+)",
                re.IGNORECASE,
            ),
            "standards": re.compile(
                r"NGSS[\w.\-]+|NJSLS[\w.\-]+|"
                r"\d+-[A-Z]{1,6}\d[\w.\-]*|"
                r"(?:PS|LS|ESS|ETS)[\w.\-]+",
                re.IGNORECASE,
            ),
        },
    }

    # Unit-level "Summary of Key Learning" matrix (row 1 title, row 2 headers). SSOT for ela_summary_table.
    ELA_SUMMARY_TABLE = {
        "title": "summary of key learning",
        "headers": [
            "lesson",
            "learning intentions and success criteria",
            "daily instructional task",
            "content and learning strategies",
        ],
    }

    ELA = {
        "name": "ELA",
        "anchors": {
            "learning_intentions": ["learning intention"],
            "success_criteria": ["success criteria"],
            "daily_instructional_task": ["daily instructional task"],
            "practices": ["key instructional practices"],
            "procedures": ["learning procedures"],
            "differentiation": ["differentiation"],
        },
        "patterns": {
            "lesson_title": re.compile(r"Lesson\s+(\d+)\s*[:\-]\s*(.+)", re.IGNORECASE),
            # Spelled-out NJSLS lines (smoke tests) plus compact NJ codes in teacher guides (e.g. RI.CR.3.1).
            "standards": re.compile(
                r"NJSLS\s+[A-Z]+\.[A-Z0-9\.]+|(?:RL|RI|SL|W|L)\.[A-Z]{1,4}\.\d+\.\d+",
                re.IGNORECASE,
            ),
            # Broader findall for standards tokens in summary-matrix column D (Grade 2–3, NJ SS-style ids).
            "standards_summary_mentions": re.compile(
                r"NJSLS\s+[A-Z]+\.[A-Z0-9\.]+|"
                r"(?:RL|RI|SL|W|L)\.[A-Z]{1,4}\.\d+\.\d+[A-Za-z]?(?:-[A-Z])?|"
                r"6\.1\.\d+\.[A-Za-z][A-Za-z0-9\.]*",
                re.IGNORECASE,
            ),
        }
    }

    @classmethod
    def get_config(cls, subject: str) -> Dict:
        u = subject.upper()
        if u == "MATH":
            return cls.MATH
        if u == "ELA":
            return cls.ELA
        if u in ("SCIENCE", "SCI"):
            return cls.SCIENCE
        return cls.MATH  # Default to Math
