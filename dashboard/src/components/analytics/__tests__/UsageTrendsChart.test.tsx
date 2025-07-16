import React from 'react';
import { render, screen } from '@testing-library/react';
import UsageTrendsChart from '../UsageTrendsChart';

// Mock Recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  LineChart: () => <div data-testid="line-chart" />,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Legend: () => <div />,
}));

describe('UsageTrendsChart', () => {
  const mockData = [
    { date: '2025-01-01T00:00:00.000Z', count: 45 },
    { date: '2025-01-02T00:00:00.000Z', count: 52 },
    { date: '2025-01-03T00:00:00.000Z', count: 38 },
  ];

  it('renders the chart title correctly', () => {
    render(<UsageTrendsChart data={mockData} period="week" />);
    expect(screen.getByText('Request Volume Over Time')).toBeInTheDocument();
  });

  it('renders the chart container', () => {
    render(<UsageTrendsChart data={mockData} period="week" />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders with different periods', () => {
    const { rerender } = render(<UsageTrendsChart data={mockData} period="day" />);
    expect(screen.getByText('Request Volume Over Time')).toBeInTheDocument();
    
    rerender(<UsageTrendsChart data={mockData} period="month" />);
    expect(screen.getByText('Request Volume Over Time')).toBeInTheDocument();
    
    rerender(<UsageTrendsChart data={mockData} period="year" />);
    expect(screen.getByText('Request Volume Over Time')).toBeInTheDocument();
  });
});