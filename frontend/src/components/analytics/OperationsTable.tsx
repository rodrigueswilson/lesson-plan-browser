import type { AnalyticsSummary } from '@lesson-api';
import type { OperationChartEntry } from './useAnalytics';

interface OperationsTableProps {
  operationChartData: OperationChartEntry[];
  summary: AnalyticsSummary;
}

export function OperationsTable({ operationChartData, summary }: OperationsTableProps) {
  if (operationChartData.length === 0) return null;

  const totalTime = summary.total_duration_ms || 1;

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Detailed Operation Breakdown</h3>
          <p className="text-sm text-muted-foreground mt-1">
            All operations sorted by phase and time (slowest first within each phase)
          </p>
        </div>
        {operationChartData.length === 1 && (
          <div className="text-xs text-muted-foreground bg-muted px-3 py-1.5 rounded-md">
            Only one operation type tracked
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-3">Phase</th>
              <th className="text-left py-2 px-3">Operation</th>
              <th className="text-right py-2 px-3">Avg Time</th>
              <th className="text-right py-2 px-3">Count</th>
              <th className="text-right py-2 px-3">% of Total</th>
            </tr>
          </thead>
          <tbody>
            {operationChartData.map((op, index) => {
              const opTotalTime = op.avgTime * op.count;
              const percentage = (opTotalTime / totalTime * 100).toFixed(1);
              const isBottleneck = parseFloat(percentage) > 20;

              return (
                <tr
                  key={index}
                  className={`border-b hover:bg-muted/50 ${isBottleneck ? 'bg-orange-50 dark:bg-orange-950/20' : ''}`}
                >
                  <td className="py-2 px-3">
                    <span
                      className="inline-block px-2 py-1 rounded text-xs font-semibold"
                      style={{
                        backgroundColor: `${op.color}20`,
                        color: op.color
                      }}
                    >
                      {op.phase}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono text-xs">{op.fullName}</td>
                  <td className="py-2 px-3 text-right font-semibold">
                    {op.avgTime}ms
                    <span className="text-muted-foreground ml-1">
                      ({(op.avgTime / 1000).toFixed(2)}s)
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">{op.count}</td>
                  <td className="py-2 px-3 text-right">
                    {percentage}%
                    {isBottleneck && (
                      <span className="ml-1 text-orange-500" title="This operation accounts for more than 20% of total time">
                        (bottleneck)
                      </span>
                    )}
                    {parseFloat(percentage) === 100 && operationChartData.length === 1 && (
                      <span className="ml-1 text-xs text-muted-foreground" title="100% is normal when only one operation type exists">
                        (all operations)
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {['PARSE', 'PROCESS', 'RENDER'].map((phase) => {
          const phaseOps = operationChartData.filter(op => op.phase === phase);
          if (phaseOps.length === 0) return null;

          const phaseTotal = phaseOps.reduce((sum, op) => sum + (op.avgTime * op.count), 0);
          const phasePercentage = ((phaseTotal / totalTime) * 100).toFixed(1);
          const phaseColor = phaseOps[0]?.color || '#94a3b8';

          return (
            <div
              key={phase}
              className="border rounded-lg p-4"
              style={{ borderColor: phaseColor }}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className="font-semibold"
                  style={{ color: phaseColor }}
                >
                  {phase} PHASE
                </span>
                <span className="text-sm text-muted-foreground">
                  {phaseOps.length} ops
                </span>
              </div>
              <div className="text-2xl font-bold">
                {(phaseTotal / 1000).toFixed(2)}s
              </div>
              <div className="text-sm text-muted-foreground">
                {phasePercentage}% of total time
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
