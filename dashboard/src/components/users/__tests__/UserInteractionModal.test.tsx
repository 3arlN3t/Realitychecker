import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import UserInteractionModal from '../UserInteractionModal';
import { UserDetails } from '../types';

// Mock user data for testing
const mockUser: UserDetails = {
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
    },
    {
      id: 'int-1-2',
      timestamp: '2024-07-10T11:15:00Z',
      messageType: 'pdf',
      content: 'PDF document content...',
      analysisResult: {
        trustScore: 30,
        classification: 'Likely Scam',
        reasons: ['Reason 1', 'Reason 2', 'Reason 3']
      },
      responseTime: 1.5
    },
    {
      id: 'int-1-3',
      timestamp: '2024-07-05T09:45:00Z',
      messageType: 'text',
      content: 'Another job posting...',
      analysisResult: {
        trustScore: 60,
        classification: 'Suspicious',
        reasons: ['Reason 1', 'Reason 2', 'Reason 3']
      },
      responseTime: 1.3
    },
    {
      id: 'int-1-4',
      timestamp: '2024-06-28T16:30:00Z',
      messageType: 'text',
      content: 'Error test...',
      error: 'Processing error',
      responseTime: 0.8
    }
  ],
  engagementScore: 75,
  averageResponseTime: 1.2,
  mostFrequentHour: 14
};

describe('UserInteractionModal Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders modal with user details when open', () => {
    render(
      <UserInteractionModal
        user={mockUser}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Check if modal title contains phone number
    expect(screen.getByText(/User Details: \+1 \(123\) 456-7890/)).toBeInTheDocument();
    
    // Check if tabs are rendered
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Interaction History')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    
    // Check if user information is displayed in overview tab
    expect(screen.getByText('User Information')).toBeInTheDocument();
    expect(screen.getByText('First Interaction:')).toBeInTheDocument();
    expect(screen.getByText('Last Interaction:')).toBeInTheDocument();
    expect(screen.getByText('Total Requests:')).toBeInTheDocument();
    
    // Check if interaction summary is displayed
    expect(screen.getByText('Interaction Summary')).toBeInTheDocument();
    expect(screen.getByText('Text Messages')).toBeInTheDocument();
    expect(screen.getByText('PDF Uploads')).toBeInTheDocument();
    expect(screen.getByText('Classification Breakdown')).toBeInTheDocument();
  });

  test('does not render when user is null', () => {
    render(
      <UserInteractionModal
        user={null}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Check that modal content is not rendered
    expect(screen.queryByText('User Details:')).not.toBeInTheDocument();
  });

  test('calls onClose when close button is clicked', () => {
    render(
      <UserInteractionModal
        user={mockUser}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Find and click the close button
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    // Check if onClose was called
    expect(mockOnClose).toHaveBeenCalled();
  });

  test('switches tabs when tab is clicked', () => {
    render(
      <UserInteractionModal
        user={mockUser}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Initially, Overview tab should be active and showing content
    expect(screen.getByText('User Information')).toBeInTheDocument();
    
    // Click on Interaction History tab
    const historyTab = screen.getByText('Interaction History');
    fireEvent.click(historyTab);
    
    // Check if Interaction History content is displayed
    expect(screen.getByText('Date & Time')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Classification')).toBeInTheDocument();
    expect(screen.getByText('Trust Score')).toBeInTheDocument();
    
    // Click on Analytics tab
    const analyticsTab = screen.getByText('Analytics');
    fireEvent.click(analyticsTab);
    
    // Check if Analytics content is displayed
    expect(screen.getByText('User Behavior Insights')).toBeInTheDocument();
    expect(screen.getByText('Activity Pattern')).toBeInTheDocument();
    expect(screen.getByText('Content Analysis')).toBeInTheDocument();
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
  });

  test('displays interaction history in table format', () => {
    render(
      <UserInteractionModal
        user={mockUser}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Click on Interaction History tab
    const historyTab = screen.getByText('Interaction History');
    fireEvent.click(historyTab);
    
    // Check if interaction history items are displayed
    expect(screen.getByText('85/100')).toBeInTheDocument(); // Trust score
    expect(screen.getByText('30/100')).toBeInTheDocument(); // Trust score
    expect(screen.getByText('60/100')).toBeInTheDocument(); // Trust score
    expect(screen.getByText('N/A')).toBeInTheDocument(); // For the error case
    
    // Check if classification chips are displayed
    expect(screen.getByText('Legit')).toBeInTheDocument();
    expect(screen.getByText('Likely Scam')).toBeInTheDocument();
    expect(screen.getByText('Suspicious')).toBeInTheDocument();
    
    // Check if error status is displayed
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getAllByText('Success').length).toBe(3);
  });

  test('calculates and displays correct statistics', () => {
    render(
      <UserInteractionModal
        user={mockUser}
        open={true}
        onClose={mockOnClose}
      />
    );
    
    // Check text vs PDF counts
    expect(screen.getByText('3')).toBeInTheDocument(); // 3 text messages
    expect(screen.getByText('1')).toBeInTheDocument(); // 1 PDF upload
    
    // Check classification counts
    expect(screen.getByText('Legitimate:')).toBeInTheDocument();
    expect(screen.getByText('Suspicious:')).toBeInTheDocument();
    expect(screen.getByText('Likely Scam:')).toBeInTheDocument();
    expect(screen.getByText('Errors:')).toBeInTheDocument();
  });
});