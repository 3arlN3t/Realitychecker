import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import MetricsOverviewCard, { MetricsOverview } from '../MetricsOverviewCard';

const theme = createTheme();

const mockMetrics: MetricsOverview = {
  totalRequests: 1250,
  requestsToday: 45,
  requestsTrend: 'up',
  requestsChange: 12.5,
  errorRate: 2.3,
  errorTrend: 'down',
  errorChange: -0.8,
  avgResponseTime: 1.2,
  responseTrend: 'stable',
  responseChange: 0.1,
  activeUsers: 23,
  usersTrend: 'up',
  usersChange: 15.2,
  successRate: 97.7,
  peakHour: '2:00 PM',
  lastUpdated: '10:30:00 AM',
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('MetricsOverviewCard', () => {
  it('renders key performance indicators correctly', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Key Performance Indicators')).toBeInTheDocument();
    expect(screen.getByText('Updated: 10:30:00 AM')).toBeInTheDocument();
  });

  it('displays total requests with trend', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Total Requests')).toBeInTheDocument();
    expect(screen.getByText('1.3K')).toBeInTheDocument(); // 1250 formatted
    
    // Use getAllByText to handle multiple matches
    const trendElements = screen.getAllByText('+12.5%');
    expect(trendElements.length).toBeGreaterThan(0);
  });

  it('displays requests today with trend', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Requests Today')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    
    // Use getAllByText to handle multiple matches
    const trendElements = screen.getAllByText('+12.5%');
    expect(trendElements.length).toBeGreaterThan(0);
  });

  it('displays error rate with trend', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
    expect(screen.getByText('2.3%')).toBeInTheDocument();
    expect(screen.getByText('-0.8%')).toBeInTheDocument();
  });

  it('displays active users with trend', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('23')).toBeInTheDocument();
    expect(screen.getByText('+15.2%')).toBeInTheDocument();
  });

  it('displays average response time', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Avg Response Time')).toBeInTheDocument();
    expect(screen.getByText('1.2s')).toBeInTheDocument();
    expect(screen.getByText('+0.1%')).toBeInTheDocument();
  });

  it('displays success rate', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
    expect(screen.getByText('97.7%')).toBeInTheDocument();
  });

  it('displays peak hour', () => {
    renderWithTheme(<MetricsOverviewCard metrics={mockMetrics} />);
    
    expect(screen.getByText('Peak Hour')).toBeInTheDocument();
    expect(screen.getByText('2:00 PM')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    const largeMetrics: MetricsOverview = {
      ...mockMetrics,
      totalRequests: 1500000,
      requestsToday: 2500,
    };
    
    renderWithTheme(<MetricsOverviewCard metrics={largeMetrics} />);
    
    expect(screen.getByText('1.5M')).toBeInTheDocument();
    expect(screen.getByText('2.5K')).toBeInTheDocument();
  });

  it('handles negative trend changes', () => {
    const negativeMetrics: MetricsOverview = {
      ...mockMetrics,
      requestsTrend: 'down',
      requestsChange: -5.2,
      usersTrend: 'down',
      usersChange: -8.1,
    };
    
    renderWithTheme(<MetricsOverviewCard metrics={negativeMetrics} />);
    
    // Use getAllByText to handle multiple matches
    const negativeChanges = screen.getAllByText('-5.2%');
    expect(negativeChanges.length).toBeGreaterThan(0);
    
    const userChanges = screen.getAllByText('-8.1%');
    expect(userChanges.length).toBeGreaterThan(0);
  });

  it('handles stable trends', () => {
    const stableMetrics: MetricsOverview = {
      ...mockMetrics,
      requestsTrend: 'stable',
      errorTrend: 'stable',
      usersTrend: 'stable',
    };
    
    renderWithTheme(<MetricsOverviewCard metrics={stableMetrics} />);
    
    // Should still show the change percentages even for stable trends
    // Use getAllByText to handle multiple matches
    const positiveChanges = screen.getAllByText('+12.5%');
    expect(positiveChanges.length).toBeGreaterThan(0);
    
    const errorChanges = screen.getAllByText('-0.8%');
    expect(errorChanges.length).toBeGreaterThan(0);
    
    const userChanges = screen.getAllByText('+15.2%');
    expect(userChanges.length).toBeGreaterThan(0);
  });

  it('handles zero values', () => {
    const zeroMetrics: MetricsOverview = {
      ...mockMetrics,
      requestsToday: 0,
      activeUsers: 0,
      errorRate: 0,
    };
    
    renderWithTheme(<MetricsOverviewCard metrics={zeroMetrics} />);
    
    // Check for specific zero values in context
    expect(screen.getByText('Requests Today')).toBeInTheDocument();
    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
    
    // Use getAllByText to handle multiple "0" values
    const zeroElements = screen.getAllByText('0');
    expect(zeroElements.length).toBeGreaterThan(0);
    
    const zeroPercentElements = screen.getAllByText('0%');
    expect(zeroPercentElements.length).toBeGreaterThan(0);
  });
});