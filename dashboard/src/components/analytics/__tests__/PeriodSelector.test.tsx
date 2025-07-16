import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PeriodSelector from '../PeriodSelector';
import { PeriodType } from '../types';

describe('PeriodSelector', () => {
  const mockOnChange = jest.fn();
  
  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it('renders all period options', () => {
    render(<PeriodSelector period="week" onChange={mockOnChange} />);
    
    expect(screen.getByText('Day')).toBeInTheDocument();
    expect(screen.getByText('Week')).toBeInTheDocument();
    expect(screen.getByText('Month')).toBeInTheDocument();
    expect(screen.getByText('Year')).toBeInTheDocument();
  });

  it('highlights the selected period', () => {
    render(<PeriodSelector period="month" onChange={mockOnChange} />);
    
    const monthButton = screen.getByText('Month').closest('button');
    expect(monthButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('calls onChange when a different period is selected', () => {
    render(<PeriodSelector period="week" onChange={mockOnChange} />);
    
    fireEvent.click(screen.getByText('Month'));
    expect(mockOnChange).toHaveBeenCalledWith('month');
  });

  it('does not call onChange when the same period is selected', () => {
    render(<PeriodSelector period="week" onChange={mockOnChange} />);
    
    fireEvent.click(screen.getByText('Week'));
    expect(mockOnChange).not.toHaveBeenCalled();
  });
});