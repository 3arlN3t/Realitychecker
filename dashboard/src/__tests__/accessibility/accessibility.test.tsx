import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import components to test
import App from '../../App';
import Layout from '../../components/Layout';
import SystemHealthCard from '../../components/admin/SystemHealthCard';
import UserTable from '../../components/users/UserTable';
import ClassificationChart from '../../components/analytics/ClassificationChart';
import LoginPage from '../../pages/LoginPage';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock dependencies
jest.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: '1', username: 'admin', role: 'admin' },
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

jest.mock('../../providers/QueryProvider', () => ({
  QueryProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    lastMessage: null,
    sendMessage: jest.fn(),
    connectionStatus: 'Connected',
  }),
}));

// Mock chart components
jest.mock('recharts', () => ({
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div role="img" aria-label="Pie Chart">{children}</div>
  ),
  Pie: () => <div />,
  Cell: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  Tooltip: () => <div />,
  Legend: () => <div />,
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

describe('Accessibility Tests', () => {
  it('should not have accessibility violations in the main App', async () => {
    const { container } = renderWithProviders(<App />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations in the Layout component', async () => {
    const { container } = renderWithProviders(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations in the SystemHealthCard', async () => {
    const mockHealth = {
      status: 'healthy' as const,
      uptime: '99.9%',
      lastUpdated: '10:30:00 AM',
      memoryUsage: 65,
      cpuUsage: 45,
      services: {
        openai: {
          status: 'healthy' as const,
          responseTime: 250,
          lastCheck: '2025-01-16T10:30:00Z',
          errorCount: 0,
        },
        twilio: {
          status: 'healthy' as const,
          responseTime: 150,
          lastCheck: '2025-01-16T10:29:00Z',
          errorCount: 0,
        },
      },
    };

    const { container } = renderWithProviders(
      <SystemHealthCard health={mockHealth} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations in the UserTable', async () => {
    const mockUsers = [
      {
        id: '1',
        phoneNumber: '+1234567890',
        interactionCount: 5,
        lastInteraction: '2025-01-16T10:30:00Z',
        status: 'active' as const,
        trustScore: 85,
      },
      {
        id: '2',
        phoneNumber: '+0987654321',
        interactionCount: 12,
        lastInteraction: '2025-01-15T14:20:00Z',
        status: 'blocked' as const,
        trustScore: 25,
      },
    ];

    const { container } = renderWithProviders(
      <UserTable
        users={mockUsers}
        onUserSelect={jest.fn()}
        onStatusChange={jest.fn()}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations in the ClassificationChart', async () => {
    const mockData = [
      { name: 'Legitimate', value: 500, color: '#4caf50' },
      { name: 'Suspicious', value: 200, color: '#ff9800' },
      { name: 'Likely Scam', value: 100, color: '#f44336' },
    ];

    const { container } = renderWithProviders(
      <ClassificationChart data={mockData} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations in the LoginPage', async () => {
    const { container } = renderWithProviders(<LoginPage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper heading hierarchy', async () => {
    const { container } = renderWithProviders(
      <div>
        <h1>Main Title</h1>
        <h2>Section Title</h2>
        <h3>Subsection Title</h3>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper form labels', async () => {
    const { container } = renderWithProviders(
      <form>
        <label htmlFor="username">Username:</label>
        <input id="username" type="text" />
        <label htmlFor="password">Password:</label>
        <input id="password" type="password" />
        <button type="submit">Login</button>
      </form>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper button accessibility', async () => {
    const { container } = renderWithProviders(
      <div>
        <button type="button">Regular Button</button>
        <button type="submit">Submit Button</button>
        <button type="button" aria-label="Close dialog">
          ×
        </button>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper table accessibility', async () => {
    const { container } = renderWithProviders(
      <table>
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Email</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>John Doe</td>
            <td>john@example.com</td>
            <td>Active</td>
          </tr>
          <tr>
            <td>Jane Smith</td>
            <td>jane@example.com</td>
            <td>Inactive</td>
          </tr>
        </tbody>
      </table>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper image accessibility', async () => {
    const { container } = renderWithProviders(
      <div>
        <img src="/test-image.jpg" alt="Test image description" />
        <img src="/decorative-image.jpg" alt="" role="presentation" />
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper link accessibility', async () => {
    const { container } = renderWithProviders(
      <div>
        <a href="/dashboard">Dashboard</a>
        <a href="/analytics">Analytics</a>
        <a href="https://external.com" target="_blank" rel="noopener noreferrer">
          External Link
        </a>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper navigation accessibility', async () => {
    const { container } = renderWithProviders(
      <nav aria-label="Main navigation">
        <ul>
          <li><a href="/dashboard">Dashboard</a></li>
          <li><a href="/analytics">Analytics</a></li>
          <li><a href="/users">Users</a></li>
        </ul>
      </nav>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA attributes', async () => {
    const { container } = renderWithProviders(
      <div>
        <button aria-expanded="false" aria-controls="menu">
          Menu
        </button>
        <div id="menu" role="menu" aria-hidden="true">
          <div role="menuitem">Item 1</div>
          <div role="menuitem">Item 2</div>
        </div>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper focus management', async () => {
    const { container } = renderWithProviders(
      <div>
        <button tabIndex={0}>First Button</button>
        <button tabIndex={0}>Second Button</button>
        <button tabIndex={-1}>Skip Tab Button</button>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper color contrast', async () => {
    const { container } = renderWithProviders(
      <div>
        <p style={{ color: '#000000', backgroundColor: '#ffffff' }}>
          High contrast text
        </p>
        <button style={{ color: '#ffffff', backgroundColor: '#0066cc' }}>
          High contrast button
        </button>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should handle empty states accessibly', async () => {
    const { container } = renderWithProviders(
      <div>
        <h2>Data Table</h2>
        <p>No data available</p>
        <table>
          <thead>
            <tr>
              <th>Column 1</th>
              <th>Column 2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={2}>No data to display</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should handle error states accessibly', async () => {
    const { container } = renderWithProviders(
      <div>
        <div role="alert" aria-live="polite">
          Error: Unable to load data
        </div>
        <button type="button">Retry</button>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should handle loading states accessibly', async () => {
    const { container } = renderWithProviders(
      <div>
        <div role="status" aria-live="polite">
          Loading data...
        </div>
        <div aria-label="Loading" role="progressbar">
          <div style={{ width: '50%' }} />
        </div>
      </div>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});