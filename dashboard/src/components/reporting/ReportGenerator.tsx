import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Button, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  FormControlLabel, 
  Checkbox, 
  CircularProgress, 
  Alert, 
  Snackbar,
  Divider
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { subDays, isAfter, isBefore } from 'date-fns';
import DescriptionIcon from '@mui/icons-material/Description';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { ReportParameters, ReportType, ExportFormat, ReportData } from './types';

interface ReportGeneratorProps {
  onGenerateReport: (parameters: ReportParameters) => Promise<ReportData>;
}

const ReportGenerator: React.FC<ReportGeneratorProps> = ({ onGenerateReport }) => {
  const [reportType, setReportType] = useState<ReportType>('usage_summary');
  const [startDate, setStartDate] = useState<Date>(subDays(new Date(), 30));
  const [endDate, setEndDate] = useState<Date>(new Date());
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf');
  const [includeUserDetails, setIncludeUserDetails] = useState(false);
  const [includeErrorDetails, setIncludeErrorDetails] = useState(false);
  const [userFilter, setUserFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<ReportData | null>(null);

  const reportTypeOptions: { value: ReportType; label: string; description: string }[] = [
    { 
      value: 'usage_summary', 
      label: 'Usage Summary', 
      description: 'Overview of system usage including message counts, success rates, and basic metrics' 
    },
    { 
      value: 'classification_analysis', 
      label: 'Classification Analysis', 
      description: 'Detailed breakdown of job ad classifications with trends and patterns' 
    },
    { 
      value: 'user_behavior', 
      label: 'User Behavior', 
      description: 'Analysis of user engagement patterns, retention, and interaction habits' 
    },
    { 
      value: 'performance_metrics', 
      label: 'Performance Metrics', 
      description: 'System performance data including response times, success rates, and resource usage' 
    },
    { 
      value: 'error_analysis', 
      label: 'Error Analysis', 
      description: 'Breakdown of errors by type, frequency, and impact on system performance' 
    },
    { 
      value: 'trend_analysis', 
      label: 'Trend Analysis', 
      description: 'Long-term trends in usage, classifications, and system performance' 
    },
  ];

  const exportFormatOptions: { value: ExportFormat; label: string; icon: string }[] = [
    { value: 'pdf', label: 'PDF Document', icon: 'picture_as_pdf' },
    { value: 'csv', label: 'CSV Spreadsheet', icon: 'table_chart' },
    { value: 'xlsx', label: 'Excel Spreadsheet', icon: 'table_view' },
    { value: 'json', label: 'JSON Data', icon: 'data_object' },
  ];

  const handleReportTypeChange = (event: any) => {
    setReportType(event.target.value as ReportType);
  };

  const handleExportFormatChange = (event: any) => {
    setExportFormat(event.target.value as ExportFormat);
  };

  const handleStartDateChange = (date: Date | null) => {
    if (date) {
      setStartDate(date);
      
      // Ensure end date is not before start date
      if (isBefore(endDate, date)) {
        setEndDate(date);
      }
    }
  };

  const handleEndDateChange = (date: Date | null) => {
    if (date) {
      setEndDate(date);
      
      // Ensure start date is not after end date
      if (isAfter(startDate, date)) {
        setStartDate(date);
      }
    }
  };

  const validateDateRange = (): boolean => {
    // Check if date range is valid (not more than 365 days)
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays <= 365;
  };

  const handleGenerateReport = async () => {
    if (!validateDateRange()) {
      setError('Date range cannot exceed 365 days');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const parameters: ReportParameters = {
        report_type: reportType,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        export_format: exportFormat,
        include_user_details: includeUserDetails,
        include_error_details: includeErrorDetails,
        user_filter: userFilter || null,
      };
      
      const report = await onGenerateReport(parameters);
      setGeneratedReport(report);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess(false);
  };

  const getSelectedReportTypeDescription = () => {
    const selected = reportTypeOptions.find(option => option.value === reportType);
    return selected ? selected.description : '';
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          <DescriptionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Generate Custom Report
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Create custom reports with specific parameters and export in your preferred format.
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {/* Report Type Selection */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
            <FormControl fullWidth>
              <InputLabel id="report-type-label">Report Type</InputLabel>
              <Select
                labelId="report-type-label"
                id="report-type"
                value={reportType}
                label="Report Type"
                onChange={handleReportTypeChange}
              >
                {reportTypeOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              {getSelectedReportTypeDescription()}
            </Typography>
          </Box>
          
          {/* Export Format Selection */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
            <FormControl fullWidth>
              <InputLabel id="export-format-label">Export Format</InputLabel>
              <Select
                labelId="export-format-label"
                id="export-format"
                value={exportFormat}
                label="Export Format"
                onChange={handleExportFormatChange}
              >
                {exportFormatOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <span className="material-icons" style={{ marginRight: 8 }}>
                        {option.icon}
                      </span>
                      {option.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          
          {/* Date Range Selection */}
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={handleStartDateChange}
              maxDate={new Date()}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Box>
          
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
            <DatePicker
              label="End Date"
              value={endDate}
              onChange={handleEndDateChange}
              minDate={startDate}
              maxDate={new Date()}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Box>
          
          {/* Additional Options */}
          <Box sx={{ flex: '1 1 100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              Additional Options
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeUserDetails}
                    onChange={(e) => setIncludeUserDetails(e.target.checked)}
                  />
                }
                label="Include User Details"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeErrorDetails}
                    onChange={(e) => setIncludeErrorDetails(e.target.checked)}
                  />
                }
                label="Include Error Details"
              />
            </Box>
          </Box>
          
          {/* User Filter */}
          <Box sx={{ flex: '1 1 100%' }}>
            <TextField
              fullWidth
              label="Filter by User (Phone Number)"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              placeholder="e.g., whatsapp:+1234567890"
              helperText="Optional: Filter report to specific user"
            />
          </Box>
          
          {/* Error Display */}
          {error && (
            <Box sx={{ flex: '1 1 100%' }}>
              <Alert severity="error">{error}</Alert>
            </Box>
          )}
          
          {/* Generate Button */}
          <Box sx={{ flex: '1 1 100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="contained"
                color="primary"
                onClick={handleGenerateReport}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <DescriptionIcon />}
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </Box>
          </Box>
        </Box>
      </Paper>
      
      {/* Generated Report Display */}
      {generatedReport && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generated Report
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
              <Typography variant="body2">
                <strong>Report Type:</strong> {reportTypeOptions.find(o => o.value === generatedReport.report_type)?.label}
              </Typography>
              <Typography variant="body2">
                <strong>Generated At:</strong> {new Date(generatedReport.generated_at).toLocaleString()}
              </Typography>
              <Typography variant="body2">
                <strong>Period:</strong> {generatedReport.period}
              </Typography>
            </Box>
            <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
              <Typography variant="body2">
                <strong>Format:</strong> {exportFormatOptions.find(o => o.value === generatedReport.export_format)?.label}
              </Typography>
              {generatedReport.file_size && (
                <Typography variant="body2">
                  <strong>File Size:</strong> {(generatedReport.file_size / 1024).toFixed(2)} KB
                </Typography>
              )}
            </Box>
            <Box sx={{ flex: '1 1 100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                {generatedReport.download_url && (
                  <Button
                    variant="contained"
                    color="primary"
                    href={generatedReport.download_url}
                    startIcon={<FileDownloadIcon />}
                  >
                    Download Report
                  </Button>
                )}
              </Box>
            </Box>
          </Box>
        </Paper>
      )}
      
      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message="Report generated successfully"
      />
    </LocalizationProvider>
  );
};

export default ReportGenerator;