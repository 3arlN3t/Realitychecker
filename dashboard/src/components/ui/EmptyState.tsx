import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { 
  Refresh as RefreshIcon,
  CloudOff as CloudOffIcon,
  BarChart as BarChartIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'no-data' | 'error' | 'loading';
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  variant = 'no-data'
}) => {
  const getDefaultIcon = () => {
    switch (variant) {
      case 'error':
        return <WarningIcon sx={{ fontSize: 48, color: 'error.main' }} />;
      case 'loading':
        return <CloudOffIcon sx={{ fontSize: 48, color: 'warning.main' }} />;
      default:
        return <BarChartIcon sx={{ fontSize: 48, color: 'text.secondary' }} />;
    }
  };

  const getBackgroundColor = () => {
    switch (variant) {
      case 'error':
        return 'rgba(244, 67, 54, 0.05)';
      case 'loading':
        return 'rgba(255, 152, 0, 0.05)';
      default:
        return 'rgba(158, 158, 158, 0.05)';
    }
  };

  return (
    <Paper
      sx={{
        p: 4,
        textAlign: 'center',
        bgcolor: getBackgroundColor(),
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 200
      }}
    >
      <Box sx={{ mb: 2 }}>
        {icon || getDefaultIcon()}
      </Box>
      
      <Typography variant="h6" sx={{ mb: 1, color: 'text.primary' }}>
        {title}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 300 }}>
        {description}
      </Typography>
      
      {action && (
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={action.onClick}
          size="small"
        >
          {action.label}
        </Button>
      )}
    </Paper>
  );
};

export default EmptyState;