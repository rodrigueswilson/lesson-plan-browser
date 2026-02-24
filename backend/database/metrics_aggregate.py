"""Aggregate analytics queries for performance metrics. Used by metrics.py."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from backend.schema import PerformanceMetric, WeeklyPlan

logger = logging.getLogger(__name__)


def get_aggregate_stats(
    db, days: int = 30, user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get aggregate analytics across all plans."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            query = select(
                func.count(PerformanceMetric.id).label("total_operations"),
                func.sum(PerformanceMetric.duration_ms).label("total_duration_ms"),
                func.sum(PerformanceMetric.tokens_total).label("total_tokens"),
                func.sum(PerformanceMetric.tokens_input).label("total_tokens_input"),
                func.sum(PerformanceMetric.tokens_output).label("total_tokens_output"),
                func.sum(PerformanceMetric.cost_usd).label("total_cost"),
                func.avg(PerformanceMetric.duration_ms).label("avg_latency"),
            ).where(PerformanceMetric.started_at >= start_date)

            if user_id:
                query = query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            metrics = session.exec(query).first()

            plan_query = select(func.count(WeeklyPlan.id)).where(
                WeeklyPlan.generated_at >= start_date
            )
            if user_id:
                plan_query = plan_query.where(WeeklyPlan.user_id == user_id)

            total_plans = session.exec(plan_query).one()

            plan_stats_query = select(
                func.avg(WeeklyPlan.processing_time_ms).label("avg_duration"),
                func.avg(WeeklyPlan.total_cost_usd).label("avg_cost"),
            ).where(WeeklyPlan.generated_at >= start_date)
            if user_id:
                plan_stats_query = plan_stats_query.where(WeeklyPlan.user_id == user_id)

            plan_stats = session.exec(plan_stats_query).first()

            model_query = select(
                PerformanceMetric.llm_model,
                func.count(PerformanceMetric.id).label("count"),
                func.sum(PerformanceMetric.cost_usd).label("cost"),
            ).where(PerformanceMetric.started_at >= start_date)

            if user_id:
                model_query = model_query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            model_query = model_query.group_by(PerformanceMetric.llm_model)
            model_results = session.exec(model_query).all()
            model_distribution = [
                {
                    "llm_model": row.llm_model or "Unknown",
                    "count": row.count or 0,
                    "cost": float(row.cost or 0),
                }
                for row in model_results
            ]

            operation_query = select(
                PerformanceMetric.operation_type,
                func.avg(PerformanceMetric.duration_ms).label("avg_duration"),
                func.count(PerformanceMetric.id).label("count"),
            ).where(PerformanceMetric.started_at >= start_date)

            if user_id:
                operation_query = operation_query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            operation_query = operation_query.group_by(PerformanceMetric.operation_type)
            operation_results = session.exec(operation_query).all()
            operation_breakdown = [
                {
                    "operation_type": row.operation_type,
                    "avg_duration_ms": float(row.avg_duration or 0),
                    "count": row.count or 0,
                }
                for row in operation_results
            ]

            return {
                "total_operations": metrics.total_operations or 0,
                "total_duration_ms": float(metrics.total_duration_ms or 0),
                "total_tokens": metrics.total_tokens or 0,
                "total_tokens_input": metrics.total_tokens_input or 0,
                "total_tokens_output": metrics.total_tokens_output or 0,
                "total_cost_usd": metrics.total_cost or 0,
                "avg_cost_usd": float(plan_stats.avg_cost or 0) if plan_stats else 0,
                "avg_latency_ms": metrics.avg_latency or 0,
                "avg_duration_ms": float(metrics.avg_latency or 0),
                "total_plans": total_plans or 0,
                "avg_duration_per_plan_ms": float(plan_stats.avg_duration or 0) if plan_stats else 0,
                "model_distribution": model_distribution,
                "operation_breakdown": operation_breakdown,
            }
    except Exception as e:
        logger.error(f"Error getting aggregate stats: {e}")
        return {}
