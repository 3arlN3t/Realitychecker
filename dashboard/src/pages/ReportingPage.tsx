import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Chip
} from '@mui/material';
import {
  Description as FileTextIcon,
  ViewModule as LayoutIcon,
  Event as CalendarIcon,
  History as HistoryIcon,
  BarChart as BarChart3Icon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import ReportGenerator from '../components/reporting/ReportGenerator';
import ReportTemplates from '../components/reporting/ReportTemplates';
import ReportHistory from '../components/reporting/ReportHistory';
import ReportScheduler from '../components/reporting/ReportScheduler';
import { 
  ReportParameters, 
  ReportData, 
  ReportTemplate, 
  ScheduledReport, 
  ReportHistoryItem 
} from '../components/reporting/types';
import { format, subDays } from 'date-fns';

// Sample data for demonstration
const sampleTemplates: ReportTemplate[] = [
  {
    id: '1',
    name: 'Monthly Usage Summary',
    description: 'Overview of system usage for the past month',
    report_type: 'usage_summary',
    default_parameters: {
      start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd'),
      export_format: 'pdf'
    },
    icon: 'bar_chart'
  },
  {
    id: '2',
    name: 'Classification Breakdown',
    description: 'Detailed analysis of job ad classifications',
    report_type: 'classification_analysis',
    default_parameters: {
      start_date: format(subDays(new Date(), 14), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd'),
      export_format: 'xlsx'
    },
    icon: 'pie_chart'
  },
  {
    id: '3',
    name: 'Performance Report',
    description: 'System performance metrics and response times',
    report_type: 'performance_metrics',
    default_parameters: {
      start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      end_date: format(new Date(), 'yyyy-MM-dd'),
      export_format: 'pdf'
    },
    icon: 'speed'
  }
];

const sampleScheduledReports: ScheduledReport[] = [
  {
    id: '1',
    name: 'Weekly Performance Report',
    parameters: {
      report_type: 'performance_metrics',
      start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'pdf'
    },
    schedule: {
      frequency: 'weekly',
      day: 1, // Monday
      time: '08:00',
      recipients: ['admin@example.com', 'analyst@example.com']
    },
    last_run: format(subDays(new Date(), 7), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    next_run: format(new Date(new Date().setDate(new Date().getDate() + (1 + 7 - new Date().getDay()) % 7)), 'yyyy-MM-dd\'T\'08:00:00')
  },
  {
    id: '2',
    name: 'Monthly Usage Summary',
    parameters: {
      report_type: 'usage_summary',
      start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'xlsx'
    },
    schedule: {
      frequency: 'monthly',
      day: 1,
      time: '09:00',
      recipients: ['admin@example.com']
    },
    last_run: format(subDays(new Date(), 15), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    next_run: format(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1, 9, 0, 0), 'yyyy-MM-dd\'T\'09:00:00')
  }
];

const sampleReportHistory: ReportHistoryItem[] = [
  {
    id: '1',
    report_type: 'usage_summary',
    generated_at: format(subDays(new Date(), 1), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    parameters: {
      report_type: 'usage_summary',
      start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'pdf'
    },
    download_url: '#',
    file_size: 1024 * 512, // 512 KB
    generated_by: 'admin',
    scheduled: false
  },
  {
    id: '2',
    report_type: 'classification_analysis',
    generated_at: format(subDays(new Date(), 3), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    parameters: {
      report_type: 'classification_analysis',
      start_date: format(subDays(new Date(), 14), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'xlsx'
    },
    download_url: '#',
    file_size: 1024 * 256, // 256 KB
    generated_by: 'analyst',
    scheduled: false
  },
  {
    id: '3',
    report_type: 'performance_metrics',
    generated_at: format(subDays(new Date(), 7), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    parameters: {
      report_type: 'performance_metrics',
      start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'pdf'
    },
    download_url: '#',
    file_size: 1024 * 384, // 384 KB
    generated_by: 'system',
    scheduled: true
  },
  {
    id: '4',
    report_type: 'error_analysis',
    generated_at: format(subDays(new Date(), 10), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    parameters: {
      report_type: 'error_analysis',
      start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'csv'
    },
    download_url: '#',
    file_size: 1024 * 128, // 128 KB
    generated_by: 'admin',
    scheduled: false
  },
  {
    id: '5',
    report_type: 'user_behavior',
    generated_at: format(subDays(new Date(), 15), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    parameters: {
      report_type: 'user_behavior',
      start_date: format(subDays(new Date(), 90), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: 'json'
    },
    download_url: '#',
    file_size: 1024 * 64, // 64 KB
    generated_by: 'analyst',
    scheduled: false
  }
];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`reporting-tabpanel-${index}`}
      aria-labelledby={`reporting-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ReportingPage: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [templates] = useState<ReportTemplate[]>(sampleTemplates);
  const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>(sampleScheduledReports);
  const [reportHistory, setReportHistory] = useState<ReportHistoryItem[]>(sampleReportHistory);
  const [historyPage, setHistoryPage] = useState(1);
  const [historySearch, setHistorySearch] = useState('');
  const [reportParameters, setReportParameters] = useState<ReportParameters>({
    report_type: 'usage_summary',
    start_date: format(subDays(new Date(), 30), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    end_date: format(new Date(), 'yyyy-MM-dd\'T\'HH:mm:ss'),
    export_format: 'pdf'
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleGenerateReport = async (parameters: ReportParameters): Promise<ReportData> => {
    // In a real application, this would make an API call
    console.log('Generating report with parameters:', parameters);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Create a new report
    const newReport: ReportData = {
      report_type: parameters.report_type,
      generated_at: new Date().toISOString(),
      period: `${new Date(parameters.start_date).toLocaleDateString()} to ${new Date(parameters.end_date).toLocaleDateString()}`,
      data: { /* Sample data would go here */ },
      export_format: parameters.export_format,
      download_url: '#',
      file_size: Math.floor(Math.random() * 1024 * 1024) // Random file size up to 1MB
    };
    
    // Add to history
    const historyItem: ReportHistoryItem = {
      id: Date.now().toString(),
      report_type: parameters.report_type,
      generated_at: newReport.generated_at,
      parameters,
      download_url: newReport.download_url,
      file_size: newReport.file_size,
      generated_by: user?.username || 'unknown',
      scheduled: false
    };
    
    setReportHistory([historyItem, ...reportHistory]);
    
    return newReport;
  };

  const handleUseTemplate = (template: ReportTemplate) => {
    // Set the report parameters based on the template
    const now = new Date();
    const parameters: ReportParameters = {
      report_type: template.report_type,
      start_date: template.default_parameters.start_date || format(subDays(now, 30), 'yyyy-MM-dd\'T\'HH:mm:ss'),
      end_date: template.default_parameters.end_date || format(now, 'yyyy-MM-dd\'T\'HH:mm:ss'),
      export_format: template.default_parameters.export_format || 'pdf',
      include_user_details: template.default_parameters.include_user_details,
      include_error_details: template.default_parameters.include_error_details,
      classification_filter: template.default_parameters.classification_filter,
      user_filter: template.default_parameters.user_filter
    };
    
    setReportParameters(parameters);
    setTabValue(0); // Switch to Generate tab
  };

  const handleScheduleReport = async (report: Omit<ScheduledReport, 'id'>): Promise<void> => {
    // In a real application, this would make an API call
    console.log('Scheduling report:', report);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Add to scheduled reports
    const newScheduledReport: ScheduledReport = {
      ...report,
      id: Date.now().toString(),
      next_run: calculateNextRun(report.schedule)
    };
    
    setScheduledReports([...scheduledReports, newScheduledReport]);
  };

  const handleEditScheduledReport = async (report: ScheduledReport): Promise<void> => {
    // In a real application, this would make an API call
    console.log('Editing scheduled report:', report);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Update the scheduled report
    const updatedReport = {
      ...report,
      next_run: calculateNextRun(report.schedule)
    };
    
    setScheduledReports(scheduledReports.map(r => r.id === report.id ? updatedReport : r));
  };

  const handleDeleteScheduledReport = async (id: string): Promise<void> => {
    // In a real application, this would make an API call
    console.log('Deleting scheduled report:', id);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Remove from scheduled reports
    setScheduledReports(scheduledReports.filter(r => r.id !== id));
  };

  const handleDeleteReport = async (id: string): Promise<void> => {
    // In a real application, this would make an API call
    console.log('Deleting report:', id);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Remove from history
    setReportHistory(reportHistory.filter(r => r.id !== id));
  };

  const calculateNextRun = (schedule: ScheduledReport['schedule']): string => {
    const now = new Date();
    let nextRun = new Date();
    
    if (schedule.frequency === 'daily') {
      // Set time for next day
      nextRun.setDate(now.getDate() + 1);
      const [hours, minutes] = schedule.time.split(':').map(Number);
      nextRun.setHours(hours, minutes, 0, 0);
    } else if (schedule.frequency === 'weekly') {
      // Set day of week and time
      const scheduleDay = schedule.day ?? 1; // Default to Monday if undefined
      const dayDiff = (scheduleDay - now.getDay() + 7) % 7;
      nextRun.setDate(now.getDate() + (dayDiff === 0 ? 7 : dayDiff));
      const [hours, minutes] = schedule.time.split(':').map(Number);
      nextRun.setHours(hours, minutes, 0, 0);
    } else if (schedule.frequency === 'monthly') {
      // Set day of month and time
      const scheduleDay = schedule.day ?? 1; // Default to 1st of month if undefined
      nextRun = new Date(now.getFullYear(), now.getMonth() + 1, scheduleDay, 0, 0, 0);
      const [hours, minutes] = schedule.time.split(':').map(Number);
      nextRun.setHours(hours, minutes, 0, 0);
    }
    
    return nextRun.toISOString();
  };

  // Filter history based on search
  const filteredHistory = historySearch
    ? reportHistory.filter(report => 
        report.report_type.includes(historySearch.toLowerCase()) ||
        report.generated_by.toLowerCase().includes(historySearch.toLowerCase())
      )
    : reportHistory;

  // Paginate history
  const pageSize = 10;
  const paginatedHistory = filteredHistory.slice((historyPage - 1) * pageSize, historyPage * pageSize);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
          <BarChart3Icon sx={{ mr: 1, fontSize: 32 }} />
          Reporting
        </Typography>
        <Chip
          icon={<FileTextIcon />}
          label={user?.role?.toUpperCase()}
          variant="outlined"
          color="primary"
        />
      </Box>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="reporting tabs">
            <Tab
              icon={<FileTextIcon />}
              label="Generate Report"
              iconPosition="start"
              id="reporting-tab-0"
              aria-controls="reporting-tabpanel-0"
            />
            <Tab
              icon={<LayoutIcon />}
              label="Templates"
              iconPosition="start"
              id="reporting-tab-1"
              aria-controls="reporting-tabpanel-1"
            />
            <Tab
              icon={<CalendarIcon />}
              label="Scheduled Reports"
              iconPosition="start"
              id="reporting-tab-2"
              aria-controls="reporting-tabpanel-2"
            />
            <Tab
              icon={<HistoryIcon />}
              label="Report History"
              iconPosition="start"
              id="reporting-tab-3"
              aria-controls="reporting-tabpanel-3"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Generate Custom Report</Typography>
            <Typography variant="body2" color="text.secondary">
              Create custom reports with specific parameters and export in your preferred format.
            </Typography>
          </Box>
          <ReportGenerator onGenerateReport={handleGenerateReport} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Report Templates</Typography>
            <Typography variant="body2" color="text.secondary">
              Use pre-configured templates for common reporting needs.
            </Typography>
          </Box>
          <ReportTemplates 
            templates={templates} 
            onUseTemplate={handleUseTemplate} 
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Scheduled Reports</Typography>
            <Typography variant="body2" color="text.secondary">
              Manage automated report generation and delivery schedules.
            </Typography>
          </Box>
          <ReportScheduler 
            scheduledReports={scheduledReports}
            onScheduleReport={handleScheduleReport}
            onDeleteScheduledReport={handleDeleteScheduledReport}
            onEditScheduledReport={handleEditScheduledReport}
            reportParameters={reportParameters}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Report History</Typography>
            <Typography variant="body2" color="text.secondary">
              View and manage previously generated reports.
            </Typography>
          </Box>
          <ReportHistory 
            reports={paginatedHistory}
            totalReports={filteredHistory.length}
            page={historyPage}
            pageSize={pageSize}
            onPageChange={setHistoryPage}
            onDeleteReport={handleDeleteReport}
            onSearchChange={setHistorySearch}
          />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default ReportingPage;