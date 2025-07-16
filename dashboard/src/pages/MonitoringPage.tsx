import React, { useState, useEffect, useCallback } from 'react';
import { Typography, Box, Grid, Paper, Alert, Snackbar } from '@mui/material';
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

export interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  timestamp: string;
  context: Record<string, any>;
}

const MonitoringPage: React.FC = () => {
  const [metrics, setMetrics] = useState<LiveMetrics | null>(null);
  const [activeRequests, setActiveRequests] = useState<ActiveRequest[]>([]);
  const [errorRates, setErrorRates] = useState<ErrorRate[]>([]);
  const [responseTimes, setResponseTimes] = useState<ResponseTime[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
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
          const newAlert: Alert = {
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
          setNotification({
            open: true,
            message: `${newAlert.title}: ${newAlert.message}`,
            severity: newAlert.severity === 'critical' ? 'error' : 
                     newAlert.severity === 'high' ? 'warning' : 'info'
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

  // Handle notification close
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Real-Time Monitoring
      </Typography>
      
      {connectionStatus !== 'Connected' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          WebSocket {connectionStatus}. Real-time updates may be delayed.
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Live Metrics Card */}
        <Grid item xs={12} md={6}>
          <LiveMetricsCard metrics={metrics} />
        </Grid>
        
        {/* Active Requests Table */}
        <Grid item xs={12} md={6}>
          <ActiveRequestsTable requests={activeRequests} />
        </Grid>
        
        {/* Error Rate Chart */}
        <Grid item xs={12} md={6}>
          <ErrorRateChart data={errorRates} />
        </Grid>
        
        {/* Response Time Chart */}
        <Grid item xs={12} md={6}>
          <ResponseTimeChart data={responseTimes} />
        </Grid>
        
        {/* Recent Alerts */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Recent Alerts</Typography>
            {alerts.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No recent alerts</Typography>
            ) : (
              alerts.slice(0, 5).map(alert => (
                <Alert 
                  key={alert.id} 
                  severity={
                    alert.severity === 'critical' ? 'error' : 
                    alert.severity === 'high' ? 'warning' : 
                    alert.severity === 'medium' ? 'info' : 'success'
                  }
                  sx={{ mb: 1 }}
                >
                  <Typography variant="subtitle2">{alert.title}</Typography>
                  <Typography variant="body2">{alert.message}</Typography>
                  <Typography variant="caption" display="block">
                    {new Date(alert.timestamp).toLocaleString()}
                  </Typography>
                </Alert>
              ))
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {/* Alert Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MonitoringPage;