import { Download, RefreshCw } from 'lucide-react';

interface AnalyticsHeaderProps {
  timeRange: number;
  setTimeRange: (days: number) => void;
  showSessions: boolean;
  setShowSessions: (show: boolean) => void;
  onExport: () => void;
  exporting: boolean;
}

export function AnalyticsHeader({
  timeRange,
  setTimeRange,
  showSessions,
  setShowSessions,
  onExport,
  exporting,
}: AnalyticsHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Performance metrics and usage statistics
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex gap-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${timeRange === days
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
            >
              {days}d
            </button>
          ))}
        </div>

        <button
          onClick={() => setShowSessions(!showSessions)}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${showSessions
            ? 'bg-primary text-primary-foreground'
            : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
        >
          {showSessions ? 'Hide' : 'Show'} Sessions
        </button>

        <button
          onClick={onExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {exporting ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          Export CSV
        </button>
      </div>
    </div>
  );
}
