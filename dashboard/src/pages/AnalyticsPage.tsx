import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper, Chip, LinearProgress } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

// Sample analytics data
const generateAnalyticsData = () => {
  return {
    classificationAccuracy: Math.floor(Math.random() * 10) + 85, // 85-95%
    totalAnalyses: Math.floor(Math.random() * 500) + 2500,
    weeklyGrowth: (Math.random() * 20 + 5).toFixed(1), // 5-25%
    topCategories: [
      { name: 'Job Postings', count: Math.floor(Math.random() * 200) + 800, percentage: 45 },
      { name: 'Scam Detection', count: Math.floor(Math.random() * 150) + 600, percentage: 32 },
      { name: 'Document Analysis', count: Math.floor(Math.random() * 100) + 300, percentage: 15 },
      { name: 'General Inquiry', count: Math.floor(Math.random() * 80) + 150, percentage: 8 },
    ],
    userEngagement: {
      dailyActiveUsers: Math.floor(Math.random() * 20) + 40,
      avgSessionTime: (Math.random() * 5 + 3).toFixed(1), // 3-8 minutes
      returnRate: Math.floor(Math.random() * 15) + 70, // 70-85%
    },
    systemPerformance: {
      avgResponseTime: (Math.random() * 0.8 + 0.5).toFixed(2), // 0.5-1.3s
      successRate: (Math.random() * 5 + 95).toFixed(1), // 95-100%
      uptime: (Math.random() * 0.5 + 99.5).toFixed(2), // 99.5-100%
    }
  };
};

const AnalyticsPage: React.FC = () => {
  const { user } = useAuth();
  const [analyticsData, setAnalyticsData] = useState(generateAnalyticsData());

  // Update analytics data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setAnalyticsData(generateAnalyticsData());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

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

      {/* Category Breakdown */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <Box sx={{ flex: '1 1 400px', minWidth: '400px' }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Analysis Categories
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {analyticsData.topCategories.map((category, index) => (
                <Box key={index}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">{category.name}</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {category.count} ({category.percentage}%)
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={category.percentage} 
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              User Engagement
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Daily Active Users:</Typography>
                <Typography variant="body2" fontWeight="bold" color="primary">
                  {analyticsData.userEngagement.dailyActiveUsers}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Avg Session Time:</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {analyticsData.userEngagement.avgSessionTime} min
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Return Rate:</Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  {analyticsData.userEngagement.returnRate}%
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Box>
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