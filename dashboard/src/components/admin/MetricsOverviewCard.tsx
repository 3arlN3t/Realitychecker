import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Gauge,
  Users,
  BarChart,
  AlertTriangle,
} from 'lucide-react';

// Define a type alias for trend directions
type TrendDirection = 'up' | 'down' | 'stable';

export interface MetricsOverview {
  totalRequests: number;
  requestsToday: number;
  requestsTrend: TrendDirection;
  requestsChange: number; // percentage change
  errorRate: number;
  errorTrend: TrendDirection;
  errorChange: number;
  avgResponseTime: number; // in seconds
  responseTrend: TrendDirection;
  responseChange: number;
  activeUsers: number;
  usersTrend: TrendDirection;
  usersChange: number;
  successRate: number;
  peakHour: string;
  lastUpdated: string;
}

// Helper functions for trend visualization
const getTrendIcon = (trend: TrendDirection) => {
  switch (trend) {
    case 'up':
      return <TrendingUp className="w-4 h-4" />;
    case 'down':
      return <TrendingDown className="w-4 h-4" />;
    default:
      return <Minus className="w-4 h-4" />;
  }
};

const getTrendColor = (trend: TrendDirection, isGoodWhenUp: boolean = true) => {
  if (trend === 'stable') return 'text-gray-400';
  const isPositive = isGoodWhenUp ? trend === 'up' : trend === 'down';
  return isPositive ? 'text-green-500' : 'text-red-500';
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
  <div className="text-center p-2 bg-card/30 backdrop-blur-sm rounded-lg border border-border/50 shadow-lg">
    <div className="flex justify-center mb-2">
      <div className="text-primary">{icon}</div>
    </div>
    <div className="text-xl font-bold mb-1">
      {typeof value === 'number' ? formatNumber(value) : value}{suffix}
    </div>
    <div className="text-sm text-muted-foreground mb-1">
      {title}
    </div>
    <div className={`flex items-center justify-center ${getTrendColor(trend, isGoodWhenUp)}`}>
      {getTrendIcon(trend)}
      <span className="text-xs ml-1">
        {change > 0 ? '+' : ''}{change.toFixed(1)}%
      </span>
    </div>
  </div>
);

interface MetricsOverviewCardProps {
  metrics: MetricsOverview;
}

const MetricsOverviewCard: React.FC<MetricsOverviewCardProps> = ({ metrics }) => {
  return (
    <div className="h-full">
      <div className="flex items-center mb-4">
        <Gauge className="w-5 h-5 text-primary" />
        <h3 className="ml-2 flex-grow text-lg font-medium">
          Key Performance Indicators
        </h3>
        <span className="text-xs text-muted-foreground">
          Updated: {metrics.lastUpdated}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <MetricItem
          icon={<BarChart className="w-5 h-5" />}
          title="Total Requests"
          value={metrics.totalRequests}
          trend={metrics.requestsTrend}
          change={metrics.requestsChange}
        />
        <MetricItem
          icon={<BarChart className="w-5 h-5" />}
          title="Requests Today"
          value={metrics.requestsToday}
          trend={metrics.requestsTrend}
          change={metrics.requestsChange}
        />
        <MetricItem
          icon={<AlertTriangle className="w-5 h-5" />}
          title="Error Rate"
          value={metrics.errorRate}
          trend={metrics.errorTrend}
          change={metrics.errorChange}
          isGoodWhenUp={false}
          suffix="%"
        />
        <MetricItem
          icon={<Users className="w-5 h-5" />}
          title="Active Users"
          value={metrics.activeUsers}
          trend={metrics.usersTrend}
          change={metrics.usersChange}
        />
      </div>

      <div className="border-t border-gray-800 my-4"></div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="text-center p-3 bg-card/30 backdrop-blur-sm rounded-lg border border-border/50">
          <div className="text-xl font-bold text-primary">
            {metrics.avgResponseTime.toFixed(1)}s
          </div>
          <div className="text-sm text-muted-foreground">
            Avg Response Time
          </div>
          <div className={`flex items-center justify-center mt-1 ${getTrendColor(metrics.responseTrend, false)}`}>
            {getTrendIcon(metrics.responseTrend)}
            <span className="text-xs ml-1">
              {metrics.responseChange > 0 ? '+' : ''}{metrics.responseChange.toFixed(1)}%
            </span>
          </div>
        </div>
        <div className="text-center p-3 bg-card/30 backdrop-blur-sm rounded-lg border border-border/50">
          <div className="text-xl font-bold text-green-500">
            {metrics.successRate.toFixed(1)}%
          </div>
          <div className="text-sm text-muted-foreground">
            Success Rate
          </div>
          <div className="text-xs text-muted-foreground">
            Last 24 hours
          </div>
        </div>
        <div className="text-center p-3 bg-card/30 backdrop-blur-sm rounded-lg border border-border/50">
          <div className="text-xl font-bold text-blue-500">
            {metrics.peakHour}
          </div>
          <div className="text-sm text-muted-foreground">
            Peak Hour
          </div>
          <div className="text-xs text-muted-foreground">
            Highest activity
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsOverviewCard;