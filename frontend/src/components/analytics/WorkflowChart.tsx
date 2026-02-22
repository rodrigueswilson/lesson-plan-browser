import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { OperationChartEntry } from './useAnalytics';

interface WorkflowChartProps {
  data: OperationChartEntry[];
}

export function WorkflowChart({ data }: WorkflowChartProps) {
  if (data.length === 0) {
    return <p className="text-center text-muted-foreground py-12">No data available</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
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
              const d = payload[0].payload as OperationChartEntry;
              return (
                <div className="bg-card border rounded p-2 shadow-lg">
                  <p className="font-semibold">{d.name}</p>
                  <p className="text-sm">Phase: <span style={{ color: d.color }}>{d.phase}</span></p>
                  <p className="text-sm">Avg Time: {d.avgTime}ms ({(d.avgTime / 1000).toFixed(2)}s)</p>
                  <p className="text-sm">Count: {d.count}</p>
                </div>
              );
            }
            return null;
          }}
        />
        <Bar dataKey="avgTime" name="Avg Time (ms)">
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
