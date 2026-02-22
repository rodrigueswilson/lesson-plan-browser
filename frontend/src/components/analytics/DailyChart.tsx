import { BarChart3 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DailyChartDataEntry {
  date: string;
  plans: number;
  cost: number;
  operations: number;
}

interface DailyChartProps {
  data: DailyChartDataEntry[];
}

export function DailyChart({ data }: DailyChartProps) {
  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
        <p className="text-muted-foreground">No daily data available</p>
        <p className="text-xs text-muted-foreground mt-2">
          Generate some lesson plans to see daily activity trends
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          angle={-45}
          textAnchor="end"
          height={100}
          interval={data.length > 14 ? Math.floor(data.length / 14) : 0}
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
  );
}
