import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper, Chip } from '@mui/material';
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
  const [analyticsData, setAnalyticsData] = useState(generateAnalyticsData(period));

  // Update analytics data when period changes or every 30 seconds
  useEffect(() => {
    setAnalyticsData(generateAnalyticsData(period));
    
    const interval = setInterval(() => {
      setAnalyticsData(generateAnalyticsData(period));
    }, 30000);

    return () => clearInterval(interval);
  }, [period]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Chip 
          label={`Viewing as: ${user?.role?.toUpperCase()}`}
          color="primary"
          variant="outlined"
        />
      </Box>

      {/* Period Selector */}
      <PeriodSelector 
        period={period} 
        onChange={(newPeriod) => setPeriod(newPeriod)} 
      />

      {/* Key Metrics */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Classification Accuracy
            </Typography>
            <Typography variant="h3" color="success.main">
              {analyticsData.classificationAccuracy}%
            </Typography>
            <Typography variant="body2" color="textSecondary">
              AI Model Performance
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Total Analyses
            </Typography>
            <Typography variant="h3" color="primary">
              {analyticsData.totalAnalyses.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              All time
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 250px', minWidth: '250px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Weekly Growth
            </Typography>
            <Typography variant="h3" color="success.main">
              +{analyticsData.weeklyGrowth}%
            </Typography>
            <Typography variant="body2" color="textSecondary">
              vs last week
            </Typography>
          </Paper>
        </Box>
      </Box>

      {/* Charts - First Row */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <ClassificationChart data={analyticsData.classifications} />
        <UsageTrendsChart data={analyticsData.usageTrends} period={period} />
      </Box>

      {/* Charts - Second Row */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <PeakHoursChart data={analyticsData.peakHours} />
        <UserEngagementMetrics data={analyticsData.userEngagement} />
      </Box>

      {/* System Performance */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Performance
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Average Response Time:</Typography>
                <Typography variant="body2" fontWeight="bold" color="info.main">
                  {analyticsData.systemPerformance.avgResponseTime}s
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Success Rate:</Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  {analyticsData.systemPerformance.successRate}%
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">System Uptime:</Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  {analyticsData.systemPerformance.uptime}%
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Insights
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" color="success.main">
                • Job posting detection accuracy improved by 3%
              </Typography>
              <Typography variant="body2" color="info.main">
                • Peak usage hours: 2-4 PM weekdays
              </Typography>
              <Typography variant="body2" color="warning.main">
                • Scam detection requests increased 15%
              </Typography>
              <Typography variant="body2" color="primary">
                • New user onboarding rate: 85%
              </Typography>
              <Typography variant="body2">
                • Most common query: Job legitimacy check
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default AnalyticsPage;