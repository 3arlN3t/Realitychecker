import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ServiceStatusGrid, { ServiceDetails } from '../ServiceStatusGrid';

const theme = createTheme();

const mockServices: Record<string, ServiceDetails> = {
  openai: {
    name: 'OpenAI GPT-4',
    description: 'AI analysis service for job ad scam detection',
    status: 'healthy',
    responseTime: 250,
    lastCheck: '2025-01-16T10:30:00Z',
    errorCount: 0,
    version: 'gpt-4-turbo',
    endpoint: 'https://api.openai.com/v1/chat/completions',
    dependencies: ['Internet', 'API Key'],
    metrics: {
      requestsPerMinute: 15,
      successRate: 98.5,
      avgResponseTime: 750,
      uptime: '99.5%',
    },
    recentErrors: [],
  },
  twilio: {
    name: 'Twilio WhatsApp',
    description: 'WhatsApp messaging service integration',
    status: 'warning',
    responseTime: 150,
    lastCheck: '2025-01-16T10:29:00Z',
    errorCount: 2,
    version: 'v2024-01-01',
    endpoint: 'https://api.twilio.com/2010-04-01/Accounts',
    dependencies: ['Internet', 'Webhook'],
    metrics: {
      requestsPerMinute: 25,
      successRate: 96.2,
      avgResponseTime: 300,
      uptime: '99.8%',
    },
    recentErrors: [
      {
        timestamp: '2025-01-16T10:25:00Z',
        error: 'Rate limit exceeded',
        count: 2,
      },
    ],
  },
  database: {
    name: 'Application Database',
    description: 'User data and analytics storage',
    status: 'critical',
    responseTime: 25,
    lastCheck: '2025-01-16T10:30:00Z',
    errorCount: 5,
    version: 'SQLite 3.40',
    dependencies: ['File System'],
    metrics: {
      requestsPerMinute: 40,
      successRate: 85.0,
      avgResponseTime: 50,
      uptime: '98.2%',
    },
    recentErrors: [
      {
        timestamp: '2025-01-16T10:28:00Z',
        error: 'Connection timeout',
        count: 3,
      },
      {
        timestamp: '2025-01-16T10:26:00Z',
        error: 'Lock timeout',
        count: 2,
      },
    ],
  },
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ServiceStatusGrid', () => {
  it('renders service health monitoring header', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    expect(screen.getByText('Service Health Monitoring')).toBeInTheDocument();
    expect(screen.getByText('3 Services')).toBeInTheDocument();
  });

  it('displays all services with their status', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    expect(screen.getByText('OpenAI GPT-4')).toBeInTheDocument();
    expect(screen.getByText('Twilio WhatsApp')).toBeInTheDocument();
    expect(screen.getByText('Application Database')).toBeInTheDocument();
    
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('WARNING')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('shows service descriptions', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    expect(screen.getByText('AI analysis service for job ad scam detection')).toBeInTheDocument();
    expect(screen.getByText('WhatsApp messaging service integration')).toBeInTheDocument();
    expect(screen.getByText('User data and analytics storage')).toBeInTheDocument();
  });

  it('displays response times correctly', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    expect(screen.getByText('250ms')).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
    expect(screen.getByText('25ms')).toBeInTheDocument();
  });

  it('shows error counts for services with errors', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    expect(screen.getByText('2')).toBeInTheDocument(); // Twilio errors
    expect(screen.getByText('5')).toBeInTheDocument(); // Database errors
  });

  it('expands service details when clicked', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    // Initially detailed info should not be visible
    expect(screen.queryByText('gpt-4-turbo')).not.toBeInTheDocument();
    
    // Find the OpenAI service card and its expand button
    const openaiCard = screen.getByText('OpenAI GPT-4').closest('.MuiCard-root');
    const expandButton = openaiCard?.querySelector('button:last-child'); // Last button should be expand
    
    if (expandButton) {
      fireEvent.click(expandButton as HTMLElement);
    }
    
    // Details should now be visible
    expect(screen.getByText('gpt-4-turbo')).toBeInTheDocument();
    expect(screen.getByText('https://api.openai.com/v1/chat/completions')).toBeInTheDocument();
  });

  it('shows performance metrics when expanded', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    // Find the OpenAI service card and its expand button
    const openaiCard = screen.getByText('OpenAI GPT-4').closest('.MuiCard-root');
    const expandButton = openaiCard?.querySelector('button:last-child');
    
    if (expandButton) {
      fireEvent.click(expandButton as HTMLElement);
    }
    
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('98.5%')).toBeInTheDocument(); // Success rate
    expect(screen.getByText('15')).toBeInTheDocument(); // Requests per minute
    expect(screen.getByText('99.5%')).toBeInTheDocument(); // Uptime
  });

  it('displays dependencies when expanded', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    // Find the OpenAI service card and its expand button
    const openaiCard = screen.getByText('OpenAI GPT-4').closest('.MuiCard-root');
    const expandButton = openaiCard?.querySelector('button:last-child');
    
    if (expandButton) {
      fireEvent.click(expandButton as HTMLElement);
    }
    
    expect(screen.getByText('Dependencies')).toBeInTheDocument();
    expect(screen.getByText('Internet')).toBeInTheDocument();
    expect(screen.getByText('API Key')).toBeInTheDocument();
  });

  it('shows recent errors when expanded', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    // Find and expand Twilio service (has recent errors)
    const twilioCard = screen.getByText('Twilio WhatsApp').closest('.MuiCard-root');
    const expandButton = twilioCard?.querySelector('button:last-child');
    
    if (expandButton) {
      fireEvent.click(expandButton as HTMLElement);
    }
    
    expect(screen.getAllByText('Recent Errors')[0]).toBeInTheDocument();
    expect(screen.getByText('Rate limit exceeded')).toBeInTheDocument();
  });

  it('handles service refresh', () => {
    const mockRefresh = jest.fn();
    renderWithTheme(<ServiceStatusGrid services={mockServices} onRefreshService={mockRefresh} />);
    
    const refreshButtons = screen.getAllByLabelText('Refresh status');
    fireEvent.click(refreshButtons[0]);
    
    expect(mockRefresh).toHaveBeenCalledWith('openai');
  });

  it('formats response times correctly', () => {
    const servicesWithLongResponseTime = {
      ...mockServices,
      slowService: {
        ...mockServices.openai,
        name: 'Slow Service',
        responseTime: 2500, // 2.5 seconds
      },
    };
    
    renderWithTheme(<ServiceStatusGrid services={servicesWithLongResponseTime} />);
    
    expect(screen.getByText('2.5s')).toBeInTheDocument();
  });

  it('handles services without optional fields', () => {
    const minimalService = {
      minimal: {
        name: 'Minimal Service',
        description: 'Basic service',
        status: 'healthy' as const,
        lastCheck: '2025-01-16T10:30:00Z',
      },
    };
    
    renderWithTheme(<ServiceStatusGrid services={minimalService} />);
    
    expect(screen.getByText('Minimal Service')).toBeInTheDocument();
    expect(screen.getByText('Basic service')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument(); // No response time
  });

  it('applies correct styling based on service status', () => {
    renderWithTheme(<ServiceStatusGrid services={mockServices} />);
    
    const healthyCard = screen.getByText('OpenAI GPT-4').closest('.MuiCard-root');
    const warningCard = screen.getByText('Twilio WhatsApp').closest('.MuiCard-root');
    const criticalCard = screen.getByText('Application Database').closest('.MuiCard-root');
    
    expect(healthyCard).toHaveStyle({ borderColor: expect.stringContaining('success') });
    expect(warningCard).toHaveStyle({ borderColor: expect.stringContaining('warning') });
    expect(criticalCard).toHaveStyle({ borderColor: expect.stringContaining('error') });
  });
});