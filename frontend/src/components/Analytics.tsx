import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, DollarSign, Download, RefreshCw } from 'lucide-react';
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { analyticsApi, AnalyticsSummary, DailyAnalytics } from '@lesson-api';
import { useStore } from '@lesson-browser';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function Analytics() {
  const { currentUser } = useStore();
  const [timeRange, setTimeRange] = useState(30);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [dailyData, setDailyData] = useState<DailyAnalytics[]>([]);
  const [sessionData, setSessionData] = useState<any[]>([]);
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
      // Filter by current user
      const [summaryRes, dailyRes, sessionRes] = await Promise.all([
        analyticsApi.getSummary(timeRange, currentUser.id),
        analyticsApi.getDaily(timeRange, currentUser.id),
        analyticsApi.getSessions(timeRange, currentUser.id).catch(() => ({ data: [] })),
      ]);
      
      setSummary(summaryRes.data);
      setDailyData(dailyRes.data);
      setSessionData(sessionRes.data || []);
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
      // Export analytics for current user
      const csvData = await analyticsApi.exportCsv(timeRange, currentUser.id);
      
      // Create blob and download
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

  // Prepare chart data
  const modelChartData = (summary.model_distribution || []).map((item) => ({
    name: item.llm_model || 'Unknown',
    value: item.count,
    cost: item.cost,
  }));

  // Group operations by phase and add color coding
  const operationChartData = (summary.operation_breakdown || [])
    .map((item) => {
      const opType = item.operation_type;
      let phase = 'OTHER';
      let color = '#94a3b8'; // gray
      let sortOrder = 999;
      
      if (opType.startsWith('parse_')) {
        phase = 'PARSE';
        color = '#3b82f6'; // blue
        sortOrder = 1;
      } else if (opType.startsWith('llm_') || opType.includes('transform') || opType.includes('process')) {
        // Include 'process_slot', 'process_day', etc. in PROCESS phase
        phase = 'PROCESS';
        color = '#f59e0b'; // orange
        sortOrder = 2;
      } else if (opType.startsWith('render_')) {
        phase = 'RENDER';
        color = '#10b981'; // green
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
      // Sort by phase first, then by avgTime descending within phase
      if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder;
      return b.avgTime - a.avgTime;
    });

  // Prepare daily chart data
  const dailyChartData = dailyData
    .map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      plans: item.plans,
      cost: item.cost_usd,
      operations: item.operations,
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Performance metrics and usage statistics
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <div className="flex gap-2">
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  timeRange === days
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
          
          {/* Session Toggle */}
          <button
            onClick={() => setShowSessions(!showSessions)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              showSessions
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            {showSessions ? 'Hide' : 'Show'} Sessions
          </button>
          
          {/* Export Button */}
          <button
            onClick={handleExport}
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Distribution Pie Chart */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Model Distribution</h3>
          {modelChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={modelChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {modelChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-12">No data available</p>
          )}
        </div>

        {/* Workflow Breakdown Bar Chart */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Workflow Performance</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Average time per operation (identify bottlenecks)
          </p>
          {operationChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={operationChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                  style={{ fontSize: '11px' }}
                />
                <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-card border rounded p-2 shadow-lg">
                          <p className="font-semibold">{data.name}</p>
                          <p className="text-sm">Phase: <span style={{ color: data.color }}>{data.phase}</span></p>
                          <p className="text-sm">Avg Time: {data.avgTime}ms ({(data.avgTime / 1000).toFixed(2)}s)</p>
                          <p className="text-sm">Count: {data.count}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="avgTime" name="Avg Time (ms)">
                  {operationChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-12">No data available</p>
          )}
        </div>

        {/* Daily Activity Line Chart */}
        <div className="bg-card border rounded-lg p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Daily Activity</h3>
          {dailyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={dailyChartData.length > 14 ? Math.floor(dailyChartData.length / 14) : 0}
                  style={{ fontSize: '11px' }}
                />
                <YAxis yAxisId="left" label={{ value: 'Plans', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Cost ($)', angle: 90, position: 'insideRight' }} />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="plans"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Plans"
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cost"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Cost ($)"
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12">
              <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
              <p className="text-muted-foreground">No daily data available</p>
              <p className="text-xs text-muted-foreground mt-2">
                Generate some lesson plans to see daily activity trends
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Detailed Operations Table */}
      {operationChartData.length > 0 && (
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
                ℹ️ Only one operation type tracked
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
                  const totalTime = summary.total_duration_ms || 1;
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
                            ⚠️
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
          
          {/* Phase Summary */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            {['PARSE', 'PROCESS', 'RENDER'].map((phase) => {
              const phaseOps = operationChartData.filter(op => op.phase === phase);
              if (phaseOps.length === 0) return null;
              
              const phaseTotal = phaseOps.reduce((sum, op) => sum + (op.avgTime * op.count), 0);
              const phasePercentage = ((phaseTotal / (summary.total_duration_ms || 1)) * 100).toFixed(1);
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
      )}

      {/* Session Breakdown Table */}
      {showSessions && sessionData.length > 0 && (
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
      )}

      {showSessions && sessionData.length === 0 && (
        <div className="bg-card border rounded-lg p-6 text-center">
          <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
          <p className="text-muted-foreground">No session data available</p>
          <p className="text-xs text-muted-foreground mt-2">
            Generate some lesson plans to see session breakdown
          </p>
        </div>
      )}
    </div>
  );
}
