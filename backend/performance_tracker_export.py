"""
CSV export helpers for performance tracker metrics.
"""

import csv
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.telemetry import logger


def write_metrics_to_csv_file(
    metrics: List[Dict[str, Any]],
    output_path: str,
    plan_id: str,
) -> str:
    """
    Write plan metrics to a CSV file.

    Args:
        metrics: List of metric dicts
        output_path: Path to save CSV file
        plan_id: Plan ID (for logging)

    Returns:
        output_path if metrics were written, empty string otherwise
    """
    if not metrics:
        logger.warning("no_metrics_to_export", extra={"plan_id": plan_id})
        return ""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
        writer.writeheader()
        writer.writerows(metrics)

    logger.info(
        "metrics_exported",
        extra={
            "plan_id": plan_id,
            "output_path": output_path,
            "metric_count": len(metrics),
        },
    )
    return output_path


def get_most_common_model(metrics: List[Dict[str, Any]]) -> Optional[str]:
    """Return the most frequently used llm_model in the metrics list, or None."""
    model_counts: Dict[str, int] = {}
    for m in metrics:
        model = m.get("llm_model")
        if model:
            model_counts[model] = model_counts.get(model, 0) + 1
    return max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None


def metrics_to_csv_string(rows: List[Dict[str, Any]]) -> str:
    """
    Convert a list of dicts (e.g. daily breakdown) to a CSV string.

    Args:
        rows: List of row dicts

    Returns:
        CSV string, or empty string if rows is empty
    """
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
