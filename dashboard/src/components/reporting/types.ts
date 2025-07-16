/**
 * Type definitions for reporting components
 */

export type ReportType = 
  | 'usage_summary'
  | 'classification_analysis'
  | 'user_behavior'
  | 'performance_metrics'
  | 'error_analysis'
  | 'trend_analysis';

export type ExportFormat = 'json' | 'csv' | 'pdf' | 'xlsx';

export interface ReportParameters {
  report_type: ReportType;
  start_date: string; // ISO format date string
  end_date: string; // ISO format date string
  export_format: ExportFormat;
  include_user_details?: boolean;
  include_error_details?: boolean;
  classification_filter?: string | null;
  user_filter?: string | null;
}

export interface ReportData {
  report_type: ReportType;
  generated_at: string; // ISO format date string
  period: string;
  data: any;
  export_format: ExportFormat;
  download_url?: string;
  file_size?: number;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  report_type: ReportType;
  default_parameters: Partial<ReportParameters>;
  icon: string;
}

export interface ScheduledReport {
  id: string;
  name: string;
  parameters: ReportParameters;
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly';
    day?: number; // Day of week (0-6) or day of month (1-31)
    time: string; // HH:MM format
    recipients: string[]; // Email addresses
  };
  last_run?: string; // ISO format date string
  next_run?: string; // ISO format date string
}

export interface ReportHistoryItem {
  id: string;
  report_type: ReportType;
  generated_at: string; // ISO format date string
  parameters: ReportParameters;
  download_url?: string;
  file_size?: number;
  generated_by: string; // Username
  scheduled?: boolean;
}