import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Paper, Typography, Box } from '@mui/material';
import { UsageTrendData } from './types';

interface UsageTrendsChartProps {
  data: UsageTrendData[];
  period: string;
}

const UsageTrendsChart: React.FC<UsageTrendsChartProps> = ({ data, period }) => {
  // Handle empty or invalid data
  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3, height: '400px', flex: '1 1 400px', minWidth: '400px' }}>
        <Typography variant="h6" gutterBottom>
          Request Volume Over Time
        </Typography>
        <Box sx={{ 
          width: '100%', 
          height: '90%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column'
        }}>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            No usage trend data available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Usage patterns will appear here over time
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Format X-axis tick based on period
  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    switch (period) {
      case 'day':
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case 'week':
        return date.toLocaleDateString([], { weekday: 'short' });
      case 'month':
        return date.toLocaleDateString([], { day: 'numeric' });
      case 'year':
        return date.toLocaleDateString([], { month: 'short' });
      default:
        return tickItem;
    }
  };

  return (
    <Paper sx={{ p: 3, height: '400px', flex: '1 1 400px', minWidth: '400px' }}>
      <Typography variant="h6" gutterBottom>
        Request Volume Over Time
      </Typography>
      <Box sx={{ width: '100%', height: '90%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatXAxis}
              padding={{ left: 10, right: 10 }}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number) => [`${value} requests`, 'Count']}
              labelFormatter={(label) => `Date: ${new Date(label).toLocaleDateString()}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#2196f3"
              activeDot={{ r: 8 }}
              name="Request Volume"
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default UsageTrendsChart;