import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  username: string;
  role: 'admin' | 'analyst';
  createdAt: string;
  lastLogin?: string;
}

export interface AuthResult {
  success: boolean;
  user?: User;
  token?: string;
  refreshToken?: string;
  errorMessage?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<AuthResult>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Sample users for testing
const SAMPLE_USERS = [
  {
    username: 'admin',
    password: 'admin123',
    role: 'admin' as const,
    createdAt: '2024-01-15T10:00:00Z',
    lastLogin: '2024-07-16T08:30:00Z',
  },
  {
    username: 'analyst',
    password: 'analyst123',
    role: 'analyst' as const,
    createdAt: '2024-02-01T14:00:00Z',
    lastLogin: '2024-07-16T09:15:00Z',
  },
  {
    username: 'demo',
    password: 'demo123',
    role: 'analyst' as const,
    createdAt: '2024-03-10T16:30:00Z',
    lastLogin: '2024-07-15T17:45:00Z',
  },
];

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth data on app load
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<AuthResult> => {
    try {
      // Get API base URL
      const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      // Make API call to backend
      const response = await fetch(`${apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const user: User = {
          username: data.user.username,
          role: data.user.role,
          createdAt: data.user.created_at,
          lastLogin: data.user.last_login,
        };
        
        const token = data.access_token;
        
        setUser(user);
        setToken(token);
        
        // Store in localStorage
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify(user));
        
        console.log('✅ Login successful:', { username: user.username, role: user.role });
        
        return {
          success: true,
          user,
          token,
          refreshToken: data.refresh_token,
        };
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
        console.warn('⚠️ Login failed:', errorData.detail);
        
        return {
          success: false,
          errorMessage: errorData.detail || 'Invalid username or password',
        };
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      
      // Fallback to sample users if API is not available
      console.log('🎭 API unavailable, trying sample users...');
      
      const sampleUser = SAMPLE_USERS.find(
        user => user.username === username && user.password === password
      );

      if (sampleUser) {
        const user: User = {
          username: sampleUser.username,
          role: sampleUser.role,
          createdAt: sampleUser.createdAt,
          lastLogin: new Date().toISOString(),
        };
        
        const token = `mock-jwt-token-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        setUser(user);
        setToken(token);
        
        // Store in localStorage
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify(user));
        
        console.log('🎭 Using mock authentication:', { username: user.username, role: user.role });
        
        return {
          success: true,
          user,
          token,
        };
      }

      return {
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Network error occurred',
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};