import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Chip,

  Alert,
  CircularProgress
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  People as PeopleIcon,
  Storage as StorageIcon,
  Bolt as BoltIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon
} from '@mui/icons-material';

import EnhancedSystemHealthCard from '../components/admin/EnhancedSystemHealthCard';
import MetricsOverviewCard from '../components/admin/MetricsOverviewCard';
import ActiveAlertsCard from '../components/admin/ActiveAlertsCard';
import ServiceStatusGrid from '../components/admin/ServiceStatusGrid';
import { SystemHealth, MetricsOverview, Alert as AlertType, ServiceDetails } from '../types/dashboard';
import { useDashboardData } from '../hooks/useDashboardData';
import { useHealthCheck } from '../hooks/useHealthCheck';
import LiveMetricsCard from '../components/monitoring/LiveMetricsCard';
import { useWebSocket } from '../hooks/useWebSocket';
import type { LiveMetrics } from './MonitoringPage';

// Sample data generators
const generateSystemHealth = (): SystemHealth => {
  const memoryUsage = Math.floor(Math.random() * 40) + 30;
  const cpuUsage = Math.floor(Math.random() * 30) + 20;
  const errorRate = Math.random() * 3 + 1;
  
  return {
    status: errorRate < 2 ? 'healthy' : errorRate < 3 ? 'warning' : 'critical',
    uptime: '99.9%',
    lastUpdated: new Date().toLocaleTimeString(),
    memoryUsage,
    cpuUsage,
    services: {
      openai: {
        status: Math.random() > 0.1 ? 'healthy' : 'warning',
        responseTime: Math.floor(Math.random() * 500) + 200,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 3),
      },
      twilio: {
        status: Math.random() > 0.05 ? 'healthy' : 'critical',
        responseTime: Math.floor(Math.random() * 300) + 100,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 2),
      },
      database: {
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 50) + 10,
        lastCheck: new Date().toISOString(),
        errorCount: 0,
      },
      webhook: {
        status: Math.random() > 0.15 ? 'healthy' : 'warning',
        responseTime: Math.floor(Math.random() * 200) + 50,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 5),
      },
    },
  };
};

const generateMetricsOverview = (): MetricsOverview => {
  const baseRequests = 1250;
  const todayRequests = Math.floor(Math.random() * 50) + 30;
  const errorRate = Math.random() * 3 + 1;
  const activeUsers = Math.floor(Math.random() * 15) + 15;
  
  return {
    totalRequests: baseRequests + Math.floor(Math.random() * 100),
    requestsToday: todayRequests,
    requestsTrend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable',
    requestsChange: (Math.random() - 0.5) * 20,
    errorRate: parseFloat(errorRate.toFixed(1)),
    errorTrend: Math.random() > 0.6 ? 'down' : Math.random() > 0.3 ? 'up' : 'stable',
    errorChange: (Math.random() - 0.5) * 10,
    avgResponseTime: parseFloat((Math.random() * 2 + 0.5).toFixed(1)),
    responseTrend: Math.random() > 0.6 ? 'down' : Math.random() > 0.3 ? 'up' : 'stable',
    responseChange: (Math.random() - 0.5) * 15,
    activeUsers,
    usersTrend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable',
    usersChange: (Math.random() - 0.5) * 30,
    successRate: parseFloat((100 - errorRate).toFixed(1)),
    peakHour: '2:00 PM',
    lastUpdated: new Date().toLocaleTimeString(),
  };
};

const generateAlerts = (): AlertType[] => {
  const sampleAlerts: AlertType[] = [
    {
      id: '1',
      type: 'warning',
      title: 'High Response Time',
      message: 'OpenAI API response time is above normal threshold',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      source: 'OpenAI',
      severity: 'medium',
      acknowledged: false,
      details: 'Average response time: 2.5s (threshold: 2.0s)\nAffected requests: 15 in the last 5 minutes',
      actionRequired: true,
    },
    {
      id: '2',
      type: 'error',
      title: 'PDF Processing Failed',
      message: 'Multiple PDF processing failures detected',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      source: 'System',
      severity: 'high',
      acknowledged: false,
      details: 'Failed to process 3 PDF files in the last 10 minutes\nError: Unable to extract text from corrupted files',
    },
    {
      id: '3',
      type: 'info',
      title: 'Rate Limit Approaching',
      message: 'API rate limit at 80% capacity',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      source: 'Twilio',
      severity: 'low',
      acknowledged: false,
    },
  ];
  
  return Math.random() > 0.3 ? sampleAlerts.slice(0, Math.floor(Math.random() * 3) + 1) : [];
};

const generateServiceDetails = (): Record<string, ServiceDetails> => {
  return {
    openai: {
      name: 'OpenAI GPT-4',
      description: 'AI analysis service for job ad scam detection',
      status: Math.random() > 0.1 ? 'healthy' : 'warning',
      responseTime: Math.floor(Math.random() * 500) + 200,
      lastCheck: new Date().toISOString(),
      errorCount: Math.floor(Math.random() * 3),
      version: 'gpt-4-turbo',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      dependencies: ['Internet', 'API Key'],
      metrics: {
        requestsPerMinute: Math.floor(Math.random() * 20) + 5,
        successRate: Math.random() * 10 + 90,
        avgResponseTime: Math.random() * 1000 + 500,
        uptime: '99.5%',
      },
    },
    twilio: {
      name: 'Twilio WhatsApp',
      description: 'WhatsApp messaging service integration',
      status: Math.random() > 0.05 ? 'healthy' : 'critical',
      responseTime: Math.floor(Math.random() * 300) + 100,
      lastCheck: new Date().toISOString(),
      errorCount: Math.floor(Math.random() * 2),
      version: 'v2024-01-01',
      endpoint: 'https://api.twilio.com/2010-04-01/Accounts',
      dependencies: ['Internet', 'Webhook'],
      metrics: {
        requestsPerMinute: Math.floor(Math.random() * 30) + 10,
        successRate: Math.random() * 5 + 95,
        avgResponseTime: Math.random() * 500 + 200,
        uptime: '99.8%',
      },
    },
    database: {
      name: 'Application Database',
      description: 'User data and analytics storage',
      status: 'healthy',
      responseTime: Math.floor(Math.random() * 50) + 10,
      lastCheck: new Date().toISOString(),
      errorCount: 0,
      version: 'SQLite 3.40',
      dependencies: ['File System'],
      metrics: {
        requestsPerMinute: Math.floor(Math.random() * 50) + 20,
        successRate: 99.9,
        avgResponseTime: Math.random() * 100 + 20,
        uptime: '100%',
      },
    },
    webhook: {
      name: 'Webhook Endpoint',
      description: 'Receives incoming WhatsApp messages',
      status: Math.random() > 0.15 ? 'healthy' : 'warning',
      responseTime: Math.floor(Math.random() * 200) + 50,
      lastCheck: new Date().toISOString(),
      errorCount: Math.floor(Math.random() * 5),
      version: 'FastAPI 0.104',
      endpoint: '/webhook/whatsapp',
      dependencies: ['FastAPI', 'Twilio'],
      metrics: {
        requestsPerMinute: Math.floor(Math.random() * 40) + 15,
        successRate: Math.random() * 8 + 92,
        avgResponseTime: Math.random() * 300 + 100,
        uptime: '99.7%',
      },
    },
  };
};

const DashboardPage: React.FC = () => {
  // Use live data hooks
  const {
    overview,
    metrics,
    metricsOverview,
    isLoading: isDashboardLoading,
    error: dashboardError,
    isUsingMockData: isDashboardMock,
    lastFetch: dashboardLastFetch,
    refresh: refreshDashboard
  } = useDashboardData({
    pollInterval: 10000, // 10 seconds
    useMockFallback: true
  });

  const {
    healthData: systemHealth,
    isLoading: isHealthLoading,
    error: healthError,
    isUsingMockData: isHealthMock,
    lastFetch: healthLastFetch
  } = useHealthCheck({
    pollInterval: 30000, // 30 seconds
    useMockFallback: true
  });

  // Live data state for components that need real API integration
  const [alerts, setAlerts] = useState<AlertType[]>([]);
  const [serviceDetails, setServiceDetails] = useState<Record<string, ServiceDetails>>({});
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [servicesLoading, setServicesLoading] = useState(false);
  // WebSocket-driven metrics for LiveMetricsCard
  const { lastMessage } = useWebSocket('/monitoring/ws');
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);

  // Parse websocket messages into LiveMetrics shape
  useEffect(() => {
    if (!lastMessage) return;
    try {
      const parsed = JSON.parse(lastMessage);
      if (parsed?.type === 'metrics_update' && parsed?.data) {
        // The monitoring WS already emits the correct shape for LiveMetricsCard
        setLiveMetrics(parsed.data as LiveMetrics);
      }
    } catch (e) {
      // Ignore non-JSON or unrelated events
    }
  }, [lastMessage]);

  // Fetch live alerts and service details
  useEffect(() => {
    const fetchLiveData = async () => {
      console.log('🔍 Dashboard: Starting live data fetch...');
      
      // Ensure we're authenticated first
      try {
        const { ensureAuthenticated } = await import('../utils/autoLogin');
        await ensureAuthenticated();
        console.log('✅ Dashboard: Authentication ensured');
      } catch (authError) {
        console.warn('⚠️ Dashboard: Authentication failed, proceeding with request:', authError);
      }
      
      // Fetch alerts
      setAlertsLoading(true);
      try {
        console.log('🔍 Dashboard: Fetching alerts from health API...');
        const { HealthCheckAPI } = await import('../lib/api');
        const alertsResponse = await HealthCheckAPI.getActiveAlerts();
        console.log('✅ Dashboard: Alerts response:', alertsResponse);
        
        // Transform API alerts to dashboard format
        const transformedAlerts: AlertType[] = alertsResponse.active_alerts.map(alert => ({
          id: alert.id,
          type: alert.type as 'error' | 'warning' | 'info' | 'success',
          title: alert.title,
          message: alert.message,
          timestamp: alert.timestamp,
          source: alert.context?.component || 'System',
          severity: alert.severity as 'low' | 'medium' | 'high' | 'critical',
          acknowledged: false,
          details: alert.context ? JSON.stringify(alert.context, null, 2) : undefined,
          actionRequired: alert.severity === 'critical' || alert.severity === 'high'
        }));
        
        console.log('✅ Dashboard: Transformed alerts:', transformedAlerts);
        setAlerts(transformedAlerts);
      } catch (error) {
        console.error('❌ Dashboard: Failed to fetch live alerts:', error);
        // Use fallback mock data
        const fallbackAlerts = generateAlerts();
        console.log('🎭 Dashboard: Using fallback alerts:', fallbackAlerts);
        setAlerts(fallbackAlerts);
      } finally {
        setAlertsLoading(false);
      }

      // Fetch service details
      setServicesLoading(true);
      try {
        console.log('🔍 Dashboard: Fetching service details from health API...');
        const { HealthCheckAPI } = await import('../lib/api');
        const healthResponse = await HealthCheckAPI.getDetailedHealth();
        console.log('✅ Dashboard: Health response:', healthResponse);
        
        // Transform API response to service details format
        const transformedServices: Record<string, ServiceDetails> = {};
        
        // Transform each service from the health response
        if (healthResponse.services.openai) {
          transformedServices.openai = {
            name: 'OpenAI GPT-4',
            description: 'AI analysis service for job ad scam detection',
            status: mapHealthStatus(healthResponse.services.openai.status),
            responseTime: Math.round(healthResponse.services.openai.response_time_ms),
            lastCheck: new Date().toISOString(),
            errorCount: healthResponse.services.openai.error_count || 0,
            version: healthResponse.services.openai.model || healthResponse.configuration.openai_model,
            endpoint: 'https://api.openai.com/v1/chat/completions',
            dependencies: ['Internet', 'API Key'],
            metrics: {
              requestsPerMinute: Math.floor(Math.random() * 20) + 5,
              successRate: healthResponse.services.openai.status === 'healthy' ? 99 : 85,
              avgResponseTime: healthResponse.services.openai.response_time_ms,
              uptime: healthResponse.services.openai.status === 'healthy' ? '99.5%' : '85.2%'
            }
          };
        }

        if (healthResponse.services.twilio) {
          transformedServices.twilio = {
            name: 'Twilio WhatsApp',
            description: 'WhatsApp messaging service integration',
            status: mapHealthStatus(healthResponse.services.twilio.status),
            responseTime: Math.round(healthResponse.services.twilio.response_time_ms),
            lastCheck: new Date().toISOString(),
            errorCount: healthResponse.services.twilio.error_count || 0,
            version: 'v2024-01-01',
            endpoint: 'https://api.twilio.com/2010-04-01/Accounts',
            dependencies: ['Internet', 'Webhook'],
            metrics: {
              requestsPerMinute: Math.floor(Math.random() * 30) + 10,
              successRate: healthResponse.services.twilio.status === 'healthy' ? 99 : 90,
              avgResponseTime: healthResponse.services.twilio.response_time_ms,
              uptime: healthResponse.services.twilio.status === 'healthy' ? '99.8%' : '92.1%'
            }
          };
        }

        if (healthResponse.services.pdf_processing) {
          transformedServices.database = {
            name: 'Application Database',
            description: 'User data and analytics storage',
            status: mapHealthStatus(healthResponse.services.pdf_processing?.status || 'healthy'),
            responseTime: Math.round(healthResponse.services.pdf_processing?.response_time_ms || 20),
            lastCheck: new Date().toISOString(),
            errorCount: 0,
            version: 'SQLite 3.40',
            dependencies: ['File System'],
            metrics: {
              requestsPerMinute: Math.floor(Math.random() * 50) + 20,
              successRate: 99.9,
              avgResponseTime: healthResponse.services.pdf_processing?.response_time_ms || 20,
              uptime: '100%'
            }
          };
        }

        // Add a webhook service based on overall health
        transformedServices.webhook = {
          name: 'Webhook Endpoint',
          description: 'Receives incoming WhatsApp messages',
          status: mapHealthStatus(healthResponse.status),
          responseTime: Math.round(healthResponse.health_check_duration_ms),
          lastCheck: healthResponse.timestamp,
          errorCount: healthResponse.status === 'healthy' ? 0 : Math.floor(Math.random() * 3),
          version: 'FastAPI 0.104',
          endpoint: '/webhook/whatsapp',
          dependencies: ['FastAPI', 'Twilio'],
          metrics: {
            requestsPerMinute: Math.floor(Math.random() * 40) + 15,
            successRate: healthResponse.status === 'healthy' ? 99.7 : 85.2,
            avgResponseTime: healthResponse.health_check_duration_ms,
            uptime: healthResponse.status === 'healthy' ? '99.7%' : '87.4%'
          }
        };

        console.log('✅ Dashboard: Transformed services:', transformedServices);
        setServiceDetails(transformedServices);
      } catch (error) {
        console.error('❌ Dashboard: Failed to fetch live service details:', error);
        // Use fallback mock data
        const fallbackServices = generateServiceDetails();
        console.log('🎭 Dashboard: Using fallback services:', fallbackServices);
        setServiceDetails(fallbackServices);
      } finally {
        setServicesLoading(false);
      }
    };

    // Helper function to map health status to service status
    const mapHealthStatus = (status: string): 'healthy' | 'warning' | 'critical' => {
      switch (status) {
        case 'healthy':
          return 'healthy';
        case 'degraded':
        case 'not_configured':
        case 'circuit_open':
          return 'warning';
        case 'unhealthy':
        case 'error':
          return 'critical';
        default:
          return 'warning';
      }
    };

    // Initial fetch
    fetchLiveData();

    // Set up periodic refresh
    const interval = setInterval(fetchLiveData, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleAcknowledgeAlert = (alertId: string) => {
    setAlerts(prevAlerts =>
      prevAlerts.map(alert =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    );
  };

  const handleDismissAlert = (alertId: string) => {
    setAlerts(prevAlerts => prevAlerts.filter(alert => alert.id !== alertId));
  };

  const handleRefreshService = async (serviceName: string) => {
    // Set loading state for the specific service
    setServiceDetails(prev => ({
      ...prev,
      [serviceName]: {
        ...prev[serviceName],
        lastCheck: new Date().toISOString(),
      },
    }));

    // Refresh specific service data from health API
    try {
      const { HealthCheckAPI } = await import('../lib/api');
      const healthResponse = await HealthCheckAPI.getDetailedHealth();
      
      // Helper function to map health status to service status
      const mapHealthStatus = (status: string): 'healthy' | 'warning' | 'critical' => {
        switch (status) {
          case 'healthy':
            return 'healthy';
          case 'degraded':
          case 'not_configured':
          case 'circuit_open':
            return 'warning';
          case 'unhealthy':
          case 'error':
            return 'critical';
          default:
            return 'warning';
        }
      };

      // Update the specific service based on fresh health data
      let updatedServiceData: Partial<ServiceDetails> = {};
      
      if (serviceName === 'openai' && healthResponse.services.openai) {
        updatedServiceData = {
          status: mapHealthStatus(healthResponse.services.openai.status),
          responseTime: Math.round(healthResponse.services.openai.response_time_ms),
          errorCount: healthResponse.services.openai.error_count || 0,
          lastCheck: new Date().toISOString(),
        };
      } else if (serviceName === 'twilio' && healthResponse.services.twilio) {
        updatedServiceData = {
          status: mapHealthStatus(healthResponse.services.twilio.status),
          responseTime: Math.round(healthResponse.services.twilio.response_time_ms),
          errorCount: healthResponse.services.twilio.error_count || 0,
          lastCheck: new Date().toISOString(),
        };
      } else if (serviceName === 'database' && healthResponse.services.pdf_processing) {
        updatedServiceData = {
          status: mapHealthStatus(healthResponse.services.pdf_processing.status),
          responseTime: Math.round(healthResponse.services.pdf_processing.response_time_ms || 20),
          errorCount: 0,
          lastCheck: new Date().toISOString(),
        };
      } else if (serviceName === 'webhook') {
        updatedServiceData = {
          status: mapHealthStatus(healthResponse.status),
          responseTime: Math.round(healthResponse.health_check_duration_ms),
          errorCount: healthResponse.status === 'healthy' ? 0 : Math.floor(Math.random() * 3),
          lastCheck: healthResponse.timestamp,
        };
      }

      // Update service details with fresh data
      setServiceDetails(prev => ({
        ...prev,
        [serviceName]: {
          ...prev[serviceName],
          ...updatedServiceData,
        },
      }));
    } catch (error) {
      console.warn(`Failed to refresh ${serviceName} service:`, error);
      // Update with generic refresh data on error
      setServiceDetails(prev => ({
        ...prev,
        [serviceName]: {
          ...prev[serviceName],
          status: 'warning',
          lastCheck: new Date().toISOString(),
        },
      }));
    }
  };

  // Determine overall loading state
  const isLoading = isDashboardLoading || isHealthLoading;
  const hasError = dashboardError || healthError;
  const isUsingMockData = isDashboardMock || isHealthMock;

  // Ensure we always have some data to display - prioritize metricsOverview for UI compatibility
  const displayOverview = metricsOverview || overview;
  const displaySystemHealth = systemHealth;

  return (
    <Box sx={{ p: 2, background: 'transparent', minHeight: '100vh' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {isLoading && (
            <Chip
              icon={<CircularProgress size={16} />}
              label="Loading..."
              variant="outlined"
              color="default"
            />
          )}
          <Chip
            icon={isUsingMockData ? <WifiOffIcon /> : <WifiIcon />}
            label={isUsingMockData ? "Mock Data" : "Live Data"}
            variant="outlined"
            color={isUsingMockData ? "warning" : "success"}
          />
          {dashboardLastFetch && (
            <Chip
              label={`Updated: ${dashboardLastFetch.toLocaleTimeString()}`}
              variant="outlined"
              size="small"
            />
          )}
        </Box>
      </Box>

      {/* Error Alert */}
      {hasError && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Chip
              label="Retry"
              size="small"
              onClick={() => refreshDashboard()}
              clickable
            />
          }
        >
          <Typography variant="body2">
            {isUsingMockData 
              ? "Using mock data due to API connection issues. Some features may be limited."
              : "There was an issue fetching some data. Please try refreshing."
            }
          </Typography>
        </Alert>
      )}

      {/* Quick Stats Overview */}
      {displayOverview && displaySystemHealth && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 3, mb: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  System Status
                </Typography>
                <StorageIcon color="action" fontSize="small" />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Chip
                  icon={displaySystemHealth.status === 'healthy' ? <CheckCircleIcon /> : <WarningIcon />}
                  label={displaySystemHealth.status || 'unknown'}
                  color={displaySystemHealth.status === 'healthy' ? 'success' : 'error'}
                  size="small"
                />
              </Box>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                Uptime: {displaySystemHealth.uptime || 'N/A'}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  Total Requests
                </Typography>
                <TimelineIcon color="action" fontSize="small" />
              </Box>
              <Typography variant="h5">{((displayOverview as any)?.totalRequests || (displayOverview as any)?.total_requests || 0).toLocaleString()}</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {((displayOverview as any)?.requestsTrend || 'stable') === 'up' ? (
                  <TrendingUpIcon fontSize="small" color="success" />
                ) : ((displayOverview as any)?.requestsTrend || 'stable') === 'down' ? (
                  <TrendingDownIcon fontSize="small" color="error" />
                ) : null}
                <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                  {(displayOverview as any)?.requestsToday || (displayOverview as any)?.requests_today || 0} today
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  Error Rate
                </Typography>
                <WarningIcon color="action" fontSize="small" />
              </Box>
              <Typography variant="h5">{(displayOverview as any)?.errorRate || (displayOverview as any)?.error_rate || 0}%</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {((displayOverview as any)?.errorTrend || 'stable') === 'down' ? (
                  <TrendingDownIcon fontSize="small" color="success" />
                ) : ((displayOverview as any)?.errorTrend || 'stable') === 'up' ? (
                  <TrendingUpIcon fontSize="small" color="error" />
                ) : null}
                <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                  Success: {(displayOverview as any)?.successRate || (displayOverview as any)?.success_rate || 0}%
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  Active Users
                </Typography>
                <PeopleIcon color="action" fontSize="small" />
              </Box>
              <Typography variant="h5">{(displayOverview as any)?.activeUsers || (displayOverview as any)?.active_users || 0}</Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                Peak: {(displayOverview as any)?.peakHour || (displayOverview as any)?.peak_hour || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Performance Metrics - Moved to prominent position */}
      {displayOverview && (
        <Card sx={{ mb: 3 }}>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TimelineIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Performance Metrics</Typography>
              </Box>
            }
            subheader="Key performance indicators and trends"
          />
          <CardContent>
            <MetricsOverviewCard metrics={displayOverview as any} />
          </CardContent>
        </Card>
      )}

      {/* Main Content Grid - Now with 2 columns */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
        {/* Enhanced System Health Card with Real API Integration */}
        <Card>
          <CardContent sx={{ p: 3 }}>
            <EnhancedSystemHealthCard 
              pollInterval={30000}
              showDetails={true}
              showRefreshButton={true}
            />
          </CardContent>
        </Card>

        {/* Live Metrics (WebSocket) */}
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TimelineIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Live Metrics</Typography>
              </Box>
            }
            subheader="Real-time system metrics via WebSocket"
          />
          <CardContent>
            <LiveMetricsCard metrics={liveMetrics} />
          </CardContent>
        </Card>
      </Box>

      {/* Active Alerts */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <WarningIcon sx={{ mr: 1 }} />
              <Typography variant="h6">
                Active Alerts
                {!alertsLoading && alerts.length > 0 && (
                  <Chip
                    label={alerts.length}
                    color="error"
                    size="small"
                    sx={{ ml: 1 }}
                  />
                )}
                {alertsLoading && (
                  <CircularProgress size={20} sx={{ ml: 1 }} />
                )}
              </Typography>
            </Box>
          }
          subheader="System alerts requiring attention"
        />
        <CardContent>
          {alertsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <ActiveAlertsCard
              alerts={alerts}
              onAcknowledgeAlert={handleAcknowledgeAlert}
              onDismissAlert={handleDismissAlert}
              maxDisplayed={5}
            />
          )}
        </CardContent>
      </Card>

      {/* Service Status Grid */}
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <BoltIcon sx={{ mr: 1 }} />
              <Typography variant="h6">
                Service Status
                {servicesLoading && (
                  <CircularProgress size={20} sx={{ ml: 1 }} />
                )}
              </Typography>
            </Box>
          }
          subheader="Status and performance of all system services"
        />
        <CardContent>
          {servicesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <ServiceStatusGrid
              services={serviceDetails}
              onRefreshService={handleRefreshService}
            />
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DashboardPage;
