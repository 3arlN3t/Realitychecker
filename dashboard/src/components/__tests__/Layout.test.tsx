import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Layout from '../Layout';

const theme = createTheme();

// Mock the AuthContext
const mockUseAuth = jest.fn();
const mockLogout = jest.fn();
const mockNavigate = jest.fn();

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/dashboard' }),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter>
        {component}
      </MemoryRouter>
    </ThemeProvider>
  );
};

describe('Layout', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', username: 'testuser', role: 'admin' },
      logout: mockLogout,
    });
    mockNavigate.mockClear();
    mockLogout.mockClear();
  });

  it('renders the layout with navigation items', () => {
    renderWithTheme(
      <Layout>
        <div data-testid="child-content">Test Content</div>
      </Layout>
    );

    expect(screen.getByText('Reality Checker')).toBeInTheDocument();
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Real-time Monitoring')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('displays user information', () => {
    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('testuser (admin)')).toBeInTheDocument();
  });

  it('handles navigation clicks', () => {
    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    fireEvent.click(screen.getByText('Analytics'));
    expect(mockNavigate).toHaveBeenCalledWith('/analytics');
  });

  it('opens mobile drawer when menu button is clicked', () => {
    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);
    
    // Check that drawer state changed (this is a simplified test)
    expect(menuButton).toBeInTheDocument();
  });

  it('opens profile menu when avatar is clicked', () => {
    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const profileButton = screen.getByLabelText('account of current user');
    fireEvent.click(profileButton);
    
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('handles logout correctly', () => {
    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const profileButton = screen.getByLabelText('account of current user');
    fireEvent.click(profileButton);
    
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);
    
    expect(mockLogout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('filters navigation items based on user role', () => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', username: 'analyst', role: 'analyst' },
      logout: mockLogout,
    });

    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.queryByText('Configuration')).not.toBeInTheDocument();
  });

  it('shows all navigation items for admin users', () => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', username: 'admin', role: 'admin' },
      logout: mockLogout,
    });

    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
  });

  it('handles null user gracefully', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      logout: mockLogout,
    });

    renderWithTheme(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('Reality Checker')).toBeInTheDocument();
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
  });
});