import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ActiveAlertsCard, { Alert } from '../ActiveAlertsCard';

const theme = createTheme();

const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'error',
    title: 'Critical System Error',
    message: 'Database connection failed',
    timestamp: '2025-01-16T10:00:00Z',
    source: 'Database',
    severity: 'critical',
    acknowledged: false,
    details: 'Connection timeout after 30 seconds\nRetry attempts: 3\nLast successful connection: 2025-01-16T09:45:00Z',
    actionRequired: true,
  },
  {
    id: '2',
    type: 'warning',
    title: 'High Response Time',
    message: 'API response time above threshold',
    timestamp: '2025-01-16T10:15:00Z',
    source: 'OpenAI',
    severity: 'medium',
    acknowledged: false,
    details: 'Average response time: 2.5s (threshold: 2.0s)',
  },
  {
    id: '3',
    type: 'info',
    title: 'Maintenance Scheduled',
    message: 'System maintenance in 2 hours',
    timestamp: '2025-01-16T10:30:00Z',
    source: 'System',
    severity: 'low',
    acknowledged: true,
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ActiveAlertsCard', () => {
  it('renders active alerts correctly', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    expect(screen.getByText('Active Alerts')).toBeInTheDocument();
    expect(screen.getByText('Critical System Error')).toBeInTheDocument();
    expect(screen.getByText('High Response Time')).toBeInTheDocument();
    // Acknowledged alert should not be shown in active alerts
    expect(screen.queryByText('Maintenance Scheduled')).not.toBeInTheDocument();
  });

  it('displays critical alerts badge', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    expect(screen.getByText('1 Critical')).toBeInTheDocument();
  });

  it('shows alert details and metadata', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    expect(screen.getByText('API response time above threshold')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    expect(screen.getByText('ACTION REQUIRED')).toBeInTheDocument();
  });

  it('displays source and timestamp information', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    expect(screen.getByText(/Database •/)).toBeInTheDocument();
    expect(screen.getByText(/OpenAI •/)).toBeInTheDocument();
  });

  it('shows "All Clear" when no active alerts', () => {
    const acknowledgedAlerts = mockAlerts.map(alert => ({ ...alert, acknowledged: true }));
    renderWithTheme(<ActiveAlertsCard alerts={acknowledgedAlerts} />);
    
    expect(screen.getByText('All Clear!')).toBeInTheDocument();
    expect(screen.getByText('No active alerts at this time')).toBeInTheDocument();
  });

  it('handles alert acknowledgment', () => {
    const mockAcknowledge = jest.fn();
    renderWithTheme(
      <ActiveAlertsCard alerts={mockAlerts} onAcknowledgeAlert={mockAcknowledge} />
    );
    
    const acknowledgeButtons = screen.getAllByLabelText('Acknowledge');
    fireEvent.click(acknowledgeButtons[0]);
    
    expect(mockAcknowledge).toHaveBeenCalledWith('1');
  });

  it('handles alert dismissal', () => {
    const mockDismiss = jest.fn();
    renderWithTheme(
      <ActiveAlertsCard alerts={mockAlerts} onDismissAlert={mockDismiss} />
    );
    
    const dismissButtons = screen.getAllByLabelText('Dismiss');
    fireEvent.click(dismissButtons[0]);
    
    expect(mockDismiss).toHaveBeenCalledWith('1');
  });

  it('expands alert details when clicked', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    // Initially details should not be visible
    expect(screen.queryByText(/Connection timeout after 30 seconds/)).not.toBeInTheDocument();
    
    // Click to expand details
    const expandButton = screen.getAllByLabelText('View details')[0];
    fireEvent.click(expandButton);
    
    // Details should now be visible - use regex to handle text split across elements
    expect(screen.getByText(/Connection timeout after 30 seconds/)).toBeInTheDocument();
    expect(screen.getByText(/Retry attempts: 3/)).toBeInTheDocument();
  });

  it('limits displayed alerts and shows "Show All" button', () => {
    const manyAlerts = Array.from({ length: 10 }, (_, i) => ({
      ...mockAlerts[0],
      id: `alert-${i}`,
      title: `Alert ${i}`,
      acknowledged: false,
    }));
    
    renderWithTheme(<ActiveAlertsCard alerts={manyAlerts} maxDisplayed={3} />);
    
    expect(screen.getByText('Show All (10)')).toBeInTheDocument();
  });

  it('expands to show all alerts when "Show All" is clicked', () => {
    const manyAlerts = Array.from({ length: 6 }, (_, i) => ({
      ...mockAlerts[0],
      id: `alert-${i}`,
      title: `Alert ${i}`,
      acknowledged: false,
    }));
    
    renderWithTheme(<ActiveAlertsCard alerts={manyAlerts} maxDisplayed={3} />);
    
    const showAllButton = screen.getByText('Show All (6)');
    fireEvent.click(showAllButton);
    
    expect(screen.getByText('Show Less')).toBeInTheDocument();
  });

  it('displays alert statistics correctly', () => {
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    expect(screen.getByText(/2 active alert/)).toBeInTheDocument();
    expect(screen.getByText(/1 critical/)).toBeInTheDocument();
    expect(screen.getByText(/1 acknowledged/)).toBeInTheDocument();
  });

  it('handles empty alerts array', () => {
    renderWithTheme(<ActiveAlertsCard alerts={[]} />);
    
    expect(screen.getByText('All Clear!')).toBeInTheDocument();
  });

  it('formats timestamps correctly', () => {
    // Mock Date.now to control relative time calculation
    const mockDate = new Date('2025-01-16T10:35:00Z');
    jest.spyOn(Date, 'now').mockImplementation(() => mockDate.getTime());
    
    renderWithTheme(<ActiveAlertsCard alerts={mockAlerts} />);
    
    // Should show relative times - use getAllByText to handle multiple matches
    const timeElements = screen.getAllByText(/ago/);
    expect(timeElements.length).toBeGreaterThan(0);
    
    jest.restoreAllMocks();
  });
});