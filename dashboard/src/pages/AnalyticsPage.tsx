import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Clock, 
  Target, 
  Activity,
  CheckCircle,
  AlertCircle,
  Info
} from 'lucide-react';
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
    <div className="space-y-6 p-6">
      {/* Enhanced Header Section */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 p-8 shadow-2xl">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm">
              <BarChart3 className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white tracking-tight">Analytics Dashboard</h1>
              <p className="text-blue-100 mt-1 text-lg">Real-time insights and performance metrics</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 rounded-full bg-white/20 px-4 py-2 backdrop-blur-sm">
              <Activity className="h-4 w-4 text-white" />
              <span className="text-white font-medium">Live Data</span>
            </div>
            <Badge variant="secondary" className="bg-white/20 text-white border-white/30 px-4 py-2">
              <Users className="w-4 h-4 mr-2" />
              {user?.role?.toUpperCase()}
            </Badge>
          </div>
        </div>
        <div className="absolute -top-4 -right-4 h-24 w-24 rounded-full bg-white/10"></div>
        <div className="absolute -bottom-8 -left-8 h-32 w-32 rounded-full bg-white/5"></div>
      </div>

      {/* Period Selector */}
      <PeriodSelector 
        period={period} 
        onChange={(newPeriod) => setPeriod(newPeriod)} 
      />

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Classification Accuracy</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {analyticsData.classificationAccuracy}%
            </div>
            <p className="text-xs text-muted-foreground">
              AI Model Performance
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {analyticsData.totalAnalyses.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              All time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Weekly Growth</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +{analyticsData.weeklyGrowth}%
            </div>
            <p className="text-xs text-muted-foreground">
              vs last week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts - First Row */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Classification Breakdown
            </CardTitle>
            <CardDescription>Distribution of job posting classifications</CardDescription>
          </CardHeader>
          <CardContent>
            <ClassificationChart data={analyticsData.classifications} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Usage Trends
            </CardTitle>
            <CardDescription>Request volume over time</CardDescription>
          </CardHeader>
          <CardContent>
            <UsageTrendsChart data={analyticsData.usageTrends} period={period} />
          </CardContent>
        </Card>
      </div>

      {/* Charts - Second Row */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Peak Hours
            </CardTitle>
            <CardDescription>Usage patterns throughout the day</CardDescription>
          </CardHeader>
          <CardContent>
            <PeakHoursChart data={analyticsData.peakHours} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="w-5 h-5 mr-2" />
              User Engagement
            </CardTitle>
            <CardDescription>User behavior and engagement metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <UserEngagementMetrics data={analyticsData.userEngagement} />
          </CardContent>
        </Card>
      </div>

      {/* System Performance & Insights */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              System Performance
            </CardTitle>
            <CardDescription>Current system health and performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Average Response Time:</span>
                <Badge variant="outline" className="text-blue-600">
                  {analyticsData.systemPerformance.avgResponseTime}s
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Success Rate:</span>
                <Badge variant="outline" className="text-green-600">
                  {analyticsData.systemPerformance.successRate}%
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">System Uptime:</span>
                <Badge variant="outline" className="text-green-600">
                  {analyticsData.systemPerformance.uptime}%
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Info className="w-5 h-5 mr-2" />
              Recent Insights
            </CardTitle>
            <CardDescription>Key findings and trends</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-start space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                <span className="text-sm">Job posting detection accuracy improved by 3%</span>
              </div>
              <div className="flex items-start space-x-2">
                <Info className="w-4 h-4 text-blue-500 mt-0.5" />
                <span className="text-sm">Peak usage hours: 2-4 PM weekdays</span>
              </div>
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
                <span className="text-sm">Scam detection requests increased 15%</span>
              </div>
              <div className="flex items-start space-x-2">
                <TrendingUp className="w-4 h-4 text-blue-500 mt-0.5" />
                <span className="text-sm">New user onboarding rate: 85%</span>
              </div>
              <div className="flex items-start space-x-2">
                <BarChart3 className="w-4 h-4 text-gray-500 mt-0.5" />
                <span className="text-sm">Most common query: Job legitimacy check</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsPage;