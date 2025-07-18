import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
// Removed unused Alert imports
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Server,
  Zap
} from 'lucide-react';
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
  // Remove unused variable to fix ESLint warning
  // const { user } = useAuth();
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
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <Badge variant="outline" className="text-sm">
          <Activity className="w-4 h-4 mr-1" />
          Live Data
        </Badge>
      </div>

      {/* Quick Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Badge variant={systemHealth.status === 'healthy' ? 'default' : 'destructive'}>
                {systemHealth.status === 'healthy' ? (
                  <CheckCircle className="w-3 h-3 mr-1" />
                ) : (
                  <AlertTriangle className="w-3 h-3 mr-1" />
                )}
                {systemHealth.status}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Uptime: {systemHealth.uptime}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metricsOverview.totalRequests.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metricsOverview.requestsTrend === 'up' ? (
                <TrendingUp className="w-3 h-3 mr-1 text-green-500" />
              ) : metricsOverview.requestsTrend === 'down' ? (
                <TrendingDown className="w-3 h-3 mr-1 text-red-500" />
              ) : null}
              {metricsOverview.requestsToday} today
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metricsOverview.errorRate}%</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metricsOverview.errorTrend === 'down' ? (
                <TrendingDown className="w-3 h-3 mr-1 text-green-500" />
              ) : metricsOverview.errorTrend === 'up' ? (
                <TrendingUp className="w-3 h-3 mr-1 text-red-500" />
              ) : null}
              Success: {metricsOverview.successRate}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metricsOverview.activeUsers}</div>
            <p className="text-xs text-muted-foreground">
              Peak: {metricsOverview.peakHour}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* System Health Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Server className="w-5 h-5 mr-2" />
              System Health
            </CardTitle>
            <CardDescription>Current system performance and resource usage</CardDescription>
          </CardHeader>
          <CardContent>
            <SystemHealthCard health={systemHealth} />
          </CardContent>
        </Card>

        {/* Metrics Overview Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Performance Metrics
            </CardTitle>
            <CardDescription>Key performance indicators and trends</CardDescription>
          </CardHeader>
          <CardContent>
            <MetricsOverviewCard metrics={metricsOverview} />
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              Active Alerts
              <Badge variant="destructive" className="ml-2">
                {alerts.length}
              </Badge>
            </CardTitle>
            <CardDescription>System alerts requiring attention</CardDescription>
          </CardHeader>
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
        <CardHeader>
          <CardTitle className="flex items-center">
            <Zap className="w-5 h-5 mr-2" />
            Service Status
          </CardTitle>
          <CardDescription>Status and performance of all system services</CardDescription>
        </CardHeader>
        <CardContent>
          <ServiceStatusGrid
            services={serviceDetails}
            onRefreshService={handleRefreshService}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage;