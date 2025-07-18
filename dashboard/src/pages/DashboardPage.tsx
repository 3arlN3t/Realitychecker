import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Chip,
  Divider,
  Paper
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  People as PeopleIcon,
  Storage as StorageIcon,
  Bolt as BoltIcon
} from '@mui/icons-material';

import SystemHealthCard, { SystemHealth } from '../components/admin/SystemHealthCard';
import MetricsOverviewCard, { MetricsOverview } from '../components/admin/MetricsOverviewCard';
import ActiveAlertsCard, { Alert as AlertType } from '../components/admin/ActiveAlertsCard';
import ServiceStatusGrid, { ServiceDetails } from '../components/admin/ServiceStatusGrid';

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
  const [systemHealth, setSystemHealth] = useState<SystemHealth>(generateSystemHealth());
  const [metricsOverview, setMetricsOverview] = useState<MetricsOverview>(generateMetricsOverview());
  const [alerts, setAlerts] = useState<AlertType[]>(generateAlerts());
  const [serviceDetails, setServiceDetails] = useState<Record<string, ServiceDetails>>(generateServiceDetails());

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemHealth(generateSystemHealth());
      setMetricsOverview(generateMetricsOverview());
      setAlerts(generateAlerts());
      setServiceDetails(generateServiceDetails());
    }, 10000); // Update every 10 seconds

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

  const handleRefreshService = (serviceName: string) => {
    // Simulate service refresh
    setServiceDetails(prev => ({
      ...prev,
      [serviceName]: {
        ...prev[serviceName],
        lastCheck: new Date().toISOString(),
        status: Math.random() > 0.8 ? 'warning' : 'healthy',
        responseTime: Math.floor(Math.random() * 500) + 100,
      },
    }));
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Chip
          icon={<TimelineIcon />}
          label="Live Data"
          variant="outlined"
          color="primary"
        />
      </Box>

      {/* Quick Stats Overview */}
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
                icon={systemHealth.status === 'healthy' ? <CheckCircleIcon /> : <WarningIcon />}
                label={systemHealth.status}
                color={systemHealth.status === 'healthy' ? 'success' : 'error'}
                size="small"
              />
            </Box>
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              Uptime: {systemHealth.uptime}
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
            <Typography variant="h5">{metricsOverview.totalRequests.toLocaleString()}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {metricsOverview.requestsTrend === 'up' ? (
                <TrendingUpIcon fontSize="small" color="success" />
              ) : metricsOverview.requestsTrend === 'down' ? (
                <TrendingDownIcon fontSize="small" color="error" />
              ) : null}
              <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                {metricsOverview.requestsToday} today
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
            <Typography variant="h5">{metricsOverview.errorRate}%</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {metricsOverview.errorTrend === 'down' ? (
                <TrendingDownIcon fontSize="small" color="success" />
              ) : metricsOverview.errorTrend === 'up' ? (
                <TrendingUpIcon fontSize="small" color="error" />
              ) : null}
              <Typography variant="caption" color="textSecondary" sx={{ ml: 0.5 }}>
                Success: {metricsOverview.successRate}%
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
            <Typography variant="h5">{metricsOverview.activeUsers}</Typography>
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              Peak: {metricsOverview.peakHour}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Main Content Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
        {/* System Health Card */}
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 1 }} />
                <Typography variant="h6">System Health</Typography>
              </Box>
            }
            subheader="Current system performance and resource usage"
          />
          <CardContent>
            <SystemHealthCard health={systemHealth} />
          </CardContent>
        </Card>

        {/* Metrics Overview Card */}
        <Card>
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
            <MetricsOverviewCard metrics={metricsOverview} />
          </CardContent>
        </Card>
      </Box>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <WarningIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Active Alerts
                  <Chip
                    label={alerts.length}
                    color="error"
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Typography>
              </Box>
            }
            subheader="System alerts requiring attention"
          />
          <CardContent>
            <ActiveAlertsCard
              alerts={alerts}
              onAcknowledgeAlert={handleAcknowledgeAlert}
              onDismissAlert={handleDismissAlert}
              maxDisplayed={5}
            />
          </CardContent>
        </Card>
      )}

      {/* Service Status Grid */}
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <BoltIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Service Status</Typography>
            </Box>
          }
          subheader="Status and performance of all system services"
        />
        <CardContent>
          <ServiceStatusGrid
            services={serviceDetails}
            onRefreshService={handleRefreshService}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default DashboardPage;