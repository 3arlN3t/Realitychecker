import React from 'react';
import { render, screen } from '@testing-library/react';
import LiveMetricsCard from '../LiveMetricsCard';
import { LiveMetrics } from '../../../pages/MonitoringPage';

describe('LiveMetricsCard', () => {
  const mockMetrics: LiveMetrics = {
    timestamp: '2025-01-16T12:00:00Z',
    requests: {
      total: 1250,
      errors: 25,
      error_rate_percent: 2.0,
      avg_response_time_seconds: 1.2
    },
    services: {
      'openai_analyze': {
        total_calls: 500,
        errors: 10,
        error_rate_percent: 2.0,
        avg_response_time_seconds: 1.5
      },
      'twilio_send': {
        total_calls: 750,
        errors: 15,
        error_rate_percent: 2.0,
        avg_response_time_seconds: 0.8
      }
    }
  };

  test('renders loading state when no metrics provided', () => {
    render(<LiveMetricsCard metrics={null} />);
    
    expect(screen.getByText('Live System Metrics')).toBeInTheDocument();
    expect(screen.getByText('Waiting for metrics data...')).toBeInTheDocument();
  });

  test('renders metrics data correctly', () => {
    render(<LiveMetricsCard metrics={mockMetrics} />);
    
    // Check title
    expect(screen.getByText('Live System Metrics')).toBeInTheDocument();
    
    // Check request metrics
    expect(screen.getByText('1250')).toBeInTheDocument(); // Total requests
    expect(screen.getByText('2.0%')).toBeInTheDocument(); // Error rate
    expect(screen.getByText('1.20s')).toBeInTheDocument(); // Avg response time
    expect(screen.getByText('98.0%')).toBeInTheDocument(); // Success rate
    
    // Check service health
    expect(screen.getByText('openai_analyze')).toBeInTheDocument();
    expect(screen.getByText('twilio_send')).toBeInTheDocument();
    expect(screen.getAllByText('healthy').length).toBe(2); // Both services should be healthy
  });

  test('shows warning for high error rates', () => {
    const highErrorMetrics = {
      ...mockMetrics,
      requests: {
        ...mockMetrics.requests,
        error_rate_percent: 8.0
      },
      services: {
        'openai_analyze': {
          ...mockMetrics.services['openai_analyze'],
          error_rate_percent: 10.0
        },
        'twilio_send': {
          ...mockMetrics.services['twilio_send']
        }
      }
    };
    
    render(<LiveMetricsCard metrics={highErrorMetrics} />);
    
    expect(screen.getByText('8.0%')).toBeInTheDocument(); // High error rate
    expect(screen.getByText('92.0%')).toBeInTheDocument(); // Lower success rate
    expect(screen.getByText('warning')).toBeInTheDocument(); // Service should show warning
  });
});