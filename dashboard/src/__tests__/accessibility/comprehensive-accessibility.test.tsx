import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Import all components to test
import App from '../../App';
import DashboardPage from '../../pages/DashboardPage';
import AnalyticsPage from '../../pages/AnalyticsPage';
import ConfigurationPage from '../../pages/ConfigurationPage';
import MonitoringPage from '../../pages/MonitoringPage';
import ReportingPage from '../../pages/ReportingPage';
import UsersPage from '../../pages/UsersPage';
import LoginPage from '../../pages/LoginPage';

// Import components
import Layout from '../../components/Layout';
import ProtectedRoute from '../../components/ProtectedRoute';
import SystemHealthCard from '../../components/admin/SystemHealthCard';
import MetricsOverviewCard from '../../components/admin/MetricsOverviewCard';
import ActiveAlertsCard from '../../components/admin/ActiveAlertsCard';
import ServiceStatusGrid from '../../components/admin/ServiceStatusGrid';
import ClassificationChart from '../../components/analytics/ClassificationChart';
import PeakHoursChart from '../../components/analytics/PeakHoursChart';
import PeriodSelector from '../../components/analytics/PeriodSelector';
import UsageTrendsChart from '../../components/analytics/UsageTrendsChart';
import UserEngagementMetrics from '../../components/analytics/UserEngagementMetrics';
import AlertThresholdSettings from '../../components/configuration/AlertThresholdSettings';
import ConfigSection from '../../components/configuration/ConfigSection';
import ConfigurationForm from '../../components/configuration/ConfigurationForm';
import LogLevelSelector from '../../components/configuration/LogLevelSelector';
import ModelSelector from '../../components/configuration/ModelSelector';
import PDFSizeInput from '../../components/configuration/PDFSizeInput';
import RateLimitInput from '../../components/configuration/RateLimitInput';
import ActiveRequestsTable from '../../components/monitoring/ActiveRequestsTable';
import ErrorRateChart from '../../components/monitoring/ErrorRateChart';
import LiveMetricsCard from '../../components/monitoring/LiveMetricsCard';
import ResponseTimeChart from '../../components/monitoring/ResponseTimeChart';
import ReportGenerator from '../../components/reporting/ReportGenerator';
import ReportHistory from '../../components/reporting/ReportHistory';
import ReportScheduler from '../../components/reporting/ReportScheduler';
import ReportTemplates from '../../components/reporting/ReportTemplates';
import UserInteractionModal from '../../components/users/UserInteractionModal';
import UserSearchBar from '../../components/users/UserSearchBar';
import UserTable from '../../components/users/UserTable';

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

jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    lastMessage: null,
    sendMessage: jest.fn(),
    connectionStatus: 'Connected',
  }),
}));

// Mock chart components
jest.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div role="img" aria-label="Line Chart">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div role="img" aria-label="Bar Chart">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div role="img" aria-label="Pie Chart">{children}</div>
  ),
  Line: () => <div />,
  Bar: () => <div />,
  Pie: () => <div />,
  Cell: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  Tooltip: () => <div role="tooltip" />,
  Legend: () => <div role="legend" />,
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

// Mock data for components
const mockSystemHealth = {
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
    database: {
      status: 'degraded' as const,
      responseTime: 350,
      lastCheck: '2025-01-16T10:28:00Z',
      errorCount: 2,
    },
  },
};

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

const mockClassificationData = [
  { name: 'Legitimate', value: 500, color: '#4caf50' },
  { name: 'Suspicious', value: 200, color: '#ff9800' },
  { name: 'Likely Scam', value: 100, color: '#f44336' },
];

const mockUsageTrendsData = Array.from({ length: 7 }, (_, i) => ({
  date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
  requests: Math.floor(Math.random() * 100) + 50,
}));

const mockActiveRequests = [
  {
    id: 'req-1',
    type: 'text_analysis',
    status: 'processing',
    startedAt: '2025-01-16T15:25:00Z',
    duration: 5000,
    user: '+1234567890',
  },
  {
    id: 'req-2',
    type: 'pdf_processing',
    status: 'completed',
    startedAt: '2025-01-16T15:20:00Z',
    duration: 12000,
    user: '+0987654321',
  },
];

describe('Comprehensive Accessibility Tests', () => {
  describe('Page-level accessibility', () => {
    it('should not have accessibility violations in the main App', async () => {
      const { container } = renderWithProviders(<App />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Dashboard page', async () => {
      const { container } = renderWithProviders(<DashboardPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Analytics page', async () => {
      const { container } = renderWithProviders(<AnalyticsPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Configuration page', async () => {
      const { container } = renderWithProviders(<ConfigurationPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Monitoring page', async () => {
      const { container } = renderWithProviders(<MonitoringPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Reporting page', async () => {
      const { container } = renderWithProviders(<ReportingPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Users page', async () => {
      const { container } = renderWithProviders(<UsersPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the Login page', async () => {
      const { container } = renderWithProviders(<LoginPage />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Layout and navigation accessibility', () => {
    it('should not have accessibility violations in the Layout component', async () => {
      const { container } = renderWithProviders(
        <Layout>
          <div>Test Content</div>
        </Layout>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ProtectedRoute component', async () => {
      const { container } = renderWithProviders(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Admin dashboard components accessibility', () => {
    it('should not have accessibility violations in the SystemHealthCard', async () => {
      const { container } = renderWithProviders(
        <SystemHealthCard health={mockSystemHealth} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the MetricsOverviewCard', async () => {
      const mockMetrics = {
        totalRequests: 1250,
        requestsToday: 45,
        errorRate: 2.3,
        avgResponseTime: 1.2,
      };
      const { container } = renderWithProviders(
        <MetricsOverviewCard metrics={mockMetrics} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ActiveAlertsCard', async () => {
      const mockAlerts = [
        { id: '1', severity: 'high', message: 'API error rate above threshold', timestamp: '2025-01-16T10:30:00Z' },
        { id: '2', severity: 'medium', message: 'Database response time degraded', timestamp: '2025-01-16T09:45:00Z' },
      ];
      const { container } = renderWithProviders(
        <ActiveAlertsCard alerts={mockAlerts} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ServiceStatusGrid', async () => {
      const { container } = renderWithProviders(
        <ServiceStatusGrid services={mockSystemHealth.services} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Analytics components accessibility', () => {
    it('should not have accessibility violations in the ClassificationChart', async () => {
      const { container } = renderWithProviders(
        <ClassificationChart data={mockClassificationData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the PeakHoursChart', async () => {
      const mockPeakHoursData = Array.from({ length: 24 }, (_, i) => ({
        hour: i,
        requests: Math.floor(Math.random() * 50),
      }));
      const { container } = renderWithProviders(
        <PeakHoursChart data={mockPeakHoursData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the PeriodSelector', async () => {
      const { container } = renderWithProviders(
        <PeriodSelector value="week" onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the UsageTrendsChart', async () => {
      const { container } = renderWithProviders(
        <UsageTrendsChart data={mockUsageTrendsData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the UserEngagementMetrics', async () => {
      const mockEngagementData = {
        activeUsers: 120,
        returningUsers: 75,
        averageInteractions: 3.5,
        retentionRate: 68,
      };
      const { container } = renderWithProviders(
        <UserEngagementMetrics data={mockEngagementData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Configuration components accessibility', () => {
    it('should not have accessibility violations in the AlertThresholdSettings', async () => {
      const mockThresholds = {
        errorRate: 5,
        responseTime: 2000,
        cpuUsage: 80,
        memoryUsage: 85,
      };
      const { container } = renderWithProviders(
        <AlertThresholdSettings thresholds={mockThresholds} onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ConfigSection', async () => {
      const { container } = renderWithProviders(
        <ConfigSection title="Test Section">
          <div>Test Content</div>
        </ConfigSection>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ConfigurationForm', async () => {
      const mockConfig = {
        openaiModel: 'gpt-4',
        maxPdfSizeMb: 10,
        rateLimitPerMinute: 60,
        logLevel: 'INFO',
        alertThresholds: {
          errorRate: 5,
          responseTime: 2000,
          cpuUsage: 80,
          memoryUsage: 85,
        },
      };
      const { container } = renderWithProviders(
        <ConfigurationForm config={mockConfig} onSave={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the LogLevelSelector', async () => {
      const { container } = renderWithProviders(
        <LogLevelSelector value="INFO" onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ModelSelector', async () => {
      const { container } = renderWithProviders(
        <ModelSelector value="gpt-4" onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the PDFSizeInput', async () => {
      const { container } = renderWithProviders(
        <PDFSizeInput value={10} onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the RateLimitInput', async () => {
      const { container } = renderWithProviders(
        <RateLimitInput value={60} onChange={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Monitoring components accessibility', () => {
    it('should not have accessibility violations in the ActiveRequestsTable', async () => {
      const { container } = renderWithProviders(
        <ActiveRequestsTable requests={mockActiveRequests} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ErrorRateChart', async () => {
      const mockErrorData = Array.from({ length: 10 }, (_, i) => ({
        time: new Date(Date.now() - i * 60000).toISOString(),
        rate: Math.random() * 5,
      }));
      const { container } = renderWithProviders(
        <ErrorRateChart data={mockErrorData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the LiveMetricsCard', async () => {
      const mockLiveMetrics = {
        activeRequests: 3,
        requestsPerMinute: 12,
        errorRate: 1.5,
        avgResponseTime: 0.8,
      };
      const { container } = renderWithProviders(
        <LiveMetricsCard metrics={mockLiveMetrics} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ResponseTimeChart', async () => {
      const mockResponseTimeData = Array.from({ length: 10 }, (_, i) => ({
        time: new Date(Date.now() - i * 60000).toISOString(),
        p50: Math.random() * 0.5,
        p95: Math.random() * 1.5,
        p99: Math.random() * 3.0,
      }));
      const { container } = renderWithProviders(
        <ResponseTimeChart data={mockResponseTimeData} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Reporting components accessibility', () => {
    it('should not have accessibility violations in the ReportGenerator', async () => {
      const { container } = renderWithProviders(
        <ReportGenerator onGenerate={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ReportHistory', async () => {
      const mockReports = [
        { id: '1', name: 'Monthly Usage Report', createdAt: '2025-01-15T10:30:00Z', format: 'PDF' },
        { id: '2', name: 'Weekly Analysis Summary', createdAt: '2025-01-10T14:20:00Z', format: 'CSV' },
      ];
      const { container } = renderWithProviders(
        <ReportHistory reports={mockReports} onDownload={() => {}} onDelete={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ReportScheduler', async () => {
      const { container } = renderWithProviders(
        <ReportScheduler onSchedule={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the ReportTemplates', async () => {
      const mockTemplates = [
        { id: '1', name: 'Monthly Usage Report', description: 'Detailed usage statistics for the month' },
        { id: '2', name: 'Scam Analysis Summary', description: 'Summary of scam detection patterns' },
      ];
      const { container } = renderWithProviders(
        <ReportTemplates templates={mockTemplates} onSelect={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('User management components accessibility', () => {
    it('should not have accessibility violations in the UserInteractionModal', async () => {
      const mockInteractions = [
        { id: '1', timestamp: '2025-01-16T10:30:00Z', messageType: 'text', content: 'Job posting analysis request' },
        { id: '2', timestamp: '2025-01-16T10:32:00Z', messageType: 'response', content: 'Analysis result: Legitimate' },
      ];
      const { container } = renderWithProviders(
        <UserInteractionModal
          open={true}
          onClose={() => {}}
          user={mockUsers[0]}
          interactions={mockInteractions}
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the UserSearchBar', async () => {
      const { container } = renderWithProviders(
        <UserSearchBar onSearch={() => {}} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should not have accessibility violations in the UserTable', async () => {
      const { container } = renderWithProviders(
        <UserTable
          users={mockUsers}
          onUserSelect={() => {}}
          onStatusChange={() => {}}
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('WCAG compliance for specific accessibility features', () => {
    it('should have proper keyboard navigation', async () => {
      const { container } = renderWithProviders(
        <div>
          <button>First Button</button>
          <button>Second Button</button>
          <a href="#">Link</a>
          <input type="text" placeholder="Input field" />
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

    it('should have proper form labels', async () => {
      const { container } = renderWithProviders(
        <form>
          <div>
            <label htmlFor="username">Username:</label>
            <input id="username" type="text" />
          </div>
          <div>
            <label htmlFor="password">Password:</label>
            <input id="password" type="password" />
          </div>
          <button type="submit">Submit</button>
        </form>
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
            <div role="menuitem" tabIndex={-1}>Item 1</div>
            <div role="menuitem" tabIndex={-1}>Item 2</div>
          </div>
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
          <div aria-label="Loading" role="progressbar" aria-valuenow={50} aria-valuemin={0} aria-valuemax={100}>
            <div style={{ width: '50%' }} />
          </div>
        </div>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});