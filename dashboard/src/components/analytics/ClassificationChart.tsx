import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend 
} from 'recharts';
import { Paper, Typography, Box } from '@mui/material';
import { ClassificationData } from './types';

interface ClassificationChartProps {
  data: ClassificationData[];
}

const COLORS = ['#4caf50', '#ff9800', '#f44336', '#2196f3'];

const ClassificationChart: React.FC<ClassificationChartProps> = ({ data }) => {
  // Handle empty or invalid data
  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3, height: '400px', flex: '1 1 400px', minWidth: '400px' }}>
        <Typography variant="h6" gutterBottom>
          Scam Detection Breakdown
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
            No classification data available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Data will appear here once requests are processed
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, height: '400px', flex: '1 1 400px', minWidth: '400px' }}>
      <Typography variant="h6" gutterBottom>
        Scam Detection Breakdown
      </Typography>
      <Box sx={{ width: '100%', height: '90%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
              nameKey="name"
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color || COLORS[index % COLORS.length]} 
                />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number) => [`${value} requests`, 'Count']}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default ClassificationChart;