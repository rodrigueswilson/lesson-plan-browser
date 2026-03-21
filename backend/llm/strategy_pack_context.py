"""
Build injected strategy-pack context for LLM prompts and validate ell_support ids.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.llm.domain_analysis import _canonical_strategy_id
from backend.metrics import record_strategy_pack_injection_chars
from backend.telemetry import logger

_PACK_DIR_NAME = "strategies_pack_v2"
_INDEX_NAME = "_index.json"
_MAX_INJECTION_CHARS = 14_000
_TRIM_KEYS = (
    "id",
    "strategy_name",
    "core_principle",
    "implementation_steps",
    "applicable_contexts",
    "skill_weights",
    "delivery_modes",
    "l1_modes",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@lru_cache(maxsize=1)
def _load_index() -> Dict[str, Any]:
    path = _project_root() / _PACK_DIR_NAME / _INDEX_NAME
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def all_pack_strategy_ids() -> frozenset[str]:
    """Canonical ids from strategies_pack_v2/_index.json category lists."""
    data = _load_index()
    out: set[str] = set()
    for cat in (data.get("categories") or {}).values():
        for sid in cat.get("strategies") or []:
            out.add(str(sid).strip())
    return frozenset(out)


def allowed_strategy_ids_retry_suffix() -> str:
    """Short appendix for validation/retry messages when ids are invalid."""
    ids = sorted(all_pack_strategy_ids())
    if not ids:
        return ""
    return (
        "\n\nReference: each `tailored_instruction.ell_support[].strategy_id` must be one of "
        "the pack ids (legacy aliases are accepted): "
        + ", ".join(ids)
        + "."
    )


def _grade_to_cluster(grade: str) -> str:
    g = (grade or "").strip().lower()
    if g in ("k", "kindergarten", "0"):
        return "K-2"
    if g.isdigit():
        n = int(g)
        if n <= 2:
            return "K-2"
        if n <= 5:
            return "3-5"
        if n <= 8:
            return "6-8"
        return "9-12"
    if "9" in g or "10" in g or "11" in g or "12" in g:
        return "9-12"
    return "3-5"


def _subject_to_lesson_type(subject: str) -> str:
    s = (subject or "").lower()
    if any(x in s for x in ("ela", "english", "literacy", "reading")):
        return "reading_comprehension"
    if "writing" in s:
        return "writing_workshop"
    if "math" in s:
        return "math_problem_solving"
    if "science" in s:
        return "science_inquiry"
    if any(x in s for x in ("social", "history", "civics", "ss")):
        return "social_studies_discussion"
    return "reading_comprehension"


def _select_category_keys(grade: str, subject: str) -> List[str]:
    data = _load_index()
    rules = data.get("selection_rules") or {}
    by_lt = rules.get("by_lesson_type") or {}
    by_gc = rules.get("by_grade_cluster") or {}
    lt = _subject_to_lesson_type(subject)
    gc = _grade_to_cluster(grade)
    keys: List[str] = []
    keys.extend(by_lt.get(lt, []))
    keys.extend(by_gc.get(gc, []))
    seen: Set[str] = set()
    out: List[str] = []
    for k in keys:
        if k not in seen and k in (data.get("categories") or {}):
            seen.add(k)
            out.append(k)
    if not out:
        fb = (data.get("loading_algorithm") or {}).get("fallback_rules") or {}
        if fb.get("if_uncertain"):
            out = ["language_skills"]
    return out[:4]


def _trim_strategy(obj: Dict[str, Any]) -> Dict[str, Any]:
    return {k: obj[k] for k in _TRIM_KEYS if k in obj}


def _load_category_strategies(rel_file: str) -> List[Dict[str, Any]]:
    path = _project_root() / _PACK_DIR_NAME / rel_file.replace("\\", "/")
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [_trim_strategy(s) for s in data.get("strategies") or [] if isinstance(s, dict)]


def _wida_snippets_for_ids(ids: List[str], max_chars: int) -> str:
    path = _project_root() / "wida" / "wida_strategy_enhancements.json"
    if not path.is_file() or max_chars < 200:
        return ""
    with open(path, encoding="utf-8") as f:
        wida = json.load(f)
    adaptations = wida.get("strategy_adaptations") or {}
    lines: List[str] = []
    budget = max_chars
    for sid in ids:
        block = adaptations.get(sid)
        if not isinstance(block, dict):
            continue
        pa = block.get("proficiency_adaptations") or {}
        snippet: Dict[str, Any] = {}
        for band in ("levels_1_2", "levels_3_4", "levels_5_6"):
            b = pa.get(band)
            if isinstance(b, dict) and b.get("implementation"):
                impl = str(b["implementation"])[:200]
                snippet[band] = impl + ("..." if len(str(b["implementation"])) > 200 else "")
        if not snippet:
            continue
        piece = json.dumps({"strategy_id": sid, "proficiency_hints": snippet}, ensure_ascii=False)
        if len(piece) + 2 > budget:
            break
        lines.append(piece)
        budget -= len(piece) + 2
    if not lines:
        return ""
    return "WIDA proficiency hints (selected strategies):\n" + "\n".join(lines)


def build_strategy_pack_injection_block(
    grade: str,
    subject: str,
    *,
    include_category_json: bool = True,
    include_wida_hints: bool = True,
) -> str:
    """
    Markdown block appended to the user prompt with allow-list and optional pack JSON.
    """
    data = _load_index()
    if not data:
        record_strategy_pack_injection_chars(0)
        return ""

    lines: List[str] = [
        "## STRATEGY PACK (AUTHORITATIVE)",
        "",
        "Use **only** the following `strategy_id` values in `tailored_instruction.ell_support` "
        "(exact snake_case match to pack `id`).",
        "",
    ]

    cats = data.get("categories") or {}
    for ckey, cmeta in cats.items():
        ids = cmeta.get("strategies") or []
        if not ids:
            continue
        lines.append(f"- **{ckey}:** {', '.join(ids)}")
    lines.append("")

    body = "\n".join(lines)
    if not include_category_json:
        out = body[:_MAX_INJECTION_CHARS]
        record_strategy_pack_injection_chars(len(out))
        return out

    cat_keys = _select_category_keys(grade, subject)
    trimmed: List[Dict[str, Any]] = []
    pack_ids_for_wida: List[str] = []
    for ck in cat_keys:
        rel = (cats.get(ck) or {}).get("file")
        if not rel:
            continue
        for s in _load_category_strategies(str(rel)):
            sid = s.get("id")
            if sid:
                pack_ids_for_wida.append(str(sid))
            trimmed.append(s)

    json_block = json.dumps(
        {"selected_categories": cat_keys, "strategies": trimmed},
        ensure_ascii=False,
        indent=2,
    )
    section = (
        body
        + "### Selected category strategies (trimmed JSON)\n\n"
        + "```json\n"
        + json_block
        + "\n```\n"
    )

    if include_wida_hints and pack_ids_for_wida:
        budget = max(0, _MAX_INJECTION_CHARS - len(section) - 500)
        wida_part = _wida_snippets_for_ids(pack_ids_for_wida[:12], budget)
        if wida_part:
            section += "\n" + wida_part + "\n"

    if len(section) > _MAX_INJECTION_CHARS:
        section = section[:_MAX_INJECTION_CHARS] + "\n\n[... strategy pack context truncated ...]\n"
    try:
        logger.info(
            "strategy_pack_injection_built",
            extra={
                "chars": len(section),
                "categories": cat_keys,
                "strategy_rows": len(trimmed),
            },
        )
    except Exception:
        pass
    record_strategy_pack_injection_chars(len(section))
    return section


def validate_ell_support_strategy_ids(
    lesson_json: Dict[str, Any],
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Return (ok, error_message, unknown_ids) after resolving LEGACY_ALIASES.
    """
    allowed = all_pack_strategy_ids()
    if not allowed:
        return True, None, []

    unknown: List[str] = []
    days = lesson_json.get("days")
    if not isinstance(days, dict):
        return True, None, []

    for day_name, day in days.items():
        if not isinstance(day, dict):
            continue
        day_inner = day.get("root") if "root" in day else day
        if not isinstance(day_inner, dict):
            continue
        ti = day_inner.get("tailored_instruction")
        if not isinstance(ti, dict):
            continue
        ell = ti.get("ell_support")
        if not isinstance(ell, list):
            continue
        for item in ell:
            if not isinstance(item, dict):
                continue
            sid_raw = item.get("strategy_id", "")
            c = _canonical_strategy_id(str(sid_raw))
            if not c:
                unknown.append(str(sid_raw))
            elif c not in allowed:
                unknown.append(str(sid_raw))

    if unknown:
        msg = (
            "Invalid or unknown tailored_instruction.ell_support.strategy_id value(s): "
            + ", ".join(sorted(set(unknown)))
            + ". Each must match a pack `id` from strategies_pack_v2 (see injected STRATEGY PACK section)."
        )
        return False, msg, sorted(set(unknown))
    return True, None, []
