import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ModelSelector from '../ModelSelector';

describe('ModelSelector', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  test('renders with the correct value', () => {
    render(<ModelSelector value="gpt-4" onChange={mockOnChange} />);
    
    const select = screen.getByLabelText('OpenAI Model');
    expect(select).toHaveValue('gpt-4');
  });

  test('calls onChange when selection changes', () => {
    render(<ModelSelector value="gpt-4" onChange={mockOnChange} />);
    
    // Open the select dropdown
    fireEvent.mouseDown(screen.getByLabelText('OpenAI Model'));
    
    // Click on a different option
    fireEvent.click(screen.getByText('GPT-3.5 Turbo'));
    
    // Check if onChange was called with the new value
    expect(mockOnChange).toHaveBeenCalledWith('gpt-3.5-turbo');
  });

  test('displays error message when provided', () => {
    const errorMessage = 'This field is required';
    render(<ModelSelector value="" onChange={mockOnChange} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('renders all model options', () => {
    render(<ModelSelector value="gpt-4" onChange={mockOnChange} />);
    
    // Open the select dropdown
    fireEvent.mouseDown(screen.getByLabelText('OpenAI Model'));
    
    // Check if all options are rendered
    expect(screen.getByText('GPT-4')).toBeInTheDocument();
    expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument();
    expect(screen.getByText('GPT-3.5 Turbo')).toBeInTheDocument();
  });
});