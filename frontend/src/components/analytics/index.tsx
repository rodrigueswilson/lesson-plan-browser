import { BarChart3, RefreshCw } from 'lucide-react';
import { useAnalytics } from './useAnalytics';
import { AnalyticsHeader } from './AnalyticsHeader';
import { SummaryCards } from './SummaryCards';
import { ErrorBreakdown } from './ErrorBreakdown';
import { ModelChart } from './ModelChart';
import { WorkflowChart } from './WorkflowChart';
import { DailyChart } from './DailyChart';
import { OperationsTable } from './OperationsTable';
import { ParallelStats } from './ParallelStats';
import { SessionTable } from './SessionTable';

export function AnalyticsView() {
  const {
    timeRange,
    setTimeRange,
    summary,
    errorStats,
    loading,
    error,
    exporting,
    showSessions,
    setShowSessions,
    fetchAnalytics,
    handleExport,
    formatDuration,
    formatCost,
    formatNumber,
    modelChartData,
    operationChartData,
    dailyChartData,
    sessionData,
    parallelStats,
  } = useAnalytics();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-destructive/10 border border-destructive rounded-lg p-6">
        <p className="text-destructive font-medium">Error loading analytics</p>
        <p className="text-sm text-muted-foreground mt-1">{error}</p>
        <button
          onClick={fetchAnalytics}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AnalyticsHeader
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        showSessions={showSessions}
        setShowSessions={setShowSessions}
        onExport={handleExport}
        exporting={exporting}
      />

      <SummaryCards
        summary={summary}
        errorStats={errorStats}
        formatDuration={formatDuration}
        formatCost={formatCost}
        formatNumber={formatNumber}
      />

      {errorStats && <ErrorBreakdown errorStats={errorStats} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Model Distribution</h3>
          <ModelChart data={modelChartData} />
        </div>

        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Workflow Performance</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Average time per operation (identify bottlenecks)
          </p>
          <WorkflowChart data={operationChartData} />
        </div>

        <div className="bg-card border rounded-lg p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Daily Activity</h3>
          <DailyChart data={dailyChartData} />
        </div>
      </div>

      <OperationsTable operationChartData={operationChartData} summary={summary} />

      {parallelStats && (
        <ParallelStats
          parallelStats={parallelStats}
          formatDuration={formatDuration}
          formatNumber={formatNumber}
        />
      )}

      {showSessions && (
        <SessionTable
          sessionData={sessionData}
          formatCost={formatCost}
          formatNumber={formatNumber}
        />
      )}
    </div>
  );
}
