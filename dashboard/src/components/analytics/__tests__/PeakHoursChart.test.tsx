import React from 'react';
import { render, screen } from '@testing-library/react';
import PeakHoursChart from '../PeakHoursChart';

// Mock Recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}));

describe('PeakHoursChart', () => {
  const mockData = [
    { hour: '00:00', requests: 10 },
    { hour: '01:00', requests: 5 },
    { hour: '02:00', requests: 3 },
    { hour: '03:00', requests: 2 },
    { hour: '04:00', requests: 1 },
    { hour: '05:00', requests: 2 },
    { hour: '06:00', requests: 8 },
    { hour: '07:00', requests: 15 },
    { hour: '08:00', requests: 25 },
    { hour: '09:00', requests: 35 },
    { hour: '10:00', requests: 40 },
    { hour: '11:00', requests: 38 },
    { hour: '12:00', requests: 42 },
    { hour: '13:00', requests: 45 },
    { hour: '14:00', requests: 43 },
    { hour: '15:00', requests: 41 },
    { hour: '16:00', requests: 39 },
    { hour: '17:00', requests: 37 },
    { hour: '18:00', requests: 30 },
    { hour: '19:00', requests: 25 },
    { hour: '20:00', requests: 20 },
    { hour: '21:00', requests: 18 },
    { hour: '22:00', requests: 15 },
    { hour: '23:00', requests: 12 },
  ];

  it('renders the chart title correctly', () => {
    render(<PeakHoursChart data={mockData} />);
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
  });

  it('renders the chart container and components', () => {
    render(<PeakHoursChart data={mockData} />);
    
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('bar')).toBeInTheDocument();
    expect(screen.getByTestId('x-axis')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis')).toBeInTheDocument();
    expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
    expect(screen.getByTestId('tooltip')).toBeInTheDocument();
  });

  it('renders with empty data', () => {
    render(<PeakHoursChart data={[]} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles undefined data gracefully', () => {
    render(<PeakHoursChart data={undefined as any} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('handles data with missing fields', () => {
    const incompleteData = [
      { hour: '00:00' }, // missing requests
      { requests: 10 }, // missing hour
      { hour: '02:00', requests: 5 },
    ];

    render(<PeakHoursChart data={incompleteData} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles large datasets', () => {
    const largeData = Array.from({ length: 168 }, (_, i) => ({
      hour: `${Math.floor(i / 7)}:${(i % 7) * 10}`,
      requests: Math.floor(Math.random() * 100),
    }));

    render(<PeakHoursChart data={largeData} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles zero values correctly', () => {
    const zeroData = [
      { hour: '00:00', requests: 0 },
      { hour: '01:00', requests: 0 },
      { hour: '02:00', requests: 0 },
    ];

    render(<PeakHoursChart data={zeroData} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles negative values correctly', () => {
    const negativeData = [
      { hour: '00:00', requests: -5 },
      { hour: '01:00', requests: 10 },
      { hour: '02:00', requests: -2 },
    ];

    render(<PeakHoursChart data={negativeData} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles very large values', () => {
    const largeValueData = [
      { hour: '00:00', requests: 1000000 },
      { hour: '01:00', requests: 999999 },
      { hour: '02:00', requests: 1000001 },
    ];

    render(<PeakHoursChart data={largeValueData} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('handles string values in requests field', () => {
    const stringData = [
      { hour: '00:00', requests: '10' },
      { hour: '01:00', requests: '20' },
      { hour: '02:00', requests: '30' },
    ];

    render(<PeakHoursChart data={stringData as any} />);
    
    expect(screen.getByText('Peak Usage Hours')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });
});