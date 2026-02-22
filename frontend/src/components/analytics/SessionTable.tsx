import { BarChart3 } from 'lucide-react';

interface SessionRow {
  plan_id?: string;
  session_start?: string;
  duration_ms?: number;
  operations?: number;
  tokens_total?: number;
  cost_usd?: number;
  models_used?: string[];
  week_of?: string;
}

interface SessionTableProps {
  sessionData: SessionRow[];
  formatCost: (usd: number | null | undefined) => string;
  formatNumber: (num: number | null | undefined) => string;
}

export function SessionTable({ sessionData, formatCost, formatNumber }: SessionTableProps) {
  if (sessionData.length === 0) {
    return (
      <div className="bg-card border rounded-lg p-6 text-center">
        <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
        <p className="text-muted-foreground">No session data available</p>
        <p className="text-xs text-muted-foreground mt-2">
          Generate some lesson plans to see session breakdown
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Session Breakdown</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Each session represents one plan generation (most recent first)
          </p>
        </div>
        <div className="text-sm text-muted-foreground">
          {sessionData.length} session{sessionData.length !== 1 ? 's' : ''}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-3">Week</th>
              <th className="text-left py-2 px-3">Session Start</th>
              <th className="text-right py-2 px-3">Duration</th>
              <th className="text-right py-2 px-3">Operations</th>
              <th className="text-right py-2 px-3">Tokens</th>
              <th className="text-right py-2 px-3">Cost</th>
              <th className="text-left py-2 px-3">Models</th>
            </tr>
          </thead>
          <tbody>
            {sessionData.map((session, index) => {
              const sessionStart = session.session_start ? new Date(session.session_start) : null;
              const duration = session.duration_ms ? session.duration_ms / 1000 : 0;

              return (
                <tr
                  key={session.plan_id || index}
                  className={`border-b hover:bg-muted/50 ${index === 0 ? 'bg-primary/5' : ''}`}
                >
                  <td className="py-2 px-3 font-medium">
                    {session.week_of || 'N/A'}
                    {index === 0 && (
                      <span className="ml-2 text-xs text-primary">(Latest)</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-muted-foreground">
                    {sessionStart
                      ? sessionStart.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })
                      : 'N/A'}
                  </td>
                  <td className="py-2 px-3 text-right">
                    {duration > 0
                      ? `${(duration / 60).toFixed(1)}m`
                      : '0s'}
                  </td>
                  <td className="py-2 px-3 text-right">{session.operations || 0}</td>
                  <td className="py-2 px-3 text-right">
                    {formatNumber(session.tokens_total || 0)}
                  </td>
                  <td className="py-2 px-3 text-right font-semibold">
                    {formatCost(session.cost_usd || 0)}
                  </td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1">
                      {(session.models_used || []).slice(0, 2).map((model: string, idx: number) => (
                        <span
                          key={idx}
                          className="text-xs bg-muted px-2 py-0.5 rounded"
                        >
                          {model}
                        </span>
                      ))}
                      {(session.models_used || []).length > 2 && (
                        <span className="text-xs text-muted-foreground">
                          +{(session.models_used || []).length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
