"""
Lesson Plan Processing Pipeline
Integrates all components: validation, rendering, retry logic, token tracking.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Callable, Tuple

from .render_lesson_plan import LessonPlanRenderer
from .retry_logic import generate_with_retry, RetryExhausted
from .token_tracker import TokenTracker, get_tracker
from backend.telemetry import (
    log_json_pipeline_event,
    log_token_footprint_comparison,
    log_validation_error,
    log_render_success,
    log_json_repair_attempt,
    track_duration
)
from backend.config import settings


class LessonPlanPipeline:
    """
    Complete pipeline for processing lesson plans.
    
    Handles: LLM generation → Validation → Retry → Rendering
    """
    
    def __init__(
        self,
        schema_path: Path,
        template_dir: Path,
        token_tracker: Optional[TokenTracker] = None
    ):
        """
        Initialize pipeline.
        
        Args:
            schema_path: Path to JSON schema
            template_dir: Path to Jinja2 templates
            token_tracker: Optional token tracker (uses global if None)
        """
        self.renderer = LessonPlanRenderer(schema_path, template_dir)
        self.token_tracker = token_tracker or get_tracker()
        self.schema_path = schema_path
        self.template_dir = template_dir
    
    def process(
        self,
        llm_generate: Callable[[str], str],
        prompt: str,
        lesson_id: str,
        output_path: Optional[Path] = None,
        max_retries: int = None,
        enable_repair: bool = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process a lesson plan through the complete pipeline.
        
        Args:
            llm_generate: Function to call LLM
            prompt: Prompt to send to LLM
            lesson_id: Lesson identifier
            output_path: Optional path to save rendered output
            max_retries: Max retry attempts (uses config default if None)
            enable_repair: Enable JSON repair (uses config default if None)
            
        Returns:
            Tuple of (success, rendered_output, error_message)
        """
        if max_retries is None:
            max_retries = settings.MAX_VALIDATION_RETRIES
        
        if enable_repair is None:
            enable_repair = settings.ENABLE_JSON_REPAIR
        
        start_time = time.time()
        
        # Telemetry callback for retry logic
        def telemetry_callback(**kwargs):
            attempt = kwargs.get('attempt', 1)
            success = kwargs.get('success', False)
            duration_ms = kwargs.get('duration_ms', 0)
            
            # Log attempt
            log_json_pipeline_event(
                event_type="llm_generation",
                success=success,
                duration_ms=duration_ms,
                retry_count=attempt - 1,
                lesson_id=lesson_id,
                extra=kwargs
            )
            
            # Log repair attempts
            if kwargs.get('repair_attempted'):
                log_json_repair_attempt(
                    lesson_id=lesson_id,
                    original_error=kwargs.get('error', 'Unknown'),
                    repair_success=success
                )
        
        # Validator function
        def validator(data: Dict) -> Tuple[bool, list]:
            with track_duration("validation", lesson_id=lesson_id):
                return self.renderer.validate(data)
        
        # Generate with retry
        try:
            with track_duration("generation_with_retry", lesson_id=lesson_id):
                data = generate_with_retry(
                    llm_generate=llm_generate,
                    initial_prompt=prompt,
                    validator=validator,
                    max_retries=max_retries,
                    enable_repair=enable_repair,
                    telemetry_callback=telemetry_callback
                )
        
        except RetryExhausted as e:
            total_duration = (time.time() - start_time) * 1000
            
            log_json_pipeline_event(
                event_type="pipeline_failed",
                success=False,
                duration_ms=total_duration,
                lesson_id=lesson_id,
                extra={'error': str(e)}
            )
            
            return False, None, str(e)
        
        except Exception as e:
            total_duration = (time.time() - start_time) * 1000
            
            log_json_pipeline_event(
                event_type="pipeline_error",
                success=False,
                duration_ms=total_duration,
                lesson_id=lesson_id,
                extra={'error': str(e)}
            )
            
            return False, None, f"Unexpected error: {str(e)}"
        
        # Render
        try:
            with track_duration("rendering", lesson_id=lesson_id):
                rendered = self.renderer.render(data, output_path)
            
            render_duration = (time.time() - start_time) * 1000
            
            log_render_success(
                lesson_id=lesson_id,
                duration_ms=render_duration,
                output_format="markdown",
                output_size_bytes=len(rendered)
            )
            
            total_duration = (time.time() - start_time) * 1000
            
            log_json_pipeline_event(
                event_type="pipeline_success",
                success=True,
                duration_ms=total_duration,
                lesson_id=lesson_id
            )
            
            return True, rendered, None
            
        except Exception as e:
            total_duration = (time.time() - start_time) * 1000
            
            log_json_pipeline_event(
                event_type="rendering_failed",
                success=False,
                duration_ms=total_duration,
                lesson_id=lesson_id,
                extra={'error': str(e)}
            )
            
            return False, None, f"Rendering failed: {str(e)}"
    
    def process_from_json(
        self,
        json_data: Dict,
        lesson_id: str,
        output_path: Optional[Path] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process pre-generated JSON (skip LLM generation).
        
        Args:
            json_data: Lesson plan JSON data
            lesson_id: Lesson identifier
            output_path: Optional path to save rendered output
            
        Returns:
            Tuple of (success, rendered_output, error_message)
        """
        start_time = time.time()
        
        # Validate
        with track_duration("validation", lesson_id=lesson_id):
            valid, errors = self.renderer.validate(json_data)
        
        if not valid:
            log_validation_error(
                lesson_id=lesson_id,
                errors=errors
            )
            return False, None, f"Validation failed: {errors}"
        
        # Render
        try:
            with track_duration("rendering", lesson_id=lesson_id):
                rendered = self.renderer.render(json_data, output_path)
            
            duration_ms = (time.time() - start_time) * 1000
            
            log_render_success(
                lesson_id=lesson_id,
                duration_ms=duration_ms,
                output_format="markdown",
                output_size_bytes=len(rendered)
            )
            
            return True, rendered, None
            
        except Exception as e:
            return False, None, f"Rendering failed: {str(e)}"


def create_pipeline(
    schema_path: Optional[Path] = None,
    template_dir: Optional[Path] = None
) -> LessonPlanPipeline:
    """
    Create a lesson plan pipeline with default paths.
    
    Args:
        schema_path: Optional custom schema path
        template_dir: Optional custom template directory
        
    Returns:
        LessonPlanPipeline instance
    """
    if schema_path is None:
        schema_path = Path(settings.SCHEMA_PATH)
    
    if template_dir is None:
        template_dir = Path(settings.TEMPLATE_DIR)
    
    return LessonPlanPipeline(schema_path, template_dir)
