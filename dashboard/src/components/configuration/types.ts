export interface SystemConfiguration {
  openaiModel: string;
  maxPdfSizeMb: number;
  rateLimitPerMinute: number;
  webhookValidation: boolean;
  logLevel: string;
  alertThresholds: {
    errorRate: number;
    responseTime: number;
    cpuUsage: number;
    memoryUsage: number;
  };
}

export interface ConfigSectionProps {
  title: string;
  children: React.ReactNode;
}

export interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export interface RateLimitInputProps {
  value: number;
  onChange: (value: number) => void;
  error?: string;
}

export interface PDFSizeInputProps {
  value: number;
  onChange: (value: number) => void;
  error?: string;
}

export interface LogLevelSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export interface AlertThresholdSettingsProps {
  thresholds: {
    errorRate: number;
    responseTime: number;
    cpuUsage: number;
    memoryUsage: number;
  };
  onChange: (thresholds: {
    errorRate: number;
    responseTime: number;
    cpuUsage: number;
    memoryUsage: number;
  }) => void;
  errors?: {
    errorRate?: string;
    responseTime?: string;
    cpuUsage?: string;
    memoryUsage?: string;
  };
}

export interface ConfigurationFormProps {
  config: SystemConfiguration;
  onSave: (config: SystemConfiguration) => void;
  isLoading?: boolean;
}