import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { ConfigSectionProps } from './types';

const ConfigSection: React.FC<ConfigSectionProps> = ({ title, children }) => {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Box sx={{ mt: 2 }}>{children}</Box>
    </Paper>
  );
};

export default ConfigSection;