import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  LinearProgress,
  Divider,
  Grid
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Storage as DatabaseIcon,
  Cloud as CloudIcon,
  Http as WebhookIcon,
  Psychology as BrainIcon
} from '@mui/icons-material';
import { ServiceStatus, ServiceDetails } from '../../types/dashboard';

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
  const [expandedService, setExpandedService] = useState<string | null>(null);

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'openai':
        return <BrainIcon />;
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

  const getProgressColor = (percentage: number): 'success' | 'warning' | 'error' => {
    if (percentage > 95) return 'success';
    if (percentage > 90) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TimelineIcon color="primary" />
        <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
          Service Health Monitoring
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {Object.keys(services).length} Services
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr', lg: '1fr 1fr 1fr' }, gap: 2 }}>
        {Object.entries(services).map(([serviceName, service]) => (
          <Paper
            key={serviceName}
            elevation={1}
            sx={{
              height: '100%',
              border: 2,
              borderColor: `${getStatusColor(service.status)}.main`,
              bgcolor: `${getStatusColor(service.status)}.main`,
              opacity: 0.05,
              borderRadius: 2,
              overflow: 'hidden'
            }}
          >
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                  <Box sx={{ color: 'primary.main', mr: 1 }}>
                    {getServiceIcon(serviceName)}
                  </Box>
                  <Typography variant="subtitle1" sx={{ textTransform: 'capitalize' }}>
                    {service.name || serviceName}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {onRefreshService && (
                    <IconButton
                      size="small"
                      onClick={() => onRefreshService(serviceName)}
                      aria-label="Refresh status"
                      title="Refresh status"
                    >
                      <RefreshIcon fontSize="small" />
                    </IconButton>
                  )}
                  <IconButton
                    size="small"
                    onClick={() => handleExpandClick(serviceName)}
                    aria-label={expandedService === serviceName ? "Hide details" : "Show details"}
                    title={expandedService === serviceName ? "Hide details" : "Show details"}
                  >
                    {expandedService === serviceName ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  </IconButton>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getStatusIcon(service.status)}
                <Chip
                  label={service.status.toUpperCase()}
                  color={getStatusColor(service.status)}
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Box>

              <Typography variant="body2" sx={{ mb: 1.5 }}>
                {service.description}
              </Typography>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Response Time
                </Typography>
                <Typography variant="caption" fontWeight="medium">
                  {formatResponseTime(service.responseTime)}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Last Check
                </Typography>
                <Typography variant="caption">
                  {formatTimestamp(service.lastCheck)}
                </Typography>
              </Box>

              {service.errorCount !== undefined && service.errorCount > 0 && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" color="error">
                    Recent Errors
                  </Typography>
                  <Typography variant="caption" fontWeight="medium" color="error">
                    {service.errorCount}
                  </Typography>
                </Box>
              )}

              {expandedService === serviceName && (
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  {service.version && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Version
                      </Typography>
                      <Typography variant="caption">
                        {service.version}
                      </Typography>
                    </Box>
                  )}

                  {service.endpoint && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                        Endpoint
                      </Typography>
                      <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>
                        {service.endpoint}
                      </Typography>
                    </Box>
                  )}

                  {service.dependencies && service.dependencies.length > 0 && (
                    <Box sx={{ mb: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                        Dependencies
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {service.dependencies.map((dep) => (
                          <Chip
                            key={`${serviceName}-dep-${dep}`}
                            label={dep}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {service.metrics && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                        Performance Metrics
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption">Success Rate</Typography>
                          <Typography variant="caption" fontWeight="medium">
                            {service.metrics.successRate.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={service.metrics.successRate}
                          color={getProgressColor(service.metrics.successRate)}
                          sx={{ height: 4, borderRadius: 1, mb: 1 }}
                        />
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption">Requests/min</Typography>
                          <Typography variant="caption" fontWeight="medium">
                            {service.metrics.requestsPerMinute}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption">Uptime</Typography>
                          <Typography variant="caption" fontWeight="medium">
                            {service.metrics.uptime}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  )}

                  {service.recentErrors && service.recentErrors.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="error" display="block" sx={{ mb: 0.5 }}>
                        Recent Errors
                      </Typography>
                      <Box sx={{ maxHeight: 100, overflow: 'auto' }}>
                        {service.recentErrors.slice(0, 3).map((error) => (
                          <Box key={`${serviceName}-error-${error.timestamp}-${error.error}`} sx={{ mb: 1 }}>
                            <Typography variant="caption" color="error" display="block">
                              {formatTimestamp(error.timestamp)} ({error.count}x)
                            </Typography>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {error.error}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
};

export default ServiceStatusGrid;