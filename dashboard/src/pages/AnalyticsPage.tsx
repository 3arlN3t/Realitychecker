import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const AnalyticsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics Dashboard
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Analytics dashboard will be implemented in future tasks.
          This will include charts for classification trends, usage statistics, and user engagement metrics.
        </Typography>
      </Paper>
    </Box>
  );
};

export default AnalyticsPage;