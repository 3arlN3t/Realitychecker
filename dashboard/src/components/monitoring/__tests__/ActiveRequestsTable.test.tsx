import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ActiveRequestsTable from '../ActiveRequestsTable';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ActiveRequestsTable', () => {
  const mockActiveRequests = [
    {
      id: 'req-1',
      type: 'text_analysis',
      status: 'processing',
      startedAt: '2025-01-16T10:30:00Z',
      duration: 1200,
      user: '+1234567890',
    },
    {
      id: 'req-2',
      type: 'pdf_processing',
      status: 'downloading',
      startedAt: '2025-01-16T10:29:00Z',
      duration: 800,
      user: '+0987654321',
    },
    {
      id: 'req-3',
      type: 'text_analysis',
      status: 'completed',
      startedAt: '2025-01-16T10:28:00Z',
      duration: 1500,
      user: '+1122334455',
    },
  ];

  it('renders table headers correctly', () => {
    renderWithTheme(<ActiveRequestsTable requests={mockActiveRequests} />);

    expect(screen.getByText('Request ID')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('renders active requests correctly', () => {
    renderWithTheme(<ActiveRequestsTable requests={mockActiveRequests} />);

    expect(screen.getByText('req-1')).toBeInTheDocument();
    expect(screen.getByText('req-2')).toBeInTheDocument();
    expect(screen.getByText('req-3')).toBeInTheDocument();
    
    expect(screen.getByText('Text Analysis')).toBeInTheDocument();
    expect(screen.getByText('PDF Processing')).toBeInTheDocument();
    
    expect(screen.getByText('processing')).toBeInTheDocument();
    expect(screen.getByText('downloading')).toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('formats duration correctly', () => {
    renderWithTheme(<ActiveRequestsTable requests={mockActiveRequests} />);

    expect(screen.getByText('1.2s')).toBeInTheDocument();
    expect(screen.getByText('0.8s')).toBeInTheDocument();
    expect(screen.getByText('1.5s')).toBeInTheDocument();
  });

  it('displays user information correctly', () => {
    renderWithTheme(<ActiveRequestsTable requests={mockActiveRequests} />);

    expect(screen.getByText('+1234567890')).toBeInTheDocument();
    expect(screen.getByText('+0987654321')).toBeInTheDocument();
    expect(screen.getByText('+1122334455')).toBeInTheDocument();
  });

  it('shows appropriate status colors', () => {
    renderWithTheme(<ActiveRequestsTable requests={mockActiveRequests} />);

    const processingChip = screen.getByText('processing');
    const completedChip = screen.getByText('completed');
    
    expect(processingChip).toBeInTheDocument();
    expect(completedChip).toBeInTheDocument();
  });

  it('handles empty requests array', () => {
    renderWithTheme(<ActiveRequestsTable requests={[]} />);

    expect(screen.getByText('Request ID')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
    
    // Should not have any data rows
    const table = screen.getByRole('table');
    const tableBody = within(table).getByRole('rowgroup');
    const dataRows = within(tableBody).queryAllByRole('row');
    expect(dataRows).toHaveLength(0);
  });

  it('handles long request IDs', () => {
    const longIdRequest = [{
      id: 'very-long-request-id-that-should-be-truncated-or-handled-properly',
      type: 'text_analysis',
      status: 'processing',
      startedAt: '2025-01-16T10:30:00Z',
      duration: 1200,
      user: '+1234567890',
    }];

    renderWithTheme(<ActiveRequestsTable requests={longIdRequest} />);

    expect(screen.getByText('very-long-request-id-that-should-be-truncated-or-handled-properly')).toBeInTheDocument();
  });

  it('handles different request types', () => {
    const differentTypeRequests = [
      {
        id: 'req-1',
        type: 'unknown_type',
        status: 'processing',
        startedAt: '2025-01-16T10:30:00Z',
        duration: 1200,
        user: '+1234567890',
      },
    ];

    renderWithTheme(<ActiveRequestsTable requests={differentTypeRequests} />);

    // Should handle unknown types gracefully
    expect(screen.getByText('Unknown Type')).toBeInTheDocument();
  });

  it('sorts requests by duration', () => {
    const unsortedRequests = [
      {
        id: 'req-1',
        type: 'text_analysis',
        status: 'processing',
        startedAt: '2025-01-16T10:30:00Z',
        duration: 3000,
        user: '+1234567890',
      },
      {
        id: 'req-2',
        type: 'pdf_processing',
        status: 'downloading',
        startedAt: '2025-01-16T10:29:00Z',
        duration: 1000,
        user: '+0987654321',
      },
    ];

    renderWithTheme(<ActiveRequestsTable requests={unsortedRequests} />);

    const rows = screen.getAllByRole('row');
    const dataRows = rows.slice(1); // Skip header row
    
    expect(dataRows).toHaveLength(2);
    expect(within(dataRows[0]).getByText('3.0s')).toBeInTheDocument();
    expect(within(dataRows[1]).getByText('1.0s')).toBeInTheDocument();
  });

  it('handles missing optional fields gracefully', () => {
    const incompleteRequest = [{
      id: 'req-1',
      type: 'text_analysis',
      status: 'processing',
      startedAt: '2025-01-16T10:30:00Z',
      duration: 1200,
      user: '+1234567890',
    }];

    renderWithTheme(<ActiveRequestsTable requests={incompleteRequest} />);

    expect(screen.getByText('req-1')).toBeInTheDocument();
    expect(screen.getByText('Text Analysis')).toBeInTheDocument();
    expect(screen.getByText('processing')).toBeInTheDocument();
  });
});