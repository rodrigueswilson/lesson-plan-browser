import { BarChart3, TrendingUp, Clock, DollarSign, AlertCircle, CheckCircle } from 'lucide-react';
import type { AnalyticsSummary } from '@lesson-api';
import type { AnalyticsErrorStats } from '@lesson-api';

interface SummaryCardsProps {
  summary: AnalyticsSummary;
  errorStats: AnalyticsErrorStats | null;
  formatDuration: (ms: number | null | undefined) => string;
  formatCost: (usd: number | null | undefined) => string;
  formatNumber: (num: number | null | undefined) => string;
}

export function SummaryCards({
  summary,
  errorStats,
  formatDuration,
  formatCost,
  formatNumber,
}: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-muted-foreground">Success Rate</p>
          {errorStats && errorStats.success_rate >= 90 ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-500" />
          )}
        </div>
        <p className="text-3xl font-bold">
          {errorStats ? `${errorStats.success_rate.toFixed(1)}%` : 'N/A'}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {errorStats ? `${errorStats.success} ok / ${errorStats.failure} fail` : 'No data'}
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-muted-foreground">Total Plans</p>
          <BarChart3 className="w-5 h-5 text-primary" />
        </div>
        <p className="text-3xl font-bold">{summary.total_plans || 0}</p>
        <p className="text-xs text-muted-foreground mt-1">
          {summary.total_operations || 0} operations
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-muted-foreground">Avg Time Per Plan</p>
          <Clock className="w-5 h-5 text-blue-500" />
        </div>
        <p className="text-3xl font-bold">
          {formatDuration(summary.avg_duration_per_plan_ms || 0)}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          total workflow time
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-muted-foreground">Total Tokens</p>
          <TrendingUp className="w-5 h-5 text-green-500" />
        </div>
        <p className="text-3xl font-bold">
          {formatNumber(summary.total_tokens || 0)}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {formatNumber(summary.total_tokens_input || 0)} in / {formatNumber(summary.total_tokens_output || 0)} out
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-muted-foreground">Total Cost</p>
          <DollarSign className="w-5 h-5 text-orange-500" />
        </div>
        <p className="text-3xl font-bold">
          {formatCost(summary.total_cost_usd || 0)}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {formatCost(summary.avg_cost_usd || 0)} avg
        </p>
      </div>
    </div>
  );
}
