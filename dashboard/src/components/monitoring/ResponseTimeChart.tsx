import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { ResponseTime } from '../../pages/MonitoringPage';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart
} from 'recharts';

interface ResponseTimeChartProps {
  data: ResponseTime[];
}

const ResponseTimeChart: React.FC<ResponseTimeChartProps> = ({ data }) => {
  // Format timestamp for display
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Prepare chart data
  const chartData = data.map(item => ({
    ...item,
    time: formatTimestamp(item.timestamp)
  }));

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Response Time Monitoring</Typography>
        
        {data.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <Typography variant="body2" color="text.secondary">
              No response time data available
            </Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis 
                yAxisId="left" 
                domain={[0, 'auto']} 
                label={{ value: 'Time (s)', angle: -90, position: 'insideLeft' }} 
              />
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                domain={[0, 'auto']} 
                label={{ value: 'Requests', angle: 90, position: 'insideRight' }} 
              />
              <Tooltip 
                formatter={(value: any, name: string) => {
                  if (name === 'avg_response_time') return [`${value}s`, 'Avg Response Time'];
                  if (name === 'p95') return [`${value}s`, '95th Percentile'];
                  if (name === 'p99') return [`${value}s`, '99th Percentile'];
                  if (name === 'total_requests') return [value, 'Total Requests'];
                  return [value, name];
                }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="avg_response_time"
                name="Avg Response Time"
                stroke="#2196f3"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 8 }}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="p95"
                name="95th Percentile"
                stroke="#9c27b0"
                strokeDasharray="5 5"
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="p99"
                name="99th Percentile"
                stroke="#e91e63"
                strokeDasharray="3 3"
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="total_requests"
                name="Total Requests"
                fill="#4caf50"
                stroke="#4caf50"
                fillOpacity={0.2}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default ResponseTimeChart;