"""
Domain analysis for lesson activities (WIDA language domains).
"""

from typing import Any, Dict, List, Optional


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

    strategy_domain_map = {
        "think_pair_share": {"listening", "speaking"},
        "collaborative_learning": {"listening", "speaking"},
        "sentence_frames": {"speaking", "writing"},
        "graphic_organizers": {"reading", "writing"},
        "cognate_awareness": {"reading", "writing"},
        "oral_rehearsal": {"speaking", "listening"},
        "peer_tutoring": {"listening", "speaking"},
        "literature_circles": {"reading", "speaking", "listening"},
        "jigsaw": {"reading", "speaking", "listening"},
        "read_aloud": {"listening", "reading"},
        "shared_reading": {"reading", "speaking"},
        "interactive_writing": {"writing", "speaking"},
        "guided_writing": {"writing", "reading"},
    }

    if ell_support:
        for strategy in ell_support:
            strategy_id = strategy.get("strategy_id", "").lower()
            if strategy_id in strategy_domain_map:
                for domain in strategy_domain_map[strategy_id]:
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
