import { useState, useEffect, useMemo } from 'react';
import { analyticsApi, AnalyticsSummary, DailyAnalytics, AnalyticsErrorStats, AnalyticsOperationBreakdown, ParallelProcessingStats } from '@lesson-api';
import { useStore } from '@lesson-browser';

export type OperationChartEntry = {
  name: string;
  fullName: string;
  count: number;
  avgTime: number;
  phase: string;
  color: string;
  sortOrder: number;
};

export function useAnalytics() {
  const { currentUser } = useStore();
  const [timeRange, setTimeRange] = useState(30);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [dailyData, setDailyData] = useState<DailyAnalytics[]>([]);
  const [sessionData, setSessionData] = useState<any[]>([]);
  const [operationsData, setOperationsData] = useState<AnalyticsOperationBreakdown[]>([]);
  const [errorStats, setErrorStats] = useState<AnalyticsErrorStats | null>(null);
  const [parallelStats, setParallelStats] = useState<ParallelProcessingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [showSessions, setShowSessions] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange, currentUser?.id]);

  const fetchAnalytics = async () => {
    if (!currentUser?.id) {
      setLoading(false);
      setError('Please select a user to view analytics');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [summaryRes, dailyRes, sessionRes, opsRes, errorsRes, parallelRes] = await Promise.all([
        analyticsApi.getSummary(timeRange, currentUser.id),
        analyticsApi.getDaily(timeRange, currentUser.id),
        analyticsApi.getSessions(timeRange, currentUser.id).catch(() => ({ data: [] })),
        analyticsApi.getOperations(timeRange, currentUser.id).catch(() => ({ data: [] })),
        analyticsApi.getErrors(timeRange, currentUser.id).catch(() => ({ data: null })),
        analyticsApi.getParallel(timeRange, currentUser.id).catch(() => ({ data: null })),
      ]);

      setSummary(summaryRes.data);
      setDailyData(dailyRes.data);
      setSessionData(sessionRes.data || []);
      setOperationsData(opsRes.data || []);
      setErrorStats(errorsRes.data);
      setParallelStats(parallelRes.data);
    } catch (err: any) {
      console.error('Failed to fetch analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!currentUser?.id) {
      alert('Please select a user to export analytics');
      return;
    }

    setExporting(true);
    try {
      const csvData = await analyticsApi.exportCsv(timeRange, currentUser.id);
      const blob = new Blob([csvData as any], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Failed to export analytics:', err);
      alert('Failed to export analytics: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  const formatDuration = (ms: number | null | undefined) => {
    if (!ms) return '0s';
    const seconds = Math.round(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatCost = (usd: number | null | undefined) => {
    return `$${(usd || 0).toFixed(4)}`;
  };

  const formatNumber = (num: number | null | undefined) => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const modelChartData = useMemo(() => {
    if (!summary?.model_distribution) return [];
    return summary.model_distribution.map((item) => ({
      name: item.llm_model || 'Unknown',
      value: item.count,
      cost: item.cost,
    }));
  }, [summary]);

  const operationChartData = useMemo((): OperationChartEntry[] => {
    const source = operationsData.length > 0 ? operationsData : summary?.operation_breakdown || [];
    return source
      .map((item) => {
        const opType = item.operation_type;
        let phase = 'OTHER';
        let color = '#94a3b8';
        let sortOrder = 999;

        if (opType.startsWith('parse_')) {
          phase = 'PARSE';
          color = '#3b82f6';
          sortOrder = 1;
        } else if (opType.startsWith('llm_') || opType.includes('transform') || opType.includes('process')) {
          phase = 'PROCESS';
          color = '#f59e0b';
          sortOrder = 2;
        } else if (opType.startsWith('render_')) {
          phase = 'RENDER';
          color = '#10b981';
          sortOrder = 3;
        }

        return {
          name: item.operation_type.replace(/_/g, ' '),
          fullName: item.operation_type,
          count: item.count,
          avgTime: Math.round(item.avg_duration_ms),
          phase,
          color,
          sortOrder,
        };
      })
      .sort((a, b) => {
        if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
        return b.avgTime - a.avgTime;
      });
  }, [operationsData, summary]);

  const dailyChartData = useMemo(() => {
    return dailyData
      .map((item) => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        plans: item.plans ?? 0,
        cost: item.cost_usd ?? 0,
        operations: item.operations ?? 0,
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [dailyData]);

  return {
    timeRange,
    setTimeRange,
    summary,
    dailyData,
    sessionData,
    operationsData,
    errorStats,
    parallelStats,
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
  };
}
