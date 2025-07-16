import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const DashboardPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Dashboard
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Total Requests
            </Typography>
            <Typography variant="h3">
              1,250
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Requests Today
            </Typography>
            <Typography variant="h3">
              45
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Error Rate
            </Typography>
            <Typography variant="h3">
              2.3%
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Active Users
            </Typography>
            <Typography variant="h3">
              23
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default DashboardPage;