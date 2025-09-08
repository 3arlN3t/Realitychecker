import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Alert,
  Grid,
  Paper,
  Divider,
  CircularProgress,
  Chip,
  Stack,
  Avatar,
  Fade,
  Zoom
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { subDays, isBefore } from 'date-fns';
import {
  Description as FileTextIcon,
  CloudDownload as DownloadIcon,
  Assessment as AssessmentIcon,
  PieChart as PieChartIcon,
  People as PeopleIcon,
  Speed as SpeedIcon,
  BugReport as BugReportIcon,
  TrendingUp as TrendingUpIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  GridOn as ExcelIcon,
  Code as JsonIcon,
  CalendarToday as CalendarIcon,
  FilterList as FilterIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
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
  const [generatedReport, setGeneratedReport] = useState<ReportData | null>(null);
  const [showJson, setShowJson] = useState(false);

  const reportTypeOptions: { value: ReportType; label: string; description: string; icon: React.ReactElement; color: string }[] = [
    { 
      value: 'usage_summary', 
      label: 'Usage Summary', 
      description: 'Overview of system usage including message counts, success rates, and basic metrics',
      icon: <AssessmentIcon />,
      color: '#1976d2'
    },
    { 
      value: 'classification_analysis', 
      label: 'Classification Analysis', 
      description: 'Detailed breakdown of job ad classifications with trends and patterns',
      icon: <PieChartIcon />,
      color: '#7b1fa2'
    },
    { 
      value: 'user_behavior', 
      label: 'User Behavior', 
      description: 'Analysis of user engagement patterns, retention, and interaction habits',
      icon: <PeopleIcon />,
      color: '#388e3c'
    },
    { 
      value: 'performance_metrics', 
      label: 'Performance Metrics', 
      description: 'System performance data including response times, success rates, and resource usage',
      icon: <SpeedIcon />,
      color: '#f57c00'
    },
    { 
      value: 'error_analysis', 
      label: 'Error Analysis', 
      description: 'Breakdown of errors by type, frequency, and impact on system performance',
      icon: <BugReportIcon />,
      color: '#d32f2f'
    },
    { 
      value: 'trend_analysis', 
      label: 'Trend Analysis', 
      description: 'Long-term trends in usage, classifications, and system performance',
      icon: <TrendingUpIcon />,
      color: '#0288d1'
    },
  ];

  const exportFormatOptions: { value: ExportFormat; label: string; icon: React.ReactElement; color: string }[] = [
    { value: 'pdf', label: 'PDF Document', icon: <PdfIcon />, color: '#d32f2f' },
    { value: 'csv', label: 'CSV Spreadsheet', icon: <CsvIcon />, color: '#388e3c' },
    { value: 'xlsx', label: 'Excel Spreadsheet', icon: <ExcelIcon />, color: '#1976d2' },
    { value: 'json', label: 'JSON Data', icon: <JsonIcon />, color: '#7b1fa2' },
  ];

  const validateDateRange = (): boolean => {
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
        user_filter: userFilter || undefined,
      };
      
      const report = await onGenerateReport(parameters);
      setGeneratedReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const getSelectedReportType = () => {
    return reportTypeOptions.find(option => option.value === reportType);
  };

  const getSelectedExportFormat = () => {
    return exportFormatOptions.find(option => option.value === exportFormat);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {/* Header Section */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            borderRadius: 3,
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <Box sx={{ position: 'absolute', top: -50, right: -50, opacity: 0.1 }}>
            <FileTextIcon sx={{ fontSize: 200 }} />
          </Box>
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
              Generate Custom Report
            </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9 }}>
              Create detailed reports with custom parameters and export in your preferred format
            </Typography>
          </Box>
        </Paper>

        {/* Report Type Selection */}
        <Card elevation={2} sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <AssessmentIcon />
              </Avatar>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Select Report Type
              </Typography>
            </Box>
            
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, 
              gap: 2 
            }}>
              {reportTypeOptions.map((option) => (
                <Paper
                  key={option.value}
                  elevation={reportType === option.value ? 4 : 1}
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    border: reportType === option.value ? 2 : 1,
                    borderColor: reportType === option.value ? option.color : 'divider',
                    bgcolor: reportType === option.value ? `${option.color}10` : 'background.paper',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      elevation: 3,
                      transform: 'translateY(-2px)'
                    }
                  }}
                  onClick={() => setReportType(option.value)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Avatar sx={{ bgcolor: option.color, width: 32, height: 32, mr: 1 }}>
                      <Box sx={{ fontSize: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {option.icon}
                      </Box>
                    </Avatar>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                      {option.label}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                    {option.description}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Configuration Section */}
        <Card elevation={2} sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                <SettingsIcon />
              </Avatar>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Report Configuration
              </Typography>
            </Box>

            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
              gap: 3 
            }}>
              {/* Export Format Selection */}
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'medium' }}>
                  Export Format
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {exportFormatOptions.map((option) => (
                    <Chip
                      key={option.value}
                      icon={option.icon}
                      label={option.label}
                      onClick={() => setExportFormat(option.value)}
                      color={exportFormat === option.value ? 'primary' : 'default'}
                      variant={exportFormat === option.value ? 'filled' : 'outlined'}
                      sx={{
                        mb: 1,
                        '&:hover': {
                          transform: 'scale(1.05)'
                        }
                      }}
                    />
                  ))}
                </Stack>
              </Box>

              {/* Date Range */}
              <Box>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'medium' }}>
                  <CalendarIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Date Range
                </Typography>
                <Stack spacing={2}>
                  <DatePicker
                    label="Start Date"
                    value={startDate}
                    onChange={(date) => {
                      if (date) {
                        setStartDate(date);
                        if (isBefore(endDate, date)) {
                          setEndDate(date);
                        }
                      }
                    }}
                    maxDate={new Date()}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        variant: 'outlined',
                        size: 'small'
                      }
                    }}
                  />
                  <DatePicker
                    label="End Date"
                    value={endDate}
                    onChange={(date) => {
                      if (date) {
                        setEndDate(date);
                      }
                    }}
                    minDate={startDate}
                    maxDate={new Date()}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        variant: 'outlined',
                        size: 'small'
                      }
                    }}
                  />
                </Stack>
              </Box>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Additional Options */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'medium' }}>
                <FilterIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Additional Options
              </Typography>
              <Stack direction="row" spacing={3} flexWrap="wrap">
                <FormControlLabel
                  control={
                    <Checkbox 
                      checked={includeUserDetails}
                      onChange={(e) => setIncludeUserDetails(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Include User Details"
                />
                <FormControlLabel
                  control={
                    <Checkbox 
                      checked={includeErrorDetails}
                      onChange={(e) => setIncludeErrorDetails(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Include Error Details"
                />
              </Stack>
            </Box>

            {/* User Filter */}
            <TextField
              fullWidth
              label="Filter by User (Optional)"
              placeholder="e.g., whatsapp:+1234567890"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              helperText="Optional: Filter report to specific user"
              variant="outlined"
              size="small"
              sx={{ mb: 3 }}
            />

            {/* Error Display */}
            {error && (
              <Fade in={!!error}>
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              </Fade>
            )}

            {/* Generate Button */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Button
                variant="contained"
                size="large"
                onClick={handleGenerateReport}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileTextIcon />}
                sx={{
                  px: 6,
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 'bold',
                  background: 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 4px 20px rgba(102, 126, 234, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #5a6fd8 0%, #6a4190 100%)',
                    boxShadow: '0 6px 25px rgba(102, 126, 234, 0.6)',
                    transform: 'translateY(-2px)'
                  },
                  '&:disabled': {
                    background: 'linear-gradient(45deg, #ccc 0%, #999 100%)',
                  }
                }}
              >
                {loading ? 'Generating Report...' : 'Generate Report'}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Generated Report Display */}
        {generatedReport && (
          <Zoom in={!!generatedReport}>
            <Card 
              elevation={4} 
              sx={{ 
                borderRadius: 3,
                border: '2px solid',
                borderColor: 'success.main',
                bgcolor: 'success.main',
                opacity: 0.05
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <CheckIcon />
                  </Avatar>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                    Report Generated Successfully!
                  </Typography>
                </Box>

                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
                  gap: 3, 
                  mb: 3 
                }}>
                  <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Report Details
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="body2">
                        <strong>Type:</strong> {reportTypeOptions.find(o => o.value === generatedReport.report_type)?.label}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Generated:</strong> {new Date(generatedReport.generated_at).toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Period:</strong> {generatedReport.period}
                      </Typography>
                    </Stack>
                  </Paper>
                  <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      File Information
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="body2">
                        <strong>Format:</strong> {exportFormatOptions.find(o => o.value === generatedReport.export_format)?.label}
                      </Typography>
                      {generatedReport.file_size && (
                        <Typography variant="body2">
                          <strong>Size:</strong> {(generatedReport.file_size / 1024).toFixed(2)} KB
                        </Typography>
                      )}
                    </Stack>
                  </Paper>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                  {generatedReport.download_url && (
                    <Button
                      variant="contained"
                      color="success"
                      size="large"
                      startIcon={<DownloadIcon />}
                      component="a"
                      href={generatedReport.download_url}
                      sx={{
                        px: 4,
                        py: 1.5,
                        fontWeight: 'bold',
                        boxShadow: '0 4px 20px rgba(76, 175, 80, 0.4)',
                        '&:hover': {
                          boxShadow: '0 6px 25px rgba(76, 175, 80, 0.6)',
                          transform: 'translateY(-2px)'
                        }
                      }}
                    >
                      Download Report
                    </Button>
                  )}
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={() => setShowJson(prev => !prev)}
                  >
                    {showJson ? 'Hide Details' : 'View Details'}
                  </Button>
                </Box>

                {showJson && (
                  <Paper elevation={0} sx={{ mt: 3, p: 2, bgcolor: 'grey.100', maxHeight: 360, overflow: 'auto' }}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                      Report Data (JSON)
                    </Typography>
                    <pre style={{ margin: 0, fontSize: 12 }}>
                      {JSON.stringify(generatedReport.data ?? {}, null, 2)}
                    </pre>
                  </Paper>
                )}
              </CardContent>
            </Card>
          </Zoom>
        )}
      </Box>
    </LocalizationProvider>
  );
};

export default ReportGenerator;
