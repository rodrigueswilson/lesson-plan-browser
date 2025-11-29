import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, delete, desc, select

from backend.config import settings
from backend.database_interface import DatabaseInterface
from backend.schema import (
    ClassSlot,
    LessonModeSession,
    LessonStep,
    PerformanceMetric,
    ScheduleEntry,
    User,
    WeeklyPlan,
)
from backend.services.objectives_utils import normalize_objectives_in_lesson

logger = logging.getLogger(__name__)


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of DatabaseInterface using SQLModel."""

    def __init__(self, use_ipc: bool = False):
        """
        Initialize database.
        
        Args:
            use_ipc: If True, route SQL through Rust IPC (for Android sidecar mode)
        """
        self.use_ipc = use_ipc
        
        if use_ipc:
            from backend.ipc_database import IPCDatabaseAdapter
            self._adapter = IPCDatabaseAdapter()
        else:
            # Existing SQLAlchemy setup
            self.db_path = settings.SQLITE_DB_PATH
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # check_same_thread=False is needed for FastAPI concurrency with SQLite
            sqlite_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(
                sqlite_url, connect_args={"check_same_thread": False}
            )

    @staticmethod
    def _normalize_day(day: Optional[str]) -> Optional[str]:
        if isinstance(day, str):
            return day.lower()
        return day

    @staticmethod
    def _coerce_json_field(value: Any) -> Any:
        if value is None or isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value

    def _hydrate_lesson_step(self, step: LessonStep) -> LessonStep:
        """Ensure JSON/text fields are returned as Python objects."""
        step.hidden_content = self._coerce_json_field(
            getattr(step, "hidden_content", None)
        )
        step.sentence_frames = self._coerce_json_field(
            getattr(step, "sentence_frames", None)
        )
        step.materials_needed = self._coerce_json_field(
            getattr(step, "materials_needed", None)
        )
        step.vocabulary_cognates = self._coerce_json_field(
            getattr(step, "vocabulary_cognates", None)
        )
        if step.day_of_week:
            step.day_of_week = step.day_of_week.lower()
        return step

    @contextmanager
    def get_connection(self):
        """Yields a SQLModel Session."""
        with Session(self.engine) as session:
            yield session

    def init_db(self):
        """Initialize database schema."""
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    # User CRUD operations
    def create_user(
        self,
        first_name: str = None,
        last_name: str = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Create a new user."""
        try:
            # Handle legacy name field
            if name and not first_name and not last_name:
                parts = name.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

            if not name:
                name = f"{first_name} {last_name}".strip()

            user = User(
                id=f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=name,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )

            with Session(self.engine) as session:
                session.add(user)
                session.commit()
                session.refresh(user)
                return user.id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID - works in both modes."""
        if self.use_ipc:
            row = self._adapter.query_one(
                "SELECT * FROM users WHERE id = ?", [user_id]
            )
            if not row:
                return None
            # Convert dict to User object
            # Parse datetime strings if needed
            def parse_datetime(dt_value):
                if isinstance(dt_value, datetime):
                    return dt_value
                if isinstance(dt_value, str):
                    try:
                        return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return datetime.utcnow()
                return datetime.utcnow()
            
            return User(
                id=row["id"],
                email=row.get("email"),
                first_name=row.get("first_name"),
                last_name=row.get("last_name"),
                name=row.get("name", ""),
                base_path_override=row.get("base_path_override"),
                template_path=row.get("template_path"),
                signature_image_path=row.get("signature_image_path"),
                created_at=parse_datetime(row.get("created_at")),
                updated_at=parse_datetime(row.get("updated_at")),
            )
        else:
            with Session(self.engine) as session:
                return session.get(User, user_id)

    def get_user_by_name(self, name: str) -> Optional[User]:
        """Get user by name."""
        with Session(self.engine) as session:
            statement = select(User).where(User.name == name)
            return session.exec(statement).first()

    def list_users(self) -> List[User]:
        """Get all users."""
        with Session(self.engine) as session:
            statement = select(User)
            return list(session.exec(statement).all())

    def update_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> bool:
        """Update user information."""
        try:
            with Session(self.engine) as session:
                user = session.get(User, user_id)
                if not user:
                    return False

                if first_name is not None:
                    user.first_name = first_name
                if last_name is not None:
                    user.last_name = last_name
                if email is not None:
                    user.email = email

                # Update full name if components changed or explicit name provided
                if name:
                    user.name = name
                elif first_name is not None or last_name is not None:
                    f = first_name if first_name is not None else user.first_name
                    l = last_name if last_name is not None else user.last_name
                    user.name = f"{f} {l}".strip()

                user.updated_at = datetime.utcnow()
                session.add(user)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    def update_user_base_path(self, user_id: str, base_path: str) -> bool:
        """Update user's base path override."""
        try:
            with Session(self.engine) as session:
                user = session.get(User, user_id)
                if not user:
                    return False
                user.base_path_override = base_path
                user.updated_at = datetime.utcnow()
                session.add(user)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user base path: {e}")
            return False

    def update_user_template_paths(
        self,
        user_id: str,
        template_path: Optional[str] = None,
        signature_image_path: Optional[str] = None,
    ) -> bool:
        """Update user's template path and/or signature image path."""
        try:
            with Session(self.engine) as session:
                user = session.get(User, user_id)
                if not user:
                    return False

                if template_path is not None:
                    user.template_path = template_path
                if signature_image_path is not None:
                    user.signature_image_path = signature_image_path

                user.updated_at = datetime.utcnow()
                session.add(user)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user template paths: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data."""
        try:
            with Session(self.engine) as session:
                user = session.get(User, user_id)
                if not user:
                    return False

                # Cascade delete logic (if not handled by DB FKs)
                # Delete slots
                session.exec(delete(ClassSlot).where(ClassSlot.user_id == user_id))
                # Delete plans
                session.exec(delete(WeeklyPlan).where(WeeklyPlan.user_id == user_id))
                # Delete schedules
                session.exec(
                    delete(ScheduleEntry).where(ScheduleEntry.user_id == user_id)
                )

                session.delete(user)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    # Class slot operations
    def create_class_slot(
        self,
        user_id: str,
        slot_number: int,
        subject: str,
        grade: str,
        homeroom: Optional[str] = None,
        plan_group_label: Optional[str] = None,
        proficiency_levels: Optional[str] = None,
        primary_teacher_file: Optional[str] = None,
        primary_teacher_first_name: Optional[str] = None,
        primary_teacher_last_name: Optional[str] = None,
    ) -> str:
        """Create a class slot configuration."""
        try:
            # Construct legacy primary_teacher_name
            primary_teacher_name = None
            if primary_teacher_first_name or primary_teacher_last_name:
                primary_teacher_name = f"{primary_teacher_first_name or ''} {primary_teacher_last_name or ''}".strip()

            slot = ClassSlot(
                id=f"slot_{datetime.now().strftime('%Y%m%d%H%M%S')}_{slot_number}",
                user_id=user_id,
                slot_number=slot_number,
                subject=subject,
                grade=grade,
                homeroom=homeroom,
                plan_group_label=plan_group_label,
                proficiency_levels=proficiency_levels,
                primary_teacher_file=primary_teacher_file,
                primary_teacher_name=primary_teacher_name,
                primary_teacher_first_name=primary_teacher_first_name,
                primary_teacher_last_name=primary_teacher_last_name,
            )

            with Session(self.engine) as session:
                session.add(slot)
                session.commit()
                session.refresh(slot)
                return slot.id
        except Exception as e:
            logger.error(f"Error creating class slot: {e}")
            raise

    def get_user_slots(self, user_id: str) -> List[ClassSlot]:
        """Get all class slots for a user - works in both modes."""
        if self.use_ipc:
            rows = self._adapter.query(
                "SELECT * FROM class_slots WHERE user_id = ? ORDER BY slot_number", [user_id]
            )
            slots = []
            # Helper to parse datetime
            def parse_datetime(dt_value):
                if isinstance(dt_value, datetime):
                    return dt_value
                if isinstance(dt_value, str):
                    try:
                        return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return datetime.utcnow()
                return datetime.utcnow()
            
            for row in rows:
                slots.append(ClassSlot(
                    id=row["id"],
                    user_id=row["user_id"],
                    slot_number=row["slot_number"],
                    subject=row["subject"],
                    grade=row["grade"],
                    homeroom=row.get("homeroom"),
                    plan_group_label=row.get("plan_group_label"),
                    proficiency_levels=row.get("proficiency_levels"),
                    primary_teacher_file=row.get("primary_teacher_file"),
                    primary_teacher_name=row.get("primary_teacher_name"),
                    primary_teacher_first_name=row.get("primary_teacher_first_name"),
                    primary_teacher_last_name=row.get("primary_teacher_last_name"),
                    primary_teacher_file_pattern=row.get("primary_teacher_file_pattern"),
                    display_order=row.get("display_order", 0),
                    created_at=parse_datetime(row.get("created_at")),
                    updated_at=parse_datetime(row.get("updated_at")),
                ))
            return slots
        else:
            with Session(self.engine) as session:
                statement = (
                    select(ClassSlot)
                    .where(ClassSlot.user_id == user_id)
                    .order_by(ClassSlot.slot_number)
                )
                return list(session.exec(statement).all())

    def get_slot(self, slot_id: str) -> Optional[ClassSlot]:
        """Get a specific class slot."""
        with Session(self.engine) as session:
            return session.get(ClassSlot, slot_id)

    def update_class_slot(self, slot_id: str, **kwargs) -> bool:
        """Update class slot configuration."""
        try:
            with Session(self.engine) as session:
                slot = session.get(ClassSlot, slot_id)
                if not slot:
                    return False

                for key, value in kwargs.items():
                    if hasattr(slot, key):
                        setattr(slot, key, value)

                # Update legacy name if parts changed
                if (
                    "primary_teacher_first_name" in kwargs
                    or "primary_teacher_last_name" in kwargs
                ):
                    f = kwargs.get(
                        "primary_teacher_first_name", slot.primary_teacher_first_name
                    )
                    l = kwargs.get(
                        "primary_teacher_last_name", slot.primary_teacher_last_name
                    )
                    slot.primary_teacher_name = f"{f or ''} {l or ''}".strip()

                slot.updated_at = datetime.utcnow()
                session.add(slot)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating class slot: {e}")
            return False

    def delete_class_slot(self, slot_id: str) -> bool:
        """Delete a class slot."""
        try:
            with Session(self.engine) as session:
                slot = session.get(ClassSlot, slot_id)
                if not slot:
                    return False
                session.delete(slot)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting class slot: {e}")
            return False

    def delete_user_slots(self, user_id: str) -> int:
        """Delete all class slots for a user."""
        try:
            with Session(self.engine) as session:
                statement = delete(ClassSlot).where(ClassSlot.user_id == user_id)
                result = session.exec(statement)
                session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting user slots: {e}")
            return 0

    # Weekly plan operations
    def create_weekly_plan(
        self,
        user_id: str,
        week_of: str,
        output_file: str,
        week_folder_path: str,
        consolidated: bool = False,
        total_slots: int = 1,
    ) -> str:
        """Create a new weekly plan record - works in both modes."""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if self.use_ipc:
            try:
                self._adapter.execute(
                    """INSERT INTO weekly_plans 
                       (id, user_id, week_of, output_file, week_folder_path, consolidated, total_slots, status, generated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        plan_id,
                        user_id,
                        week_of,
                        output_file,
                        week_folder_path,
                        1 if consolidated else 0,
                        total_slots,
                        "pending",
                        datetime.utcnow().isoformat()
                    ]
                )
                return plan_id
            except Exception as e:
                logger.error(f"Error creating weekly plan via IPC: {e}")
                raise
        else:
            try:
                plan = WeeklyPlan(
                    id=plan_id,
                    user_id=user_id,
                    week_of=week_of,
                    output_file=output_file,
                    week_folder_path=week_folder_path,
                    consolidated=1 if consolidated else 0,
                    total_slots=total_slots,
                    status="pending",
                )

                with Session(self.engine) as session:
                    session.add(plan)
                    session.commit()
                    session.refresh(plan)
                    return plan.id
            except Exception as e:
                logger.error(f"Error creating weekly plan: {e}")
                raise

    def get_weekly_plan(self, plan_id: str) -> Optional[WeeklyPlan]:
        """Get a weekly plan by ID - works in both modes."""
        import json

        if self.use_ipc:
            row = self._adapter.query_one(
                "SELECT * FROM weekly_plans WHERE id = ?", [plan_id]
            )
            if not row:
                return None
            
            # Parse lesson_json if it's a string
            lesson_json = row.get("lesson_json")
            if isinstance(lesson_json, str):
                try:
                    lesson_json = json.loads(lesson_json)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse lesson_json for plan {plan_id}")
                    lesson_json = None
            
            # Helper to parse datetime
            def parse_datetime(dt_value):
                if isinstance(dt_value, datetime):
                    return dt_value
                if isinstance(dt_value, str):
                    try:
                        return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        return datetime.utcnow()
                return datetime.utcnow()
            
            return WeeklyPlan(
                id=row["id"],
                user_id=row["user_id"],
                week_of=row["week_of"],
                status=row.get("status", "pending"),
                output_file=row.get("output_file"),
                week_folder_path=row.get("week_folder_path"),
                consolidated=row.get("consolidated", 0),
                total_slots=row.get("total_slots", 1),
                generated_at=parse_datetime(row.get("generated_at")),
                processing_time_ms=row.get("processing_time_ms"),
                total_tokens=row.get("total_tokens"),
                total_cost_usd=row.get("total_cost_usd"),
                llm_model=row.get("llm_model"),
                error_message=row.get("error_message"),
                lesson_json=lesson_json,
            )
        else:
            with Session(self.engine) as session:
                plan = session.get(WeeklyPlan, plan_id)
                if plan and plan.lesson_json and isinstance(plan.lesson_json, str):
                    # SQLite stores JSON as TEXT, so parse it back to dict
                    try:
                        plan.lesson_json = json.loads(plan.lesson_json)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Failed to parse lesson_json for plan {plan_id}")
                        plan.lesson_json = None
                return plan

    def get_user_plans(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[WeeklyPlan]:
        """Get weekly plans for a user."""
        with Session(self.engine) as session:
            statement = (
                select(WeeklyPlan)
                .where(WeeklyPlan.user_id == user_id)
                .order_by(desc(WeeklyPlan.generated_at))
            )
            if limit:
                statement = statement.limit(limit)
            plans = list(session.exec(statement).all())
            # SQLite stores JSON as TEXT, so parse lesson_json back to dict for each plan
            for plan in plans:
                if plan.lesson_json and isinstance(plan.lesson_json, str):
                    try:
                        plan.lesson_json = json.loads(plan.lesson_json)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"Failed to parse lesson_json for plan {plan.id}"
                        )
                        plan.lesson_json = None
            return plans

    def update_weekly_plan(
        self,
        plan_id: str,
        status: Optional[str] = None,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        lesson_json: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update weekly plan status or lesson_json.
        
        NOTE: When updating lesson_json, ensure vocabulary_cognates and sentence_frames
        are properly populated under days[day]["slots"][slot_number]. If these are
        missing or empty, vocabulary/frames steps will not be created during step
        generation. Use the validate_lesson_json_vocab_frames() helper to check
        lesson_json structure before updating.
        """
        try:
            with Session(self.engine) as session:
                plan = session.get(WeeklyPlan, plan_id)
                if not plan:
                    return False

                if status:
                    plan.status = status
                if output_file:
                    plan.output_file = output_file
                if error_message:
                    plan.error_message = error_message
                if lesson_json is not None:
                    normalize_objectives_in_lesson(lesson_json)
                    plan.lesson_json = lesson_json

                session.add(plan)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating weekly plan: {e}")
            return False

    # Performance metrics operations
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
            )
            with Session(self.engine) as session:
                session.add(metric)
                session.commit()
        except Exception as e:
            logger.error(f"Error saving performance metric: {e}")

    def delete_old_metrics(self, days: int = 30) -> int:
        """Delete performance metrics older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with Session(self.engine) as session:
                statement = delete(PerformanceMetric).where(
                    PerformanceMetric.started_at < cutoff_date
                )
                result = session.exec(statement)
                session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting old metrics: {e}")
            return 0

    def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for a weekly plan."""
        with Session(self.engine) as session:
            statement = select(PerformanceMetric).where(
                PerformanceMetric.plan_id == plan_id
            )
            metrics = session.exec(statement).all()
            # Convert PerformanceMetric objects to dictionaries
            return [
                m.model_dump() if hasattr(m, "model_dump") else m.dict()
                for m in metrics
            ]

    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for a weekly plan."""
        with Session(self.engine) as session:
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
        self,
        plan_id: str,
        processing_time_ms: Optional[float],
        total_tokens: Optional[int],
        total_cost_usd: Optional[float],
        llm_model: Optional[str],
    ) -> bool:
        """Update weekly_plans table with aggregated metrics."""
        try:
            with Session(self.engine) as session:
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

    def get_aggregate_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregate analytics across all plans."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            with Session(self.engine) as session:
                # Base query for metrics
                query = select(
                    func.count(PerformanceMetric.id).label("total_requests"),
                    func.sum(PerformanceMetric.tokens_total).label("total_tokens"),
                    func.sum(PerformanceMetric.cost_usd).label("total_cost"),
                    func.avg(PerformanceMetric.duration_ms).label("avg_latency"),
                ).where(PerformanceMetric.started_at >= start_date)

                if user_id:
                    # Join with WeeklyPlan to filter by user_id
                    query = query.join(WeeklyPlan).where(WeeklyPlan.user_id == user_id)

                metrics = session.exec(query).first()

                # Count plans
                plan_query = select(func.count(WeeklyPlan.id)).where(
                    WeeklyPlan.generated_at >= start_date
                )
                if user_id:
                    plan_query = plan_query.where(WeeklyPlan.user_id == user_id)

                total_plans = session.exec(plan_query).one()

                return {
                    "total_requests": metrics.total_requests or 0,
                    "total_tokens": metrics.total_tokens or 0,
                    "total_cost_usd": metrics.total_cost or 0,
                    "avg_latency_ms": metrics.avg_latency or 0,
                    "total_plans": total_plans or 0,
                }
        except Exception as e:
            logger.error(f"Error getting aggregate stats: {e}")
            return {}

    def get_daily_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily breakdown of activity."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            with Session(self.engine) as session:
                # Group by date
                query = (
                    select(
                        func.date(PerformanceMetric.started_at).label("date"),
                        func.count(PerformanceMetric.id).label("requests"),
                        func.sum(PerformanceMetric.tokens_total).label("tokens"),
                        func.sum(PerformanceMetric.cost_usd).label("cost"),
                    )
                    .where(PerformanceMetric.started_at >= start_date)
                    .group_by(func.date(PerformanceMetric.started_at))
                )

                if user_id:
                    query = query.join(WeeklyPlan).where(WeeklyPlan.user_id == user_id)

                results = session.exec(query).all()

                return [
                    {
                        "date": row.date,
                        "requests": row.requests,
                        "tokens": row.tokens,
                        "cost": row.cost,
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Error getting daily breakdown: {e}")
            return []

    def get_session_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get session-by-session breakdown."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            with Session(self.engine) as session:
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

    # Schedule operations
    def create_schedule_entry(self, entry_data: Dict[str, Any]) -> str:
        """Create a new schedule entry."""
        try:
            entry = ScheduleEntry(
                id=f"sched_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entry_data.get('day_of_week')}_{entry_data.get('slot_number')}",
                **entry_data,
            )
            with Session(self.engine) as session:
                session.add(entry)
                session.commit()
                session.refresh(entry)
                return entry.id
        except Exception as e:
            logger.error(f"Error creating schedule entry: {e}")
            raise

    def get_user_schedule(
        self,
        user_id: str,
        day_of_week: Optional[str] = None,
        homeroom: Optional[str] = None,
        grade: Optional[str] = None,
    ) -> List[ScheduleEntry]:
        """Get schedule entries for a user."""
        with Session(self.engine) as session:
            query = select(ScheduleEntry).where(ScheduleEntry.user_id == user_id)

            if day_of_week:
                query = query.where(ScheduleEntry.day_of_week == day_of_week)
            if homeroom:
                query = query.where(ScheduleEntry.homeroom == homeroom)
            if grade:
                query = query.where(ScheduleEntry.grade == grade)

            query = query.order_by(ScheduleEntry.day_of_week, ScheduleEntry.start_time)
            return list(session.exec(query).all())

    def get_current_lesson(self, user_id: str) -> Optional[ScheduleEntry]:
        """Get current lesson based on current time."""
        try:
            now = datetime.now()
            current_day = now.strftime("%A").lower()
            current_time = now.strftime("%H:%M")

            with Session(self.engine) as session:
                query = select(ScheduleEntry).where(
                    ScheduleEntry.user_id == user_id,
                    ScheduleEntry.day_of_week == current_day,
                    ScheduleEntry.start_time <= current_time,
                    ScheduleEntry.end_time > current_time,
                    ScheduleEntry.is_active == True,
                )
                return session.exec(query).first()
        except Exception as e:
            logger.error(f"Error getting current lesson: {e}")
            return None

    def update_schedule_entry(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a schedule entry."""
        try:
            with Session(self.engine) as session:
                entry = session.get(ScheduleEntry, schedule_id)
                if not entry:
                    return False

                for key, value in updates.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)

                entry.updated_at = datetime.utcnow()
                session.add(entry)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating schedule entry: {e}")
            return False

    def delete_schedule_entry(self, schedule_id: str) -> bool:
        """Delete a schedule entry."""
        try:
            with Session(self.engine) as session:
                entry = session.get(ScheduleEntry, schedule_id)
                if not entry:
                    return False
                session.delete(entry)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting schedule entry: {e}")
            return False

    def bulk_create_schedule_entries(
        self, entries: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Bulk create schedule entries."""
        created_count = 0
        errors = []

        with Session(self.engine) as session:
            for entry_data in entries:
                try:
                    entry = ScheduleEntry(
                        id=f"sched_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entry_data.get('day_of_week')}_{entry_data.get('slot_number')}",
                        **entry_data,
                    )
                    session.add(entry)
                    created_count += 1
                except Exception as e:
                    errors.append(
                        f"Error creating entry for {entry_data.get('day_of_week')}: {str(e)}"
                    )

            try:
                session.commit()
            except Exception as e:
                errors.append(f"Commit failed: {str(e)}")
                return 0, errors

        return created_count, errors

    def clear_user_schedule(self, user_id: str) -> int:
        """Delete all schedule entries for a user."""
        try:
            with Session(self.engine) as session:
                result = session.exec(
                    delete(ScheduleEntry).where(ScheduleEntry.user_id == user_id)
                )
                session.commit()
                return result.rowcount or 0
        except Exception as e:
            logger.error(f"Error clearing schedule for user {user_id}: {e}")
            raise

    # Lesson Step operations
    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
        """Create a lesson step."""
        try:
            payload = step_data.copy()
            payload["day_of_week"] = self._normalize_day(payload.get("day_of_week"))
            
            # DEBUG: Log vocabulary_cognates before creating LessonStep
            vocab_in_payload = payload.get("vocabulary_cognates")
            print(f"[DEBUG] create_lesson_step: vocabulary_cognates in payload: type={type(vocab_in_payload)}, value={vocab_in_payload}, length={len(vocab_in_payload) if isinstance(vocab_in_payload, list) else 'N/A'}")
            logger.info(
                "create_lesson_step_vocab_check",
                extra={
                    "step_name": payload.get("step_name"),
                    "vocab_type": str(type(vocab_in_payload)),
                    "vocab_is_list": isinstance(vocab_in_payload, list),
                    "vocab_length": len(vocab_in_payload) if isinstance(vocab_in_payload, list) else 0,
                    "vocab_is_none": vocab_in_payload is None,
                },
            )
            
            step = LessonStep(**payload)
            
            # DEBUG: Log after creating LessonStep object
            vocab_in_step = getattr(step, "vocabulary_cognates", None)
            print(f"[DEBUG] create_lesson_step: vocabulary_cognates in step object: type={type(vocab_in_step)}, value={vocab_in_step}, length={len(vocab_in_step) if isinstance(vocab_in_step, list) else 'N/A'}")
            
            with Session(self.engine) as session:
                session.add(step)
                session.commit()
                session.refresh(step)
                
                # DEBUG: Log after saving to database
                vocab_after_save = getattr(step, "vocabulary_cognates", None)
                print(f"[DEBUG] create_lesson_step: vocabulary_cognates after save: type={type(vocab_after_save)}, value={vocab_after_save}, length={len(vocab_after_save) if isinstance(vocab_after_save, list) else 'N/A'}")
                
                return step.id
        except Exception as e:
            logger.error(f"Error creating lesson step: {e}")
            raise

    def delete_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> int:
        """Delete lesson steps for a plan/day/slot."""
        try:
            with Session(self.engine) as session:
                stmt = delete(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
                normalized_day = self._normalize_day(day_of_week)
                if normalized_day:
                    stmt = stmt.where(LessonStep.day_of_week == normalized_day)
                if slot_number is not None:
                    stmt = stmt.where(LessonStep.slot_number == slot_number)
                result = session.exec(stmt)
                session.commit()
                return result.rowcount or 0
        except Exception as e:
            logger.error(f"Error deleting lesson steps: {e}")
            return 0

    def get_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> List[LessonStep]:
        """Get lesson steps."""
        with Session(self.engine) as session:
            query = select(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
            normalized_day = self._normalize_day(day_of_week)
            if normalized_day:
                query = query.where(LessonStep.day_of_week == normalized_day)
            if slot_number is not None:
                query = query.where(LessonStep.slot_number == slot_number)

            query = query.order_by(LessonStep.step_number)
            steps = list(session.exec(query).all())
            return [self._hydrate_lesson_step(step) for step in steps]

    # Lesson Mode Session operations
    def create_lesson_mode_session(self, session_data: Dict[str, Any]) -> str:
        """Create a lesson mode session."""
        try:
            payload = session_data.copy()
            # Normalize day_of_week
            if "day_of_week" in payload:
                payload["day_of_week"] = self._normalize_day(payload["day_of_week"])
            # Convert adjusted_durations dict to JSON string if present
            if "adjusted_durations" in payload and isinstance(
                payload["adjusted_durations"], dict
            ):
                payload["adjusted_durations"] = json.dumps(
                    payload["adjusted_durations"]
                )

            session_obj = LessonModeSession(**payload)
            with Session(self.engine) as session:
                session.add(session_obj)
                session.commit()
                session.refresh(session_obj)
                return session_obj.id
        except Exception as e:
            logger.error(f"Error creating lesson mode session: {e}")
            raise

    def get_lesson_mode_session(self, session_id: str) -> Optional[LessonModeSession]:
        """Get a lesson mode session by ID."""
        try:
            with Session(self.engine) as session:
                session_obj = session.get(LessonModeSession, session_id)
                if session_obj:
                    # Hydrate adjusted_durations from JSON string
                    if session_obj.adjusted_durations and isinstance(
                        session_obj.adjusted_durations, str
                    ):
                        try:
                            session_obj.adjusted_durations = json.loads(
                                session_obj.adjusted_durations
                            )
                        except (json.JSONDecodeError, TypeError):
                            session_obj.adjusted_durations = None
                return session_obj
        except Exception as e:
            logger.error(f"Error getting lesson mode session: {e}")
            return None

    def get_active_lesson_mode_session(
        self,
        user_id: str,
        lesson_plan_id: Optional[str] = None,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> Optional[LessonModeSession]:
        """Get the active (not ended) lesson mode session for a user/lesson."""
        try:
            with Session(self.engine) as session:
                query = select(LessonModeSession).where(
                    LessonModeSession.user_id == user_id,
                    LessonModeSession.ended_at.is_(None),
                )
                if lesson_plan_id:
                    query = query.where(
                        LessonModeSession.lesson_plan_id == lesson_plan_id
                    )
                if day_of_week:
                    normalized_day = self._normalize_day(day_of_week)
                    query = query.where(LessonModeSession.day_of_week == normalized_day)
                if slot_number is not None:
                    query = query.where(LessonModeSession.slot_number == slot_number)

                query = query.order_by(desc(LessonModeSession.last_updated))
                result = session.exec(query).first()

                if result:
                    # Hydrate adjusted_durations from JSON string
                    if result.adjusted_durations and isinstance(
                        result.adjusted_durations, str
                    ):
                        try:
                            result.adjusted_durations = json.loads(
                                result.adjusted_durations
                            )
                        except (json.JSONDecodeError, TypeError):
                            result.adjusted_durations = None

                return result
        except Exception as e:
            logger.error(f"Error getting active lesson mode session: {e}")
            return None

    def update_lesson_mode_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a lesson mode session."""
        try:
            with Session(self.engine) as session:
                session_obj = session.get(LessonModeSession, session_id)
                if not session_obj:
                    return False

                # Normalize day_of_week if present
                if "day_of_week" in updates:
                    updates["day_of_week"] = self._normalize_day(updates["day_of_week"])

                # Convert adjusted_durations dict to JSON string if present
                if "adjusted_durations" in updates and isinstance(
                    updates["adjusted_durations"], dict
                ):
                    updates["adjusted_durations"] = json.dumps(
                        updates["adjusted_durations"]
                    )

                # Update fields
                for key, value in updates.items():
                    if hasattr(session_obj, key):
                        setattr(session_obj, key, value)

                session_obj.last_updated = datetime.utcnow()
                session.add(session_obj)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating lesson mode session: {e}")
            return False

    def end_lesson_mode_session(self, session_id: str) -> bool:
        """Mark a lesson mode session as ended."""
        try:
            with Session(self.engine) as session:
                session_obj = session.get(LessonModeSession, session_id)
                if not session_obj:
                    return False

                session_obj.ended_at = datetime.utcnow()
                session_obj.last_updated = datetime.utcnow()
                session.add(session_obj)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error ending lesson mode session: {e}")
            return False


# Global database instance
_db_instance = None
# Cache for user_id to database instance mapping (for multi-project Supabase)
_user_db_cache: Dict[str, DatabaseInterface] = {}


def get_db(user_id: Optional[str] = None, **kwargs) -> DatabaseInterface:
    """Get database instance (Singleton or user-specific for Supabase multi-project).

    Args:
        user_id: Optional user_id for multi-tenant DB selection (Supabase)
        **kwargs: Additional arguments

    Returns:
        DatabaseInterface instance
    """
    global _db_instance, _user_db_cache

    # If using Supabase and user_id is provided, try to find user-specific database
    if settings.USE_SUPABASE and user_id:
        # Check cache first
        if user_id in _user_db_cache:
            return _user_db_cache[user_id]

        # Try to find user in project1, then project2
        try:
            from backend.config import Settings
            from backend.supabase_database import SupabaseDatabase

            # Try project1 first
            if settings.SUPABASE_URL_PROJECT1 and settings.SUPABASE_KEY_PROJECT1:
                try:
                    s1 = Settings()
                    s1.SUPABASE_PROJECT = "project1"
                    db1 = SupabaseDatabase(custom_settings=s1)
                    user1 = db1.get_user(user_id)
                    if user1:
                        logger.info(f"User {user_id} found in project1")
                        _user_db_cache[user_id] = db1
                        return db1
                except Exception as e:
                    logger.debug(f"User {user_id} not found in project1: {e}")

            # Try project2
            if settings.SUPABASE_URL_PROJECT2 and settings.SUPABASE_KEY_PROJECT2:
                try:
                    s2 = Settings()
                    s2.SUPABASE_PROJECT = "project2"
                    db2 = SupabaseDatabase(custom_settings=s2)
                    user2 = db2.get_user(user_id)
                    if user2:
                        logger.info(f"User {user_id} found in project2")
                        _user_db_cache[user_id] = db2
                        return db2
                except Exception as e:
                    logger.debug(f"User {user_id} not found in project2: {e}")

            # If user not found in either project, log warning and fall back to default
            logger.warning(
                f"User {user_id} not found in any Supabase project, using default database"
            )
        except ImportError:
            # Supabase not available, fall through to default
            logger.debug("SupabaseDatabase not available, using default database")
        except Exception as e:
            logger.warning(
                f"Error determining user database project: {e}, using default database"
            )

    # Default singleton behavior (SQLite or default Supabase)
    if _db_instance is None:
        # Initialize based on settings
        if settings.USE_SUPABASE:
            # For now, we only have SQLite implementation in this file
            # Ideally we would import Supabase implementation here
            logger.info(
                "Using SQLite Database (Supabase flag set but not implemented in this factory)"
            )
            _db_instance = SQLiteDatabase()
        else:
            logger.info("Using SQLite Database")
            _db_instance = SQLiteDatabase()

        # Initialize schema
        _db_instance.init_db()

    return _db_instance
