"""Format objectives for printing (text, markdown, HTML)."""

from typing import Any, Dict, List


def format_for_print(
    objectives: List[Dict[str, Any]], format_type: str = "text"
) -> str:
    """Format objectives for printing.

    Args:
        objectives: List of objective dictionaries
        format_type: 'text', 'markdown', or 'html'

    Returns:
        Formatted string ready for printing
    """
    if not objectives:
        return "No objectives found."

    week_of = objectives[0].get("week_of", "Unknown")

    if format_type == "markdown":
        return _format_markdown(objectives, week_of)
    elif format_type == "html":
        return _format_html(objectives, week_of)
    else:
        return _format_text(objectives, week_of)


def _format_text(objectives: List[Dict[str, Any]], week_of: str) -> str:
    """Format as plain text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"LESSON PLAN OBJECTIVES - Week of {week_of}")
    lines.append("=" * 80)
    lines.append("")

    current_day = None
    for obj in objectives:
        day = obj["day"]
        if day != current_day:
            if current_day is not None:
                lines.append("")
            lines.append(f"{day.upper()}")
            lines.append("-" * 80)
            current_day = day

        lines.append(f"\nSlot {obj['slot_number']}: {obj['subject']}")
        if obj["unit_lesson"]:
            lines.append(f"Unit/Lesson: {obj['unit_lesson']}")
        if obj["teacher_name"]:
            lines.append(f"Teacher: {obj['teacher_name']}")
        lines.append("")

        if obj["content_objective"]:
            lines.append("Content Objective:")
            lines.append(f"  {obj['content_objective']}")
            lines.append("")

        if obj["student_goal"]:
            lines.append("Student Goal:")
            lines.append(f"  {obj['student_goal']}")
            lines.append("")

        if obj["wida_objective"]:
            lines.append("WIDA Objective:")
            lines.append(f"  {obj['wida_objective']}")
            lines.append("")

        lines.append("-" * 80)

    return "\n".join(lines)


def _format_markdown(objectives: List[Dict[str, Any]], week_of: str) -> str:
    """Format as Markdown."""
    lines = []
    lines.append(f"# Lesson Plan Objectives - Week of {week_of}")
    lines.append("")

    current_day = None
    for obj in objectives:
        day = obj["day"]
        if day != current_day:
            if current_day is not None:
                lines.append("")
            lines.append(f"## {day}")
            lines.append("")
            current_day = day

        lines.append(f"### Slot {obj['slot_number']}: {obj['subject']}")
        if obj["unit_lesson"]:
            lines.append(f"**Unit/Lesson:** {obj['unit_lesson']}")
        if obj["teacher_name"]:
            lines.append(f"**Teacher:** {obj['teacher_name']}")
        lines.append("")

        if obj["content_objective"]:
            lines.append("**Content Objective:**")
            lines.append(f"{obj['content_objective']}")
            lines.append("")

        if obj["student_goal"]:
            lines.append("**Student Goal:**")
            lines.append(f"{obj['student_goal']}")
            lines.append("")

        if obj["wida_objective"]:
            lines.append("**WIDA Objective:**")
            lines.append(f"{obj['wida_objective']}")
            lines.append("")

    return "\n".join(lines)


def _format_html(objectives: List[Dict[str, Any]], week_of: str) -> str:
    """Format as HTML."""
    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html><head>")
    lines.append("<meta charset='utf-8'>")
    lines.append(f"<title>Lesson Plan Objectives - Week of {week_of}</title>")
    lines.append("<style>")
    lines.append("body { font-family: Arial, sans-serif; margin: 20px; }")
    lines.append("h1 { color: #333; border-bottom: 2px solid #333; }")
    lines.append("h2 { color: #666; margin-top: 30px; }")
    lines.append("h3 { color: #888; }")
    lines.append(
        ".objective { margin: 15px 0; padding: 10px; background: #f5f5f5; }"
    )
    lines.append(".label { font-weight: bold; color: #555; }")
    lines.append("</style>")
    lines.append("</head><body>")
    lines.append(f"<h1>Lesson Plan Objectives - Week of {week_of}</h1>")

    current_day = None
    for obj in objectives:
        day = obj["day"]
        if day != current_day:
            if current_day is not None:
                lines.append("</div>")
            lines.append(f"<h2>{day}</h2>")
            lines.append("<div class='day-objectives'>")
            current_day = day

        lines.append("<div class='objective'>")
        lines.append(f"<h3>Slot {obj['slot_number']}: {obj['subject']}</h3>")
        if obj["unit_lesson"]:
            lines.append(
                f"<p><span class='label'>Unit/Lesson:</span> {obj['unit_lesson']}</p>"
            )
        if obj["teacher_name"]:
            lines.append(
                f"<p><span class='label'>Teacher:</span> {obj['teacher_name']}</p>"
            )

        if obj["content_objective"]:
            lines.append(
                f"<p><span class='label'>Content Objective:</span><br>{obj['content_objective']}</p>"
            )

        if obj["student_goal"]:
            lines.append(
                f"<p><span class='label'>Student Goal:</span><br>{obj['student_goal']}</p>"
            )

        if obj["wida_objective"]:
            lines.append(
                f"<p><span class='label'>WIDA Objective:</span><br>{obj['wida_objective']}</p>"
            )

        lines.append("</div>")

    if current_day:
        lines.append("</div>")
    lines.append("</body></html>")

    return "\n".join(lines)
