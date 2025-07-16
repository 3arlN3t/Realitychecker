import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'critical':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage < 70) return 'success';
    if (percentage < 85) return 'warning';
    return 'error';
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {getStatusIcon(health.status)}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            System Health
          </Typography>
          <Chip
            label={health.status.toUpperCase()}
            color={getStatusColor(health.status) as any}
            size="small"
            variant="filled"
          />
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="textSecondary">
              Uptime
            </Typography>
            <Typography variant="h6" color="success.main">
              {health.uptime}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="textSecondary">
              Last Updated
            </Typography>
            <Typography variant="body2">
              {health.lastUpdated}
            </Typography>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
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
              sx={{ height: 6, borderRadius: 3 }}
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
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Service Status
          </Typography>
          <Grid container spacing={1}>
            {Object.entries(health.services).map(([serviceName, service]) => (
              <Grid item xs={6} sm={isMobile ? 6 : 3} key={serviceName}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    p: 1,
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    bgcolor: service.status === 'healthy' ? 'success.light' : 
                             service.status === 'warning' ? 'warning.light' : 
                             service.status === 'critical' ? 'error.light' : 'grey.100',
                    opacity: service.status === 'healthy' ? 0.1 : 0.2,
                  }}
                >
                  {getStatusIcon(service.status)}
                  <Box sx={{ ml: 1, minWidth: 0 }}>
                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                      {serviceName}
                    </Typography>
                    {service.responseTime && (
                      <Typography variant="caption" display="block" color="textSecondary">
                        {service.responseTime}ms
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemHealthCard;