"""
Research-only: Instructor + Pydantic on a curriculum-like fixture.
See README.md in this directory.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

load_dotenv(_REPO_ROOT / ".env")

from backend.llm.api_key import get_openai_api_key_for_tests  # noqa: E402

FIXTURE = """
Lesson 3: Area models

Daily instructional task: Students build rectangles on grid paper.

Procedure: Warm-up 5 min. Launch with the anchor chart. Activity: pairs use
unit squares to find area. Cool-down: exit ticket on which shape has greater area.
"""


class LessonExtractStub(BaseModel):
    """Minimal slice; expand only when wired to real lesson schema."""

    lesson_number: Optional[int] = Field(None, description="Lesson index if stated")
    procedure_html: Optional[str] = Field(
        None,
        description="Procedure body; may be plain text for this smoke test",
    )


def main() -> None:
    model = os.getenv("INSTRUCTOR_SMOKE_MODEL", "gpt-4o-mini")
    key = get_openai_api_key_for_tests(model=model)
    if not key:
        print(
            "No API key set. For smokes prefer OPENAI_API_KEY_TESTS (or GPT5_API_KEY_TESTS "
            "for gpt-5* smoke models), or set OPENAI_API_KEY / GPT5_API_KEY / LLM_API_KEY. "
            "Install deps: pip install instructor openai pydantic. Skipping live call."
        )
        return

    try:
        import instructor
        from openai import OpenAI
    except ImportError as e:
        print(f"Missing dependency: {e}. Run: pip install instructor openai pydantic")
        sys.exit(1)

    client = instructor.from_openai(OpenAI(api_key=key))
    result = client.chat.completions.create(
        model=model,
        response_model=LessonExtractStub,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract lesson fields from the teacher-guide excerpt. "
                    "Use null for unknown fields. procedure_html may be plain text."
                ),
            },
            {"role": "user", "content": FIXTURE.strip()},
        ],
    )
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
