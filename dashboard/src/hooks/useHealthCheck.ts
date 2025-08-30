/**
 * React hook for managing health check data with real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { HealthCheckAPI, HealthCheckResponse } from '../lib/api';
import { transformHealthResponse, isHealthDataStale } from '../lib/healthTransforms';
import { SystemHealth } from '../types/dashboard';

export interface UseHealthCheckOptions {
  /** Polling interval in milliseconds (default: 30000 = 30 seconds) */
  pollInterval?: number;
  /** Whether to start polling immediately (default: true) */
  autoStart?: boolean;
  /** Whether to use mock data as fallback (default: true) */
  useMockFallback?: boolean;
  /** Callback for handling errors */
  onError?: (error: Error) => void;
}

export interface UseHealthCheckReturn {
  /** Current health data */
  healthData: SystemHealth | null;
  /** Whether data is currently being fetched */
  isLoading: boolean;
  /** Current error state */
  error: Error | null;
  /** Whether the data is stale */
  isStale: boolean;
  /** Whether currently using mock data */
  isUsingMockData: boolean;
  /** Last successful fetch timestamp */
  lastFetch: Date | null;
  /** Manually refresh health data */
  refresh: () => Promise<void>;
  /** Start polling */
  startPolling: () => void;
  /** Stop polling */
  stopPolling: () => void;
  /** Whether polling is active */
  isPolling: boolean;
}

/**
 * Generate mock health data for fallback
 */
function generateMockHealthData(): SystemHealth {
  const memoryUsage = Math.floor(Math.random() * 40) + 30;
  const cpuUsage = Math.floor(Math.random() * 30) + 20;
  const errorRate = Math.random() * 5;

  return {
    status: errorRate < 2 ? 'healthy' : errorRate < 3 ? 'warning' : 'critical',
    uptime: '99.9%',
    lastUpdated: new Date().toLocaleTimeString(),
    memoryUsage,
    cpuUsage,
    services: {
      openai: {
        status: Math.random() > 0.1 ? 'healthy' : 'warning',
        responseTime: Math.floor(Math.random() * 500) + 200,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 3),
      },
      twilio: {
        status: Math.random() > 0.05 ? 'healthy' : 'critical',
        responseTime: Math.floor(Math.random() * 300) + 100,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 2),
      },
      database: {
        status: 'healthy',
        responseTime: Math.floor(Math.random() * 50) + 10,
        lastCheck: new Date().toISOString(),
        errorCount: 0,
      },
      webhook: {
        status: Math.random() > 0.15 ? 'healthy' : 'warning',
        responseTime: Math.floor(Math.random() * 200) + 50,
        lastCheck: new Date().toISOString(),
        errorCount: Math.floor(Math.random() * 2),
      },
    },
  };
}

/**
 * Custom hook for health check data management
 */
export function useHealthCheck(options: UseHealthCheckOptions = {}): UseHealthCheckReturn {
  const {
    pollInterval = 30000, // 30 seconds
    autoStart = true,
    useMockFallback = true,
    onError
  } = options;

  // State
  const [healthData, setHealthData] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Refs
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Calculate if data is stale
  const isStale = lastFetch ? isHealthDataStale(lastFetch.toISOString()) : true;

  /**
   * Fetch health data from API
   */
  const fetchHealthData = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      console.log('🔍 Fetching health data from API...');
      const apiResponse: HealthCheckResponse = await HealthCheckAPI.getDetailedHealth();
      
      if (!mountedRef.current) return;

      const transformedData = transformHealthResponse(apiResponse);
      setHealthData(transformedData);
      setIsUsingMockData(false);
      setLastFetch(new Date());
      
      console.log('✅ Health data fetched successfully:', {
        status: apiResponse.status,
        services: Object.keys(apiResponse.services),
        timestamp: apiResponse.timestamp
      });

    } catch (err) {
      if (!mountedRef.current) return;

      const error = err instanceof Error ? err : new Error('Failed to fetch health data');
      console.warn('⚠️ Health API failed, using fallback:', error.message);
      
      setError(error);
      onError?.(error);

      // Use mock data as fallback if enabled
      if (useMockFallback) {
        const mockData = generateMockHealthData();
        setHealthData(mockData);
        setIsUsingMockData(true);
        setLastFetch(new Date());
        console.log('🎭 Using mock health data as fallback');
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [useMockFallback, onError]);

  /**
   * Start polling for health data
   */
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    setIsPolling(true);
    
    // Initial fetch
    fetchHealthData();

    // Set up polling
    pollIntervalRef.current = setInterval(() => {
      fetchHealthData();
    }, pollInterval);

    console.log(`🔄 Started health check polling (${pollInterval}ms interval)`);
  }, [fetchHealthData, pollInterval]);

  /**
   * Stop polling
   */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
    console.log('⏹️ Stopped health check polling');
  }, []);

  /**
   * Manual refresh
   */
  const refresh = useCallback(async (): Promise<void> => {
    console.log('🔄 Manual health data refresh requested');
    await fetchHealthData();
  }, [fetchHealthData]);

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
    healthData,
    isLoading,
    error,
    isStale,
    isUsingMockData,
    lastFetch,
    refresh,
    startPolling,
    stopPolling,
    isPolling
  };
}

export default useHealthCheck;