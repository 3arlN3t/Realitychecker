import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  LinearProgress,
  IconButton,
  Collapse,
  Divider,
  useTheme,
  useMediaQuery,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Storage as DatabaseIcon,
  Cloud as CloudIcon,
  Webhook as WebhookIcon,
  Psychology as AIIcon,
} from '@mui/icons-material';
import { ServiceStatus } from './SystemHealthCard';

export interface ServiceDetails extends ServiceStatus {
  name: string;
  description: string;
  version?: string;
  endpoint?: string;
  dependencies?: string[];
  metrics?: {
    requestsPerMinute: number;
    successRate: number;
    avgResponseTime: number;
    uptime: string;
  };
  recentErrors?: Array<{
    timestamp: string;
    error: string;
    count: number;
  }>;
}

interface ServiceStatusGridProps {
  services: Record<string, ServiceDetails>;
  onRefreshService?: (serviceName: string) => void;
  onViewDetails?: (serviceName: string) => void;
}

const ServiceStatusGrid: React.FC<ServiceStatusGridProps> = ({
  services,
  onRefreshService,
  onViewDetails,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expandedService, setExpandedService] = useState<string | null>(null);

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'openai':
        return <AIIcon />;
      case 'twilio':
        return <CloudIcon />;
      case 'database':
        return <DatabaseIcon />;
      case 'webhook':
        return <WebhookIcon />;
      default:
        return <InfoIcon />;
    }
  };

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

  const formatResponseTime = (time?: number) => {
    if (!time) return 'N/A';
    if (time < 1000) return `${time}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const handleExpandClick = (serviceName: string) => {
    setExpandedService(expandedService === serviceName ? null : serviceName);
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TimelineIcon color="primary" />
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Service Health Monitoring
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {Object.keys(services).length} Services
          </Typography>
        </Box>

        <Grid container spacing={2}>
          {Object.entries(services).map(([serviceName, service]) => (
            <Grid item xs={12} sm={6} md={4} key={serviceName}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  border: 2,
                  borderColor: service.status === 'critical' ? 'error.main' : 
                              service.status === 'warning' ? 'warning.main' : 
                              service.status === 'healthy' ? 'success.main' : 'divider',
                  bgcolor: service.status === 'critical' ? 'error.light' : 
                           service.status === 'warning' ? 'warning.light' : 
                           service.status === 'healthy' ? 'success.light' : 'background.paper',
                  opacity: service.status === 'healthy' ? 0.05 : 0.1,
                }}
              >
                <CardContent sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                      {getServiceIcon(serviceName)}
                      <Typography variant="h6" sx={{ ml: 1, textTransform: 'capitalize' }}>
                        {service.name || serviceName}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {onRefreshService && (
                        <Tooltip title="Refresh status">
                          <IconButton
                            size="small"
                            onClick={() => onRefreshService(serviceName)}
                            aria-label="Refresh status"
                          >
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <IconButton
                        size="small"
                        onClick={() => handleExpandClick(serviceName)}
                      >
                        {expandedService === serviceName ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    {getStatusIcon(service.status)}
                    <Chip
                      label={service.status.toUpperCase()}
                      color={getStatusColor(service.status) as any}
                      size="small"
                      variant="filled"
                      sx={{ ml: 1 }}
                    />
                  </Box>

                  <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                    {service.description}
                  </Typography>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      Response Time
                    </Typography>
                    <Typography variant="caption" fontWeight="bold">
                      {formatResponseTime(service.responseTime)}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      Last Check
                    </Typography>
                    <Typography variant="caption">
                      {formatTimestamp(service.lastCheck)}
                    </Typography>
                  </Box>

                  {service.errorCount !== undefined && service.errorCount > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="caption" color="error">
                        Recent Errors
                      </Typography>
                      <Typography variant="caption" color="error" fontWeight="bold">
                        {service.errorCount}
                      </Typography>
                    </Box>
                  )}

                  <Collapse in={expandedService === serviceName} timeout="auto" unmountOnExit>
                    <Divider sx={{ my: 1 }} />
                    
                    {service.version && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          Version
                        </Typography>
                        <Typography variant="caption">
                          {service.version}
                        </Typography>
                      </Box>
                    )}

                    {service.endpoint && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          Endpoint
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ wordBreak: 'break-all' }}>
                          {service.endpoint}
                        </Typography>
                      </Box>
                    )}

                    {service.dependencies && service.dependencies.length > 0 && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          Dependencies
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                          {service.dependencies.map((dep, index) => (
                            <Chip
                              key={index}
                              label={dep}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.6rem', height: 20 }}
                            />
                          ))}
                        </Box>
                      </Box>
                    )}

                    {service.metrics && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="textSecondary" gutterBottom>
                          Performance Metrics
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption">Success Rate</Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {service.metrics.successRate.toFixed(1)}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={service.metrics.successRate}
                            color={service.metrics.successRate > 95 ? 'success' : 
                                   service.metrics.successRate > 90 ? 'warning' : 'error'}
                            sx={{ height: 4, borderRadius: 2, mb: 1 }}
                          />
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption">Requests/min</Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {service.metrics.requestsPerMinute}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption">Uptime</Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {service.metrics.uptime}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    )}

                    {service.recentErrors && service.recentErrors.length > 0 && (
                      <Box>
                        <Typography variant="caption" color="error" gutterBottom>
                          Recent Errors
                        </Typography>
                        <Box sx={{ maxHeight: 100, overflow: 'auto' }}>
                          {service.recentErrors.slice(0, 3).map((error, index) => (
                            <Box key={index} sx={{ mb: 0.5 }}>
                              <Typography variant="caption" color="error" display="block">
                                {formatTimestamp(error.timestamp)} ({error.count}x)
                              </Typography>
                              <Typography variant="caption" color="textSecondary" display="block">
                                {error.error}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ServiceStatusGrid;