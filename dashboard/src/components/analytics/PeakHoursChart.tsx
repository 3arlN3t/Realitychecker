import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Paper, Typography, Box } from '@mui/material';
import { PeakHourData } from './types';

interface PeakHoursChartProps {
  data: PeakHourData[];
}

const PeakHoursChart: React.FC<PeakHoursChartProps> = ({ data }) => {
  // Format hour to AM/PM format
  const formatHour = (hour: number) => {
    if (hour === 0) return '12 AM';
    if (hour === 12) return '12 PM';
    return hour < 12 ? `${hour} AM` : `${hour - 12} PM`;
  };

  // Find the peak hour for highlighting
  const maxCount = Math.max(...data.map(item => item.count));

  return (
    <Paper sx={{ p: 3, height: '400px', flex: '1 1 400px', minWidth: '400px' }}>
      <Typography variant="h6" gutterBottom>
        Usage Pattern Analysis
      </Typography>
      <Box sx={{ width: '100%', height: '90%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
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
              dataKey="hour" 
              tickFormatter={formatHour}
              padding={{ left: 10, right: 10 }}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number) => [`${value} requests`, 'Count']}
              labelFormatter={(label) => `Hour: ${formatHour(Number(label))}`}
            />
            <Bar dataKey="count" name="Request Count">
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.count === maxCount ? '#f44336' : '#2196f3'} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default PeakHoursChart;