/**
 * React hook for managing users data with pagination and filtering
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { UsersAPI, UserListResponse } from '../lib/api';

export interface UseUsersDataOptions {
  /** Initial page number (default: 1) */
  initialPage?: number;
  /** Items per page (default: 20) */
  pageSize?: number;
  /** Whether to start fetching immediately (default: true) */
  autoStart?: boolean;
  /** Whether to use mock data as fallback (default: true) */
  useMockFallback?: boolean;
  /** Callback for handling errors */
  onError?: (error: Error) => void;
}

export interface UseUsersDataReturn {
  /** Current users data */
  users: UserListResponse | null;
  /** Whether data is currently being fetched */
  isLoading: boolean;
  /** Current error state */
  error: Error | null;
  /** Whether currently using mock data */
  isUsingMockData: boolean;
  /** Last successful fetch timestamp */
  lastFetch: Date | null;
  /** Current page number */
  currentPage: number;
  /** Current filters */
  filters: UserFilters;
  /** Fetch users with pagination and filters */
  fetchUsers: (page?: number, newFilters?: UserFilters) => Promise<void>;
  /** Set page number */
  setPage: (page: number) => void;
  /** Set filters */
  setFilters: (filters: UserFilters) => void;
  /** Block a user */
  blockUser: (phoneNumber: string, reason?: string) => Promise<boolean>;
  /** Unblock a user */
  unblockUser: (phoneNumber: string) => Promise<boolean>;
  /** Refresh current data */
  refresh: () => Promise<void>;
}

export interface UserFilters {
  search?: string;
  blocked?: boolean;
  minRequests?: number;
  maxRequests?: number;
  daysSinceLastInteraction?: number;
}

/**
 * Generate mock users data for fallback
 */
function generateMockUsers(page: number, limit: number, totalUsers: number = 150): UserListResponse {
  const mockUsers = [];
  const startIndex = (page - 1) * limit;
  
  for (let i = 0; i < limit && startIndex + i < totalUsers; i++) {
    const userIndex = startIndex + i;
    mockUsers.push({
      phone_number: `+1555${String(userIndex).padStart(7, '0')}`,
      total_requests: Math.floor(Math.random() * 50) + 1,
      first_interaction: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      last_interaction: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      is_blocked: Math.random() < 0.1, // 10% blocked
      success_rate: Math.random() * 20 + 80, // 80-100%
      avg_response_time: Math.random() * 2 + 0.5, // 0.5-2.5s
    });
  }

  return {
    users: mockUsers,
    total: totalUsers,
    page,
    limit,
    total_pages: Math.ceil(totalUsers / limit),
  };
}

/**
 * Custom hook for users data management
 */
export function useUsersData(options: UseUsersDataOptions = {}): UseUsersDataReturn {
  const {
    initialPage = 1,
    pageSize = 20,
    autoStart = true,
    useMockFallback = true,
    onError
  } = options;

  // State
  const [users, setUsers] = useState<UserListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [filters, setFilters] = useState<UserFilters>({});

  // Refs
  const mountedRef = useRef(true);

  /**
   * Fetch users data from API
   */
  const fetchUsers = useCallback(async (page?: number, newFilters?: UserFilters): Promise<void> => {
    if (!mountedRef.current) return;

    const activePage = page ?? currentPage;
    const activeFilters = newFilters ?? filters;

    setIsLoading(true);
    setError(null);

    try {
      if (process.env.NODE_ENV === 'development') {
        console.log('🔍 Fetching users data from API...', { page: activePage, filters: activeFilters });
      }
      
      const response = await UsersAPI.getUsers(activePage, pageSize, activeFilters);
      
      if (!mountedRef.current) return;

      setUsers(response);
      setCurrentPage(activePage);
      setFilters(activeFilters);
      setIsUsingMockData(false);
      setLastFetch(new Date());
      
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Users data fetched successfully:', {
          page: activePage,
          totalUsers: response.total,
          usersOnPage: response.users.length
        });
      }

    } catch (err) {
      if (!mountedRef.current) return;

      const error = err instanceof Error ? err : new Error('Failed to fetch users data');
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ Users API failed, using fallback:', error.message);
      }
      
      setError(error);
      onError?.(error);

      // Use mock data as fallback if enabled
      if (useMockFallback) {
        const mockData = generateMockUsers(activePage, pageSize);
        setUsers(mockData);
        setCurrentPage(activePage);
        setFilters(activeFilters);
        setIsUsingMockData(true);
        setLastFetch(new Date());
        if (process.env.NODE_ENV === 'development') {
          console.log('🎭 Using mock users data as fallback');
        }
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [currentPage, filters, pageSize, useMockFallback, onError]);

  /**
   * Set page number and fetch data
   */
  const setPage = useCallback((page: number) => {
    fetchUsers(page);
  }, [fetchUsers]);

  /**
   * Set filters and fetch data
   */
  const setFiltersAndFetch = useCallback((newFilters: UserFilters) => {
    fetchUsers(1, newFilters); // Reset to page 1 when filtering
  }, [fetchUsers]);

  /**
   * Block a user
   */
  const blockUser = useCallback(async (phoneNumber: string, reason?: string): Promise<boolean> => {
    try {
      console.log('🚫 Blocking user:', phoneNumber);
      
      const response = await UsersAPI.blockUser(phoneNumber, reason);
      
      if (response.success) {
        // Refresh current data to reflect changes
        await fetchUsers();
        console.log('✅ User blocked successfully:', phoneNumber);
        return true;
      }
      
      return false;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to block user');
      console.error('❌ Failed to block user:', error.message);
      onError?.(error);
      return false;
    }
  }, [fetchUsers, onError]);

  /**
   * Unblock a user
   */
  const unblockUser = useCallback(async (phoneNumber: string): Promise<boolean> => {
    try {
      console.log('✅ Unblocking user:', phoneNumber);
      
      const response = await UsersAPI.unblockUser(phoneNumber);
      
      if (response.success) {
        // Refresh current data to reflect changes
        await fetchUsers();
        console.log('✅ User unblocked successfully:', phoneNumber);
        return true;
      }
      
      return false;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to unblock user');
      console.error('❌ Failed to unblock user:', error.message);
      onError?.(error);
      return false;
    }
  }, [fetchUsers, onError]);

  /**
   * Refresh current data
   */
  const refresh = useCallback(async (): Promise<void> => {
    console.log('🔄 Manual users data refresh requested');
    await fetchUsers();
  }, [fetchUsers]);

  // Auto-start fetching on mount
  useEffect(() => {
    if (autoStart) {
      fetchUsers();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [autoStart, fetchUsers]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    users,
    isLoading,
    error,
    isUsingMockData,
    lastFetch,
    currentPage,
    filters,
    fetchUsers,
    setPage,
    setFilters: setFiltersAndFetch,
    blockUser,
    unblockUser,
    refresh
  };
}

export default useUsersData;