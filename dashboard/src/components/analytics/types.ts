export interface ClassificationData {
  name: string;
  value: number;
  color?: string;
}

export interface UsageTrendData {
  date: string;
  count: number;
}

export interface PeakHourData {
  hour: number;
  count: number;
}

export interface UserEngagementData {
  metric: string;
  value: number | string;
  change?: number;
}

export type PeriodType = 'day' | 'week' | 'month' | 'year';

export interface AnalyticsData {
  classifications: ClassificationData[];
  usageTrends: UsageTrendData[];
  peakHours: PeakHourData[];
  userEngagement: UserEngagementData[];
}