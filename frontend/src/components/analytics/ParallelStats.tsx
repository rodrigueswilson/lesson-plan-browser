import type { ParallelProcessingStats } from '@lesson-api';

interface ParallelStatsProps {
  parallelStats: ParallelProcessingStats;
  formatDuration: (ms: number | null | undefined) => string;
  formatNumber: (num: number | null | undefined) => string;
}

export function ParallelStats({ parallelStats, formatDuration, formatNumber }: ParallelStatsProps) {
  if (!parallelStats || parallelStats.total_operations <= 0) return null;

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Parallel Processing Performance</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Metrics for parallel vs sequential processing
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Parallel Operations</p>
          <p className="text-2xl font-bold">{parallelStats.parallel_operations}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {parallelStats.parallel_percentage.toFixed(1)}% of total
          </p>
        </div>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Time Savings</p>
          <p className="text-2xl font-bold text-green-600">
            {formatDuration(parallelStats.time_savings_ms)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {parallelStats.time_savings_percent.toFixed(1)}% faster
          </p>
        </div>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Parallel Time</p>
          <p className="text-2xl font-bold">{formatDuration(parallelStats.avg_parallel_duration_ms)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            vs {formatDuration(parallelStats.avg_sequential_duration_ms)} sequential
          </p>
        </div>

        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Rate Limit Errors</p>
          <p className="text-2xl font-bold">
            {parallelStats.total_rate_limit_errors}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {parallelStats.avg_concurrency_level > 0
              ? `Avg concurrency: ${parallelStats.avg_concurrency_level.toFixed(1)}`
              : 'No concurrency data'}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-3">Metric</th>
              <th className="text-right py-2 px-3">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b">
              <td className="py-2 px-3">Total Operations</td>
              <td className="py-2 px-3 text-right font-medium">{parallelStats.total_operations}</td>
            </tr>
            <tr className="border-b">
              <td className="py-2 px-3">Sequential Operations</td>
              <td className="py-2 px-3 text-right">{parallelStats.sequential_operations}</td>
            </tr>
            <tr className="border-b">
              <td className="py-2 px-3">Avg Parallel Slot Count</td>
              <td className="py-2 px-3 text-right">
                {parallelStats.avg_parallel_slot_count > 0
                  ? parallelStats.avg_parallel_slot_count.toFixed(1)
                  : 'N/A'}
              </td>
            </tr>
            <tr className="border-b">
              <td className="py-2 px-3">Avg Sequential Time (Est.)</td>
              <td className="py-2 px-3 text-right">
                {formatDuration(parallelStats.avg_sequential_time_ms)}
              </td>
            </tr>
            {parallelStats.avg_tpm_usage > 0 && (
              <tr className="border-b">
                <td className="py-2 px-3">Avg TPM Usage</td>
                <td className="py-2 px-3 text-right">
                  {formatNumber(parallelStats.avg_tpm_usage)} tokens/min
                </td>
              </tr>
            )}
            {parallelStats.avg_rpm_usage > 0 && (
              <tr className="border-b">
                <td className="py-2 px-3">Avg RPM Usage</td>
                <td className="py-2 px-3 text-right">
                  {formatNumber(parallelStats.avg_rpm_usage)} requests/min
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
