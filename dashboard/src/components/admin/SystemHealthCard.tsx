import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  Paper
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  uptime: string;
  lastUpdated: string;
  services: {
    openai: ServiceStatus;
    twilio: ServiceStatus;
    database: ServiceStatus;
    webhook: ServiceStatus;
  };
  memoryUsage: number; // percentage
  cpuUsage: number; // percentage
}

export interface ServiceStatus {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  responseTime?: number; // in ms
  lastCheck: string;
  errorCount?: number;
}

interface SystemHealthCardProps {
  health: SystemHealth;
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon fontSize="small" color="success" />;
      case 'warning':
        return <WarningIcon fontSize="small" color="warning" />;
      case 'critical':
        return <ErrorIcon fontSize="small" color="error" />;
      default:
        return <InfoIcon fontSize="small" color="info" />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'info';
    }
  };

  const getProgressColor = (percentage: number): 'success' | 'warning' | 'error' => {
    if (percentage < 70) return 'success';
    if (percentage < 85) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        {getStatusIcon(health.status)}
        <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
          System Health
        </Typography>
        <Chip
          label={health.status.toUpperCase()}
          color={getStatusColor(health.status)}
          size="small"
        />
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="body2" color="text.secondary">
            Uptime
          </Typography>
          <Typography variant="h6" color="success.main">
            {health.uptime}
          </Typography>
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary">
            Last Updated
          </Typography>
          <Typography variant="body2">
            {health.lastUpdated}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Resource Usage
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2">Memory</Typography>
            <Typography variant="body2">{health.memoryUsage}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={health.memoryUsage}
            color={getProgressColor(health.memoryUsage)}
            sx={{ height: 8, borderRadius: 1 }}
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2">CPU</Typography>
            <Typography variant="body2">{health.cpuUsage}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={health.cpuUsage}
            color={getProgressColor(health.cpuUsage)}
            sx={{ height: 8, borderRadius: 1 }}
          />
        </Box>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Service Status
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' }, gap: 1 }}>
          {Object.entries(health.services).map(([serviceName, service]) => (
            <Paper
              key={serviceName}
              elevation={0}
              sx={{
                p: 1,
                border: 1,
                borderColor: `${getStatusColor(service.status)}.main`,
                bgcolor: `${getStatusColor(service.status)}.main`,
                opacity: 0.1,
                display: 'flex',
                alignItems: 'center'
              }}
            >
              {getStatusIcon(service.status)}
              <Box sx={{ ml: 1, minWidth: 0 }}>
                <Typography variant="caption" sx={{ display: 'block', textTransform: 'capitalize' }}>
                  {serviceName}
                </Typography>
                {service.responseTime && (
                  <Typography variant="caption" color="text.secondary">
                    {service.responseTime}ms
                  </Typography>
                )}
              </Box>
            </Paper>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default SystemHealthCard;