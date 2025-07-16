import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConfigurationForm from '../ConfigurationForm';
import { SystemConfiguration } from '../types';

const mockConfig: SystemConfiguration = {
  openaiModel: 'gpt-4',
  maxPdfSizeMb: 10,
  rateLimitPerMinute: 60,
  webhookValidation: true,
  logLevel: 'INFO',
  alertThresholds: {
    errorRate: 5,
    responseTime: 3,
    cpuUsage: 80,
    memoryUsage: 85
  }
};

describe('ConfigurationForm', () => {
  const mockSave = jest.fn();

  beforeEach(() => {
    mockSave.mockClear();
  });

  test('renders all form sections', () => {
    render(<ConfigurationForm config={mockConfig} onSave={mockSave} />);
    
    // Check section titles
    expect(screen.getByText('OpenAI Settings')).toBeInTheDocument();
    expect(screen.getByText('API Settings')).toBeInTheDocument();
    expect(screen.getByText('System Settings')).toBeInTheDocument();
    expect(screen.getByText('Monitoring Settings')).toBeInTheDocument();
    
    // Check form controls
    expect(screen.getByLabelText('OpenAI Model')).toBeInTheDocument();
    expect(screen.getByLabelText('Rate Limit')).toBeInTheDocument();
    expect(screen.getByLabelText('Enable Webhook Signature Validation')).toBeInTheDocument();
    expect(screen.getByLabelText('PDF Size Limit')).toBeInTheDocument();
    expect(screen.getByLabelText('Log Level')).toBeInTheDocument();
    
    // Check alert threshold fields
    expect(screen.getByLabelText('Error Rate Threshold')).toBeInTheDocument();
    expect(screen.getByLabelText('Response Time Threshold')).toBeInTheDocument();
    expect(screen.getByLabelText('CPU Usage Threshold')).toBeInTheDocument();
    expect(screen.getByLabelText('Memory Usage Threshold')).toBeInTheDocument();
    
    // Check save button
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    render(<ConfigurationForm config={mockConfig} onSave={mockSave} />);
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
    
    // Check if onSave was called with the correct data
    await waitFor(() => {
      expect(mockSave).toHaveBeenCalledWith(mockConfig);
    });
  });

  test('shows validation errors for invalid data', async () => {
    const invalidConfig: SystemConfiguration = {
      ...mockConfig,
      maxPdfSizeMb: 0, // Invalid value
      alertThresholds: {
        ...mockConfig.alertThresholds,
        errorRate: 101 // Invalid value (over 100%)
      }
    };
    
    render(<ConfigurationForm config={invalidConfig} onSave={mockSave} />);
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
    
    // Check for validation error messages
    await waitFor(() => {
      expect(screen.getByText('PDF size limit must be greater than 0')).toBeInTheDocument();
      expect(screen.getByText('Error rate must be between 0 and 100')).toBeInTheDocument();
    });
    
    // Verify onSave was not called
    expect(mockSave).not.toHaveBeenCalled();
  });

  test('updates form values when changed', async () => {
    render(<ConfigurationForm config={mockConfig} onSave={mockSave} />);
    
    // Change PDF size limit
    const pdfSizeInput = screen.getByLabelText('PDF Size Limit');
    fireEvent.change(pdfSizeInput, { target: { value: '20' } });
    
    // Change rate limit
    const rateLimitInput = screen.getByLabelText('Rate Limit');
    fireEvent.change(rateLimitInput, { target: { value: '100' } });
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
    
    // Check if onSave was called with updated values
    await waitFor(() => {
      expect(mockSave).toHaveBeenCalledWith(expect.objectContaining({
        maxPdfSizeMb: 20,
        rateLimitPerMinute: 100
      }));
    });
  });

  test('disables submit button when loading', () => {
    render(<ConfigurationForm config={mockConfig} onSave={mockSave} isLoading={true} />);
    
    const submitButton = screen.getByRole('button', { name: '' }); // Button text is replaced with spinner
    expect(submitButton).toBeDisabled();
  });
});