import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
  Speed as SpeedIcon,
  People as UsersIcon,
  Assessment as RequestsIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

export interface MetricsOverview {
  totalRequests: number;
  requestsToday: number;
  requestsTrend: 'up' | 'down' | 'stable';
  requestsChange: number; // percentage change
  errorRate: number;
  errorTrend: 'up' | 'down' | 'stable';
  errorChange: number;
  avgResponseTime: number; // in seconds
  responseTrend: 'up' | 'down' | 'stable';
  responseChange: number;
  activeUsers: number;
  usersTrend: 'up' | 'down' | 'stable';
  usersChange: number;
  successRate: number;
  peakHour: string;
  lastUpdated: string;
}

interface MetricsOverviewCardProps {
  metrics: MetricsOverview;
}

const MetricsOverviewCard: React.FC<MetricsOverviewCardProps> = ({ metrics }) => {
  // Remove unused variables to fix ESLint warnings
  // const theme = useTheme();
  // const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon fontSize="small" />;
      case 'down':
        return <TrendingDownIcon fontSize="small" />;
      default:
        return <StableIcon fontSize="small" />;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable', isGoodWhenUp: boolean = true) => {
    if (trend === 'stable') return 'text.secondary';
    const isPositive = isGoodWhenUp ? trend === 'up' : trend === 'down';
    return isPositive ? 'success.main' : 'error.main';
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const MetricItem: React.FC<{
    icon: React.ReactNode;
    title: string;
    value: string | number;
    trend: 'up' | 'down' | 'stable';
    change: number;
    isGoodWhenUp?: boolean;
    suffix?: string;
  }> = ({ icon, title, value, trend, change, isGoodWhenUp = true, suffix = '' }) => (
    <Box sx={{ textAlign: 'center', p: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
        {icon}
      </Box>
      <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 0.5 }}>
        {typeof value === 'number' ? formatNumber(value) : value}{suffix}
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        {title}
      </Typography>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: getTrendColor(trend, isGoodWhenUp),
        }}
      >
        {getTrendIcon(trend)}
        <Typography variant="caption" sx={{ ml: 0.5 }}>
          {change > 0 ? '+' : ''}{change.toFixed(1)}%
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SpeedIcon color="primary" />
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Key Performance Indicators
          </Typography>
          <Typography variant="caption" color="textSecondary">
            Updated: {metrics.lastUpdated}
          </Typography>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, gap: 2 }}>
          <MetricItem
            icon={<RequestsIcon color="primary" />}
            title="Total Requests"
            value={metrics.totalRequests}
            trend={metrics.requestsTrend}
            change={metrics.requestsChange}
          />
          <MetricItem
            icon={<RequestsIcon color="info" />}
            title="Requests Today"
            value={metrics.requestsToday}
            trend={metrics.requestsTrend}
            change={metrics.requestsChange}
          />
          <MetricItem
            icon={<ErrorIcon color="warning" />}
            title="Error Rate"
            value={metrics.errorRate}
            trend={metrics.errorTrend}
            change={metrics.errorChange}
            isGoodWhenUp={false}
            suffix="%"
          />
          <MetricItem
            icon={<UsersIcon color="success" />}
            title="Active Users"
            value={metrics.activeUsers}
            trend={metrics.usersTrend}
            change={metrics.usersChange}
          />
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" color="primary" sx={{ fontWeight: 'bold' }}>
              {metrics.avgResponseTime.toFixed(1)}s
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Avg Response Time
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: getTrendColor(metrics.responseTrend, false),
                mt: 0.5,
              }}
            >
              {getTrendIcon(metrics.responseTrend)}
              <Typography variant="caption" sx={{ ml: 0.5 }}>
                {metrics.responseChange > 0 ? '+' : ''}{metrics.responseChange.toFixed(1)}%
              </Typography>
            </Box>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" color="success.main" sx={{ fontWeight: 'bold' }}>
              {metrics.successRate.toFixed(1)}%
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Success Rate
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Last 24 hours
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" color="info.main" sx={{ fontWeight: 'bold' }}>
              {metrics.peakHour}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Peak Hour
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Highest activity
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MetricsOverviewCard;