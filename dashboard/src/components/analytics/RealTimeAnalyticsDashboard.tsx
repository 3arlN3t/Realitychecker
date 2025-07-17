/**
 * Real-time Analytics Dashboard component for Reality Checker.
 * 
 * Provides comprehensive real-time analytics with:
 * - Live metric updates
 * - Interactive data visualization
 * - Performance monitoring
 * - Alert system integration
 * - Business intelligence insights
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Alert,
  Chip,
  Button,
  Switch,
  FormControlLabel,
  Tooltip,
  IconButton,
  Badge,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tabs,
  Tab,
  CircularProgress
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Speed as SpeedIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  ShowChart as ShowChartIcon,
  Autorenew as AutorenewIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface RealTimeMetric {
  name: string;
  value: number | string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  unit?: string;
  target?: number;
  status?: 'healthy' | 'warning' | 'critical';
  lastUpdated: string;
}

interface AlertItem {
  id: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
  acknowledged: boolean;
}

interface PerformanceData {
  timestamp: string;
  responseTime: number;
  throughput: number;
  errorRate: number;
  activeUsers: number;
}

interface InsightItem {
  id: string;
  title: string;
  description: string;
  type: 'anomaly' | 'trend' | 'prediction' | 'correlation';
  confidence: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  recommendation: string;
}

const RealTimeAnalyticsDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Real-time data state
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetric[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'warning' | 'critical'>('healthy');

  // Mock data generation (in a real app, this would come from API)
  const generateMockData = useCallback(() => {
    const now = new Date();
    
    // Generate real-time metrics
    const metrics: RealTimeMetric[] = [
      {
        name: 'Active Users',
        value: Math.floor(Math.random() * 50) + 80,
        trend: Math.random() > 0.5 ? 'up' : 'down',
        trendValue: Math.random() * 10,
        unit: 'users',
        target: 100,
        status: 'healthy',
        lastUpdated: now.toISOString()
      },
      {
        name: 'Response Time',
        value: Number((Math.random() * 2 + 0.5).toFixed(2)),
        trend: Math.random() > 0.6 ? 'down' : 'up',
        trendValue: Math.random() * 0.5,
        unit: 's',
        target: 1.0,
        status: Math.random() > 0.8 ? 'warning' : 'healthy',
        lastUpdated: now.toISOString()
      },
      {
        name: 'Requests/Min',
        value: Math.floor(Math.random() * 200) + 150,
        trend: 'up',
        trendValue: Math.random() * 20,
        unit: 'req/min',
        target: 200,
        status: 'healthy',
        lastUpdated: now.toISOString()
      },
      {
        name: 'Error Rate',
        value: Number((Math.random() * 2).toFixed(2)),
        trend: Math.random() > 0.7 ? 'down' : 'up',
        trendValue: Math.random() * 1,
        unit: '%',
        target: 1.0,
        status: Math.random() > 0.9 ? 'critical' : 'healthy',
        lastUpdated: now.toISOString()
      },
      {
        name: 'Success Rate',
        value: Number((95 + Math.random() * 4).toFixed(1)),
        trend: 'stable',
        trendValue: 0.1,
        unit: '%',
        target: 95,
        status: 'healthy',
        lastUpdated: now.toISOString()
      },
      {
        name: 'Classification Accuracy',
        value: Number((92 + Math.random() * 6).toFixed(1)),
        trend: 'up',
        trendValue: 0.5,
        unit: '%',
        target: 95,
        status: 'healthy',
        lastUpdated: now.toISOString()
      }
    ];

    // Generate performance data (last 20 data points)
    const performanceHistory: PerformanceData[] = Array.from({ length: 20 }, (_, i) => {
      const timestamp = new Date(now.getTime() - (19 - i) * 30000); // 30-second intervals
      return {
        timestamp: timestamp.toISOString(),
        responseTime: Math.random() * 2 + 0.5,
        throughput: Math.floor(Math.random() * 100) + 150,
        errorRate: Math.random() * 3,
        activeUsers: Math.floor(Math.random() * 30) + 70
      };
    });

    // Generate alerts
    const mockAlerts: AlertItem[] = [
      {
        id: '1',
        title: 'High Response Time Detected',
        description: 'Response time exceeded 2.5s threshold',
        severity: 'warning',
        timestamp: new Date(now.getTime() - 300000).toISOString(),
        acknowledged: false
      },
      {
        id: '2',
        title: 'Successful Classification Spike',
        description: 'Classification accuracy improved by 3%',
        severity: 'success',
        timestamp: new Date(now.getTime() - 600000).toISOString(),
        acknowledged: true
      }
    ];

    // Generate insights
    const mockInsights: InsightItem[] = [
      {
        id: '1',
        title: 'Peak Usage Pattern Detected',
        description: 'Unusual activity spike during off-peak hours',
        type: 'anomaly',
        confidence: 0.85,
        impact: 'medium',
        recommendation: 'Monitor capacity and consider scaling'
      },
      {
        id: '2',
        title: 'Classification Performance Trending Up',
        description: 'Consistent improvement in ML model accuracy',
        type: 'trend',
        confidence: 0.92,
        impact: 'high',
        recommendation: 'Document changes for future reference'
      }
    ];

    return { metrics, performanceHistory, mockAlerts, mockInsights };
  }, []);

  // Fetch real-time data
  const fetchRealTimeData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const { metrics, performanceHistory, mockAlerts, mockInsights } = generateMockData();
      
      setRealTimeMetrics(metrics);
      setPerformanceData(performanceHistory);
      setAlerts(mockAlerts);
      setInsights(mockInsights);
      
      // Determine system health based on metrics
      const criticalMetrics = metrics.filter(m => m.status === 'critical');
      const warningMetrics = metrics.filter(m => m.status === 'warning');
      
      if (criticalMetrics.length > 0) {
        setSystemHealth('critical');
      } else if (warningMetrics.length > 0) {
        setSystemHealth('warning');
      } else {
        setSystemHealth('healthy');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch real-time data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [generateMockData]);

  // Auto-refresh effect
  useEffect(() => {
    fetchRealTimeData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchRealTimeData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchRealTimeData]);

  // Metric card component
  const MetricCard: React.FC<{ metric: RealTimeMetric }> = ({ metric }) => {
    const getStatusColor = (status: string) => {
      switch (status) {
        case 'healthy': return 'success.main';
        case 'warning': return 'warning.main';
        case 'critical': return 'error.main';
        default: return 'text.primary';
      }
    };

    const getTrendIcon = (trend?: string) => {
      switch (trend) {
        case 'up': return <TrendingUpIcon color="success" fontSize="small" />;
        case 'down': return <TrendingDownIcon color="error" fontSize="small" />;
        case 'stable': return <TimelineIcon color="action" fontSize="small" />;
        default: return null;
      }
    };

    const getProgress = () => {
      if (typeof metric.value === 'number' && metric.target) {
        return Math.min((metric.value / metric.target) * 100, 100);
      }
      return undefined;
    };

    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Typography variant="body2" color="text.secondary">
              {metric.name}
            </Typography>
            <Box display="flex" alignItems="center" gap={0.5}>
              {getTrendIcon(metric.trend)}
              <Chip 
                size="small" 
                label={metric.status} 
                color={metric.status === 'healthy' ? 'success' : 
                       metric.status === 'warning' ? 'warning' : 'error'}
                variant="outlined"
              />
            </Box>
          </Box>
          
          <Typography 
            variant="h4" 
            component="div" 
            color={getStatusColor(metric.status || 'healthy')}
            fontWeight="bold"
          >
            {metric.value}{metric.unit}
          </Typography>
          
          {metric.trend && metric.trendValue && (
            <Box display="flex" alignItems="center" gap={1} mt={1}>
              <Typography variant="body2" color="text.secondary">
                {metric.trend === 'up' ? '+' : metric.trend === 'down' ? '-' : '±'}
                {metric.trendValue.toFixed(1)}{metric.unit} from last period
              </Typography>
            </Box>
          )}
          
          {getProgress() !== undefined && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="caption">Progress to target</Typography>
                <Typography variant="caption">{getProgress()?.toFixed(0)}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={getProgress()} 
                color={getProgress()! >= 90 ? 'success' : getProgress()! >= 70 ? 'warning' : 'error'}
              />
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  // Performance chart component
  const PerformanceChart: React.FC = () => {
    const chartData = performanceData.map(d => ({
      time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      responseTime: d.responseTime,
      throughput: d.throughput,
      errorRate: d.errorRate,
      activeUsers: d.activeUsers
    }));

    return (
      <Card>
        <CardHeader 
          title="Performance Trends" 
          subheader="Real-time system performance metrics"
          action={
            <Tooltip title="Last updated">
              <Typography variant="caption" color="text.secondary">
                {lastUpdated.toLocaleTimeString()}
              </Typography>
            </Tooltip>
          }
        />
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip />
              <Legend />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="responseTime" 
                stroke="#8884d8" 
                name="Response Time (s)"
                strokeWidth={2}
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="throughput" 
                stroke="#82ca9d" 
                name="Throughput (req/min)"
                strokeWidth={2}
              />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="errorRate" 
                stroke="#ff7c7c" 
                name="Error Rate (%)"
                strokeWidth={2}
              />
              <ReferenceLine yAxisId="left" y={2} stroke="red" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  };

  // Alerts panel component
  const AlertsPanel: React.FC = () => {
    const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged);

    return (
      <Card>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <NotificationsIcon />
              <span>System Alerts</span>
              {unacknowledgedAlerts.length > 0 && (
                <Badge badgeContent={unacknowledgedAlerts.length} color="error">
                  <WarningIcon />
                </Badge>
              )}
            </Box>
          }
        />
        <CardContent>
          {alerts.length === 0 ? (
            <Box textAlign="center" py={2}>
              <CheckCircleIcon color="success" sx={{ fontSize: 48, mb: 1 }} />
              <Typography variant="body1">No active alerts</Typography>
              <Typography variant="body2" color="text.secondary">
                System is operating normally
              </Typography>
            </Box>
          ) : (
            <List>
              {alerts.map((alert, index) => (
                <React.Fragment key={alert.id}>
                  <ListItem>
                    <ListItemIcon>
                      {alert.severity === 'error' && <ErrorIcon color="error" />}
                      {alert.severity === 'warning' && <WarningIcon color="warning" />}
                      {alert.severity === 'success' && <CheckCircleIcon color="success" />}
                      {alert.severity === 'info' && <NotificationsIcon color="info" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle2">{alert.title}</Typography>
                          {!alert.acknowledged && (
                            <Chip size="small" label="New" color="error" variant="outlined" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2">{alert.description}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(alert.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < alerts.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    );
  };

  // Insights panel component
  const InsightsPanel: React.FC = () => {
    const getInsightIcon = (type: string) => {
      switch (type) {
        case 'anomaly': return <WarningIcon />;
        case 'trend': return <TrendingUpIcon />;
        case 'prediction': return <AssessmentIcon />;
        case 'correlation': return <ShowChartIcon />;
        default: return <NotificationsIcon />;
      }
    };

    const getImpactColor = (impact: string) => {
      switch (impact) {
        case 'critical': return 'error';
        case 'high': return 'warning';
        case 'medium': return 'info';
        case 'low': return 'success';
        default: return 'default';
      }
    };

    return (
      <Card>
        <CardHeader title="AI-Powered Insights" subheader="Business intelligence and recommendations" />
        <CardContent>
          {insights.length === 0 ? (
            <Box textAlign="center" py={2}>
              <AssessmentIcon color="action" sx={{ fontSize: 48, mb: 1 }} />
              <Typography variant="body1">No insights available</Typography>
              <Typography variant="body2" color="text.secondary">
                Insights will appear as patterns are detected
              </Typography>
            </Box>
          ) : (
            <List>
              {insights.map((insight, index) => (
                <React.Fragment key={insight.id}>
                  <ListItem alignItems="flex-start">
                    <ListItemIcon>
                      {getInsightIcon(insight.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Typography variant="subtitle2">{insight.title}</Typography>
                          <Chip 
                            size="small" 
                            label={insight.impact} 
                            color={getImpactColor(insight.impact)}
                            variant="outlined"
                          />
                          <Chip 
                            size="small" 
                            label={`${(insight.confidence * 100).toFixed(0)}% confidence`}
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" paragraph>
                            {insight.description}
                          </Typography>
                          <Typography variant="body2" color="primary" fontStyle="italic">
                            💡 {insight.recommendation}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < insights.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Real-Time Analytics Dashboard
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <Chip 
              icon={
                systemHealth === 'healthy' ? <CheckCircleIcon /> :
                systemHealth === 'warning' ? <WarningIcon /> : <ErrorIcon />
              }
              label={`System Health: ${systemHealth.toUpperCase()}`}
              color={
                systemHealth === 'healthy' ? 'success' :
                systemHealth === 'warning' ? 'warning' : 'error'
              }
            />
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch 
                checked={autoRefresh} 
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto-refresh"
          />
          <Tooltip title="Refresh data">
            <IconButton onClick={fetchRealTimeData} disabled={isLoading}>
              {isLoading ? <CircularProgress size={24} /> : <RefreshIcon />}
            </IconButton>
          </Tooltip>
          <IconButton>
            <SettingsIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
          <Tab icon={<SpeedIcon />} label="Overview" />
          <Tab icon={<ShowChartIcon />} label="Performance" />
          <Tab icon={<PeopleIcon />} label="Users" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<AssessmentIcon />} label="Insights" />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      {currentTab === 0 && (
        <Box>
          {/* Key Metrics Grid */}
          <Grid container spacing={3} mb={4}>
            {realTimeMetrics.map((metric, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <MetricCard metric={metric} />
              </Grid>
            ))}
          </Grid>

          {/* Charts and Alerts */}
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <PerformanceChart />
            </Grid>
            <Grid item xs={12} lg={4}>
              <AlertsPanel />
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Performance Tab */}
      {currentTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <PerformanceChart />
          </Grid>
          {/* Additional performance charts would go here */}
        </Grid>
      )}

      {/* Users Tab */}
      {currentTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardHeader title="User Analytics" />
              <CardContent>
                <Typography>User analytics content would go here</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Security Tab */}
      {currentTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Security Monitoring" />
              <CardContent>
                <Typography>Security monitoring content would go here</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Insights Tab */}
      {currentTab === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <InsightsPanel />
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default RealTimeAnalyticsDashboard;