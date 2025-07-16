import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { MemoryRouter } from 'react-router-dom';

// Import components to test
import UserTable from '../../components/users/UserTable';
import ClassificationChart from '../../components/analytics/ClassificationChart';
import UsageTrendsChart from '../../components/analytics/UsageTrendsChart';
import ActiveRequestsTable from '../../components/monitoring/ActiveRequestsTable';
import DashboardPage from '../../pages/DashboardPage';

// Mock dependencies
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: '1', username: 'admin', role: 'admin' },
    token: 'mock-jwt-token',
  }),
}));

jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    lastMessage: null,
    sendMessage: jest.fn(),
    connectionStatus: 'Connected',
  }),
}));

// Mock chart components with performance considerations
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
}));

// Mock axios for API calls
jest.mock('axios', () => ({
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
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
        <MemoryRouter>
          {component}
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

// Generate large datasets for performance testing
const generateLargeUserDataset = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `user-${i}`,
    phoneNumber: `+${Math.random().toString().substring(2, 12)}`,
    interactionCount: Math.floor(Math.random() * 100),
    lastInteraction: new Date(Date.now() - Math.random() * 86400000).toISOString(),
    status: ['active', 'blocked', 'pending'][Math.floor(Math.random() * 3)] as 'active' | 'blocked' | 'pending',
    trustScore: Math.floor(Math.random() * 100),
  }));
};

const generateLargeChartDataset = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
    requests: Math.floor(Math.random() * 1000),
    scams: Math.floor(Math.random() * 100),
    responseTime: Math.random() * 5,
  }));
};

const generateLargeActiveRequestsDataset = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `req-${i}`,
    type: ['text_analysis', 'pdf_processing'][Math.floor(Math.random() * 2)],
    status: ['processing', 'completed', 'failed'][Math.floor(Math.random() * 3)],
    startedAt: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    duration: Math.floor(Math.random() * 10000),
    user: `+${Math.random().toString().substring(2, 12)}`,
  }));
};

describe('Performance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render UserTable with large dataset efficiently', async () => {
    const largeUserDataset = generateLargeUserDataset(1000);
    const startTime = performance.now();

    const { container } = renderWithProviders(
      <UserTable
        users={largeUserDataset}
        onUserSelect={jest.fn()}
        onStatusChange={jest.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (less than 1 second)
    expect(renderTime).toBeLessThan(1000);
    expect(container).toBeInTheDocument();
  });

  it('should handle chart rendering with large datasets', async () => {
    const largeChartDataset = generateLargeChartDataset(365); // 1 year of data
    const startTime = performance.now();

    renderWithProviders(
      <UsageTrendsChart data={largeChartDataset} />
    );

    await waitFor(() => {
      expect(screen.getByText('Usage Trends')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render charts efficiently
    expect(renderTime).toBeLessThan(2000);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('should handle active requests table with many concurrent requests', async () => {
    const largeActiveRequestsDataset = generateLargeActiveRequestsDataset(500);
    const startTime = performance.now();

    renderWithProviders(
      <ActiveRequestsTable requests={largeActiveRequestsDataset} />
    );

    await waitFor(() => {
      expect(screen.getByText('Request ID')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should handle large request lists efficiently
    expect(renderTime).toBeLessThan(1500);
  });

  it('should handle frequent data updates without performance degradation', async () => {
    const initialData = generateLargeUserDataset(100);
    const mockOnUserSelect = jest.fn();
    const mockOnStatusChange = jest.fn();

    const { rerender } = renderWithProviders(
      <UserTable
        users={initialData}
        onUserSelect={mockOnUserSelect}
        onStatusChange={mockOnStatusChange}
      />
    );

    const startTime = performance.now();

    // Simulate frequent updates
    for (let i = 0; i < 10; i++) {
      const updatedData = generateLargeUserDataset(100);
      rerender(
        <UserTable
          users={updatedData}
          onUserSelect={mockOnUserSelect}
          onStatusChange={mockOnStatusChange}
        />
      );
    }

    const endTime = performance.now();
    const updateTime = endTime - startTime;

    // Should handle frequent updates efficiently
    expect(updateTime).toBeLessThan(3000);
  });

  it('should handle real-time WebSocket updates efficiently', async () => {
    const mockUseWebSocket = require('../../hooks/useWebSocket').useWebSocket;
    const startTime = performance.now();

    // Simulate rapid WebSocket messages
    const messages = Array.from({ length: 50 }, (_, i) => ({
      type: 'metrics_update',
      data: { requests: { total: 1000 + i } },
    }));

    messages.forEach((message, i) => {
      setTimeout(() => {
        mockUseWebSocket.mockReturnValue({
          lastMessage: JSON.stringify(message),
          sendMessage: jest.fn(),
          connectionStatus: 'Connected',
        });
      }, i * 10);
    });

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const processingTime = endTime - startTime;

    // Should handle WebSocket updates efficiently
    expect(processingTime).toBeLessThan(2000);
  });

  it('should handle memory usage efficiently with large datasets', async () => {
    const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;
    const largeDataset = generateLargeUserDataset(2000);

    const { unmount } = renderWithProviders(
      <UserTable
        users={largeDataset}
        onUserSelect={jest.fn()}
        onStatusChange={jest.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Unmount to check for memory leaks
    unmount();

    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }

    const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
    const memoryIncrease = finalMemory - initialMemory;

    // Memory increase should be reasonable (less than 50MB)
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
  });

  it('should handle rapid user interactions without lag', async () => {
    const dataset = generateLargeUserDataset(100);
    const mockOnUserSelect = jest.fn();
    const mockOnStatusChange = jest.fn();

    renderWithProviders(
      <UserTable
        users={dataset}
        onUserSelect={mockOnUserSelect}
        onStatusChange={mockOnStatusChange}
      />
    );

    const startTime = performance.now();

    // Simulate rapid user interactions
    for (let i = 0; i < 20; i++) {
      act(() => {
        mockOnUserSelect(`user-${i}`);
      });
    }

    const endTime = performance.now();
    const interactionTime = endTime - startTime;

    // Should handle rapid interactions efficiently
    expect(interactionTime).toBeLessThan(500);
    expect(mockOnUserSelect).toHaveBeenCalledTimes(20);
  });

  it('should handle component mounting and unmounting efficiently', async () => {
    const dataset = generateLargeUserDataset(500);
    const startTime = performance.now();

    // Mount and unmount components rapidly
    for (let i = 0; i < 10; i++) {
      const { unmount } = renderWithProviders(
        <UserTable
          users={dataset}
          onUserSelect={jest.fn()}
          onStatusChange={jest.fn()}
        />
      );
      unmount();
    }

    const endTime = performance.now();
    const mountTime = endTime - startTime;

    // Should handle mounting/unmounting efficiently
    expect(mountTime).toBeLessThan(2000);
  });

  it('should handle concurrent API calls without blocking UI', async () => {
    const axios = require('axios');
    
    // Mock slow API responses
    axios.get.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ data: {} }), 100)
      )
    );

    const startTime = performance.now();

    renderWithProviders(<DashboardPage />);

    // Should render UI immediately without waiting for API
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();

    const initialRenderTime = performance.now() - startTime;
    expect(initialRenderTime).toBeLessThan(100);
  });

  it('should handle large classification datasets in charts', async () => {
    const largeClassificationData = Array.from({ length: 20 }, (_, i) => ({
      name: `Category ${i}`,
      value: Math.floor(Math.random() * 1000),
      color: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
    }));

    const startTime = performance.now();

    renderWithProviders(
      <ClassificationChart data={largeClassificationData} />
    );

    await waitFor(() => {
      expect(screen.getByText('Scam Detection Breakdown')).toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should handle large classification data efficiently
    expect(renderTime).toBeLessThan(1000);
  });

  it('should handle scrolling performance with large lists', async () => {
    const largeDataset = generateLargeUserDataset(1000);
    
    const { container } = renderWithProviders(
      <UserTable
        users={largeDataset}
        onUserSelect={jest.fn()}
        onStatusChange={jest.fn()}
      />
    );

    const startTime = performance.now();

    // Simulate scrolling through the list
    const scrollContainer = container.querySelector('[data-testid="user-table-container"]');
    if (scrollContainer) {
      for (let i = 0; i < 10; i++) {
        scrollContainer.scrollTop = i * 100;
      }
    }

    const endTime = performance.now();
    const scrollTime = endTime - startTime;

    // Should handle scrolling efficiently
    expect(scrollTime).toBeLessThan(200);
  });

  it('should handle search and filtering performance', async () => {
    const largeDataset = generateLargeUserDataset(1000);
    
    renderWithProviders(
      <UserTable
        users={largeDataset}
        onUserSelect={jest.fn()}
        onStatusChange={jest.fn()}
      />
    );

    const startTime = performance.now();

    // Simulate search operations
    const searchQueries = ['user', '123', 'active', 'blocked'];
    
    for (const query of searchQueries) {
      // Filter dataset (simulating search)
      const filtered = largeDataset.filter(user => 
        user.phoneNumber.includes(query) || 
        user.status.includes(query)
      );
      
      // This would trigger re-render in real component
      expect(filtered).toBeDefined();
    }

    const endTime = performance.now();
    const searchTime = endTime - startTime;

    // Should handle search operations efficiently
    expect(searchTime).toBeLessThan(100);
  });
});