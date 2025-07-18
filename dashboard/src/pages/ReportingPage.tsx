import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { FileText, Layout, Calendar, History, BarChart3 } from 'lucide-react';
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

// Remove the TabPanel component as we'll use shadcn/ui Tabs

const ReportingPage: React.FC = () => {
  const { user } = useAuth();
  // Removed unused tabValue state as we're using shadcn/ui Tabs
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

  // Removed handleTabChange as we're using shadcn/ui Tabs

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
    // Note: With shadcn/ui Tabs, we can't programmatically switch tabs
    // The user will need to manually switch to the Generate tab
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
      const dayDiff = (schedule.day! - now.getDay() + 7) % 7;
      nextRun.setDate(now.getDate() + (dayDiff === 0 ? 7 : dayDiff));
      const [hours, minutes] = schedule.time.split(':').map(Number);
      nextRun.setHours(hours, minutes, 0, 0);
    } else if (schedule.frequency === 'monthly') {
      // Set day of month and time
      nextRun = new Date(now.getFullYear(), now.getMonth() + 1, schedule.day!, 0, 0, 0);
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
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight flex items-center">
          <BarChart3 className="w-8 h-8 mr-2" />
          Reporting
        </h1>
        <Badge variant="outline">
          <FileText className="w-4 h-4 mr-1" />
          {user?.role?.toUpperCase()}
        </Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          <Tabs defaultValue="generate" className="w-full">
            <div className="border-b">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="generate" className="flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Generate Report
                </TabsTrigger>
                <TabsTrigger value="templates" className="flex items-center">
                  <Layout className="w-4 h-4 mr-2" />
                  Templates
                </TabsTrigger>
                <TabsTrigger value="scheduled" className="flex items-center">
                  <Calendar className="w-4 h-4 mr-2" />
                  Scheduled Reports
                </TabsTrigger>
                <TabsTrigger value="history" className="flex items-center">
                  <History className="w-4 h-4 mr-2" />
                  Report History
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="generate" className="p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">Generate Custom Report</h3>
                  <p className="text-sm text-muted-foreground">
                    Create custom reports with specific parameters and export in your preferred format.
                  </p>
                </div>
                <ReportGenerator onGenerateReport={handleGenerateReport} />
              </div>
            </TabsContent>

            <TabsContent value="templates" className="p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">Report Templates</h3>
                  <p className="text-sm text-muted-foreground">
                    Use pre-configured templates for common reporting needs.
                  </p>
                </div>
                <ReportTemplates 
                  templates={templates} 
                  onUseTemplate={handleUseTemplate} 
                />
              </div>
            </TabsContent>

            <TabsContent value="scheduled" className="p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">Scheduled Reports</h3>
                  <p className="text-sm text-muted-foreground">
                    Manage automated report generation and delivery schedules.
                  </p>
                </div>
                <ReportScheduler 
                  scheduledReports={scheduledReports}
                  onScheduleReport={handleScheduleReport}
                  onDeleteScheduledReport={handleDeleteScheduledReport}
                  onEditScheduledReport={handleEditScheduledReport}
                  reportParameters={reportParameters}
                />
              </div>
            </TabsContent>

            <TabsContent value="history" className="p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">Report History</h3>
                  <p className="text-sm text-muted-foreground">
                    View and manage previously generated reports.
                  </p>
                </div>
                <ReportHistory 
                  reports={paginatedHistory}
                  totalReports={filteredHistory.length}
                  page={historyPage}
                  pageSize={pageSize}
                  onPageChange={setHistoryPage}
                  onDeleteReport={handleDeleteReport}
                  onSearchChange={setHistorySearch}
                />
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReportingPage;