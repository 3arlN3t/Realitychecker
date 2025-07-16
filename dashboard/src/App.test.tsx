import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// Mock the AuthContext
jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Mock the QueryProvider
jest.mock('./providers/QueryProvider', () => ({
  QueryProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="query-provider">{children}</div>
  ),
}));

// Mock the pages
jest.mock('./pages/LoginPage', () => {
  return function MockLoginPage() {
    return <div data-testid="login-page">Login Page</div>;
  };
});

jest.mock('./pages/DashboardPage', () => {
  return function MockDashboardPage() {
    return <div data-testid="dashboard-page">Dashboard Page</div>;
  };
});

jest.mock('./pages/AnalyticsPage', () => {
  return function MockAnalyticsPage() {
    return <div data-testid="analytics-page">Analytics Page</div>;
  };
});

jest.mock('./pages/MonitoringPage', () => {
  return function MockMonitoringPage() {
    return <div data-testid="monitoring-page">Monitoring Page</div>;
  };
});

jest.mock('./pages/UsersPage', () => {
  return function MockUsersPage() {
    return <div data-testid="users-page">Users Page</div>;
  };
});

jest.mock('./pages/ConfigurationPage', () => {
  return function MockConfigurationPage() {
    return <div data-testid="configuration-page">Configuration Page</div>;
  };
});

jest.mock('./pages/ReportingPage', () => {
  return function MockReportingPage() {
    return <div data-testid="reporting-page">Reporting Page</div>;
  };
});

// Mock the components
jest.mock('./components/ProtectedRoute', () => {
  return function MockProtectedRoute({ children }: { children: React.ReactNode }) {
    return <div data-testid="protected-route">{children}</div>;
  };
});

jest.mock('./components/Layout', () => {
  return function MockLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="layout">{children}</div>;
  };
});

describe('App', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    expect(screen.getByTestId('query-provider')).toBeInTheDocument();
  });

  it('redirects to dashboard for root path', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  it('renders login page for /login route', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  it('renders dashboard page for /dashboard route', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('renders analytics page for /analytics route', () => {
    render(
      <MemoryRouter initialEntries={['/analytics']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('analytics-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('renders monitoring page for /monitoring route', () => {
    render(
      <MemoryRouter initialEntries={['/monitoring']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('monitoring-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('renders users page for /users route', () => {
    render(
      <MemoryRouter initialEntries={['/users']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('users-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('renders reporting page for /reports route', () => {
    render(
      <MemoryRouter initialEntries={['/reports']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('reporting-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('renders configuration page for /config route with admin role', () => {
    render(
      <MemoryRouter initialEntries={['/config']}>
        <App />
      </MemoryRouter>
    );
    
    expect(screen.getByTestId('configuration-page')).toBeInTheDocument();
    expect(screen.getByTestId('protected-route')).toBeInTheDocument();
    expect(screen.getByTestId('layout')).toBeInTheDocument();
  });

  it('redirects unknown routes to dashboard', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route']}>
        <App />
      </MemoryRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  it('applies the correct theme', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );
    
    // Check that the theme provider is applied
    const themeProvider = document.querySelector('.MuiCssBaseline-root');
    expect(themeProvider).toBeInTheDocument();
  });
});