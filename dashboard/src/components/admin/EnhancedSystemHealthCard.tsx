/**
 * Enhanced System Health Card with real API integration and better UX
 * 
 * Features:
 * - Real-time health data polling with configurable intervals
 * - Graceful fallback to mock data when API is unavailable
 * - Loading states with skeleton UI for better perceived performance
 * - Comprehensive error handling and user feedback
 * - Responsive design with accessibility support
 * - Resource usage monitoring (CPU, Memory)
 * - Individual service status tracking
 * 
 * @example
 * ```tsx
 * <EnhancedSystemHealthCard 
 *   pollInterval={30000}
 *   showDetails={true}
 *   showRefreshButton={true}
 * />
 * ```
 */

import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Fade
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  CloudOff as CloudOffIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import { useHealthCheck } from '../../hooks/useHealthCheck';
// SystemHealth and ServiceStatus types are imported but used in type annotations
import { createHealthSummary, formatResponseTime, getStatusColor } from '../../lib/healthTransforms';

interface EnhancedSystemHealthCardProps {
  /** Custom polling interval in milliseconds */
  pollInterval?: number;
  /** Whether to show detailed service information */
  showDetails?: boolean;
  /** Whether to show refresh button */
  showRefreshButton?: boolean;
  /** Custom height for the card */
  height?: string | number;
}

const EnhancedSystemHealthCard: React.FC<EnhancedSystemHealthCardProps> = ({
  pollInterval = 30000,
  showDetails = true,
  showRefreshButton = true,
  height = '100%'
}) => {
  const {
    healthData,
    isLoading,
    error,
    isStale,
    isUsingMockData,
    lastFetch,
    refresh,
    isPolling
  } = useHealthCheck({
    pollInterval,
    useMockFallback: true,
    onError: (error) => {
      console.error('Health check error:', error);
    }
  });

  // Compute health summary (must be before early returns)
  const healthSummary = useMemo(() => 
    healthData ? createHealthSummary(healthData) : null, 
    [healthData]
  );

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

  const getProgressColor = (percentage: number): 'success' | 'warning' | 'error' => {
    if (percentage < 70) return 'success';
    if (percentage < 85) return 'warning';
    return 'error';
  };

  const handleRefresh = async () => {
    try {
      await refresh();
    } catch (error) {
      console.error('Failed to refresh health data:', error);
      // Error is already handled by the hook, but we can add additional UI feedback here if needed
    }
  };

  // Loading skeleton
  if (isLoading && !healthData) {
    return (
      <Box sx={{ height }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Skeleton variant="circular" width={24} height={24} />
          <Skeleton variant="text" width={120} sx={{ ml: 1, flexGrow: 1 }} />
          <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 1 }} />
        </Box>
        
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2 }}>
          <Skeleton variant="text" height={60} />
          <Skeleton variant="text" height={60} />
        </Box>

        <Skeleton variant="text" width={100} sx={{ mb: 1 }} />
        <Skeleton variant="rectangular" height={8} sx={{ mb: 2, borderRadius: 1 }} />
        <Skeleton variant="rectangular" height={8} sx={{ mb: 3, borderRadius: 1 }} />

        <Skeleton variant="text" width={100} sx={{ mb: 1 }} />
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' }, gap: 1 }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" height={60} sx={{ borderRadius: 1 }} />
          ))}
        </Box>
      </Box>
    );
  }

  if (!healthData) {
    return (
      <Box sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Alert severity="error" sx={{ width: '100%' }}>
          <Typography variant="body2">
            Unable to load health data
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Fade in={true} timeout={500}>
      <Box sx={{ height }} role="region" aria-label="System Health Dashboard">
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {getStatusIcon(healthData.status)}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            System Health
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Status indicators */}
            {isUsingMockData && (
              <Tooltip title="Using mock data - API unavailable">
                <CloudOffIcon fontSize="small" color="warning" />
              </Tooltip>
            )}
            
            {isStale && (
              <Tooltip title="Data is stale">
                <ScheduleIcon fontSize="small" color="warning" />
              </Tooltip>
            )}

            {/* Refresh button */}
            {showRefreshButton && (
              <Tooltip title="Refresh health data">
                <IconButton
                  size="small"
                  onClick={handleRefresh}
                  disabled={isLoading}
                  sx={{ 
                    animation: isLoading ? 'spin 1s linear infinite' : 'none',
                    '@keyframes spin': {
                      '0%': { transform: 'rotate(0deg)' },
                      '100%': { transform: 'rotate(360deg)' }
                    }
                  }}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {/* Status chip */}
            <Chip
              label={healthData.status.toUpperCase()}
              color={getStatusColor(healthData.status)}
              size="small"
            />
          </Box>
        </Box>

        {/* Warning for mock data */}
        {isUsingMockData && (
          <Alert severity="warning" sx={{ mb: 2 }} variant="outlined">
            <Typography variant="caption">
              Displaying mock data - Health API is unavailable
            </Typography>
          </Alert>
        )}

        {/* Error alert */}
        {error && !isUsingMockData && (
          <Alert severity="error" sx={{ mb: 2 }} variant="outlined">
            <Typography variant="caption">
              Health check failed: {error.message}
            </Typography>
          </Alert>
        )}

        {/* Overview stats */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2 }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Uptime
            </Typography>
            <Typography variant="h6" color="success.main">
              {healthData.uptime}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Last Updated
            </Typography>
            <Typography variant="body2">
              {healthData.lastUpdated}
            </Typography>
          </Box>
        </Box>

        {/* Additional stats */}
        {healthSummary && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 3 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Healthy Services
              </Typography>
              <Typography variant="h6" color={healthSummary?.healthyServices === healthSummary?.totalServices ? 'success.main' : 'warning.main'}>
                {healthSummary?.healthyServices || 0}/{healthSummary?.totalServices || 0}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Avg Response Time
              </Typography>
              <Typography variant="h6">
                {formatResponseTime(healthSummary?.avgResponseTime || 0)}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Resource usage */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Resource Usage
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2">Memory</Typography>
              <Typography variant="body2">{healthData.memoryUsage}%</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={healthData.memoryUsage}
              color={getProgressColor(healthData.memoryUsage)}
              sx={{ height: 8, borderRadius: 1 }}
              aria-label={`Memory usage: ${healthData.memoryUsage}%`}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2">CPU</Typography>
              <Typography variant="body2">{healthData.cpuUsage}%</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={healthData.cpuUsage}
              color={getProgressColor(healthData.cpuUsage)}
              sx={{ height: 8, borderRadius: 1 }}
              aria-label={`CPU usage: ${healthData.cpuUsage}%`}
            />
          </Box>
        </Box>

        {/* Service status */}
        {showDetails && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Service Status
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' }, gap: 1 }}>
              {Object.entries(healthData.services).map(([serviceName, service]) => (
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
                    alignItems: 'center',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      opacity: 0.2,
                      transform: 'translateY(-1px)'
                    }
                  }}
                >
                  {getStatusIcon(service.status)}
                  <Box sx={{ ml: 1, minWidth: 0 }}>
                    <Typography variant="caption" sx={{ display: 'block', textTransform: 'capitalize' }}>
                      {serviceName}
                    </Typography>
                    {service.responseTime && (
                      <Typography variant="caption" color="text.secondary">
                        {formatResponseTime(service.responseTime)}
                      </Typography>
                    )}
                  </Box>
                </Paper>
              ))}
            </Box>
          </Box>
        )}

        {/* Footer info */}
        <Box sx={{ mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="caption" color="text.secondary">
            {isPolling ? `Auto-refresh every ${pollInterval / 1000}s` : 'Auto-refresh disabled'}
            {lastFetch && ` • Last updated: ${lastFetch.toLocaleTimeString()}`}
          </Typography>
        </Box>
      </Box>
    </Fade>
  );
};

export default EnhancedSystemHealthCard;