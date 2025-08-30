import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Paper,

  Alert,
  CircularProgress
} from '@mui/material';
import {
  BarChart as BarChart3Icon,
  TrendingUp as TrendingUpIcon,
  People as UsersIcon,
  Schedule as ClockIcon,
  GpsFixed as TargetIcon,
  Timeline as ActivityIcon,
  CheckCircle as CheckCircleIcon,
  Error as AlertCircleIcon,
  Info as InfoIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import ClassificationChart from '../components/analytics/ClassificationChart';
import UsageTrendsChart from '../components/analytics/UsageTrendsChart';
import PeakHoursChart from '../components/analytics/PeakHoursChart';
import UserEngagementMetrics from '../components/analytics/UserEngagementMetrics';
import PeriodSelector from '../components/analytics/PeriodSelector';
import { 
  ClassificationData, 
  UsageTrendData, 
  PeakHourData, 
  UserEngagementData,
  PeriodType
} from '../components/analytics/types';
import { useAnalyticsData } from '../hooks/useAnalyticsData';

// Sample analytics data
const generateAnalyticsData = (period: PeriodType) => {
  // Classification data
  const classifications: ClassificationData[] = [
    { name: 'Legitimate', value: Math.floor(Math.random() * 200) + 500, color: '#4caf50' },
    { name: 'Suspicious', value: Math.floor(Math.random() * 100) + 200, color: '#ff9800' },
    { name: 'Likely Scam', value: Math.floor(Math.random() * 80) + 100, color: '#f44336' },
    { name: 'Inconclusive', value: Math.floor(Math.random() * 50) + 50, color: '#9e9e9e' },
  ];
  
  // Usage trends data
  const usageTrends: UsageTrendData[] = [];
  const now = new Date();
  
  // Generate different data points based on selected period
  let dataPoints = 0;
  let timeIncrement = 0;
  
  switch(period) {
    case 'day':
      dataPoints = 24;
      timeIncrement = 60 * 60 * 1000; // 1 hour
      break;
    case 'week':
      dataPoints = 7;
      timeIncrement = 24 * 60 * 60 * 1000; // 1 day
      break;
    case 'month':
      dataPoints = 30;
      timeIncrement = 24 * 60 * 60 * 1000; // 1 day
      break;
    case 'year':
      dataPoints = 12;
      timeIncrement = 30 * 24 * 60 * 60 * 1000; // ~30 days
      break;
  }
  
  for (let i = 0; i < dataPoints; i++) {
    const date = new Date(now.getTime() - (dataPoints - i - 1) * timeIncrement);
    usageTrends.push({
      date: date.toISOString(),
      count: Math.floor(Math.random() * 50) + 20
    });
  }
  
  // Peak hours data
  const peakHours: PeakHourData[] = [];
  for (let hour = 0; hour < 24; hour++) {
    // Create a realistic distribution with peak during business hours
    let baseCount = 10;
    if (hour >= 9 && hour <= 17) {
      baseCount = 30; // Higher during business hours
    }
    if (hour >= 12 && hour <= 14) {
      baseCount = 45; // Peak during lunch hours
    }
    
    peakHours.push({
      hour,
      count: Math.floor(Math.random() * 20) + baseCount
    });
  }
  
  // User engagement metrics
  const userEngagement: UserEngagementData[] = [
    { 
      metric: 'Daily Active Users', 
      value: Math.floor(Math.random() * 20) + 40,
      change: Math.floor(Math.random() * 10) + 5
    },
    { 
      metric: 'Average Session Time', 
      value: `${(Math.random() * 5 + 3).toFixed(1)} min`,
      change: Math.floor(Math.random() * 15) - 5
    },
    { 
      metric: 'Return Rate', 
      value: `${Math.floor(Math.random() * 15) + 70}%`,
      change: Math.floor(Math.random() * 8) + 2
    },
    { 
      metric: 'New Users', 
      value: Math.floor(Math.random() * 15) + 10,
      change: Math.floor(Math.random() * 20) + 10
    },
    { 
      metric: 'Avg. Requests per User', 
      value: (Math.random() * 2 + 1.5).toFixed(1),
      change: Math.floor(Math.random() * 10) - 3
    }
  ];
  
  return {
    classifications,
    usageTrends,
    peakHours,
    userEngagement,
    classificationAccuracy: Math.floor(Math.random() * 10) + 85, // 85-95%
    totalAnalyses: Math.floor(Math.random() * 500) + 2500,
    weeklyGrowth: (Math.random() * 20 + 5).toFixed(1), // 5-25%
    systemPerformance: {
      avgResponseTime: (Math.random() * 0.8 + 0.5).toFixed(2), // 0.5-1.3s
      successRate: (Math.random() * 5 + 95).toFixed(1), // 95-100%
      uptime: (Math.random() * 0.5 + 99.5).toFixed(2), // 99.5-100%
    }
  };
};

const AnalyticsPage: React.FC = () => {
  const { user } = useAuth();
  const [period, setPeriod] = useState<PeriodType>('week');
  
  // Use live analytics data
  const {
    analyticsData,
    sourceBreakdown,
    isLoading,
    error,
    isUsingMockData,
    lastFetch,
    refresh
  } = useAnalyticsData(period, {
    pollInterval: 30000, // 30 seconds
    useMockFallback: true
  });

  return (
    <Box sx={{ p: 3 }}>
      {/* Enhanced Header Section */}
      <Paper
        elevation={3}
        sx={{
          position: 'relative',
          overflow: 'hidden',
          borderRadius: 3,
          background: 'linear-gradient(135deg, #1976d2 0%, #7b1fa2 50%, #3f51b5 100%)',
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
              <BarChart3Icon sx={{ fontSize: 32 }} />
            </Box>
            <Box>
              <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                Analytics Dashboard
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Real-time insights and performance metrics
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {isLoading && (
              <Chip
                icon={<CircularProgress size={16} />}
                label="Loading..."
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  backdropFilter: 'blur(4px)'
                }}
              />
            )}
            <Chip
              icon={isUsingMockData ? <WifiOffIcon /> : <WifiIcon />}
              label={isUsingMockData ? "Mock Data" : "Live Data"}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(4px)'
              }}
            />
            <Chip
              icon={<UsersIcon />}
              label={user?.role?.toUpperCase()}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)'
              }}
            />
            {lastFetch && (
              <Chip
                label={`Updated: ${lastFetch.toLocaleTimeString()}`}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: '0.75rem'
                }}
                size="small"
              />
            )}
          </Box>
        </Box>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Chip
              label="Retry"
              size="small"
              onClick={() => refresh(period)}
              clickable
            />
          }
        >
          <Typography variant="body2">
            {isUsingMockData 
              ? "Using mock data due to API connection issues. Some features may be limited."
              : "There was an issue fetching analytics data. Please try refreshing."
            }
          </Typography>
        </Alert>
      )}

      {/* Period Selector */}
      <Box sx={{ mb: 3 }}>
        <PeriodSelector 
          period={period} 
          onChange={(newPeriod) => setPeriod(newPeriod)} 
        />
      </Box>

      {/* Key Metrics */}
      {analyticsData && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mb: 3 }}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">Classification Accuracy</Typography>
                  <TargetIcon color="action" fontSize="small" />
                </Box>
              }
              sx={{ pb: 1 }}
            />
            <CardContent sx={{ pt: 0 }}>
              <Typography variant="h4" sx={{ color: 'success.main', mb: 0.5 }}>
                {analyticsData.classificationAccuracy}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                AI Model Performance
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">Total Analyses</Typography>
                  <BarChart3Icon color="action" fontSize="small" />
                </Box>
              }
              sx={{ pb: 1 }}
            />
            <CardContent sx={{ pt: 0 }}>
              <Typography variant="h4" sx={{ color: 'primary.main', mb: 0.5 }}>
                {analyticsData.totalAnalyses.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                All time
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">Weekly Growth</Typography>
                  <TrendingUpIcon color="action" fontSize="small" />
                </Box>
              }
              sx={{ pb: 1 }}
            />
            <CardContent sx={{ pt: 0 }}>
              <Typography variant="h4" sx={{ color: 'success.main', mb: 0.5 }}>
                +{analyticsData.weeklyGrowth}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                vs last week
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Charts - First Row */}
      {analyticsData && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <BarChart3Icon sx={{ mr: 1 }} />
                  <Typography variant="h6">Classification Breakdown</Typography>
                </Box>
              }
              subheader="Distribution of job posting classifications"
            />
            <CardContent>
              <ClassificationChart data={analyticsData.classifications} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUpIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Usage Trends</Typography>
                </Box>
              }
              subheader="Request volume over time"
            />
            <CardContent>
              <UsageTrendsChart data={analyticsData.usageTrends} period={period} />
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Charts - Second Row */}
      {analyticsData && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ClockIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Peak Hours</Typography>
                </Box>
              }
              subheader="Usage patterns throughout the day"
            />
            <CardContent>
              <PeakHoursChart data={analyticsData.peakHours} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <UsersIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">User Engagement</Typography>
                </Box>
              }
              subheader="User behavior and engagement metrics"
            />
            <CardContent>
              <UserEngagementMetrics data={analyticsData.userEngagement} />
            </CardContent>
          </Card>
        </Box>
      )}

      {/* System Performance & Insights */}
      {analyticsData && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ActivityIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">System Performance</Typography>
                </Box>
              }
              subheader="Current system health and performance metrics"
            />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Average Response Time:</Typography>
                  <Chip
                    label={`${analyticsData.systemPerformance.avgResponseTime}s`}
                    variant="outlined"
                    color="primary"
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Success Rate:</Typography>
                  <Chip
                    label={`${analyticsData.systemPerformance.successRate}%`}
                    variant="outlined"
                    color="success"
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">System Uptime:</Typography>
                  <Chip
                    label={`${analyticsData.systemPerformance.uptime}%`}
                    variant="outlined"
                    color="success"
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>

        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Recent Insights</Typography>
              </Box>
            }
            subheader="Key findings and trends"
          />
          <CardContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main', mt: 0.25 }} />
                <Typography variant="body2">Job posting detection accuracy improved by 3%</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <InfoIcon sx={{ fontSize: 16, color: 'info.main', mt: 0.25 }} />
                <Typography variant="body2">Peak usage hours: 2-4 PM weekdays</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <AlertCircleIcon sx={{ fontSize: 16, color: 'warning.main', mt: 0.25 }} />
                <Typography variant="body2">Scam detection requests increased 15%</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <TrendingUpIcon sx={{ fontSize: 16, color: 'primary.main', mt: 0.25 }} />
                <Typography variant="body2">New user onboarding rate: 85%</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <BarChart3Icon sx={{ fontSize: 16, color: 'text.secondary', mt: 0.25 }} />
                <Typography variant="body2">Most common query: Job legitimacy check</Typography>
              </Box>
            </Box>
          </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default AnalyticsPage;