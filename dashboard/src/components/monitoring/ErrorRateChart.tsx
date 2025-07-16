import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { ErrorRate } from '../../pages/MonitoringPage';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ErrorRateChartProps {
  data: ErrorRate[];
}

const ErrorRateChart: React.FC<ErrorRateChartProps> = ({ data }) => {
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
        <Typography variant="h6" gutterBottom>Error Rate Monitoring</Typography>
        
        {data.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <Typography variant="body2" color="text.secondary">
              No error rate data available
            </Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
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
              <YAxis yAxisId="left" domain={[0, 'auto']} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 'auto']} />
              <Tooltip 
                formatter={(value: any, name: string) => {
                  if (name === 'error_rate') return [`${value}%`, 'Error Rate'];
                  if (name === 'error_count') return [value, 'Error Count'];
                  return [value, name];
                }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="error_rate"
                name="Error Rate (%)"
                stroke="#ff0000"
                activeDot={{ r: 8 }}
                strokeWidth={2}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="error_count"
                name="Error Count"
                stroke="#ff9800"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default ErrorRateChart;