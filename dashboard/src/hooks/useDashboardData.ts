/**
 * React hook for managing dashboard data with real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { DashboardAPI, DashboardOverviewResponse, SystemMetricsResponse } from '../lib/api';
import { MetricsOverview } from '../types/dashboard';

export interface UseDashboardDataOptions {
  /** Polling interval in milliseconds (default: 10000 = 10 seconds) */
  pollInterval?: number;
  /** Whether to start polling immediately (default: true) */
  autoStart?: boolean;
  /** Whether to use mock data as fallback (default: true) */
  useMockFallback?: boolean;
  /** Callback for handling errors */
  onError?: (error: Error) => void;
}

export interface UseDashboardDataReturn {
  /** Current dashboard overview data */
  overview: DashboardOverviewResponse | null;
  /** Current system metrics */
  metrics: SystemMetricsResponse | null;
  /** Transformed metrics for UI components */
  metricsOverview: MetricsOverview | null;
  /** Whether data is currently being fetched */
  isLoading: boolean;
  /** Current error state */
  error: Error | null;
  /** Whether currently using mock data */
  isUsingMockData: boolean;
  /** Last successful fetch timestamp */
  lastFetch: Date | null;
  /** Manually refresh data */
  refresh: () => Promise<void>;
  /** Start polling */
  startPolling: () => void;
  /** Stop polling */
  stopPolling: () => void;
  /** Whether polling is active */
  isPolling: boolean;
}

/**
 * Generate mock dashboard data for fallback
 */
function generateMockOverview(): DashboardOverviewResponse {
  const baseRequests = 1250;
  const todayRequests = Math.floor(Math.random() * 50) + 30;
  const errorRate = Math.random() * 3 + 1;
  const activeUsers = Math.floor(Math.random() * 15) + 15;

  return {
    total_requests: baseRequests + Math.floor(Math.random() * 100),
    requests_today: todayRequests,
    error_rate: parseFloat(errorRate.toFixed(1)),
    active_users: activeUsers,
    system_health: errorRate < 2 ? 'healthy' : errorRate < 3 ? 'warning' : 'critical',
    success_rate: parseFloat((100 - errorRate).toFixed(1)),
    avg_response_time: parseFloat((Math.random() * 2 + 0.5).toFixed(1)),
    peak_hour: '2:00 PM',
    server_uptime: '99.9%',
    last_updated: new Date().toISOString(),
  };
}

function generateMockMetrics(): SystemMetricsResponse {
  return {
    timestamp: new Date().toISOString(),
    active_requests: Math.floor(Math.random() * 10) + 5,
    requests_per_minute: Math.floor(Math.random() * 30) + 20,
    error_rate: Math.random() * 3 + 1,
    response_times: {
      p50: Math.random() * 500 + 200,
      p95: Math.random() * 1000 + 500,
      p99: Math.random() * 2000 + 1000,
    },
    service_status: {
      openai: Math.random() > 0.1 ? 'healthy' : 'warning',
      twilio: Math.random() > 0.05 ? 'healthy' : 'critical',
      database: 'healthy',
      webhook: Math.random() > 0.15 ? 'healthy' : 'warning',
    },
    memory_usage: Math.random() * 40 + 30,
    cpu_usage: Math.random() * 30 + 20,
  };
}

/**
 * Transform API response to UI format
 */
function transformToMetricsOverview(overview: DashboardOverviewResponse): MetricsOverview {
  return {
    totalRequests: overview.total_requests,
    requestsToday: overview.requests_today,
    requestsTrend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable',
    requestsChange: (Math.random() - 0.5) * 20,
    errorRate: overview.error_rate,
    errorTrend: Math.random() > 0.6 ? 'down' : Math.random() > 0.3 ? 'up' : 'stable',
    errorChange: (Math.random() - 0.5) * 10,
    avgResponseTime: overview.avg_response_time,
    responseTrend: Math.random() > 0.6 ? 'down' : Math.random() > 0.3 ? 'up' : 'stable',
    responseChange: (Math.random() - 0.5) * 15,
    activeUsers: overview.active_users,
    usersTrend: Math.random() > 0.5 ? 'up' : Math.random() > 0.5 ? 'down' : 'stable',
    usersChange: (Math.random() - 0.5) * 30,
    successRate: overview.success_rate,
    peakHour: overview.peak_hour,
    lastUpdated: new Date(overview.last_updated).toLocaleTimeString(),
  };
}

/**
 * Custom hook for dashboard data management
 */
export function useDashboardData(options: UseDashboardDataOptions = {}): UseDashboardDataReturn {
  const {
    pollInterval = 10000, // 10 seconds
    autoStart = true,
    useMockFallback = true,
    onError
  } = options;

  // State
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [metrics, setMetrics] = useState<SystemMetricsResponse | null>(null);
  const [metricsOverview, setMetricsOverview] = useState<MetricsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Refs
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  /**
   * Fetch dashboard data from API
   */
  const fetchDashboardData = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      console.log('🔍 Fetching dashboard data from API...');
      
      // Fetch both overview and metrics in parallel
      const [overviewResponse, metricsResponse] = await Promise.all([
        DashboardAPI.getOverview(),
        DashboardAPI.getRealtimeMetrics()
      ]);
      
      if (!mountedRef.current) return;

      setOverview(overviewResponse);
      setMetrics(metricsResponse);
      setMetricsOverview(transformToMetricsOverview(overviewResponse));
      setIsUsingMockData(false);
      setLastFetch(new Date());
      
      console.log('✅ Dashboard data fetched successfully:', {
        totalRequests: overviewResponse.total_requests,
        systemHealth: overviewResponse.system_health,
        activeRequests: metricsResponse.active_requests
      });

    } catch (err) {
      if (!mountedRef.current) return;

      const error = err instanceof Error ? err : new Error('Failed to fetch dashboard data');
      console.warn('⚠️ Dashboard API failed, using fallback:', error.message);
      
      setError(error);
      onError?.(error);

      // Use mock data as fallback if enabled
      if (useMockFallback) {
        const mockOverview = generateMockOverview();
        const mockMetrics = generateMockMetrics();
        
        setOverview(mockOverview);
        setMetrics(mockMetrics);
        setMetricsOverview(transformToMetricsOverview(mockOverview));
        setIsUsingMockData(true);
        setLastFetch(new Date());
        console.log('🎭 Using mock dashboard data as fallback');
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [useMockFallback, onError]);

  /**
   * Start polling for dashboard data
   */
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    setIsPolling(true);
    
    // Initial fetch
    fetchDashboardData();

    // Set up polling
    pollIntervalRef.current = setInterval(() => {
      fetchDashboardData();
    }, pollInterval);

    console.log(`🔄 Started dashboard polling (${pollInterval}ms interval)`);
  }, [fetchDashboardData, pollInterval]);

  /**
   * Stop polling
   */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
    console.log('⏹️ Stopped dashboard polling');
  }, []);

  /**
   * Manual refresh
   */
  const refresh = useCallback(async (): Promise<void> => {
    console.log('🔄 Manual dashboard data refresh requested');
    await fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-start polling on mount
  useEffect(() => {
    if (autoStart) {
      startPolling();
    }

    return () => {
      mountedRef.current = false;
      stopPolling();
    };
  }, [autoStart, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return {
    overview,
    metrics,
    metricsOverview,
    isLoading,
    error,
    isUsingMockData,
    lastFetch,
    refresh,
    startPolling,
    stopPolling,
    isPolling
  };
}

export default useDashboardData;