import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import ReportGenerator from '../ReportGenerator';
import { ReportParameters, ReportData } from '../types';

// Mock the date picker to avoid test issues
jest.mock('@mui/x-date-pickers/DatePicker', () => {
  return {
    DatePicker: ({ label, value, onChange, slotProps }: any) => (
      <div data-testid={`mock-date-picker-${label.replace(/\s+/g, '-').toLowerCase()}`}>
        <label>{label}</label>
        <input 
          type="text" 
          value={value ? value.toISOString() : ''} 
          onChange={(e) => onChange(new Date(e.target.value))}
          data-testid={`date-input-${label.replace(/\s+/g, '-').toLowerCase()}`}
        />
      </div>
    )
  };
});

describe('ReportGenerator Component', () => {
  const mockOnGenerateReport = jest.fn();
  
  beforeEach(() => {
    mockOnGenerateReport.mockReset();
    mockOnGenerateReport.mockImplementation(async (params: ReportParameters): Promise<ReportData> => {
      return {
        report_type: params.report_type,
        generated_at: new Date().toISOString(),
        period: 'Test Period',
        data: {},
        export_format: params.export_format,
        download_url: '#test-url'
      };
    });
  });

  const renderComponent = () => {
    return render(
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <ReportGenerator onGenerateReport={mockOnGenerateReport} />
      </LocalizationProvider>
    );
  };

  test('renders report generator form', () => {
    renderComponent();
    
    expect(screen.getByText('Generate Custom Report')).toBeInTheDocument();
    expect(screen.getByLabelText('Report Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Export Format')).toBeInTheDocument();
    expect(screen.getByTestId('mock-date-picker-start-date')).toBeInTheDocument();
    expect(screen.getByTestId('mock-date-picker-end-date')).toBeInTheDocument();
    expect(screen.getByText('Include User Details')).toBeInTheDocument();
    expect(screen.getByText('Include Error Details')).toBeInTheDocument();
    expect(screen.getByText('Generate Report')).toBeInTheDocument();
  });

  test('allows changing report type', () => {
    renderComponent();
    
    const reportTypeSelect = screen.getByLabelText('Report Type');
    fireEvent.mouseDown(reportTypeSelect);
    
    // Wait for dropdown to appear and select an option
    const classificationOption = screen.getByText('Classification Analysis');
    fireEvent.click(classificationOption);
    
    expect(reportTypeSelect).toHaveTextContent('Classification Analysis');
  });

  test('allows changing export format', () => {
    renderComponent();
    
    const exportFormatSelect = screen.getByLabelText('Export Format');
    fireEvent.mouseDown(exportFormatSelect);
    
    // Wait for dropdown to appear and select an option
    const csvOption = screen.getByText('CSV Spreadsheet');
    fireEvent.click(csvOption);
    
    expect(exportFormatSelect).toHaveTextContent('CSV Spreadsheet');
  });

  test('generates report when button is clicked', async () => {
    renderComponent();
    
    // Click the generate button
    const generateButton = screen.getByText('Generate Report');
    fireEvent.click(generateButton);
    
    // Wait for the report generation to complete
    await waitFor(() => {
      expect(mockOnGenerateReport).toHaveBeenCalledTimes(1);
    });
    
    // Verify the parameters passed to the generate function
    const params = mockOnGenerateReport.mock.calls[0][0];
    expect(params.report_type).toBe('usage_summary');
    expect(params.export_format).toBe('pdf');
  });

  test('displays generated report after successful generation', async () => {
    renderComponent();
    
    // Click the generate button
    const generateButton = screen.getByText('Generate Report');
    fireEvent.click(generateButton);
    
    // Wait for the report to be generated and displayed
    await waitFor(() => {
      expect(screen.getByText('Generated Report')).toBeInTheDocument();
    });
    
    // Check that the report details are displayed
    expect(screen.getByText('Report Type:')).toBeInTheDocument();
    expect(screen.getByText('Generated At:')).toBeInTheDocument();
    expect(screen.getByText('Format:')).toBeInTheDocument();
  });

  test('shows error message when date range is invalid', async () => {
    renderComponent();
    
    // Set an invalid date range (more than 365 days)
    const startDateInput = screen.getByTestId('date-input-start-date');
    const endDateInput = screen.getByTestId('date-input-end-date');
    
    // Set start date to 2 years ago
    const twoYearsAgo = new Date();
    twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
    
    fireEvent.change(startDateInput, { target: { value: twoYearsAgo.toISOString() } });
    fireEvent.change(endDateInput, { target: { value: new Date().toISOString() } });
    
    // Click the generate button
    const generateButton = screen.getByText('Generate Report');
    fireEvent.click(generateButton);
    
    // Check that error message is displayed
    await waitFor(() => {
      expect(screen.getByText('Date range cannot exceed 365 days')).toBeInTheDocument();
    });
    
    // Verify that the generate function was not called
    expect(mockOnGenerateReport).not.toHaveBeenCalled();
  });
});