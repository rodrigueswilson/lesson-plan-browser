"""
SSE Progress Streaming for Bilingual Lesson Plan Builder.

Provides real-time progress updates during lesson plan rendering.
"""

import asyncio
import glob
import json
import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional


def _utc_now_naive() -> datetime:
    """Naive UTC wall time (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


CANONICAL_STATUS_MAP = {
    "initialized": "processing",
    "queued": "processing",
    "processing": "processing",
    "extracting": "processing",
    "transforming": "processing",
    "rendering": "processing",
    "finalizing": "processing",
    "complete": "completed",
    "completed": "completed",
    "done": "completed",
    "error": "failed",
    "failed": "failed",
}

STAGE_LABELS = {
    "queued": "Queued",
    "extracting": "Extracting lesson data",
    "transforming": "Transforming lessons with AI",
    "rendering": "Rendering DOCX",
    "finalizing": "Finalizing outputs",
    "completed": "Completed",
    "failed": "Failed",
}


def canonical_status(raw_status: Optional[str]) -> str:
    return CANONICAL_STATUS_MAP.get(str(raw_status or "").lower(), "processing")


def normalize_stage(raw_stage: Optional[str]) -> str:
    stage = str(raw_stage or "").lower()
    if stage in ("initialized", "processing"):
        return "extracting"
    if stage in ("complete", "completed", "done"):
        return "completed"
    if stage in ("error", "failed"):
        return "failed"
    if stage in STAGE_LABELS:
        return stage
    return "extracting"


def stage_label(stage: Optional[str]) -> str:
    return STAGE_LABELS.get(str(stage or "").lower(), "Processing")


class ProgressTracker:
    """Track and stream progress updates with file-based persistence."""

    def __init__(self, persistence_file: Optional[str] = None):
        """Initialize progress tracker with optional persistence.

        Args:
            persistence_file: Path to JSON file for persisting task state.
                             Defaults to 'logs/progress_state.json'
        """
        self.tasks = {}
        self.persistence_file = persistence_file or "logs/progress_state.json"
        self.completed_task_retention_minutes = (
            10  # Keep completed tasks for 10 minutes
        )
        # Lock to prevent concurrent writes to persistence file
        self._save_lock = threading.Lock()

        # Ensure logs directory exists
        persistence_path = Path(self.persistence_file)
        persistence_path.parent.mkdir(parents=True, exist_ok=True)

        # Load persisted state on initialization
        self._load_state()

    def _load_state(self):
        """Load task state from persistence file, merging with existing tasks."""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded_tasks = data.get("tasks", {})

                    # Filter out old completed tasks
                    now = _utc_now_naive()
                    tasks_to_remove = []
                    for task_id, task in loaded_tasks.items():
                        if canonical_status(task.get("status") or task.get("stage")) in [
                            "completed",
                            "failed",
                        ]:
                            # Check if task is too old
                            updates = task.get("updates", [])
                            if updates:
                                last_update_str = updates[-1].get("timestamp", "")
                            else:
                                last_update_str = ""

                            if last_update_str:
                                try:
                                    # Try parsing the timestamp
                                    clean_timestamp = last_update_str.replace(
                                        "Z", "+00:00"
                                    )
                                    last_update = datetime.fromisoformat(
                                        clean_timestamp
                                    )
                                    if isinstance(last_update, datetime):
                                        # Handle timezone-aware datetime
                                        if last_update.tzinfo:
                                            last_update = last_update.replace(
                                                tzinfo=None
                                            )
                                        age = now - last_update
                                        retention_delta = timedelta(
                                            minutes=self.completed_task_retention_minutes
                                        )
                                        if age > retention_delta:
                                            tasks_to_remove.append(task_id)
                                except (ValueError, TypeError):
                                    # If timestamp parsing fails, keep the task
                                    pass
                            # If no timestamp found, keep the task to be safe

                    # Remove old completed tasks from loaded_tasks and self.tasks
                    for task_id in tasks_to_remove:
                        if task_id in loaded_tasks:
                            del loaded_tasks[task_id]
                        # Also remove from self.tasks if it's already there
                        if task_id in self.tasks:
                            del self.tasks[task_id]

                    if tasks_to_remove:
                        print(
                            f"DEBUG: Filtered out {len(tasks_to_remove)} old completed task(s) during load"
                        )

                    # Merge loaded tasks with existing tasks (existing tasks take precedence)
                    merged_count = 0
                    for task_id, task in loaded_tasks.items():
                        if task_id not in self.tasks:
                            self.tasks[task_id] = task
                            merged_count += 1

                    if merged_count > 0:
                        print(
                            f"DEBUG: Loaded {merged_count} tasks from persistence file (merged with {len(self.tasks) - merged_count} existing)"
                        )
            else:
                if not self.tasks:
                    print(
                        "DEBUG: No persistence file found, starting with empty tracker"
                    )
        except Exception as e:
            print(f"DEBUG: WARNING - Failed to load persisted state: {e}")
            # Don't clear existing tasks on load failure

    def _save_state(self):
        """Save current task state to persistence file.

        Uses a lock to prevent concurrent writes from multiple threads.
        Each thread gets a unique temp file to avoid overwriting.
        """
        # Use lock to prevent concurrent writes
        with self._save_lock:
            try:
                # Prepare data for serialization (create a copy to avoid modification during save)
                data = {
                    "tasks": self.tasks,
                    "last_updated": _utc_now_naive().isoformat(),
                }

                # Create unique temp file for this thread to avoid race conditions
                # Use thread ID and timestamp to ensure uniqueness
                thread_id = threading.get_ident()
                timestamp = int(time.time() * 1000000)  # Microseconds for uniqueness
                temp_file = f"{self.persistence_file}.tmp.{thread_id}.{timestamp}"

                try:
                    # Write to unique temporary file first
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, default=str)

                    # Atomic rename (this is the critical section)
                    if os.path.exists(self.persistence_file):
                        os.replace(temp_file, self.persistence_file)
                    else:
                        os.rename(temp_file, self.persistence_file)
                finally:
                    # Clean up temp file if it still exists (shouldn't happen after successful rename)
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass

            except Exception as e:
                print(f"DEBUG: WARNING - Failed to save state to persistence: {e}")
                # Clean up any temp files that might exist
                temp_pattern = f"{self.persistence_file}.tmp.*"
                for temp_file in glob.glob(temp_pattern):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

    def _cleanup_old_tasks(self):
        """Remove completed tasks older than retention period."""
        now = _utc_now_naive()
        removed_count = 0

        for task_id, task in list(self.tasks.items()):
            if canonical_status(task.get("status") or task.get("stage")) in [
                "completed",
                "failed",
            ]:
                last_update_str = task.get("updates", [{}])[-1].get("timestamp", "")
                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(
                            last_update_str.replace("Z", "+00:00")
                        )
                        if isinstance(last_update, datetime):
                            if last_update.tzinfo:
                                last_update = last_update.replace(tzinfo=None)
                            age = now - last_update
                            if age > timedelta(
                                minutes=self.completed_task_retention_minutes
                            ):
                                del self.tasks[task_id]
                                removed_count += 1
                    except (ValueError, TypeError):
                        pass

        if removed_count > 0:
            print(f"DEBUG: Cleaned up {removed_count} old completed tasks")
            self._save_state()

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "progress": 0,
            "stage": "initialized",
            "message": "Task created",
            "updates": [],
            "created_at": _utc_now_naive().isoformat(),
        }
        self._save_state()
        return task_id

    def update(
        self,
        task_id: str,
        stage: str,
        progress: int,
        message: str,
        result: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ):
        """Update task progress.

        Args:
            task_id: Task ID
            stage: Current stage
            progress: Progress percentage (0-100)
            message: Progress message
            result: Optional final result data (processed_slots, output_file, etc.)
        """
        # Ensure task exists - create if it doesn't (handles server reloads)
        if task_id not in self.tasks:
            print(f"DEBUG: Creating missing task {task_id} in progress tracker")
            self.tasks[task_id] = {
                "progress": 0,
                "stage": "initialized",
                "message": "Task created",
                "updates": [],
            }

        normalized_stage = normalize_stage(stage)
        normalized_status = canonical_status(stage)
        update = {
            "stage": normalized_stage,
            "status": normalized_status,
            "progress": progress,
            "message": message,
            "stage_label": stage_label(normalized_stage),
            "timestamp": _utc_now_naive().isoformat(),
        }

        # Include result data if provided
        if result:
            update.update(result)
            self.tasks[task_id]["result"] = result
        if metadata:
            update.update(metadata)

        self.tasks[task_id].update(update)
        self.tasks[task_id]["updates"].append(update)
        print(
            f"DEBUG: Progress tracker updated: task_id={task_id}, stage={normalized_stage}, progress={progress}%, message={message[:50]}"
        )

        # Persist state on important updates (every 10% or on stage changes)
        if progress % 10 == 0 or normalized_status in ["completed", "failed"]:
            self._save_state()

    def get_updates(self, task_id: str) -> list:
        """Get all updates for a task."""
        task = self.get_task(task_id)
        if task:
            return task.get("updates", [])
        return []

    def complete(self, task_id: str):
        """Mark task as complete."""
        if task_id in self.tasks:
            self.update(task_id, "completed", 100, "Task completed successfully")
            print(f"DEBUG: Progress tracker marked task {task_id} as complete")
            # Force save on completion
            self._save_state()
        else:
            print(f"DEBUG: WARNING - Cannot complete task {task_id}, task not found")

    def error(self, task_id: str, error_message: str):
        """Mark task as failed."""
        if task_id in self.tasks:
            self.update(task_id, "failed", 0, f"Error: {error_message}")
            # Force save on error
            self._save_state()
        else:
            print(
                f"DEBUG: WARNING - Cannot mark task {task_id} as error, task not found"
            )

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task by ID, loading from persistence if not in memory."""
        if task_id in self.tasks:
            return self.tasks[task_id]

        # Try loading from persistence once (in case of server reload)
        # Only reload if we haven't loaded recently to avoid excessive I/O
        if (
            not hasattr(self, "_last_load_attempt")
            or (_utc_now_naive() - self._last_load_attempt).total_seconds() > 5
        ):
            self._load_state()
            self._last_load_attempt = _utc_now_naive()
            return self.tasks.get(task_id)

        return None


# Global progress tracker
progress_tracker = ProgressTracker()


async def stream_render_progress(
    task_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream progress updates via SSE.

    Args:
        task_id: Optional task ID to stream specific task progress

    Yields:
        SSE formatted progress updates
    """
    # If no task_id, create a demo stream
    if not task_id:
        stages = [
            ("validating", 10, "Validating JSON schema..."),
            ("repairing", 20, "Repairing JSON if needed..."),
            ("loading_template", 30, "Loading district template..."),
            ("rendering", 60, "Rendering DOCX file..."),
            ("saving", 90, "Saving file..."),
            ("complete", 100, "Rendering complete!"),
        ]

        for stage, progress, message in stages:
            data = {
                "stage": stage,
                "progress": progress,
                "message": message,
                "timestamp": _utc_now_naive().isoformat(),
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.5)
    else:
        # Stream updates for specific task
        last_update_count = 0
        max_wait = 30  # Maximum 30 seconds
        waited = 0

        while waited < max_wait:
            updates = progress_tracker.get_updates(task_id)

            # Send new updates
            for update in updates[last_update_count:]:
                yield f"data: {json.dumps(update)}\n\n"
                last_update_count += 1

            # Check if complete using get_task (handles persistence)
            task = progress_tracker.get_task(task_id)
            if task and canonical_status(task.get("status") or task.get("stage")) in [
                "completed",
                "failed",
            ]:
                break

            await asyncio.sleep(0.1)
            waited += 0.1

        # Send final completion message
        yield f"data: {json.dumps({'stage': 'done', 'progress': 100, 'message': 'Stream ended'})}\n\n"


async def simulate_render_progress() -> AsyncGenerator[str, None]:
    """
    Simulate rendering progress for testing.

    Yields:
        SSE formatted progress updates
    """
    async for update in stream_render_progress():
        yield update
