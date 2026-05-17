"""
Verify LangExtract-style char_interval grounding against the source string.

Semantics match langextract.core.data.CharInterval: start_pos inclusive, end_pos exclusive.

LangExtract's WordAligner sets alignment_status (match_exact, match_lesser, match_fuzzy).
Requiring slice == extraction_text for every row fights that design: MATCH_LESSER / MATCH_FUZZY
are intentional non-exact spans (see google/langextract resolver + prompt_validation).

Default policy:
  - match_exact: source slice must equal extraction_text
  - match_lesser / match_fuzzy / match_greater: interval in bounds and non-empty slice (library already aligned)
  - no alignment_status (duck-typed fixtures): whitespace-collapsed equality (handles layout spaces)

Optional: require_all_exact=True (env LANGEXTRACT_SMOKE_REQUIRE_EXACT_ALIGNMENT=1 in smoke_extract)
fails if any grounded extraction is not match_exact — stricter product-style gate.
"""
from __future__ import annotations

from typing import Any


def _interval_bounds(char_interval: Any) -> tuple[int | None, int | None]:
    if char_interval is None:
        return None, None
    if isinstance(char_interval, (tuple, list)) and len(char_interval) == 2:
        a, b = char_interval[0], char_interval[1]
        if isinstance(a, int) and isinstance(b, int):
            return a, b
        return None, None
    sp = getattr(char_interval, "start_pos", None)
    ep = getattr(char_interval, "end_pos", None)
    if isinstance(sp, int) and isinstance(ep, int):
        return sp, ep
    return None, None


def _collapse_ws(s: str) -> str:
    """Same idea as langextract.prompt_validation._preview: single spaces."""
    return " ".join(s.split())


def _alignment_status_str(status: Any) -> str | None:
    if status is None:
        return None
    v = getattr(status, "value", None)
    if isinstance(v, str):
        return v
    if isinstance(status, str):
        return status
    return None


def slice_for_char_interval(source_text: str, char_interval: Any) -> str | None:
    sp, ep = _interval_bounds(char_interval)
    if sp is None or ep is None:
        return None
    return source_text[sp:ep]


def verify_grounded_extractions(
    source_text: str,
    extractions: list[Any],
    *,
    require_all_exact: bool = False,
) -> list[str]:
    """
    Validate grounded extractions. Returns human-readable error lines (empty if OK).

    Ungrounded rows (no char_interval) are skipped.
    """
    n = len(source_text)
    errors: list[str] = []
    for i, ex in enumerate(extractions):
        ci = getattr(ex, "char_interval", None)
        sp, ep = _interval_bounds(ci)
        if sp is None and ep is None:
            continue
        if sp is None or ep is None:
            errors.append(
                f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                f"incomplete char_interval {ci!r}"
            )
            continue
        etext = getattr(ex, "extraction_text", "") or ""
        if sp < 0 or ep < sp or ep > n:
            errors.append(
                f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                f"char_interval ({sp}, {ep}) out of range for text length {n}"
            )
            continue

        got = source_text[sp:ep]
        status = _alignment_status_str(getattr(ex, "alignment_status", None))

        if require_all_exact:
            if status != "match_exact":
                errors.append(
                    f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                    f"require_all_exact but alignment_status={status!r} (expected 'match_exact')"
                )
            elif got != etext:
                errors.append(
                    f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                    f"slice[{sp}:{ep}] != extraction_text\n"
                    f"  slice:     {got!r}\n"
                    f"  expected:  {etext!r}"
                )
            continue

        if status == "match_exact":
            if got != etext:
                errors.append(
                    f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                    f"match_exact but slice[{sp}:{ep}] != extraction_text\n"
                    f"  slice:     {got!r}\n"
                    f"  expected:  {etext!r}"
                )
        elif status in ("match_lesser", "match_fuzzy", "match_greater"):
            if not got.strip() or not etext.strip():
                errors.append(
                    f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                    f"alignment_status={status!r} but empty slice or extraction_text"
                )
        else:
            # No status (tests / older objects): tolerate layout whitespace only.
            if _collapse_ws(got) != _collapse_ws(etext):
                errors.append(
                    f"extraction[{i}] {getattr(ex, 'extraction_class', '?')!r}: "
                    f"no alignment_status; whitespace-normalized slice != extraction_text\n"
                    f"  slice:     {_collapse_ws(got)!r}\n"
                    f"  expected:  {_collapse_ws(etext)!r}"
                )
    return errors
