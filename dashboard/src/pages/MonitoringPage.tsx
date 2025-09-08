import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Alert,
  Chip,
  Paper
} from '@mui/material';
import {
  Warning as AlertTriangleIcon,
  Timeline as ActivityIcon,
  People as UsersIcon,
  Schedule as ClockIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import LiveMetricsCard from '../components/monitoring/LiveMetricsCard';
import ActiveRequestsTable from '../components/monitoring/ActiveRequestsTable';
import ErrorRateChart from '../components/monitoring/ErrorRateChart';
import ResponseTimeChart from '../components/monitoring/ResponseTimeChart';
import { useWebSocket } from '../hooks/useWebSocket';

// Types
export interface LiveMetrics {
  timestamp: string;
  requests: {
    total: number;
    errors: number;
    error_rate_percent: number;
    avg_response_time_seconds: number;
  };
  services: Record<string, {
    total_calls: number;
    errors: number;
    error_rate_percent: number;
    avg_response_time_seconds: number;
  }>;
}

export interface ActiveRequest {
  id: string;
  type: string;
  status: string;
  started_at: string;
  duration_ms: number;
  user: string;
}

export interface ErrorRate {
  timestamp: string;
  error_rate: number;
  total_requests: number;
  error_count: number;
}

export interface ResponseTime {
  timestamp: string;
  avg_response_time: number;
  p50: number;
  p95: number;
  p99: number;
  total_requests: number;
}

export interface MonitoringAlert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  timestamp: string;
  context: Record<string, any>;
}

const MonitoringPage: React.FC = () => {
  // Feature flags to hide sections (easy to re-enable later)
  const SHOW_LIVE_METRICS = false;
  const SHOW_ACTIVE_REQUESTS = false;
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);
  const [activeRequests, setActiveRequests] = useState<ActiveRequest[]>([]);
  const [errorRates, setErrorRates] = useState<ErrorRate[]>([]);
  const [responseTimes, setResponseTimes] = useState<ResponseTime[]>([]);
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [notification, setNotification] = useState<{open: boolean, message: string, severity: 'error' | 'warning' | 'info' | 'success'}>({
    open: false,
    message: '',
    severity: 'info'
  });

  // Connect to WebSocket for real-time updates
  const { lastMessage, connectionStatus } = useWebSocket('/monitoring/ws');

  // Process WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage);
        
        if (data.type === 'metrics_update') {
          setMetrics(data.data);
          
          // Update charts with new data point
          if (data.data.requests) {
            const newErrorRate: ErrorRate = {
              timestamp: data.timestamp,
              error_rate: data.data.requests.error_rate_percent,
              total_requests: data.data.requests.total,
              error_count: data.data.requests.errors
            };
            
            const newResponseTime: ResponseTime = {
              timestamp: data.timestamp,
              avg_response_time: data.data.requests.avg_response_time_seconds,
              p50: 0, // These would come from actual metrics
              p95: 0,
              p99: 0,
              total_requests: data.data.requests.total
            };
            
            setErrorRates(prev => [...prev.slice(-19), newErrorRate]);
            setResponseTimes(prev => [...prev.slice(-19), newResponseTime]);
          }
        } else if (data.type === 'alert') {
          // Add new alert
          const newAlert: MonitoringAlert = {
            id: data.data.id,
            alert_type: data.data.alert_type,
            severity: data.data.severity,
            title: data.data.title,
            message: data.data.message,
            timestamp: data.data.alert_timestamp,
            context: data.data.context
          };
          
          setAlerts(prev => [newAlert, ...prev]);
          
          // Show notification
          let severity: 'error' | 'warning' | 'info' = 'info';
          if (newAlert.severity === 'critical') {
            severity = 'error';
          } else if (newAlert.severity === 'high') {
            severity = 'warning';
          }
          
          setNotification({
            open: true,
            message: `${newAlert.title}: ${newAlert.message}`,
            severity
          });
        } else if (data.type === 'active_alerts') {
          // Set initial alerts
          setAlerts(data.data.map((alert: any) => ({
            id: alert.id,
            alert_type: alert.alert_type,
            severity: alert.severity,
            title: alert.title,
            message: alert.message,
            timestamp: alert.timestamp,
            context: alert.context
          })));
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Fetch active requests
  const fetchActiveRequests = useCallback(async () => {
    try {
      const response = await fetch('/api/monitoring/active-requests', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setActiveRequests(data.active_requests);
      }
    } catch (error) {
      console.error('Error fetching active requests:', error);
    }
  }, []);

  // Fetch initial error rates and response times
  const fetchInitialData = useCallback(async () => {
    try {
      const [errorRatesResponse, responseTimesResponse] = await Promise.all([
        fetch('/api/monitoring/error-rates', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }),
        fetch('/api/monitoring/response-times', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
      ]);
      
      if (errorRatesResponse.ok) {
        const data = await errorRatesResponse.json();
        setErrorRates(data.error_rates);
      }
      
      if (responseTimesResponse.ok) {
        const data = await responseTimesResponse.json();
        setResponseTimes(data.response_times);
      }
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchActiveRequests();
    fetchInitialData();
    
    // Refresh active requests every 10 seconds
    const interval = setInterval(fetchActiveRequests, 10000);
    
    return () => clearInterval(interval);
  }, [fetchActiveRequests, fetchInitialData]);

  return (
    <Box sx={{ p: 3 }}>
      {/* Enhanced Header Section */}
      <Paper
        elevation={3}
        sx={{
          position: 'relative',
          overflow: 'hidden',
          borderRadius: 3,
          background: 'linear-gradient(135deg, #2e7d32 0%, #00695c 50%, #0277bd 100%)',
          p: 4,
          mb: 3,
          color: 'white'
        }}
      >
        <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.1)' }} />
        <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(4px)',
                mr: 2
              }}
            >
              <ActivityIcon sx={{ fontSize: 32, animation: 'pulse 2s infinite' }} />
            </Box>
            <Box>
              <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                Real-Time Monitoring
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Live system performance and health metrics
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: connectionStatus === 'Connected' ? 'success.main' : 'error.main',
                      animation: connectionStatus === 'Connected' ? 'pulse 2s infinite' : 'none'
                    }}
                  />
                  WebSocket
                </Box>
              }
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(4px)'
              }}
            />
            <Chip
              icon={<ActivityIcon />}
              label={connectionStatus}
              color={connectionStatus === 'Connected' ? 'success' : 'error'}
              sx={{
                bgcolor: connectionStatus === 'Connected' ? 'rgba(76, 175, 80, 0.2)' : 'rgba(244, 67, 54, 0.2)',
                color: 'white',
                border: connectionStatus === 'Connected' ? '1px solid rgba(76, 175, 80, 0.3)' : '1px solid rgba(244, 67, 54, 0.3)'
              }}
            />
          </Box>
        </Box>
      </Paper>
      
      {connectionStatus !== 'Connected' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>Connection Warning</Typography>
          WebSocket {connectionStatus}. Real-time updates may be delayed.
        </Alert>
      )}
      
      {/* Overview Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Total Requests</Typography>
                <ActivityIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {metrics?.requests.total || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {metrics?.requests.errors || 0} errors
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Error Rate</Typography>
                <TrendingDownIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {metrics?.requests.error_rate_percent?.toFixed(1) || 0}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Last 24 hours
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Avg Response Time</Typography>
                <ClockIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {metrics?.requests.avg_response_time_seconds?.toFixed(2) || 0}s
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Current average
            </Typography>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Active Requests</Typography>
                <UsersIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {activeRequests.length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Currently processing
            </Typography>
          </CardContent>
        </Card>
      </Box>
      
      {/* Main Content Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
        {/* Live Metrics Card (hidden by flag) */}
        {SHOW_LIVE_METRICS && (
          <Card>
            <CardHeader
              title="Live Metrics"
              subheader="Real-time system performance metrics"
            />
            <CardContent>
              <LiveMetricsCard metrics={metrics} />
            </CardContent>
          </Card>
        )}

        {/* Active Requests Table (hidden by flag) */}
        {SHOW_ACTIVE_REQUESTS && (
          <Card>
            <CardHeader
              title="Active Requests"
              subheader="Currently processing requests"
            />
            <CardContent>
              <ActiveRequestsTable requests={activeRequests} />
            </CardContent>
          </Card>
        )}
        
        {/* Error Rate Chart */}
        <Card>
          <CardHeader
            title="Error Rate Trends"
            subheader="Error rate over time"
          />
          <CardContent>
            <ErrorRateChart data={errorRates} />
          </CardContent>
        </Card>
        
        {/* Response Time Chart */}
        <Card>
          <CardHeader
            title="Response Time Trends"
            subheader="Response time percentiles"
          />
          <CardContent>
            <ResponseTimeChart data={responseTimes} />
          </CardContent>
        </Card>
      </Box>
      
      {/* Recent Alerts */}
      <Card>
        <CardHeader
          title="Recent Alerts"
          subheader="Latest system alerts and notifications"
        />
        <CardContent>
          {alerts.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No recent alerts
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {alerts.slice(0, 5).map(alert => (
                <Alert 
                  key={alert.id}
                  severity={alert.severity === 'critical' ? 'error' : 'warning'}
                  icon={<AlertTriangleIcon />}
                >
                  <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>{alert.title}</Typography>
                  {alert.message}
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(alert.timestamp).toLocaleString()}
                    </Typography>
                  </Box>
                </Alert>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
      
      {/* Notification Toast - Simple implementation */}
      {notification.open && (
        <Box sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 50 }}>
          <Alert severity={notification.severity} icon={<AlertTriangleIcon />}>
            {notification.message}
          </Alert>
        </Box>
      )}
    </Box>
  );
};

export default MonitoringPage;
