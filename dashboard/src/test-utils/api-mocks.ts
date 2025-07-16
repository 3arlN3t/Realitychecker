import axios from 'axios';

// Mock API responses
export const mockApiResponses = {
  // Authentication responses
  login: {
    success: {
      token: 'mock-jwt-token',
      user: { id: '1', username: 'admin', role: 'admin' }
    },
    failure: {
      message: 'Invalid credentials'
    }
  },

  // Dashboard data responses
  dashboard: {
    overview: {
      totalRequests: 1250,
      scamDetected: 89,
      legitimateJobs: 1161,
      responseTime: 1.2,
      uptime: '99.9%'
    },
    metrics: {
      requests: {
        total: 1250,
        success: 1235,
        errors: 15,
        avg_response_time_seconds: 1.2
      },
      services: {
        openai: { status: 'healthy', response_time: 0.8 },
        twilio: { status: 'healthy', response_time: 0.3 },
        database: { status: 'healthy', response_time: 0.1 }
      }
    }
  },

  // Analytics responses
  analytics: {
    trends: {
      period: '7d',
      data: [
        { date: '2025-01-10', requests: 150, scams: 12 },
        { date: '2025-01-11', requests: 180, scams: 15 },
        { date: '2025-01-12', requests: 165, scams: 8 },
        { date: '2025-01-13', requests: 200, scams: 18 },
        { date: '2025-01-14', requests: 175, scams: 10 },
        { date: '2025-01-15', requests: 190, scams: 14 },
        { date: '2025-01-16', requests: 180, scams: 12 }
      ]
    },
    classification: [
      { name: 'Legitimate', value: 1161, color: '#4caf50' },
      { name: 'Suspicious', value: 45, color: '#ff9800' },
      { name: 'Likely Scam', value: 44, color: '#f44336' }
    ]
  },

  // User management responses
  users: {
    list: {
      users: [
        {
          id: '1',
          phoneNumber: '+1234567890',
          interactionCount: 5,
          lastInteraction: '2025-01-16T10:30:00Z',
          status: 'active',
          trustScore: 85
        },
        {
          id: '2',
          phoneNumber: '+0987654321',
          interactionCount: 12,
          lastInteraction: '2025-01-15T14:20:00Z',
          status: 'active',
          trustScore: 92
        }
      ],
      pagination: {
        page: 1,
        limit: 10,
        total: 2,
        pages: 1
      }
    },
    interactions: {
      interactions: [
        {
          id: '1',
          timestamp: '2025-01-16T10:30:00Z',
          type: 'text_analysis',
          content: 'Job posting analysis request',
          result: 'legitimate',
          confidence: 0.85
        },
        {
          id: '2',
          timestamp: '2025-01-16T10:25:00Z',
          type: 'pdf_analysis',
          content: 'PDF document analysis',
          result: 'suspicious',
          confidence: 0.72
        }
      ]
    }
  },

  // Monitoring responses
  monitoring: {
    activeRequests: {
      active_requests: [
        {
          id: 'req-1',
          type: 'text_analysis',
          status: 'processing',
          started_at: '2025-01-16T10:30:00Z',
          duration_ms: 1200,
          user: '+1234567890'
        }
      ],
      queue_depth: 0,
      processing_capacity: { used: 1, total: 10, percent: 10.0 }
    },
    errorRates: {
      period: 'hour',
      error_rates: [
        { timestamp: '2025-01-16T10:00:00Z', error_rate: 2.5, total_requests: 120, error_count: 3 },
        { timestamp: '2025-01-16T11:00:00Z', error_rate: 1.8, total_requests: 110, error_count: 2 }
      ]
    }
  },

  // Configuration responses
  config: {
    current: {
      openai_model: 'gpt-4',
      rate_limit: { requests_per_minute: 10, requests_per_hour: 100 },
      pdf_size_limit_mb: 10,
      log_level: 'INFO',
      alert_thresholds: { error_rate: 5.0, response_time: 3.0 }
    },
    update: {
      message: 'Configuration updated successfully'
    }
  }
};

// Mock API error responses
export const mockApiErrors = {
  unauthorized: {
    status: 401,
    message: 'Unauthorized'
  },
  forbidden: {
    status: 403,
    message: 'Forbidden'
  },
  notFound: {
    status: 404,
    message: 'Not Found'
  },
  serverError: {
    status: 500,
    message: 'Internal Server Error'
  }
};

// Mock axios instance
export const createMockAxios = () => {
  const mockAxios = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  };

  return mockAxios;
};

// Helper function to setup API mocks
export const setupApiMocks = (mockAxios: any) => {
  // Login endpoint
  mockAxios.post.mockImplementation((url: string, data: any) => {
    if (url.includes('/auth/login')) {
      const { username, password } = data;
      if (username === 'admin' && password === 'admin123') {
        return Promise.resolve({ data: mockApiResponses.login.success });
      } else if (username === 'analyst' && password === 'analyst123') {
        return Promise.resolve({ 
          data: { 
            token: 'mock-jwt-token', 
            user: { id: '2', username: 'analyst', role: 'analyst' } 
          } 
        });
      } else {
        return Promise.reject({ response: { status: 401, data: mockApiResponses.login.failure } });
      }
    }
    return Promise.reject({ response: { status: 404, data: mockApiErrors.notFound } });
  });

  // Dashboard endpoints
  mockAxios.get.mockImplementation((url: string) => {
    if (url.includes('/api/dashboard/overview')) {
      return Promise.resolve({ data: mockApiResponses.dashboard.overview });
    }
    if (url.includes('/api/metrics/realtime')) {
      return Promise.resolve({ data: mockApiResponses.dashboard.metrics });
    }
    if (url.includes('/api/analytics/trends')) {
      return Promise.resolve({ data: mockApiResponses.analytics.trends });
    }
    if (url.includes('/api/analytics/classification')) {
      return Promise.resolve({ data: mockApiResponses.analytics.classification });
    }
    if (url.includes('/api/users')) {
      return Promise.resolve({ data: mockApiResponses.users.list });
    }
    if (url.includes('/api/users/') && url.includes('/interactions')) {
      return Promise.resolve({ data: mockApiResponses.users.interactions });
    }
    if (url.includes('/api/monitoring/active-requests')) {
      return Promise.resolve({ data: mockApiResponses.monitoring.activeRequests });
    }
    if (url.includes('/api/monitoring/error-rates')) {
      return Promise.resolve({ data: mockApiResponses.monitoring.errorRates });
    }
    if (url.includes('/api/config')) {
      return Promise.resolve({ data: mockApiResponses.config.current });
    }
    
    return Promise.reject({ response: { status: 404, data: mockApiErrors.notFound } });
  });

  // Configuration update endpoint
  mockAxios.post.mockImplementation((url: string, data: any) => {
    if (url.includes('/api/config')) {
      return Promise.resolve({ data: mockApiResponses.config.update });
    }
    return Promise.reject({ response: { status: 404, data: mockApiErrors.notFound } });
  });

  return mockAxios;
};

// Helper function to simulate network delays
export const withDelay = (response: any, delay: number = 100) => {
  return new Promise((resolve) => {
    setTimeout(() => resolve(response), delay);
  });
};

// Helper function to simulate API errors
export const simulateError = (error: any, delay: number = 100) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => reject(error), delay);
  });
};