import React, { useState } from 'react';
import { 
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '../ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { DatePicker } from '../ui/date-picker';
import { subDays, isBefore } from 'date-fns';
import { FileText, Loader2 } from 'lucide-react';
import { ReportParameters, ReportType, ExportFormat, ReportData } from './types';
import { Alert, AlertDescription } from '../ui/alert';

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

  const exportFormatOptions: { value: ExportFormat; label: string }[] = [
    { value: 'pdf', label: 'PDF Document' },
    { value: 'csv', label: 'CSV Spreadsheet' },
    { value: 'xlsx', label: 'Excel Spreadsheet' },
    { value: 'json', label: 'JSON Data' },
  ];

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

  const getSelectedReportTypeDescription = () => {
    const selected = reportTypeOptions.find(option => option.value === reportType);
    return selected ? selected.description : '';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            Generate Custom Report
          </CardTitle>
          <CardDescription>
            Create custom reports with specific parameters and export in your preferred format.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Report Type Selection */}
            <div className="space-y-2">
              <Label htmlFor="report-type">Report Type</Label>
              <Select
                value={reportType}
                onValueChange={(value) => setReportType(value as ReportType)}
              >
                <SelectTrigger id="report-type" className="w-full">
                  <SelectValue placeholder="Select report type" />
                </SelectTrigger>
                <SelectContent>
                  {reportTypeOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {getSelectedReportTypeDescription()}
              </p>
            </div>
            
            {/* Export Format Selection */}
            <div className="space-y-2">
              <Label htmlFor="export-format">Export Format</Label>
              <Select
                value={exportFormat}
                onValueChange={(value) => setExportFormat(value as ExportFormat)}
              >
                <SelectTrigger id="export-format" className="w-full">
                  <SelectValue placeholder="Select export format" />
                </SelectTrigger>
                <SelectContent>
                  {exportFormatOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Date Range Selection */}
            <DatePicker
              id="start-date"
              label="Start Date"
              value={startDate}
              onChange={(date) => {
                setStartDate(date);
                if (isBefore(endDate, date)) {
                  setEndDate(date);
                }
              }}
              max={new Date()}
            />
            
            <DatePicker
              id="end-date"
              label="End Date"
              value={endDate}
              onChange={(date) => setEndDate(date)}
              min={startDate}
              max={new Date()}
            />
          </div>
          
          {/* Additional Options */}
          <div className="mt-6 space-y-4">
            <h3 className="text-sm font-medium">Additional Options</h3>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="include-user-details" 
                  checked={includeUserDetails}
                  onCheckedChange={(checked) => setIncludeUserDetails(checked === true)}
                />
                <Label htmlFor="include-user-details">Include User Details</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="include-error-details" 
                  checked={includeErrorDetails}
                  onCheckedChange={(checked) => setIncludeErrorDetails(checked === true)}
                />
                <Label htmlFor="include-error-details">Include Error Details</Label>
              </div>
            </div>
          </div>
          
          {/* User Filter */}
          <div className="mt-4 space-y-2">
            <Label htmlFor="user-filter">Filter by User (Optional)</Label>
            <Input
              id="user-filter"
              placeholder="e.g., whatsapp:+1234567890"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Optional: Filter report to specific user
            </p>
          </div>
          
          {/* Error Display */}
          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Generate Button */}
          <div className="mt-6 flex justify-end">
            <Button
              onClick={handleGenerateReport}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Generated Report Display */}
      {generatedReport && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Report</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm"><span className="font-medium">Report Type:</span> {reportTypeOptions.find(o => o.value === generatedReport.report_type)?.label}</p>
                <p className="text-sm"><span className="font-medium">Generated At:</span> {new Date(generatedReport.generated_at).toLocaleString()}</p>
                <p className="text-sm"><span className="font-medium">Period:</span> {generatedReport.period}</p>
              </div>
              <div>
                <p className="text-sm"><span className="font-medium">Format:</span> {exportFormatOptions.find(o => o.value === generatedReport.export_format)?.label}</p>
                {generatedReport.file_size && (
                  <p className="text-sm"><span className="font-medium">File Size:</span> {(generatedReport.file_size / 1024).toFixed(2)} KB</p>
                )}
              </div>
            </div>
            {generatedReport.download_url && (
              <div className="mt-4 flex justify-end">
                <Button asChild>
                  <a href={generatedReport.download_url}>Download Report</a>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReportGenerator;