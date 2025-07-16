import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SystemHealthCard, { SystemHealth } from '../SystemHealthCard';

const theme = createTheme();

const mockSystemHealth: SystemHealth = {
  status: 'healthy',
  uptime: '99.9%',
  lastUpdated: '10:30:00 AM',
  memoryUsage: 65,
  cpuUsage: 45,
  services: {
    openai: {
      status: 'healthy',
      responseTime: 250,
      lastCheck: '2025-01-16T10:30:00Z',
      errorCount: 0,
    },
    twilio: {
      status: 'warning',
      responseTime: 150,
      lastCheck: '2025-01-16T10:29:00Z',
      errorCount: 2,
    },
    database: {
      status: 'healthy',
      responseTime: 25,
      lastCheck: '2025-01-16T10:30:00Z',
      errorCount: 0,
    },
    webhook: {
      status: 'critical',
      responseTime: 500,
      lastCheck: '2025-01-16T10:28:00Z',
      errorCount: 5,
    },
  },
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('SystemHealthCard', () => {
  it('renders system health information correctly', () => {
    renderWithTheme(<SystemHealthCard health={mockSystemHealth} />);
    
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('99.9%')).toBeInTheDocument();
    expect(screen.getByText('10:30:00 AM')).toBeInTheDocument();
  });

  it('displays resource usage correctly', () => {
    renderWithTheme(<SystemHealthCard health={mockSystemHealth} />);
    
    expect(screen.getByText('Resource Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('CPU')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('shows all service statuses', () => {
    renderWithTheme(<SystemHealthCard health={mockSystemHealth} />);
    
    expect(screen.getByText('Service Status')).toBeInTheDocument();
    expect(screen.getByText('openai')).toBeInTheDocument();
    expect(screen.getByText('twilio')).toBeInTheDocument();
    expect(screen.getByText('database')).toBeInTheDocument();
    expect(screen.getByText('webhook')).toBeInTheDocument();
  });

  it('displays service response times', () => {
    renderWithTheme(<SystemHealthCard health={mockSystemHealth} />);
    
    expect(screen.getByText('250ms')).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
    expect(screen.getByText('25ms')).toBeInTheDocument();
    expect(screen.getByText('500ms')).toBeInTheDocument();
  });

  it('handles critical system status', () => {
    const criticalHealth: SystemHealth = {
      ...mockSystemHealth,
      status: 'critical',
    };
    
    renderWithTheme(<SystemHealthCard health={criticalHealth} />);
    
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('handles warning system status', () => {
    const warningHealth: SystemHealth = {
      ...mockSystemHealth,
      status: 'warning',
    };
    
    renderWithTheme(<SystemHealthCard health={warningHealth} />);
    
    expect(screen.getByText('WARNING')).toBeInTheDocument();
  });

  it('handles high resource usage', () => {
    const highUsageHealth: SystemHealth = {
      ...mockSystemHealth,
      memoryUsage: 90,
      cpuUsage: 95,
    };
    
    renderWithTheme(<SystemHealthCard health={highUsageHealth} />);
    
    expect(screen.getByText('90%')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  it('handles services without response times', () => {
    const healthWithoutResponseTimes: SystemHealth = {
      ...mockSystemHealth,
      services: {
        ...mockSystemHealth.services,
        openai: {
          ...mockSystemHealth.services.openai,
          responseTime: undefined,
        },
      },
    };
    
    renderWithTheme(<SystemHealthCard health={healthWithoutResponseTimes} />);
    
    expect(screen.getByText('openai')).toBeInTheDocument();
  });
});