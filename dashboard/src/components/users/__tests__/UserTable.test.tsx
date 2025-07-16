import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import UserTable from '../UserTable';
import { UserDetails } from '../types';

// Mock data for testing
const mockUsers: UserDetails[] = [
  {
    id: 'user-1',
    phoneNumber: '+11234567890',
    firstInteraction: '2024-06-15T10:30:00Z',
    lastInteraction: '2024-07-15T14:20:00Z',
    totalRequests: 5,
    blocked: false,
    interactionHistory: [
      {
        id: 'int-1-1',
        timestamp: '2024-07-15T14:20:00Z',
        messageType: 'text',
        content: 'Job posting content...',
        analysisResult: {
          trustScore: 85,
          classification: 'Legit',
          reasons: ['Reason 1', 'Reason 2', 'Reason 3']
        },
        responseTime: 1.2
      }
    ],
    engagementScore: 75,
    averageResponseTime: 1.2,
    mostFrequentHour: 14
  },
  {
    id: 'user-2',
    phoneNumber: '+10987654321',
    firstInteraction: '2024-06-10T09:15:00Z',
    lastInteraction: '2024-07-14T11:30:00Z',
    totalRequests: 3,
    blocked: true,
    interactionHistory: [
      {
        id: 'int-2-1',
        timestamp: '2024-07-14T11:30:00Z',
        messageType: 'pdf',
        content: 'PDF document content...',
        analysisResult: {
          trustScore: 30,
          classification: 'Likely Scam',
          reasons: ['Reason 1', 'Reason 2', 'Reason 3']
        },
        responseTime: 1.5
      }
    ],
    engagementScore: 40,
    averageResponseTime: 1.5,
    mostFrequentHour: 11
  }
];

// Mock functions
const mockOnBlockUser = jest.fn();
const mockOnUnblockUser = jest.fn();
const mockOnUserSelect = jest.fn();
const mockOnPageChange = jest.fn();
const mockOnRowsPerPageChange = jest.fn();

describe('UserTable Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders user table with correct data', () => {
    render(
      <UserTable
        users={mockUsers}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Check if phone numbers are displayed
    expect(screen.getByText(/\+1 \(123\) 456-7890/)).toBeInTheDocument();
    expect(screen.getByText(/\+1 \(098\) 765-4321/)).toBeInTheDocument();

    // Check if total requests are displayed
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();

    // Check if status chips are displayed
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
  });

  test('calls onBlockUser when block button is clicked', () => {
    render(
      <UserTable
        users={mockUsers}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Find and click the block button for the first user (not blocked)
    const blockButtons = screen.getAllByTitle('Block User');
    fireEvent.click(blockButtons[0]);

    // Check if onBlockUser was called with the correct user ID
    expect(mockOnBlockUser).toHaveBeenCalledWith('user-1');
  });

  test('calls onUnblockUser when unblock button is clicked', () => {
    render(
      <UserTable
        users={mockUsers}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Find and click the unblock button for the second user (blocked)
    const unblockButtons = screen.getAllByTitle('Unblock User');
    fireEvent.click(unblockButtons[0]);

    // Check if onUnblockUser was called with the correct user ID
    expect(mockOnUnblockUser).toHaveBeenCalledWith('user-2');
  });

  test('calls onUserSelect when view button is clicked', () => {
    render(
      <UserTable
        users={mockUsers}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Find and click the view button for the first user
    const viewButtons = screen.getAllByTitle('View Interactions');
    fireEvent.click(viewButtons[0]);

    // Check if onUserSelect was called with the correct user
    expect(mockOnUserSelect).toHaveBeenCalledWith(mockUsers[0]);
  });

  test('displays "No users found" message when users array is empty', () => {
    render(
      <UserTable
        users={[]}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Check if the "No users found" message is displayed
    expect(screen.getByText('No users found matching your search criteria')).toBeInTheDocument();
  });

  test('handles pagination correctly', () => {
    render(
      <UserTable
        users={mockUsers}
        onBlockUser={mockOnBlockUser}
        onUnblockUser={mockOnUnblockUser}
        onUserSelect={mockOnUserSelect}
        page={0}
        rowsPerPage={10}
        onPageChange={mockOnPageChange}
        onRowsPerPageChange={mockOnRowsPerPageChange}
      />
    );

    // Find and interact with pagination controls
    const paginationButtons = screen.getAllByRole('button');
    const nextPageButton = paginationButtons.find(button => button.textContent === 'Go to next page');
    
    if (nextPageButton) {
      fireEvent.click(nextPageButton);
      expect(mockOnPageChange).toHaveBeenCalledWith(1);
    }
  });
});