import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  Box, 
  LinearProgress, 
  Chip,
  Divider
} from '@mui/material';
import { 
  Speed as SpeedIcon,
  Error as ErrorIcon,
  AccessTime as AccessTimeIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';
import { LiveMetrics } from '../../pages/MonitoringPage';

interface LiveMetricsCardProps {
  metrics: LiveMetrics | null;
}

const LiveMetricsCard: React.FC<LiveMetricsCardProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Live System Metrics</Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <LinearProgress sx={{ width: '100%' }} />
          </Box>
          <Typography variant="body2" color="text.secondary" align="center">
            Waiting for metrics data...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const { requests, services } = metrics;
  
  // Calculate service health
  const serviceHealth = Object.entries(services).map(([name, data]) => ({
    name,
    errorRate: data.error_rate_percent,
    responseTime: data.avg_response_time_seconds,
    status: data.error_rate_percent > 5 ? 'warning' : 'healthy'
  }));

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Live System Metrics</Typography>
          <Chip 
            label={`Updated: ${new Date().toLocaleTimeString()}`} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        </Box>

        <Grid container spacing={2}>
          {/* Request Rate */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center' }}>
              <SpeedIcon color="primary" />
              <Typography variant="body2" color="text.secondary">Requests</Typography>
              <Typography variant="h6">{requests.total}</Typography>
            </Box>
          </Grid>

          {/* Error Rate */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center' }}>
              <ErrorIcon color={requests.error_rate_percent > 5 ? "error" : "success"} />
              <Typography variant="body2" color="text.secondary">Error Rate</Typography>
              <Typography variant="h6">{requests.error_rate_percent.toFixed(1)}%</Typography>
            </Box>
          </Grid>

          {/* Response Time */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center' }}>
              <AccessTimeIcon color="primary" />
              <Typography variant="body2" color="text.secondary">Avg Response</Typography>
              <Typography variant="h6">{requests.avg_response_time_seconds.toFixed(2)}s</Typography>
            </Box>
          </Grid>

          {/* Success Rate */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Box sx={{ textAlign: 'center' }}>
              <MemoryIcon color="primary" />
              <Typography variant="body2" color="text.secondary">Success Rate</Typography>
              <Typography variant="h6">{(100 - requests.error_rate_percent).toFixed(1)}%</Typography>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />
        
        <Typography variant="subtitle2" gutterBottom>Service Health</Typography>
        <Grid container spacing={1}>
          {serviceHealth.map((service) => (
            <Grid size={{ xs: 6 }} key={service.name}>
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 1,
                borderRadius: 1,
                bgcolor: 'background.paper'
              }}>
                <Typography variant="body2">{service.name}</Typography>
                <Chip 
                  label={service.status} 
                  size="small"
                  color={service.status === 'healthy' ? 'success' : 'warning'}
                />
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default LiveMetricsCard;