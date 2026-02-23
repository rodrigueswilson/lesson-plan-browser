"""Performance metrics and analytics operations for SQLite database."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import case, func, or_
from sqlmodel import Session, delete, desc, select

from backend.schema import PerformanceMetric, WeeklyPlan

from backend.database.metrics_aggregate import get_aggregate_stats

logger = logging.getLogger(__name__)


def save_performance_metric(
    db,
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
    is_parallel: Optional[bool] = None,
    parallel_slot_count: Optional[int] = None,
    sequential_time_ms: Optional[float] = None,
    rate_limit_errors: Optional[int] = None,
    concurrency_level: Optional[int] = None,
    tpm_usage: Optional[int] = None,
    rpm_usage: Optional[int] = None,
) -> None:
    """Save a performance metric."""
    try:
        metric = PerformanceMetric(
            id=operation_id,
            plan_id=plan_id,
            operation_type=operation_type,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            llm_provider=llm_provider,
            llm_model=llm_model,
            cost_usd=cost_usd,
            error_message=error_message,
            slot_number=slot_number,
            day_number=day_number,
            is_parallel=is_parallel,
            parallel_slot_count=parallel_slot_count,
            sequential_time_ms=sequential_time_ms,
            rate_limit_errors=rate_limit_errors or 0,
            concurrency_level=concurrency_level,
            tpm_usage=tpm_usage,
            rpm_usage=rpm_usage,
        )
        with Session(db.engine) as session:
            session.add(metric)
            session.commit()
    except Exception as e:
        logger.error(f"Error saving performance metric: {e}")


def delete_old_metrics(db, days: int = 30) -> int:
    """Delete performance metrics older than specified days."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        with Session(db.engine) as session:
            statement = delete(PerformanceMetric).where(
                PerformanceMetric.started_at < cutoff_date
            )
            result = session.exec(statement)
            session.commit()
            return result.rowcount
    except Exception as e:
        logger.error(f"Error deleting old metrics: {e}")
        return 0


def get_plan_metrics(db, plan_id: str) -> List[Dict[str, Any]]:
    """Get all metrics for a weekly plan."""
    with Session(db.engine) as session:
        statement = select(PerformanceMetric).where(
            PerformanceMetric.plan_id == plan_id
        )
        metrics = session.exec(statement).all()
        return [
            m.model_dump() if hasattr(m, "model_dump") else m.dict()
            for m in metrics
        ]


def get_plan_summary(db, plan_id: str) -> Dict[str, Any]:
    """Get aggregated metrics for a weekly plan."""
    with Session(db.engine) as session:
        statement = select(
            func.sum(PerformanceMetric.duration_ms).label("total_time"),
            func.sum(PerformanceMetric.tokens_total).label("total_tokens"),
            func.sum(PerformanceMetric.cost_usd).label("total_cost"),
            func.count(PerformanceMetric.id).label("operation_count"),
        ).where(PerformanceMetric.plan_id == plan_id)

        result = session.exec(statement).first()
        return {
            "total_time_ms": result.total_time or 0,
            "total_tokens": result.total_tokens or 0,
            "total_cost_usd": result.total_cost or 0,
            "operation_count": result.operation_count or 0,
        }


def update_plan_summary(
    db,
    plan_id: str,
    processing_time_ms: Optional[float],
    total_tokens: Optional[int],
    total_cost_usd: Optional[float],
    llm_model: Optional[str],
) -> bool:
    """Update weekly_plans table with aggregated metrics."""
    try:
        with Session(db.engine) as session:
            plan = session.get(WeeklyPlan, plan_id)
            if not plan:
                return False

            if processing_time_ms is not None:
                plan.processing_time_ms = processing_time_ms
            if total_tokens is not None:
                plan.total_tokens = total_tokens
            if total_cost_usd is not None:
                plan.total_cost_usd = total_cost_usd
            if llm_model is not None:
                plan.llm_model = llm_model

            session.add(plan)
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating plan summary: {e}")
        return False


def get_daily_breakdown(
    db, days: int = 30, user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get daily breakdown of activity."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            metrics_query = (
                select(
                    func.date(PerformanceMetric.started_at).label("date"),
                    func.count(PerformanceMetric.id).label("operations"),
                    func.sum(PerformanceMetric.cost_usd).label("cost_usd"),
                )
                .where(PerformanceMetric.started_at >= start_date)
                .group_by(func.date(PerformanceMetric.started_at))
            )

            if user_id:
                metrics_query = metrics_query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            metrics_results = session.exec(metrics_query).all()

            plans_query = (
                select(
                    func.date(WeeklyPlan.generated_at).label("date"),
                    func.count(WeeklyPlan.id).label("plans"),
                )
                .where(WeeklyPlan.generated_at >= start_date)
                .group_by(func.date(WeeklyPlan.generated_at))
            )
            if user_id:
                plans_query = plans_query.where(WeeklyPlan.user_id == user_id)

            plans_results = session.exec(plans_query).all()

            daily_dict = {}
            for row in metrics_results:
                date_str = str(row.date)
                if date_str not in daily_dict:
                    if isinstance(row.date, datetime):
                        date_iso = row.date.date().isoformat()
                    elif isinstance(row.date, str):
                        date_iso = row.date
                    else:
                        date_iso = str(row.date)
                    daily_dict[date_str] = {"date": date_iso, "operations": 0, "cost_usd": 0, "plans": 0}
                daily_dict[date_str]["operations"] = row.operations or 0
                daily_dict[date_str]["cost_usd"] = float(row.cost_usd or 0)

            for row in plans_results:
                date_str = str(row.date)
                if date_str not in daily_dict:
                    if isinstance(row.date, datetime):
                        date_iso = row.date.date().isoformat()
                    elif isinstance(row.date, str):
                        date_iso = row.date
                    else:
                        date_iso = str(row.date)
                    daily_dict[date_str] = {"date": date_iso, "operations": 0, "cost_usd": 0, "plans": 0}
                daily_dict[date_str]["plans"] = row.plans or 0

            return list(daily_dict.values())
    except Exception as e:
        logger.error(f"Error getting daily breakdown: {e}")
        return []


def get_session_breakdown(
    db, days: int = 30, user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get session-by-session breakdown."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            query = select(WeeklyPlan).where(WeeklyPlan.generated_at >= start_date)
            if user_id:
                query = query.where(WeeklyPlan.user_id == user_id)
            query = query.order_by(desc(WeeklyPlan.generated_at))

            plans = session.exec(query).all()

            return [
                {
                    "plan_id": p.id,
                    "timestamp": p.generated_at,
                    "week_of": p.week_of,
                    "status": p.status,
                    "duration_ms": p.processing_time_ms,
                    "tokens": p.total_tokens,
                    "cost": p.total_cost_usd,
                    "model": p.llm_model,
                }
                for p in plans
            ]
    except Exception as e:
        logger.error(f"Error getting session breakdown: {e}")
        return []


def get_operation_stats(
    db, days: int = 30, user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get time breakdown by operation type."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            query = (
                select(
                    PerformanceMetric.operation_type,
                    func.avg(PerformanceMetric.duration_ms).label("avg_duration"),
                    func.count(PerformanceMetric.id).label("count"),
                )
                .where(PerformanceMetric.started_at >= start_date)
                .group_by(PerformanceMetric.operation_type)
            )

            if user_id:
                query = query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            results = session.exec(query).all()

            return [
                {
                    "operation_type": row.operation_type,
                    "avg_duration_ms": row.avg_duration,
                    "count": row.count,
                }
                for row in results
            ]
    except Exception as e:
        logger.error(f"Error getting operation stats: {e}")
        return []


def get_error_stats(
    db, days: int = 30, user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get success vs failure stats with error distribution."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            query_total = select(
                PerformanceMetric.id, PerformanceMetric.error_message
            ).where(PerformanceMetric.started_at >= start_date)

            if user_id:
                query_total = query_total.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            all_metrics = session.exec(query_total).all()

            total_count = len(all_metrics)
            failure_count = sum(1 for m in all_metrics if m.error_message)
            success_count = total_count - failure_count

            error_distribution = {}
            for m in all_metrics:
                if m.error_message:
                    err_msg = m.error_message.lower()
                    category = "unknown"
                    if "json" in err_msg or "parse" in err_msg:
                        category = "json_parse_error"
                    elif "timeout" in err_msg or "timed out" in err_msg:
                        category = "timeout"
                    elif "validation" in err_msg:
                        category = "validation_error"
                    elif "rate limit" in err_msg or "429" in err_msg:
                        category = "rate_limit"
                    else:
                        category = "other"

                    error_distribution[category] = (
                        error_distribution.get(category, 0) + 1
                    )

            return {
                "total": total_count,
                "success": success_count,
                "failure": failure_count,
                "success_rate": (success_count / total_count * 100)
                if total_count > 0
                else 100.0,
                "error_breakdown": error_distribution,
            }
    except Exception as e:
        logger.error(f"Error getting error stats: {e}")
        return {
            "total": 0,
            "success": 0,
            "failure": 0,
            "success_rate": 0,
            "error_breakdown": {},
        }


def get_parallel_processing_stats(
    db, days: int = 30, user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get parallel processing statistics."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        with Session(db.engine) as session:
            query = select(
                func.count(PerformanceMetric.id).label("total_operations"),
                func.sum(
                    case(
                        (PerformanceMetric.is_parallel == True, 1),
                        else_=0
                    )
                ).label("parallel_count"),
                func.avg(PerformanceMetric.duration_ms).label("avg_duration"),
                func.avg(
                    case(
                        (PerformanceMetric.is_parallel == True, PerformanceMetric.duration_ms),
                        else_=None
                    )
                ).label("avg_parallel_duration"),
                func.avg(
                    case(
                        (or_(PerformanceMetric.is_parallel == False, PerformanceMetric.is_parallel.is_(None)), PerformanceMetric.duration_ms),
                        else_=None
                    )
                ).label("avg_sequential_duration"),
                func.avg(PerformanceMetric.parallel_slot_count).label("avg_parallel_slot_count"),
                func.avg(PerformanceMetric.sequential_time_ms).label("avg_sequential_time"),
                func.sum(PerformanceMetric.rate_limit_errors).label("total_rate_limit_errors"),
                func.avg(PerformanceMetric.concurrency_level).label("avg_concurrency_level"),
                func.avg(PerformanceMetric.tpm_usage).label("avg_tpm_usage"),
                func.avg(PerformanceMetric.rpm_usage).label("avg_rpm_usage"),
            ).where(PerformanceMetric.started_at >= start_date)

            if user_id:
                query = query.join(
                    WeeklyPlan, PerformanceMetric.plan_id == WeeklyPlan.id
                ).where(WeeklyPlan.user_id == user_id)

            stats = session.exec(query).first()

            parallel_count = stats.parallel_count or 0
            total_ops = stats.total_operations or 0
            avg_parallel = stats.avg_parallel_duration or 0
            avg_sequential = stats.avg_sequential_duration or 0
            avg_sequential_time = stats.avg_sequential_time or 0

            time_savings_ms = 0
            time_savings_percent = 0
            if avg_parallel > 0 and avg_sequential_time > 0:
                time_savings_ms = avg_sequential_time - avg_parallel
                time_savings_percent = (time_savings_ms / avg_sequential_time * 100) if avg_sequential_time > 0 else 0

            return {
                "total_operations": total_ops,
                "parallel_operations": parallel_count,
                "sequential_operations": total_ops - parallel_count,
                "parallel_percentage": (parallel_count / total_ops * 100) if total_ops > 0 else 0,
                "avg_duration_ms": stats.avg_duration or 0,
                "avg_parallel_duration_ms": avg_parallel,
                "avg_sequential_duration_ms": avg_sequential,
                "avg_parallel_slot_count": stats.avg_parallel_slot_count or 0,
                "avg_sequential_time_ms": avg_sequential_time,
                "time_savings_ms": time_savings_ms,
                "time_savings_percent": time_savings_percent,
                "total_rate_limit_errors": stats.total_rate_limit_errors or 0,
                "avg_concurrency_level": stats.avg_concurrency_level or 0,
                "avg_tpm_usage": stats.avg_tpm_usage or 0,
                "avg_rpm_usage": stats.avg_rpm_usage or 0,
            }
    except Exception as e:
        logger.error(f"Error getting parallel processing stats: {e}")
        return {
            "total_operations": 0,
            "parallel_operations": 0,
            "sequential_operations": 0,
            "parallel_percentage": 0,
            "avg_duration_ms": 0,
            "avg_parallel_duration_ms": 0,
            "avg_sequential_duration_ms": 0,
            "avg_parallel_slot_count": 0,
            "avg_sequential_time_ms": 0,
            "time_savings_ms": 0,
            "time_savings_percent": 0,
            "total_rate_limit_errors": 0,
            "avg_concurrency_level": 0,
            "avg_tpm_usage": 0,
            "avg_rpm_usage": 0,
        }
