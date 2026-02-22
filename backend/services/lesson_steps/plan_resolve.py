"""
Resolve plan and DB for lesson step generation.
Handles multi-project Supabase fallback and clears existing steps before generation.
"""
from typing import Any, Optional, Tuple

from fastapi import HTTPException

from backend.authorization import verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.telemetry import logger


def resolve_plan_and_db(
    plan_id: str,
    day: str,
    slot: int,
    current_user_id: Optional[str] = None,
) -> Tuple[Any, Any]:
    """
    Resolve the weekly plan and the database to use for all operations.
    Clears existing steps for this plan/day/slot before returning.
    Returns (plan, db_for_plan). Raises HTTPException if plan not found.
    """
    plan = None

    if current_user_id:
        db = get_db(user_id=current_user_id)
        plan = db.get_weekly_plan(plan_id)

    try:
        logger.info(
            "clearing_existing_steps_before_regeneration",
            extra={"plan_id": plan_id, "day": day, "slot": slot},
        )
        db_to_clear = (
            get_db(user_id=current_user_id) if current_user_id else get_db()
        )
        db_to_clear.delete_lesson_steps(
            plan_id, day_of_week=day.lower(), slot_number=slot
        )
    except Exception as e:
        logger.warning(
            "failed_to_clear_steps_before_regeneration", extra={"error": str(e)}
        )

    if not plan and settings.USE_SUPABASE:
        from backend.config import Settings
        from backend.supabase_database import SupabaseDatabase

        if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
            try:
                s1 = Settings()
                s1.SUPABASE_PROJECT = "project1"
                db1 = SupabaseDatabase(custom_settings=s1)
                plan = db1.get_weekly_plan(plan_id)
                if plan:
                    logger.info(
                        f"Plan {plan_id} found in project1 for step generation"
                    )
            except Exception as e:
                logger.debug(f"Plan not found in project1: {e}")

        if (
            not plan
            and settings.SUPABASE_URL_PROJECT2
            and settings.SUPABASE_KEY_PROJECT2
        ):
            try:
                s2 = Settings()
                s2.SUPABASE_PROJECT = "project2"
                db2 = SupabaseDatabase(custom_settings=s2)
                plan = db2.get_weekly_plan(plan_id)
                if plan:
                    logger.info(
                        f"Plan {plan_id} found in project2 for step generation"
                    )
            except Exception as e:
                logger.debug(f"Plan not found in project2: {e}")

    if not plan:
        db = get_db()
        plan = db.get_weekly_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    verify_user_access(plan.user_id, current_user_id, allow_if_none=True)

    db_for_plan = get_db(user_id=plan.user_id)
    logger.info(
        "using_plan_owner_database_for_generation",
        extra={
            "plan_id": plan_id,
            "plan_user_id": plan.user_id,
            "db_type": str(type(db_for_plan).__name__),
        },
    )

    return (plan, db_for_plan)
