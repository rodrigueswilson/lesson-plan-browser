"""Supabase performance metrics mixin."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from backend.schema import PerformanceMetric

logger = logging.getLogger(__name__)


class SupabaseMetricsMixin:
    """Mixin for performance metrics and plan summary. Expects self.client (Supabase Client)."""

    def save_performance_metric(
        self,
        operation_id: str,
        plan_id: str,
        operation_type: str,
        started_at: Any,
        completed_at: Any,
        duration_ms: float,
        tokens_input: int,
        tokens_output: int,
        tokens_total: int,
        llm_provider: str,
        llm_model: str,
        cost_usd: float,
        error_message: Optional[str],
        slot_number: Optional[int] = None,
        day_number: Optional[int] = None,
    ) -> None:
        """Save a performance metric."""
        try:
            started_at_str = (
                started_at.isoformat()
                if hasattr(started_at, "isoformat")
                else str(started_at)
            )
            completed_at_str = (
                completed_at.isoformat()
                if hasattr(completed_at, "isoformat")
                else str(completed_at)
            )

            self.client.table("performance_metrics").insert(
                {
                    "id": operation_id,
                    "plan_id": plan_id,
                    "slot_number": slot_number,
                    "day_number": day_number,
                    "operation_type": operation_type,
                    "started_at": started_at_str,
                    "completed_at": completed_at_str,
                    "duration_ms": duration_ms,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "tokens_total": tokens_total,
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                    "cost_usd": cost_usd,
                    "error_message": error_message,
                }
            ).execute()
        except APIError as e:
            logger.error(
                "performance_metric_save_failed",
                extra={"error": str(e), "operation_id": operation_id},
            )
            raise

    def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for a weekly plan."""
        try:
            response = (
                self.client.table("performance_metrics")
                .select("*")
                .eq("plan_id", plan_id)
                .order("started_at")
                .execute()
            )
            metrics = [PerformanceMetric.model_validate(row) for row in response.data]
            return [m.model_dump() for m in metrics]
        except APIError as e:
            logger.error(
                "plan_metrics_fetch_failed",
                extra={"error": str(e), "plan_id": plan_id},
            )
            raise

    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for a weekly plan."""
        try:
            metrics = self.get_plan_metrics(plan_id)
            if not metrics:
                return {}

            operation_count = len(metrics)
            total_duration_ms = sum(m.get("duration_ms") or 0 for m in metrics)
            total_tokens_input = sum(m.get("tokens_input") or 0 for m in metrics)
            total_tokens_output = sum(m.get("tokens_output") or 0 for m in metrics)
            total_tokens = sum(m.get("tokens_total") or 0 for m in metrics)
            total_cost_usd = sum(m.get("cost_usd") or 0 for m in metrics)
            avg_duration_ms = (
                total_duration_ms / operation_count if operation_count > 0 else 0
            )

            return {
                "operation_count": operation_count,
                "total_duration_ms": total_duration_ms,
                "total_tokens_input": total_tokens_input,
                "total_tokens_output": total_tokens_output,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost_usd,
                "avg_duration_ms": avg_duration_ms,
            }
        except Exception as e:
            logger.error(
                "plan_summary_fetch_failed",
                extra={"error": str(e), "plan_id": plan_id},
            )
            raise

    def update_plan_summary(
        self,
        plan_id: str,
        processing_time_ms: Optional[float],
        total_tokens: Optional[int],
        total_cost_usd: Optional[float],
        llm_model: Optional[str],
    ) -> bool:
        """Update weekly_plans table with aggregated metrics."""
        updates: Dict[str, Any] = {}
        if processing_time_ms is not None:
            updates["processing_time_ms"] = processing_time_ms
        if total_tokens is not None:
            updates["total_tokens"] = total_tokens
        if total_cost_usd is not None:
            updates["total_cost_usd"] = total_cost_usd
        if llm_model is not None:
            updates["llm_model"] = llm_model

        if not updates:
            return False

        try:
            response = (
                self.client.table("weekly_plans")
                .update(updates)
                .eq("id", plan_id)
                .execute()
            )
            updated = len(response.data) > 0
            return updated
        except APIError as e:
            logger.error(
                "plan_summary_update_failed",
                extra={"error": str(e), "plan_id": plan_id},
            )
            raise

    def get_aggregate_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregate analytics across all plans."""
        try:
            threshold_date = (
                datetime.now() - timedelta(days=days)
            ).isoformat()

            query = (
                self.client.table("performance_metrics")
                .select("*, weekly_plans(user_id)")
                .gte("started_at", threshold_date)
            )

            response = query.execute()
            metrics_data = [dict(row) for row in response.data]

            if user_id:
                metrics_data = [
                    m
                    for m in metrics_data
                    if m.get("weekly_plans")
                    and m["weekly_plans"].get("user_id") == user_id
                ]

            if not metrics_data:
                return {}

            total_operations = len(metrics_data)
            total_tokens = sum(m.get("tokens_total", 0) or 0 for m in metrics_data)
            total_cost = sum(m.get("cost_usd", 0) or 0 for m in metrics_data)
            plan_ids = set(m.get("plan_id") for m in metrics_data)
            total_plans = len(plan_ids)

            return {
                "total_plans": total_plans,
                "total_operations": total_operations,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
            }
        except APIError as e:
            logger.error("aggregate_stats_fetch_failed", extra={"error": str(e)})
            return {}

    def get_daily_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily breakdown of activity."""
        try:
            threshold_date = (
                datetime.now() - timedelta(days=days)
            ).isoformat()

            query = (
                self.client.table("performance_metrics")
                .select("*, weekly_plans(user_id)")
                .gte("started_at", threshold_date)
            )

            response = query.execute()
            metrics_data = [dict(row) for row in response.data]

            if user_id:
                metrics_data = [
                    m
                    for m in metrics_data
                    if m.get("weekly_plans")
                    and m["weekly_plans"].get("user_id") == user_id
                ]

            daily_stats = {}
            for m in metrics_data:
                date = m.get("started_at", "").split("T")[0]
                if date not in daily_stats:
                    daily_stats[date] = {"requests": 0, "tokens": 0, "cost": 0.0}
                daily_stats[date]["requests"] += 1
                daily_stats[date]["tokens"] += m.get("tokens_total", 0) or 0
                daily_stats[date]["cost"] += m.get("cost_usd", 0) or 0

            return [{"date": k, **v} for k, v in sorted(daily_stats.items())]
        except Exception as e:
            logger.error("daily_breakdown_failed", extra={"error": str(e)})
            return []

    def get_session_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get session-by-session breakdown."""
        try:
            threshold_date = (
                datetime.now() - timedelta(days=days)
            ).isoformat()

            query = (
                self.client.table("weekly_plans")
                .select("*")
                .gte("generated_at", threshold_date)
                .order("generated_at", desc=True)
            )

            if user_id:
                query = query.eq("user_id", user_id)

            response = query.execute()
            plans = [dict(row) for row in response.data]

            return [
                {
                    "plan_id": p.get("id"),
                    "timestamp": p.get("generated_at"),
                    "week_of": p.get("week_of"),
                    "status": p.get("status"),
                    "duration_ms": p.get("processing_time_ms"),
                    "tokens": p.get("total_tokens"),
                    "cost": p.get("total_cost_usd"),
                    "model": p.get("llm_model"),
                }
                for p in plans
            ]
        except Exception as e:
            logger.error("session_breakdown_failed", extra={"error": str(e)})
            return []
