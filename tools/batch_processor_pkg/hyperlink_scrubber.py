"""
Hyperlink scrubbing and restoration for batch processor.

Replaces links with [[LINK_n]] placeholders before LLM and restores them after,
with day-context validation.
"""

import re
from typing import Any, Dict, Set, Tuple

from backend.telemetry import logger

from tools.batch_processor_pkg.context import SlotProcessingContext


def scrub_hyperlinks(context: SlotProcessingContext) -> None:
    """Pre-processing: Replace links with [[LINK_n]] placeholders, tracking which day they belong to."""
    if not context.extracted_content:
        return

    link_count = 0
    link_map = {}

    def replace_with_token(match, day):
        nonlocal link_count
        link_count += 1
        token = f"[[LINK_{link_count}]]"
        original = match.group(0)
        link_map[token] = {"original": original, "day": day}
        return token

    markdown_pattern = r"\[([^\]]+)\]\((https?://[^\s\)]+)\)"
    raw_url_pattern = r"https?://[^\s<>{}\"|\\^`\[\]]+"

    days_of_week = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    day_regex = r"\n(" + "|".join(days_of_week) + r")"

    parts = re.split(day_regex, context.extracted_content)

    current_day = "metadata"
    processed_parts = []

    pre_content = parts[0]
    pre_content = re.sub(markdown_pattern, lambda m: replace_with_token(m, current_day), pre_content)
    pre_content = re.sub(raw_url_pattern, lambda m: replace_with_token(m, current_day), pre_content)
    processed_parts.append(pre_content)

    for i in range(1, len(parts), 2):
        day_header = parts[i]
        current_day = day_header.lower()
        day_content = parts[i + 1] if i + 1 < len(parts) else ""

        day_content = re.sub(markdown_pattern, lambda m: replace_with_token(m, current_day), day_content)
        day_content = re.sub(raw_url_pattern, lambda m: replace_with_token(m, current_day), day_content)

        processed_parts.append(f"\n{day_header}{day_content}")

    context.extracted_content = "".join(processed_parts)
    context.link_map = link_map

    if link_count > 0:
        logger.info(
            "links_scrubbed_with_days",
            extra={
                "slot": context.slot.get("slot_number"),
                "link_count": link_count,
                "days_tracked": list(set(entry["day"] for entry in link_map.values())),
            },
        )


def restore_hyperlinks(
    data: Any, link_map: Dict[str, Dict[str, Any]]
) -> Tuple[Any, Set[str]]:
    """Post-processing: Recursively swap placeholders back for original links with day-matching validation.

    Returns:
        Tuple of (restored_data, set_of_original_links_restored).
    """
    restored_links: Set[str] = set()

    if not link_map:
        return data, restored_links

    def recurse(item, current_day=None):
        if isinstance(item, dict):
            new_dict = {}
            for k, v in item.items():
                day_context = current_day
                if k.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    day_context = k.lower()
                new_dict[k] = recurse(v, day_context)
            return new_dict
        elif isinstance(item, list):
            return [recurse(i, current_day) for i in item]
        elif isinstance(item, str):
            text = item
            sorted_tokens = sorted(link_map.keys(), key=len, reverse=True)
            for token in sorted_tokens:
                pattern = re.compile(re.escape(token), re.IGNORECASE)
                if pattern.search(text):
                    link_info = link_map[token]
                    original = link_info["original"]
                    source_day = link_info["day"]

                    if current_day and source_day and source_day != "metadata" and source_day != current_day:
                        logger.warning(
                            "cross_day_link_restoration_rejected",
                            extra={
                                "token": token,
                                "source_day": source_day,
                                "target_day": current_day,
                                "link": original,
                            },
                        )
                        text_only = original
                        if original.startswith("[") and "]" in original:
                            text_only = original[1 : original.find("]")]
                        text = pattern.sub(text_only, text)
                        continue

                    restored_links.add(original)
                    replacement = original
                    if replacement.startswith("http") and not replacement.startswith("["):
                        replacement = f"[{replacement}]({replacement})"
                    text = pattern.sub(replacement, text)
            return text
        return item

    return recurse(data), restored_links
