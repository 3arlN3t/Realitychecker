import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as MinusIcon,
  Speed as SpeedIcon,
  People as PeopleIcon,
  BarChart as BarChartIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { MetricsOverview, TrendDirection } from '../../types/dashboard';

// Helper functions for trend visualization
const getTrendIcon = (trend: TrendDirection) => {
  switch (trend) {
    case 'up':
      return <TrendingUpIcon fontSize="small" />;
    case 'down':
      return <TrendingDownIcon fontSize="small" />;
    default:
      return <MinusIcon fontSize="small" />;
  }
};

const getTrendColor = (trend: TrendDirection, isGoodWhenUp: boolean = true): string => {
  if (trend === 'stable') return 'text.secondary';
  const isPositive = isGoodWhenUp ? trend === 'up' : trend === 'down';
  return isPositive ? 'success.main' : 'error.main';
};

const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

// MetricItem component
interface MetricItemProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  trend: TrendDirection;
  change: number;
  isGoodWhenUp?: boolean;
  suffix?: string;
}

const MetricItem: React.FC<MetricItemProps> = ({ 
  icon, 
  title, 
  value, 
  trend, 
  change, 
  isGoodWhenUp = true, 
  suffix = '' 
}) => (
  <Paper
    elevation={0}
    sx={{
      p: 2,
      textAlign: 'center',
      bgcolor: 'background.paper',
      backdropFilter: 'blur(10px)',
      border: '1px solid',
      borderColor: 'divider',
      borderRadius: 2,
      boxShadow: 2
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
      <Box sx={{ color: 'primary.main' }}>{icon}</Box>
    </Box>
    <Typography variant="h5" sx={{ mb: 0.5 }}>
      {typeof value === 'number' ? formatNumber(value) : value}{suffix}
    </Typography>
    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
      {title}
    </Typography>
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: getTrendColor(trend, isGoodWhenUp) }}>
      {getTrendIcon(trend)}
      <Typography variant="caption" sx={{ ml: 0.5 }}>
        {change > 0 ? '+' : ''}{change.toFixed(1)}%
      </Typography>
    </Box>
  </Paper>
);

interface MetricsOverviewCardProps {
  metrics: MetricsOverview;
}

const MetricsOverviewCard: React.FC<MetricsOverviewCardProps> = ({ metrics }) => {
  return (
    <Box sx={{ height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <SpeedIcon sx={{ color: 'primary.main' }} />
        <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
          Key Performance Indicators
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Updated: {metrics.lastUpdated}
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 2, mb: 2 }}>
        <MetricItem
          icon={<BarChartIcon />}
          title="Total Requests"
          value={metrics.totalRequests}
          trend={metrics.requestsTrend}
          change={metrics.requestsChange}
        />
        <MetricItem
          icon={<BarChartIcon />}
          title="Requests Today"
          value={metrics.requestsToday}
          trend={metrics.requestsTrend}
          change={metrics.requestsChange}
        />
        <MetricItem
          icon={<WarningIcon />}
          title="Error Rate"
          value={metrics.errorRate}
          trend={metrics.errorTrend}
          change={metrics.errorChange}
          isGoodWhenUp={false}
          suffix="%"
        />
        <MetricItem
          icon={<PeopleIcon />}
          title="Active Users"
          value={metrics.activeUsers}
          trend={metrics.usersTrend}
          change={metrics.usersChange}
        />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: 'background.paper',
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2
          }}
        >
          <Typography variant="h5" color="primary.main">
            {metrics.avgResponseTime.toFixed(1)}s
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Avg Response Time
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 0.5, color: getTrendColor(metrics.responseTrend, false) }}>
            {getTrendIcon(metrics.responseTrend)}
            <Typography variant="caption" sx={{ ml: 0.5 }}>
              {metrics.responseChange > 0 ? '+' : ''}{metrics.responseChange.toFixed(1)}%
            </Typography>
          </Box>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: 'background.paper',
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2
          }}
        >
          <Typography variant="h5" color="success.main">
            {metrics.successRate.toFixed(1)}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Success Rate
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Last 24 hours
          </Typography>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: 'background.paper',
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2
          }}
        >
          <Typography variant="h5" color="info.main">
            {metrics.peakHour}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Peak Hour
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Highest activity
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default MetricsOverviewCard;