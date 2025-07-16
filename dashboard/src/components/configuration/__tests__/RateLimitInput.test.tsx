import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import RateLimitInput from '../RateLimitInput';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('RateLimitInput', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it('renders with default values', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByDisplayValue('100')).toBeInTheDocument();
    expect(screen.getByText('Requests per minute')).toBeInTheDocument();
    expect(screen.getByText('Requests per hour')).toBeInTheDocument();
  });

  it('calls onChange when requests per minute changes', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    fireEvent.change(perMinuteInput, { target: { value: '20' } });

    expect(mockOnChange).toHaveBeenCalledWith({
      requestsPerMinute: 20,
      requestsPerHour: 100,
    });
  });

  it('calls onChange when requests per hour changes', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perHourInput = screen.getByLabelText('Requests per hour');
    fireEvent.change(perHourInput, { target: { value: '200' } });

    expect(mockOnChange).toHaveBeenCalledWith({
      requestsPerMinute: 10,
      requestsPerHour: 200,
    });
  });

  it('handles zero values', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={0}
        requestsPerHour={0}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByDisplayValue('0')).toBeInTheDocument();
  });

  it('handles large values', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={9999}
        requestsPerHour={999999}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByDisplayValue('9999')).toBeInTheDocument();
    expect(screen.getByDisplayValue('999999')).toBeInTheDocument();
  });

  it('handles negative values by converting to positive', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    fireEvent.change(perMinuteInput, { target: { value: '-5' } });

    expect(mockOnChange).toHaveBeenCalledWith({
      requestsPerMinute: 5,
      requestsPerHour: 100,
    });
  });

  it('handles non-numeric input gracefully', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    fireEvent.change(perMinuteInput, { target: { value: 'abc' } });

    // Should not call onChange with invalid value
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('handles empty input', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    fireEvent.change(perMinuteInput, { target: { value: '' } });

    expect(mockOnChange).toHaveBeenCalledWith({
      requestsPerMinute: 0,
      requestsPerHour: 100,
    });
  });

  it('handles decimal values by rounding', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    fireEvent.change(perMinuteInput, { target: { value: '15.7' } });

    expect(mockOnChange).toHaveBeenCalledWith({
      requestsPerMinute: 16,
      requestsPerHour: 100,
    });
  });

  it('maintains focus when typing', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    perMinuteInput.focus();
    
    expect(perMinuteInput).toHaveFocus();
    
    fireEvent.change(perMinuteInput, { target: { value: '20' } });
    
    expect(perMinuteInput).toHaveFocus();
  });

  it('shows helper text for inputs', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('Maximum requests allowed per minute')).toBeInTheDocument();
    expect(screen.getByText('Maximum requests allowed per hour')).toBeInTheDocument();
  });

  it('validates logical relationship between minute and hour limits', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={100}
        requestsPerHour={50}
        onChange={mockOnChange}
      />
    );

    // Should display both values even if illogical
    expect(screen.getByDisplayValue('100')).toBeInTheDocument();
    expect(screen.getByDisplayValue('50')).toBeInTheDocument();
  });

  it('handles rapid input changes', () => {
    renderWithTheme(
      <RateLimitInput
        requestsPerMinute={10}
        requestsPerHour={100}
        onChange={mockOnChange}
      />
    );

    const perMinuteInput = screen.getByLabelText('Requests per minute');
    
    fireEvent.change(perMinuteInput, { target: { value: '5' } });
    fireEvent.change(perMinuteInput, { target: { value: '15' } });
    fireEvent.change(perMinuteInput, { target: { value: '25' } });

    expect(mockOnChange).toHaveBeenCalledTimes(3);
    expect(mockOnChange).toHaveBeenLastCalledWith({
      requestsPerMinute: 25,
      requestsPerHour: 100,
    });
  });
});