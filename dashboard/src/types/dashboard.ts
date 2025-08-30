// Centralized type definitions for the dashboard

/**
 * Overall system health status with service details and resource usage
 */
export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  uptime: string; // Human readable format (e.g., "2 days, 3 hours")
  lastUpdated: string; // ISO timestamp
  services: {
    openai: ServiceStatus;
    twilio: ServiceStatus;
    database: ServiceStatus;
    webhook: ServiceStatus;
  };
  memoryUsage: number; // percentage (0-100)
  cpuUsage: number; // percentage (0-100)
}

/**
 * Basic service status information
 */
export interface ServiceStatus {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  responseTime?: number; // in milliseconds, undefined if service is unreachable
  lastCheck: string; // ISO timestamp
  errorCount?: number; // undefined if not tracked
}

export interface ServiceDetails extends ServiceStatus {
  name: string;
  description: string;
  version?: string;
  endpoint?: string;
  dependencies?: string[];
  metrics?: {
    requestsPerMinute: number;
    successRate: number;
    avgResponseTime: number;
    uptime: string;
  };
  recentErrors?: Array<{
    timestamp: string;
    error: string;
    count: number;
  }>;
}

export type TrendDirection = 'up' | 'down' | 'stable';

/**
 * High-level metrics overview with trend analysis
 */
export interface MetricsOverview {
  totalRequests: number;
  requestsToday: number;
  requestsTrend: TrendDirection;
  requestsChange: number; // percentage change from previous period
  errorRate: number; // percentage (0-100)
  errorTrend: TrendDirection;
  errorChange: number; // percentage point change
  avgResponseTime: number; // in milliseconds (consistent with responseTime)
  responseTrend: TrendDirection;
  responseChange: number; // percentage change
  activeUsers: number;
  usersTrend: TrendDirection;
  usersChange: number; // percentage change
  successRate: number; // percentage (0-100)
  peakHour: string; // Format: "HH:MM" (24-hour)
  lastUpdated: string; // ISO timestamp
}

export interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  source: string; // e.g., 'OpenAI', 'Twilio', 'System'
  severity: 'low' | 'medium' | 'high' | 'critical';
  acknowledged: boolean;
  details?: string;
  actionRequired?: boolean;
}