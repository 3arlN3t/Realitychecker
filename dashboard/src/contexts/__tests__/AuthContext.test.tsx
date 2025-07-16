import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Test component that uses the auth context
const TestComponent = () => {
  const { isAuthenticated, user, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not authenticated'}</div>
      <div data-testid="user-info">{user ? `${user.username} (${user.role})` : 'no user'}</div>
      <button 
        data-testid="login-button" 
        onClick={() => login('admin', 'admin123')}
      >
        Login
      </button>
      <button 
        data-testid="logout-button" 
        onClick={logout}
      >
        Logout
      </button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();
    mockLocalStorage.removeItem.mockClear();
    mockLocalStorage.clear.mockClear();
  });

  it('provides initial unauthenticated state', () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');
    expect(screen.getByTestId('user-info')).toHaveTextContent('no user');
  });

  it('restores authenticated state from localStorage', () => {
    const mockToken = 'mock-token';
    const mockUser = { id: '1', username: 'admin', role: 'admin' };
    
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return mockToken;
      if (key === 'user') return JSON.stringify(mockUser);
      return null;
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)');
  });

  it('handles successful login', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');

    fireEvent.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)');
    });

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('token', 'mock-jwt-token');
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify({
      id: '1',
      username: 'admin',
      role: 'admin'
    }));
  });

  it('handles failed login with invalid credentials', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Create a button for invalid login
    const TestComponentWithInvalidLogin = () => {
      const { login } = useAuth();
      return (
        <button 
          data-testid="invalid-login-button" 
          onClick={() => login('invalid', 'invalid')}
        >
          Invalid Login
        </button>
      );
    };

    render(
      <AuthProvider>
        <TestComponentWithInvalidLogin />
      </AuthProvider>
    );

    fireEvent.click(screen.getByTestId('invalid-login-button'));

    // Should remain unauthenticated
    await waitFor(() => {
      expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
    });
  });

  it('handles logout', async () => {
    const mockToken = 'mock-token';
    const mockUser = { id: '1', username: 'admin', role: 'admin' };
    
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return mockToken;
      if (key === 'user') return JSON.stringify(mockUser);
      return null;
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');

    fireEvent.click(screen.getByTestId('logout-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');
      expect(screen.getByTestId('user-info')).toHaveTextContent('no user');
    });

    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token');
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user');
  });

  it('handles corrupted localStorage data gracefully', () => {
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return 'valid-token';
      if (key === 'user') return 'invalid-json';
      return null;
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Should fallback to unauthenticated state
    expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');
    expect(screen.getByTestId('user-info')).toHaveTextContent('no user');
  });

  it('throws error when useAuth is used outside AuthProvider', () => {
    // Mock console.error to prevent error output in tests
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });

  it('handles different user roles correctly', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    const TestAnalystLogin = () => {
      const { login } = useAuth();
      return (
        <button 
          data-testid="analyst-login-button" 
          onClick={() => login('analyst', 'analyst123')}
        >
          Analyst Login
        </button>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
        <TestAnalystLogin />
      </AuthProvider>
    );

    fireEvent.click(screen.getByTestId('analyst-login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-info')).toHaveTextContent('analyst (analyst)');
    });

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify({
      id: '2',
      username: 'analyst',
      role: 'analyst'
    }));
  });

  it('maintains authentication state across re-renders', () => {
    const mockToken = 'mock-token';
    const mockUser = { id: '1', username: 'admin', role: 'admin' };
    
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return mockToken;
      if (key === 'user') return JSON.stringify(mockUser);
      return null;
    });

    const { rerender } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');

    rerender(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user-info')).toHaveTextContent('admin (admin)');
  });
});