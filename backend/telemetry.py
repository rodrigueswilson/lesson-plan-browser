"""
Telemetry and structured logging for the JSON pipeline.
Tracks validation, rendering, token usage, and errors.
"""

import structlog
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from .config import settings


# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" 
        else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class PipelineMetrics:
    """Metrics collector for pipeline performance."""
    
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
    
    def record(self, metric: Dict[str, Any]):
        """Record a metric."""
        self.metrics.append(metric)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.metrics:
            return {}
        
        total = len(self.metrics)
        successful = sum(1 for m in self.metrics if m.get('success', False))
        
        token_counts = [m['token_count'] for m in self.metrics if 'token_count' in m]
        durations = [m['duration_ms'] for m in self.metrics if 'duration_ms' in m]
        retries = [m['retry_count'] for m in self.metrics if 'retry_count' in m]
        
        return {
            'total_requests': total,
            'successful': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'avg_token_count': sum(token_counts) / len(token_counts) if token_counts else 0,
            'median_duration_ms': sorted(durations)[len(durations) // 2] if durations else 0,
            'avg_retry_count': sum(retries) / len(retries) if retries else 0,
        }


# Global metrics collector
metrics = PipelineMetrics()


def log_json_pipeline_event(
    event_type: str,
    success: bool,
    duration_ms: float,
    token_count: Optional[int] = None,
    validation_errors: Optional[List[str]] = None,
    retry_count: int = 0,
    lesson_id: Optional[str] = None,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """
    Log a JSON pipeline event with structured data.
    
    Args:
        event_type: Type of event (generation, validation, rendering)
        success: Whether the operation succeeded
        duration_ms: Duration in milliseconds
        token_count: Number of tokens used
        validation_errors: List of validation error messages
        retry_count: Number of retry attempts
        lesson_id: Lesson plan identifier
        user_id: User identifier
        extra: Additional context
    """
    if not settings.ENABLE_TELEMETRY:
        return
    
    event_data = {
        'event_type': event_type,
        'success': success,
        'duration_ms': duration_ms,
        'retry_count': retry_count,
        'timestamp': datetime.utcnow().isoformat(),
        'pipeline_mode': 'json' if settings.ENABLE_JSON_OUTPUT else 'markdown',
    }
    
    if token_count is not None:
        event_data['token_count'] = token_count
    
    if validation_errors:
        event_data['validation_errors'] = validation_errors
        event_data['validation_error_count'] = len(validation_errors)
    
    if lesson_id:
        event_data['lesson_id'] = lesson_id
    
    if user_id:
        event_data['user_id'] = user_id
    
    if extra:
        event_data.update(extra)
    
    logger.info("json_pipeline_event", **event_data)
    
    # Record metric
    metrics.record(event_data)


def log_token_footprint_comparison(
    markdown_tokens: int,
    json_tokens: int,
    lesson_id: str,
    user_id: Optional[str] = None
):
    """
    Track token usage comparison between markdown and JSON.
    
    Args:
        markdown_tokens: Token count for markdown output
        json_tokens: Token count for JSON output
        lesson_id: Lesson plan identifier
        user_id: User identifier
    """
    if not settings.ENABLE_TELEMETRY:
        return
    
    delta = json_tokens - markdown_tokens
    delta_pct = (delta / markdown_tokens) * 100 if markdown_tokens > 0 else 0
    
    event_data = {
        'lesson_id': lesson_id,
        'markdown_tokens': markdown_tokens,
        'json_tokens': json_tokens,
        'delta': delta,
        'delta_pct': delta_pct,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if user_id:
        event_data['user_id'] = user_id
    
    logger.info("token_footprint_comparison", **event_data)
    
    # Alert if increase >20%
    if delta_pct > settings.MAX_TOKEN_INCREASE_PCT:
        logger.warning(
            "token_footprint_alert",
            lesson_id=lesson_id,
            delta_pct=delta_pct,
            threshold=settings.MAX_TOKEN_INCREASE_PCT,
            message=f"JSON token usage increased {delta_pct:.1f}% vs markdown"
        )


def log_validation_error(
    lesson_id: str,
    errors: List[str],
    raw_json: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Log validation errors for debugging.
    
    Args:
        lesson_id: Lesson plan identifier
        errors: List of validation error messages
        raw_json: Raw JSON response (truncated for logging)
        user_id: User identifier
    """
    if not settings.ENABLE_TELEMETRY:
        return
    
    event_data = {
        'lesson_id': lesson_id,
        'validation_errors': errors,
        'error_count': len(errors),
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if raw_json:
        # Truncate for logging
        event_data['raw_json_preview'] = raw_json[:500] + '...' if len(raw_json) > 500 else raw_json
    
    if user_id:
        event_data['user_id'] = user_id
    
    logger.error("validation_error", **event_data)


def log_render_success(
    lesson_id: str,
    duration_ms: float,
    output_format: str,
    output_size_bytes: int,
    user_id: Optional[str] = None
):
    """
    Log successful rendering.
    
    Args:
        lesson_id: Lesson plan identifier
        duration_ms: Rendering duration in milliseconds
        output_format: Output format (markdown, docx)
        output_size_bytes: Size of rendered output
        user_id: User identifier
    """
    if not settings.ENABLE_TELEMETRY:
        return
    
    event_data = {
        'lesson_id': lesson_id,
        'duration_ms': duration_ms,
        'output_format': output_format,
        'output_size_bytes': output_size_bytes,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if user_id:
        event_data['user_id'] = user_id
    
    logger.info("render_success", **event_data)


def log_json_repair_attempt(
    lesson_id: str,
    original_error: str,
    repair_success: bool,
    user_id: Optional[str] = None
):
    """
    Log JSON repair attempt.
    
    Args:
        lesson_id: Lesson plan identifier
        original_error: Original JSON parsing error
        repair_success: Whether repair succeeded
        user_id: User identifier
    """
    if not settings.ENABLE_TELEMETRY:
        return
    
    event_data = {
        'lesson_id': lesson_id,
        'original_error': original_error,
        'repair_success': repair_success,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if user_id:
        event_data['user_id'] = user_id
    
    if repair_success:
        logger.info("json_repair_success", **event_data)
    else:
        logger.warning("json_repair_failed", **event_data)


@contextmanager
def track_duration(event_type: str, lesson_id: Optional[str] = None):
    """
    Context manager to track operation duration.
    
    Usage:
        with track_duration("validation", lesson_id="123"):
            validate_json(data)
    
    Args:
        event_type: Type of operation
        lesson_id: Lesson plan identifier
    """
    start_time = time.time()
    success = False
    error = None
    
    try:
        yield
        success = True
    except Exception as e:
        error = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        if settings.ENABLE_TELEMETRY:
            event_data = {
                'event_type': event_type,
                'success': success,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            if lesson_id:
                event_data['lesson_id'] = lesson_id
            
            if error:
                event_data['error'] = error
            
            logger.info("operation_duration", **event_data)


def export_metrics_to_csv(output_path: Path):
    """
    Export collected metrics to CSV for analysis.
    
    Args:
        output_path: Path to output CSV file
    """
    import csv
    
    if not metrics.metrics:
        logger.warning("no_metrics_to_export")
        return
    
    # Get all unique keys
    all_keys = set()
    for metric in metrics.metrics:
        all_keys.update(metric.keys())
    
    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(metrics.metrics)
    
    logger.info("metrics_exported", path=str(output_path), count=len(metrics.metrics))


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of collected metrics.
    
    Returns:
        Dictionary with summary statistics
    """
    return metrics.get_summary()
