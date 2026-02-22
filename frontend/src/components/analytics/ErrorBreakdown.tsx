import { AlertCircle } from 'lucide-react';
import type { AnalyticsErrorStats } from '@lesson-api';

interface ErrorBreakdownProps {
  errorStats: AnalyticsErrorStats;
}

function formatFailureLabel(key: string): string {
  const normalized = key.replace(/_/g, ' ');
  if (normalized === 'json parse error') return 'JSON parse error';
  if (normalized === 'validation error') return 'Validation error';
  if (normalized === 'rate limit') return 'Rate limit';
  if (normalized === 'timeout') return 'Timeout';
  if (normalized === 'other') return 'Other';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
}

export function ErrorBreakdown({ errorStats }: ErrorBreakdownProps) {
  if (errorStats.failure <= 0) return null;

  return (
    <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1 flex items-center gap-2">
        <AlertCircle className="w-4 h-4" />
        Recent Failures Breakdown
      </h3>
      <p className="text-xs text-red-700 dark:text-red-400 mb-3">
        Count of failed operations in the selected period by failure type (not a current error).
      </p>
      <div className="flex flex-wrap gap-3">
        {Object.entries(errorStats.error_breakdown).map(([type, count]) => (
          <div
            key={type}
            className="bg-white dark:bg-black/20 px-3 py-1 rounded text-xs border border-red-100 dark:border-red-900/50"
          >
            <span className="font-medium">{formatFailureLabel(type)}:</span> {count}
          </div>
        ))}
      </div>
    </div>
  );
}
