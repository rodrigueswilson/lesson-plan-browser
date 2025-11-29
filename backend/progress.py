"""
SSE Progress Streaming for Bilingual Lesson Plan Builder.

Provides real-time progress updates during lesson plan rendering.
"""

import asyncio
import json
from typing import AsyncGenerator, Optional
from datetime import datetime
import uuid


class ProgressTracker:
    """Track and stream progress updates."""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "progress": 0,
            "stage": "initialized",
            "message": "Task created",
            "updates": []
        }
        return task_id
    
    def update(self, task_id: str, stage: str, progress: int, message: str, result: Optional[dict] = None):
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
                "updates": []
            }
        
        update = {
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Include result data if provided
        if result:
            update.update(result)
            self.tasks[task_id]["result"] = result
        
        self.tasks[task_id].update(update)
        self.tasks[task_id]["updates"].append(update)
        print(f"DEBUG: Progress tracker updated: task_id={task_id}, stage={stage}, progress={progress}%, message={message[:50]}")
    
    def get_updates(self, task_id: str) -> list:
        """Get all updates for a task."""
        if task_id in self.tasks:
            return self.tasks[task_id]["updates"]
        return []
    
    def complete(self, task_id: str):
        """Mark task as complete."""
        if task_id in self.tasks:
            self.update(task_id, "complete", 100, "Task completed successfully")
            print(f"DEBUG: Progress tracker marked task {task_id} as complete")
        else:
            print(f"DEBUG: WARNING - Cannot complete task {task_id}, task not found")
    
    def error(self, task_id: str, error_message: str):
        """Mark task as failed."""
        if task_id in self.tasks:
            self.update(task_id, "error", 0, f"Error: {error_message}")
        else:
            print(f"DEBUG: WARNING - Cannot mark task {task_id} as error, task not found")


# Global progress tracker
progress_tracker = ProgressTracker()


async def stream_render_progress(task_id: Optional[str] = None) -> AsyncGenerator[str, None]:
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
            ("complete", 100, "Rendering complete!")
        ]
        
        for stage, progress, message in stages:
            data = {
                "stage": stage,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
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
            
            # Check if complete
            if task_id in progress_tracker.tasks:
                task = progress_tracker.tasks[task_id]
                if task["stage"] in ["complete", "error"]:
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
