import React from 'react';
import { render, screen } from '@testing-library/react';
import ClassificationChart from '../ClassificationChart';

// Mock Recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  PieChart: () => <div data-testid="pie-chart" />,
  Pie: () => <div />,
  Cell: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

describe('ClassificationChart', () => {
  const mockData = [
    { name: 'Legitimate', value: 500, color: '#4caf50' },
    { name: 'Suspicious', value: 200, color: '#ff9800' },
    { name: 'Likely Scam', value: 100, color: '#f44336' },
  ];

  it('renders the chart title correctly', () => {
    render(<ClassificationChart data={mockData} />);
    expect(screen.getByText('Scam Detection Breakdown')).toBeInTheDocument();
  });

  it('renders the chart container', () => {
    render(<ClassificationChart data={mockData} />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });
});