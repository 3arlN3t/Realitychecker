/**
 * Tests for useUsersData hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useUsersData } from '../useUsersData';
import { UsersAPI } from '../../lib/api';

// Mock the API
jest.mock('../../lib/api');
const mockUsersAPI = UsersAPI as jest.Mocked<typeof UsersAPI>;

describe('useUsersData', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    console.log = jest.fn();
    console.warn = jest.fn();
    console.error = jest.fn();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useUsersData({ autoStart: false }));

    expect(result.current.users).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isUsingMockData).toBe(false);
    expect(result.current.currentPage).toBe(1);
    expect(result.current.filters).toEqual({});
  });

  it('should fetch users successfully', async () => {
    const mockResponse = {
      users: [
        {
          phone_number: '+1234567890',
          total_requests: 5,
          first_interaction: '2024-01-01T00:00:00Z',
          last_interaction: '2024-01-02T00:00:00Z',
          is_blocked: false,
          success_rate: 95,
          avg_response_time: 1.2
        }
      ],
      total: 1,
      page: 1,
      limit: 20,
      total_pages: 1
    };

    mockUsersAPI.getUsers.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useUsersData());

    await waitFor(() => {
      expect(result.current.users).toEqual(mockResponse);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isUsingMockData).toBe(false);
    });
  });

  it('should use mock data as fallback when API fails', async () => {
    mockUsersAPI.getUsers.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useUsersData({ useMockFallback: true }));

    await waitFor(() => {
      expect(result.current.users).not.toBeNull();
      expect(result.current.isUsingMockData).toBe(true);
      expect(result.current.error).toBeInstanceOf(Error);
    });
  });

  it('should handle user blocking', async () => {
    mockUsersAPI.blockUser.mockResolvedValue({ success: true, message: 'User blocked' });
    mockUsersAPI.getUsers.mockResolvedValue({
      users: [],
      total: 0,
      page: 1,
      limit: 20,
      total_pages: 0
    });

    const { result } = renderHook(() => useUsersData({ autoStart: false }));

    await act(async () => {
      const success = await result.current.blockUser('+1234567890', 'Spam');
      expect(success).toBe(true);
    });

    expect(mockUsersAPI.blockUser).toHaveBeenCalledWith('+1234567890', 'Spam');
  });

  it('should handle pagination', async () => {
    mockUsersAPI.getUsers.mockResolvedValue({
      users: [],
      total: 0,
      page: 2,
      limit: 20,
      total_pages: 1
    });

    const { result } = renderHook(() => useUsersData({ autoStart: false }));

    await act(async () => {
      result.current.setPage(2);
    });

    expect(mockUsersAPI.getUsers).toHaveBeenCalledWith(2, 20, {});
  });

  it('should handle filtering', async () => {
    const filters = { search: 'test', blocked: true };
    mockUsersAPI.getUsers.mockResolvedValue({
      users: [],
      total: 0,
      page: 1,
      limit: 20,
      total_pages: 0
    });

    const { result } = renderHook(() => useUsersData({ autoStart: false }));

    await act(async () => {
      result.current.setFilters(filters);
    });

    expect(mockUsersAPI.getUsers).toHaveBeenCalledWith(1, 20, filters);
  });
});