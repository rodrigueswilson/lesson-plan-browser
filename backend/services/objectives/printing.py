"""Save formatted objectives to file."""

from pathlib import Path
from typing import Any, Dict, List

from backend.telemetry import logger

from .formatting import format_for_print


def save_to_file(
    objectives: List[Dict[str, Any]],
    output_path: str,
    format_type: str = "text",
) -> str:
    """Save formatted objectives to file.

    Args:
        objectives: List of objective dictionaries
        output_path: Path to save file
        format_type: 'text', 'markdown', or 'html'

    Returns:
        Path to saved file
    """
    formatted = format_for_print(objectives, format_type)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted)

    logger.info(
        "objectives_saved",
        extra={
            "output_path": str(output_file),
            "format": format_type,
            "objective_count": len(objectives),
        },
    )

    return str(output_file)
