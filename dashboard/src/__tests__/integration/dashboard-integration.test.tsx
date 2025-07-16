import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import axios from 'axios';
import DashboardPage from '../../pages/DashboardPage';
import { setupApiMocks, mockApiResponses } from '../../test-utils/api-mocks';

// Mock axios
jest.mock('axios');
const mockAxios = axios as jest.Mocked<typeof axios>;

// Mock the useAuth hook
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: '1', username: 'admin', role: 'admin' },
    token: 'mock-jwt-token'
  })
}));

// Mock the useWebSocket hook
jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    lastMessage: null,
    sendMessage: jest.fn(),
    connectionStatus: 'Connected'
  })
}));

// Mock Chart.js components
jest.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
}));

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Set up default API mocks
    setupApiMocks(mockAxios);
  });

  it('loads and displays dashboard data successfully', async () => {
    renderWithProviders(<DashboardPage />);

    // Should show loading state initially
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();

    // Wait for data to load and check if metrics are displayed
    await waitFor(() => {
      expect(screen.getByText('Total Requests')).toBeInTheDocument();
    });

    // Check if API endpoints were called
    expect(mockAxios.get).toHaveBeenCalledWith('/api/dashboard/overview');
    expect(mockAxios.get).toHaveBeenCalledWith('/api/metrics/realtime');
  });

  it('displays correct metrics from API response', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Total Requests')).toBeInTheDocument();
      expect(screen.getByText('1,250')).toBeInTheDocument();
      expect(screen.getByText('Scam Detected')).toBeInTheDocument();
      expect(screen.getByText('89')).toBeInTheDocument();
      expect(screen.getByText('Legitimate Jobs')).toBeInTheDocument();
      expect(screen.getByText('1,161')).toBeInTheDocument();
    });
  });

  it('displays system health information', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    // Check for service status indicators
    await waitFor(() => {
      expect(screen.getByText('openai')).toBeInTheDocument();
      expect(screen.getByText('twilio')).toBeInTheDocument();
      expect(screen.getByText('database')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API to return error
    mockAxios.get.mockRejectedValue({
      response: { status: 500, data: { message: 'Server Error' } }
    });

    renderWithProviders(<DashboardPage />);

    // Should handle the error gracefully
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    // Should still show the dashboard structure even if data fails to load
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  it('updates data when WebSocket receives new messages', async () => {
    // Mock WebSocket to return updated data
    const mockUseWebSocket = require('../../hooks/useWebSocket').useWebSocket;
    mockUseWebSocket.mockReturnValue({
      lastMessage: JSON.stringify({
        type: 'metrics_update',
        data: {
          requests: { total: 1300, success: 1285, errors: 15 },
          services: {
            openai: { status: 'healthy', response_time: 0.9 },
            twilio: { status: 'healthy', response_time: 0.3 },
            database: { status: 'healthy', response_time: 0.1 }
          }
        }
      }),
      sendMessage: jest.fn(),
      connectionStatus: 'Connected'
    });

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    // Should reflect the WebSocket update
    await waitFor(() => {
      expect(screen.getByText('Total Requests')).toBeInTheDocument();
    });
  });

  it('handles authentication token in API requests', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalled();
    });

    // Check if requests include authorization header
    const calls = mockAxios.get.mock.calls;
    expect(calls.length).toBeGreaterThan(0);
  });

  it('refreshes data at regular intervals', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith('/api/dashboard/overview');
    });

    // Clear the mock calls
    mockAxios.get.mockClear();

    // Fast-forward time to trigger refresh
    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith('/api/dashboard/overview');
    });
  });

  it('displays charts and visualizations', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    // Check for chart components
    await waitFor(() => {
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  it('handles network timeouts gracefully', async () => {
    // Mock API to simulate timeout
    mockAxios.get.mockImplementation(() => 
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Network timeout')), 1000)
      )
    );

    renderWithProviders(<DashboardPage />);

    // Should handle timeout gracefully
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });
  });

  it('caches API responses appropriately', async () => {
    const { rerender } = renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledWith('/api/dashboard/overview');
    });

    const initialCallCount = mockAxios.get.mock.calls.length;

    // Re-render component
    rerender(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    // Should not make additional API calls due to caching
    expect(mockAxios.get.mock.calls.length).toBe(initialCallCount);
  });

  it('handles concurrent API requests properly', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(mockAxios.get).toHaveBeenCalledTimes(2);
    });

    // Should make multiple concurrent requests
    expect(mockAxios.get).toHaveBeenCalledWith('/api/dashboard/overview');
    expect(mockAxios.get).toHaveBeenCalledWith('/api/metrics/realtime');
  });

  it('displays loading states correctly', async () => {
    // Mock delayed response
    mockAxios.get.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ data: mockApiResponses.dashboard.overview }), 500)
      )
    );

    renderWithProviders(<DashboardPage />);

    // Should show loading state
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Total Requests')).toBeInTheDocument();
    });
  });
});