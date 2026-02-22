"""CLI entry point for python -m tools.docx_renderer."""

import json
import sys

from tools.docx_renderer.renderer import DOCXRenderer


def main() -> None:
    """Run DOCX renderer from command line: input.json output.docx [template.docx]."""
    if len(sys.argv) < 3:
        print(
            "Usage: python docx_renderer.py <input.json> <output.docx> [template.docx]"
        )
        print("\nExample:")
        print(
            "  python docx_renderer.py tests/fixtures/valid_lesson_minimal.json output/lesson.docx"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    template_path = (
        sys.argv[3]
        if len(sys.argv) > 3
        else "input/Lesson Plan Template SY'25-26.docx"
    )

    with open(input_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    renderer = DOCXRenderer(template_path)
    success = renderer.render(json_data, output_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
