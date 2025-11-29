"""
Token Usage Tracker
Monitors and reports token usage for LLM calls.
"""

import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    duration_ms: float
    lesson_id: Optional[str] = None
    attempt: int = 1
    success: bool = True


@dataclass
class TokenStats:
    """Aggregate token statistics."""
    total_calls: int = 0
    total_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_duration_ms: float = 0.0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_tokens_per_call: float = 0.0
    avg_duration_ms: float = 0.0
    
    def update(self, usage: TokenUsage):
        """Update stats with new usage data."""
        self.total_calls += 1
        self.total_tokens += usage.total_tokens
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_duration_ms += usage.duration_ms
        
        if usage.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        # Update averages
        if self.total_calls > 0:
            self.avg_tokens_per_call = self.total_tokens / self.total_calls
            self.avg_duration_ms = self.total_duration_ms / self.total_calls


class TokenTracker:
    """Tracks token usage across LLM calls."""
    
    def __init__(self, alert_threshold_pct: int = 20):
        """
        Initialize token tracker.
        
        Args:
            alert_threshold_pct: Alert if token usage increases by this percentage
        """
        self.usage_history: List[TokenUsage] = []
        self.stats = TokenStats()
        self.alert_threshold_pct = alert_threshold_pct
        self.baseline_tokens: Optional[int] = None
    
    def record(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        duration_ms: float,
        lesson_id: Optional[str] = None,
        attempt: int = 1,
        success: bool = True
    ) -> TokenUsage:
        """
        Record token usage for an LLM call.
        
        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion
            model: Model name
            duration_ms: Duration in milliseconds
            lesson_id: Optional lesson identifier
            attempt: Attempt number (for retries)
            success: Whether the call succeeded
            
        Returns:
            TokenUsage object
        """
        usage = TokenUsage(
            timestamp=datetime.utcnow(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            duration_ms=duration_ms,
            lesson_id=lesson_id,
            attempt=attempt,
            success=success
        )
        
        self.usage_history.append(usage)
        self.stats.update(usage)
        
        # Check for alerts
        self._check_alerts(usage)
        
        return usage
    
    def set_baseline(self, tokens: int):
        """
        Set baseline token usage for comparison.
        
        Args:
            tokens: Baseline token count (e.g., from markdown mode)
        """
        self.baseline_tokens = tokens
    
    def _check_alerts(self, usage: TokenUsage):
        """Check if usage exceeds alert thresholds."""
        if self.baseline_tokens is None:
            return
        
        increase_pct = ((usage.total_tokens - self.baseline_tokens) / self.baseline_tokens) * 100
        
        if increase_pct > self.alert_threshold_pct:
            print(f"⚠️  Token usage alert: {increase_pct:.1f}% increase over baseline")
            print(f"   Baseline: {self.baseline_tokens}, Current: {usage.total_tokens}")
    
    def get_stats(self) -> TokenStats:
        """Get aggregate statistics."""
        return self.stats
    
    def get_usage_by_lesson(self, lesson_id: str) -> List[TokenUsage]:
        """Get all usage records for a specific lesson."""
        return [u for u in self.usage_history if u.lesson_id == lesson_id]
    
    def get_recent_usage(self, count: int = 10) -> List[TokenUsage]:
        """Get most recent usage records."""
        return self.usage_history[-count:]
    
    def compare_to_baseline(self) -> Optional[Dict]:
        """
        Compare current average usage to baseline.
        
        Returns:
            Dictionary with comparison metrics or None if no baseline
        """
        if self.baseline_tokens is None or self.stats.total_calls == 0:
            return None
        
        avg_tokens = self.stats.avg_tokens_per_call
        delta = avg_tokens - self.baseline_tokens
        delta_pct = (delta / self.baseline_tokens) * 100
        
        return {
            'baseline_tokens': self.baseline_tokens,
            'avg_tokens': avg_tokens,
            'delta': delta,
            'delta_pct': delta_pct,
            'total_calls': self.stats.total_calls,
            'alert_triggered': delta_pct > self.alert_threshold_pct
        }
    
    def export_to_dict(self) -> Dict:
        """Export tracker data to dictionary."""
        return {
            'stats': {
                'total_calls': self.stats.total_calls,
                'total_tokens': self.stats.total_tokens,
                'total_prompt_tokens': self.stats.total_prompt_tokens,
                'total_completion_tokens': self.stats.total_completion_tokens,
                'avg_tokens_per_call': self.stats.avg_tokens_per_call,
                'avg_duration_ms': self.stats.avg_duration_ms,
                'successful_calls': self.stats.successful_calls,
                'failed_calls': self.stats.failed_calls
            },
            'baseline_tokens': self.baseline_tokens,
            'alert_threshold_pct': self.alert_threshold_pct,
            'usage_history_count': len(self.usage_history)
        }
    
    def print_summary(self):
        """Print a summary of token usage."""
        print("=" * 60)
        print("Token Usage Summary")
        print("=" * 60)
        print(f"Total Calls:        {self.stats.total_calls}")
        print(f"Successful:         {self.stats.successful_calls}")
        print(f"Failed:             {self.stats.failed_calls}")
        print(f"Total Tokens:       {self.stats.total_tokens:,}")
        print(f"  Prompt:           {self.stats.total_prompt_tokens:,}")
        print(f"  Completion:       {self.stats.total_completion_tokens:,}")
        print(f"Avg Tokens/Call:    {self.stats.avg_tokens_per_call:.0f}")
        print(f"Avg Duration:       {self.stats.avg_duration_ms:.0f}ms")
        
        if self.baseline_tokens:
            comparison = self.compare_to_baseline()
            if comparison:
                print(f"\nBaseline Comparison:")
                print(f"  Baseline:         {comparison['baseline_tokens']:,}")
                print(f"  Current Avg:      {comparison['avg_tokens']:.0f}")
                print(f"  Delta:            {comparison['delta']:+.0f} ({comparison['delta_pct']:+.1f}%)")
                if comparison['alert_triggered']:
                    print(f"  ⚠️  Alert: Exceeds {self.alert_threshold_pct}% threshold")
        
        print("=" * 60)


# Global tracker instance
_global_tracker: Optional[TokenTracker] = None


def get_tracker() -> TokenTracker:
    """Get or create global token tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenTracker()
    return _global_tracker


def reset_tracker():
    """Reset global token tracker."""
    global _global_tracker
    _global_tracker = TokenTracker()
