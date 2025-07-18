import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { AlertTriangle, Activity, Users, Clock, TrendingDown } from 'lucide-react';
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

  // Handle notification close - removed as it's not used

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Real-Time Monitoring</h1>
        <div className="flex items-center space-x-2">
          <Badge variant={connectionStatus === 'Connected' ? 'default' : 'destructive'}>
            <Activity className="w-3 h-3 mr-1" />
            {connectionStatus}
          </Badge>
        </div>
      </div>
      
      {connectionStatus !== 'Connected' && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Connection Warning</AlertTitle>
          <AlertDescription>
            WebSocket {connectionStatus}. Real-time updates may be delayed.
          </AlertDescription>
        </Alert>
      )}
      
      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.requests.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              {metrics?.requests.errors || 0} errors
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.requests.error_rate_percent?.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              Last 24 hours
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.requests.avg_response_time_seconds?.toFixed(2) || 0}s
            </div>
            <p className="text-xs text-muted-foreground">
              Current average
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Requests</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeRequests.length}</div>
            <p className="text-xs text-muted-foreground">
              Currently processing
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Live Metrics Card */}
        <Card>
          <CardHeader>
            <CardTitle>Live Metrics</CardTitle>
            <CardDescription>Real-time system performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <LiveMetricsCard metrics={metrics} />
          </CardContent>
        </Card>
        
        {/* Active Requests Table */}
        <Card>
          <CardHeader>
            <CardTitle>Active Requests</CardTitle>
            <CardDescription>Currently processing requests</CardDescription>
          </CardHeader>
          <CardContent>
            <ActiveRequestsTable requests={activeRequests} />
          </CardContent>
        </Card>
        
        {/* Error Rate Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Error Rate Trends</CardTitle>
            <CardDescription>Error rate over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ErrorRateChart data={errorRates} />
          </CardContent>
        </Card>
        
        {/* Response Time Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Response Time Trends</CardTitle>
            <CardDescription>Response time percentiles</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponseTimeChart data={responseTimes} />
          </CardContent>
        </Card>
      </div>
      
      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Latest system alerts and notifications</CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent alerts</p>
          ) : (
            <div className="space-y-3">
              {alerts.slice(0, 5).map(alert => (
                <Alert 
                  key={alert.id}
                  variant={alert.severity === 'critical' ? 'destructive' : 'default'}
                >
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>{alert.title}</AlertTitle>
                  <AlertDescription>
                    {alert.message}
                    <div className="text-xs text-muted-foreground mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Notification Toast - Simple implementation */}
      {notification.open && (
        <div className="fixed bottom-4 right-4 z-50">
          <Alert variant={notification.severity === 'error' ? 'destructive' : 'default'}>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{notification.message}</AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  );
};

export default MonitoringPage;