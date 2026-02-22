"""
Performance tracking module for LLM operations.
Tracks timing, token usage, and costs for research and optimization.
Follows SSOT principle - single source for performance data.
"""

import csv
import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from backend.database import get_db
from backend.model_pricing import calculate_cost
from backend.telemetry import logger


class PerformanceTracker:
    """Tracks performance metrics for LLM operations."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        retention_days: int = 30,
        sampling_rate: float = 1.0,
        debug_mode: bool = False,
    ):
        """
        Initialize performance tracker.

        Args:
            enabled: Override environment variable (for testing)
            retention_days: Number of days to keep metrics (default 30)
            sampling_rate: Probability of tracking an operation (0.0 to 1.0).
                Only applies to non-critical operations when debug_mode is False.
            debug_mode: If True, track all operations (ignore sampling for
                granular ops). If False, only critical ops are always tracked;
                others are subject to sampling_rate.
        """
        if enabled is None:
            enabled = os.getenv("ENABLE_PERFORMANCE_TRACKING", "true").lower() == "true"

        self.enabled = enabled
        self.retention_days = retention_days
        self.sampling_rate = sampling_rate
        self.debug_mode = debug_mode
        self.db = get_db()
        self._active_operations: Dict[str, Dict[str, Any]] = {}

        # Cleanup old metrics on initialization
        if self.enabled:
            self.cleanup_old_metrics()

        logger.info(
            "performance_tracker_initialized",
            extra={
                "enabled": self.enabled,
                "retention_days": self.retention_days,
                "sampling_rate": self.sampling_rate,
                "debug_mode": self.debug_mode,
            },
        )

    def cleanup_old_metrics(self) -> None:
        """Delete metrics older than retention_days."""
        try:
            count = self.db.delete_old_metrics(self.retention_days)
            if count > 0:
                logger.info(
                    "performance_tracker_cleanup",
                    extra={"deleted_count": count, "retention_days": self.retention_days},
                )
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")

    def start_operation(
        self,
        plan_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start tracking an operation.

        Args:
            plan_id: Weekly plan ID
            operation_type: Type of operation (e.g., "process_day", "process_slot")
            metadata: Additional metadata (slot_number, day_number, etc.)

        Returns:
            Operation ID for later reference (empty string if tracking disabled)
        """
        if not self.enabled:
            return ""

        # Critical operations are always stored regardless of sampling_rate.
        # All other operations (parse_*, render_*, etc.) are subject to sampling
        # unless debug_mode is True.
        import random
        _CRITICAL_OPERATIONS = frozenset([
            "batch_process", "plan_generation", "llm_call", "llm_api_call"
        ])
        is_critical = operation_type in _CRITICAL_OPERATIONS

        if not is_critical and not self.debug_mode and random.random() > self.sampling_rate:
            return ""

        operation_id = str(uuid.uuid4())

        self._active_operations[operation_id] = {
            "id": operation_id,
            "plan_id": plan_id,
            "operation_type": operation_type,
            "started_at": datetime.now(),
            "metadata": metadata or {},
        }

        logger.debug(
            "operation_started",
            extra={
                "operation_id": operation_id,
                "operation_type": operation_type,
                "plan_id": plan_id,
            },
        )

        return operation_id

    def end_operation(
        self, operation_id: str, result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End tracking an operation and save metrics.

        Args:
            operation_id: Operation ID from start_operation()
            result: Operation result with token counts, model info, etc.
        """
        if not self.enabled or not operation_id:
            return

        if operation_id not in self._active_operations:
            logger.warning("operation_not_found", extra={"operation_id": operation_id})
            return

        operation = self._active_operations.pop(operation_id)
        completed_at = datetime.now()
        duration_ms = (completed_at - operation["started_at"]).total_seconds() * 1000

        # Extract metrics from result
        result = result or {}
        tokens_input = result.get("tokens_input", 0)
        tokens_output = result.get("tokens_output", 0)
        tokens_total = tokens_input + tokens_output
        llm_model = result.get("llm_model", "")
        llm_provider = result.get("llm_provider", "")
        error_message = result.get("error")

        # Extract parallel processing metrics
        is_parallel = result.get("is_parallel", False)
        parallel_slot_count = result.get("parallel_slot_count")
        sequential_time_ms = result.get("sequential_time_ms")
        rate_limit_errors = result.get("rate_limit_errors", 0)
        concurrency_level = result.get("concurrency_level")
        tpm_usage = result.get("tpm_usage")
        rpm_usage = result.get("rpm_usage")

        # Calculate cost
        cost_usd = 0.0
        if llm_model and tokens_input > 0:
            cost_usd = calculate_cost(llm_model, tokens_input, tokens_output)

        # Save to database (silent failure)
        try:
            self._save_metric(
                operation_id=operation_id,
                plan_id=operation["plan_id"],
                operation_type=operation["operation_type"],
                started_at=operation["started_at"],
                completed_at=completed_at,
                duration_ms=duration_ms,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_total,
                llm_provider=llm_provider,
                llm_model=llm_model,
                cost_usd=cost_usd,
                error_message=error_message,
                metadata=operation["metadata"],
                is_parallel=is_parallel,
                parallel_slot_count=parallel_slot_count,
                sequential_time_ms=sequential_time_ms,
                rate_limit_errors=rate_limit_errors,
                concurrency_level=concurrency_level,
                tpm_usage=tpm_usage,
                rpm_usage=rpm_usage,
            )

            logger.info(
                "operation_completed",
                extra={
                    "operation_id": operation_id,
                    "operation_type": operation["operation_type"],
                    "duration_ms": duration_ms,
                    "tokens_total": tokens_total,
                    "cost_usd": cost_usd,
                },
            )
        except Exception as e:
            # Silent failure - tracking should never block processing
            logger.error(
                "tracking_save_failed", extra={"operation_id": operation_id, "error": str(e)}
            )

    @contextmanager
    def track_operation(
        self,
        plan_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for tracking operations.
        
        Usage:
            with tracker.track_operation(plan_id, "parse_read_docx") as op:
                # do work
                op["result"] = some_data  # Optional: store result data
        
        Args:
            plan_id: Weekly plan ID
            operation_type: Type of operation
            metadata: Additional metadata
            
        Yields:
            Dict to store operation results (tokens, model, etc.)
        """
        operation_result: Dict[str, Any] = {}
        operation_id = self.start_operation(plan_id, operation_type, metadata)
        
        try:
            yield operation_result
        finally:
            self.end_operation(operation_id, operation_result)

    def _save_metric(self, **kwargs) -> None:
        """Save metric to database."""
        metadata = kwargs.pop("metadata", {})
        slot_number = metadata.get("slot_number")
        day_number = metadata.get("day_number")

        self.db.save_performance_metric(
            operation_id=kwargs["operation_id"],
            plan_id=kwargs["plan_id"],
            operation_type=kwargs["operation_type"],
            started_at=kwargs["started_at"],
            completed_at=kwargs["completed_at"],
            duration_ms=kwargs["duration_ms"],
            tokens_input=kwargs["tokens_input"],
            tokens_output=kwargs["tokens_output"],
            tokens_total=kwargs["tokens_total"],
            llm_provider=kwargs["llm_provider"],
            llm_model=kwargs["llm_model"],
            cost_usd=kwargs["cost_usd"],
            error_message=kwargs["error_message"],
            slot_number=slot_number,
            day_number=day_number,
            is_parallel=kwargs.get("is_parallel"),
            parallel_slot_count=kwargs.get("parallel_slot_count"),
            sequential_time_ms=kwargs.get("sequential_time_ms"),
            rate_limit_errors=kwargs.get("rate_limit_errors"),
            concurrency_level=kwargs.get("concurrency_level"),
            tpm_usage=kwargs.get("tpm_usage"),
            rpm_usage=kwargs.get("rpm_usage"),
        )

    def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics for a weekly plan.

        Args:
            plan_id: Weekly plan ID

        Returns:
            List of metric dicts ordered by started_at
        """
        return self.db.get_plan_metrics(plan_id)

    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """
        Get aggregated metrics for a weekly plan.

        Args:
            plan_id: Weekly plan ID

        Returns:
            Dict with total duration, tokens, cost, and averages
        """
        return self.db.get_plan_summary(plan_id)

    def update_plan_summary(self, plan_id: str) -> bool:
        """
        Update weekly_plans table with aggregated metrics.

        Args:
            plan_id: Weekly plan ID

        Returns:
            True if updated successfully
        """
        summary = self.get_plan_summary(plan_id)

        if not summary or summary.get("operation_count", 0) == 0:
            return False

        # Get the most common model used
        metrics = self.get_plan_metrics(plan_id)
        model_counts: Dict[str, int] = {}
        for m in metrics:
            model = m.get("llm_model")
            if model:
                model_counts[model] = model_counts.get(model, 0) + 1
        
        llm_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None

        # Update weekly_plans
        updated = self.db.update_plan_summary(
            plan_id=plan_id,
            processing_time_ms=summary.get("total_time_ms"),
            total_tokens=summary.get("total_tokens"),
            total_cost_usd=summary.get("total_cost_usd"),
            llm_model=llm_model,
        )

        if updated:
            logger.info(
                "plan_summary_updated",
                extra={
                    "plan_id": plan_id,
                    "duration_ms": summary.get("total_time_ms"),
                    "tokens": summary.get("total_tokens"),
                    "cost_usd": summary.get("total_cost_usd"),
                },
            )

        return updated

    def export_to_csv(self, plan_id: str, output_path: str) -> str:
        """
        Export metrics to CSV file.

        Args:
            plan_id: Weekly plan ID
            output_path: Path to save CSV file

        Returns:
            Path to created CSV file (empty string if no metrics)
        """
        metrics = self.get_plan_metrics(plan_id)

        if not metrics:
            logger.warning("no_metrics_to_export", extra={"plan_id": plan_id})
            return ""

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
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

    def get_aggregate_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate analytics across all plans.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            Dict with aggregate statistics
        """
        return self.db.get_aggregate_stats(days=days, user_id=user_id)

    def get_daily_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily breakdown of activity.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            List of daily statistics
        """
        return self.db.get_daily_breakdown(days=days, user_id=user_id)

    def get_session_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get session-by-session breakdown (each plan is a session).

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            List of session statistics, ordered by most recent first
        """
        return self.db.get_session_breakdown(days=days, user_id=user_id)

    def get_operation_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time breakdown by operation type.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            List of operation statistics
        """
        return self.db.get_operation_stats(days=days, user_id=user_id)

    def get_error_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get success vs failure stats with error distribution.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            Dict with success/failure counts and error breakdown
        """
        return self.db.get_error_stats(days=days, user_id=user_id)

    def get_parallel_processing_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get parallel processing statistics.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            Dict with parallel processing metrics
        """
        return self.db.get_parallel_processing_stats(days=days, user_id=user_id)

    def export_analytics_csv(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> str:
        """
        Export analytics data to CSV string.

        Args:
            days: Number of days to look back
            user_id: Optional user filter

        Returns:
            CSV string with analytics data
        """
        daily_data = self.get_daily_breakdown(days, user_id)
        
        if not daily_data:
            return ""
        
        # Convert to CSV string
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=daily_data[0].keys())
        writer.writeheader()
        writer.writerows(daily_data)
        
        return output.getvalue()


# Global tracker instance (env vars are read only at first creation)
_tracker_instance: Optional[PerformanceTracker] = None


def get_tracker() -> PerformanceTracker:
    """
    Get or create global performance tracker instance.

    Environment variables (read only when the singleton is first created):
    - ENABLE_PERFORMANCE_TRACKING: enable/disable tracking (default "true")
    - DEBUG_PERFORMANCE_TRACKING: if "true", enable granular tracking for all
      operations (default "false"). Changing this after first call has no effect
      until process restart.

    Returns:
        PerformanceTracker instance
    """
    global _tracker_instance
    if _tracker_instance is None:
        debug = os.getenv("DEBUG_PERFORMANCE_TRACKING", "false").lower() == "true"
        _tracker_instance = PerformanceTracker(debug_mode=debug)
    return _tracker_instance
