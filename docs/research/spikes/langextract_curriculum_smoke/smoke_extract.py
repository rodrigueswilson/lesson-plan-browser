"""
Research-only: LangExtract on a short curriculum-like paragraph or file input.
Requires LANGEXTRACT_API_KEY for cloud Gemini (see README).
"""
from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SPIKE_DIR = Path(__file__).resolve().parent
if str(_SPIKE_DIR) not in sys.path:
    sys.path.insert(0, str(_SPIKE_DIR))

from char_interval_verify import verify_grounded_extractions  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

_SHORT_FIXTURE = (
    "Lesson 4: Area models. Procedure: Warm-up 5 minutes. Pairs build rectangles on grid paper."
)


def _resolve_input_text() -> tuple[str, str]:
    """
    Return (text, description) for logging. LANGEXTRACT_SMOKE_INPUT_FILE is UTF-8 text,
    path relative to repo root if not absolute.
    """
    path_raw = os.getenv("LANGEXTRACT_SMOKE_INPUT_FILE")
    if path_raw:
        p = Path(path_raw)
        if not p.is_absolute():
            p = _REPO_ROOT / p
        if not p.is_file():
            print(f"LANGEXTRACT_SMOKE_INPUT_FILE not found: {p}", file=sys.stderr)
            sys.exit(1)
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            label = str(p.relative_to(_REPO_ROOT))
        except ValueError:
            label = str(p)
        return text, label
    return _SHORT_FIXTURE, "built-in short fixture"


def main() -> None:
    # Windows consoles often default to cp1252; model output can include Unicode (e.g. minus U+2212).
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            pass

    input_text, input_label = _resolve_input_text()
    print(f"input={input_label} chars={len(input_text)}")

    key = os.getenv("LANGEXTRACT_API_KEY")
    if not key:
        print(
            "No LANGEXTRACT_API_KEY. Get a key from AI Studio (Gemini) and export it. "
            "Skipping live extract."
        )
        return

    try:
        import langextract as lx  # pyright: ignore[reportMissingImports]
    except ImportError:
        print("Install: pip install langextract", file=sys.stderr)
        sys.exit(1)

    prompt = textwrap.dedent(
        """\
        Extract lesson_number (integer), and any procedure_instructions as an activity extraction
        with extraction_class "procedure". Use exact substrings from the text for extraction_text.
        """
    )

    examples = [
        lx.data.ExampleData(
            text="Lesson 2: Comparing lengths. Procedure: Students use strip diagrams then share out.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="lesson_number",
                    extraction_text="Lesson 2",
                    attributes={"value": 2},
                ),
                lx.data.Extraction(
                    extraction_class="procedure",
                    extraction_text="Students use strip diagrams then share out.",
                    attributes={},
                ),
            ],
        )
    ]

    model_id = os.getenv("LANGEXTRACT_SMOKE_MODEL", "gemini-2.5-flash")

    result = lx.extract(
        text_or_documents=input_text,
        prompt_description=prompt,
        examples=examples,
        model_id=model_id,
        api_key=key,
    )
    grounded = [e for e in result.extractions if e.char_interval]
    print(f"model={model_id} extractions_total={len(result.extractions)} grounded={len(grounded)}")
    for e in result.extractions:
        st = getattr(e, "alignment_status", None)
        stv = getattr(st, "value", st) if st is not None else None
        print(
            f"  {e.extraction_class!r}: {e.extraction_text!r} "
            f"interval={e.char_interval} alignment={stv!r}"
        )

    strict_exact = os.getenv("LANGEXTRACT_SMOKE_REQUIRE_EXACT_ALIGNMENT", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    verify_errors = verify_grounded_extractions(
        input_text, result.extractions, require_all_exact=strict_exact
    )
    if verify_errors:
        for line in verify_errors:
            print(line, file=sys.stderr)
        sys.exit(1)
    print("char_interval_verify_ok")


if __name__ == "__main__":
    main()
