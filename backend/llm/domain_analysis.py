"""
Domain analysis for lesson activities (WIDA language domains).

Strategy-to-domain mapping is derived from strategies_pack_v2 category JSON
`skill_weights` (single source of truth). Legacy lesson JSON may use older
`strategy_id` strings; those are normalized via LEGACY_ALIASES.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional

_SKILL_KEYS = ("speaking", "listening", "reading", "writing")
# Exclude nominal weights (e.g. 0.1) so primary domains match instructional intent.
_WEIGHT_EPSILON = 0.15

_CATEGORY_FILES = (
    "core/language_skills.json",
    "core/frameworks_models.json",
    "core/cross_linguistic.json",
    "core/assessment_scaffolding.json",
    "specialized/social_interactive.json",
    "specialized/cultural_identity.json",
)

# Older plans / fixtures may use ids not present in v2 pack JSON.
LEGACY_ALIASES: Dict[str, str] = {
    "peer_tutoring": "collaborative_learning",
    "peer_tutoring_bilingual": "think_pair_share",
    "read_aloud": "interactive_read_alouds",
    "oral_rehearsal": "collaborative_learning",
    "literature_circles": "interactive_read_alouds",
    "jigsaw": "collaborative_learning",
    "shared_reading": "interactive_read_alouds",
    "interactive_writing": "sentence_frames",
    "guided_writing": "graphic_organizers",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@lru_cache(maxsize=1)
def _pack_strategy_domains() -> Dict[str, FrozenSet[str]]:
    """Load strategy id -> language domains from pack skill_weights."""
    pack_dir = _project_root() / "strategies_pack_v2"
    result: Dict[str, FrozenSet[str]] = {}
    for rel in _CATEGORY_FILES:
        path = pack_dir / rel
        if not path.is_file():
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for strat in data.get("strategies", []):
            sid = strat.get("id")
            weights = strat.get("skill_weights") or {}
            if not sid or not isinstance(weights, dict):
                continue
            active: set[str] = set()
            for key in _SKILL_KEYS:
                try:
                    w = float(weights.get(key, 0.0))
                except (TypeError, ValueError):
                    continue
                if w >= _WEIGHT_EPSILON:
                    active.add(key)
            if active:
                result[sid] = frozenset(active)
    return result


def _canonical_strategy_id(strategy_id: str) -> str:
    raw = (strategy_id or "").strip().lower()
    if not raw:
        return ""
    return LEGACY_ALIASES.get(raw, raw)


def analyze_domains_from_activities(
    ell_support: Optional[List[Dict[str, Any]]] = None,
    phase_plan: Optional[List[Dict[str, Any]]] = None,
    content_objective: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Analyze lesson activities to determine which language domains are used.

    Args:
        ell_support: List of ELL support strategies
        phase_plan: List of phase plan activities
        content_objective: Content objective text

    Returns:
        Dict with keys: listening, reading, speaking, writing (all bool)
    """
    domains = {
        "listening": False,
        "reading": False,
        "speaking": False,
        "writing": False,
    }

    pack_map = _pack_strategy_domains()

    if ell_support:
        for strategy in ell_support:
            sid = _canonical_strategy_id(strategy.get("strategy_id", ""))
            if not sid:
                continue
            domain_set = pack_map.get(sid)
            if domain_set:
                for domain in domain_set:
                    domains[domain] = True

    if phase_plan:
        activity_text = " ".join(
            [
                phase.get("phase_name", "")
                + " "
                + phase.get("bilingual_teacher_role", "")
                + " "
                + phase.get("primary_teacher_role", "")
                + " "
                + phase.get("details", "")
                for phase in phase_plan
            ]
        ).lower()

        if any(
            word in activity_text
            for word in ["listen", "hear", "audio", "explanation", "instruction"]
        ):
            domains["listening"] = True
        if any(
            word in activity_text
            for word in ["read", "text", "passage", "article", "book", "document"]
        ):
            domains["reading"] = True
        if any(
            word in activity_text
            for word in [
                "speak",
                "discuss",
                "share",
                "present",
                "talk",
                "say",
                "tell",
            ]
        ):
            domains["speaking"] = True
        if any(
            word in activity_text
            for word in [
                "write",
                "compose",
                "draft",
                "paragraph",
                "essay",
                "response",
            ]
        ):
            domains["writing"] = True

    if content_objective:
        obj_lower = content_objective.lower()
        if any(
            word in obj_lower for word in ["read", "comprehend", "analyze text"]
        ):
            domains["reading"] = True
        if any(
            word in obj_lower
            for word in ["write", "compose", "draft", "create text"]
        ):
            domains["writing"] = True
        if any(
            word in obj_lower
            for word in ["speak", "present", "discuss", "explain orally"]
        ):
            domains["speaking"] = True
        if any(word in obj_lower for word in ["listen", "follow instructions"]):
            domains["listening"] = True

    return domains
