import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Activity,
  Database,
  Cloud,
  Webhook,
  Brain
} from 'lucide-react';
import { ServiceStatus } from './SystemHealthCard';

export interface ServiceDetails extends ServiceStatus {
  name: string;
  description: string;
  version?: string;
  endpoint?: string;
  dependencies?: string[];
  metrics?: {
    requestsPerMinute: number;
    successRate: number;
    avgResponseTime: number;
    uptime: string;
  };
  recentErrors?: Array<{
    timestamp: string;
    error: string;
    count: number;
  }>;
}

interface ServiceStatusGridProps {
  services: Record<string, ServiceDetails>;
  onRefreshService?: (serviceName: string) => void;
  onViewDetails?: (serviceName: string) => void;
}

const ServiceStatusGrid: React.FC<ServiceStatusGridProps> = ({
  services,
  onRefreshService,
  onViewDetails,
}) => {
  const [expandedService, setExpandedService] = useState<string | null>(null);

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'openai':
        return <Brain className="w-5 h-5" />;
      case 'twilio':
        return <Cloud className="w-5 h-5" />;
      case 'database':
        return <Database className="w-5 h-5" />;
      case 'webhook':
        return <Webhook className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'warning':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'critical':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      default:
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  const getStatusBorder = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'border-green-500/30';
      case 'warning':
        return 'border-yellow-500/30';
      case 'critical':
        return 'border-red-500/30';
      default:
        return 'border-gray-700';
    }
  };

  const getStatusBackground = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500/5';
      case 'warning':
        return 'bg-yellow-500/5';
      case 'critical':
        return 'bg-red-500/5';
      default:
        return 'bg-gray-800';
    }
  };

  const formatResponseTime = (time?: number) => {
    if (!time) return 'N/A';
    if (time < 1000) return `${time}ms`;
    return `${(time / 1000).toFixed(1)}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const handleExpandClick = (serviceName: string) => {
    setExpandedService(expandedService === serviceName ? null : serviceName);
  };

  const getProgressColor = (percentage: number) => {
    if (percentage > 95) return 'bg-green-500';
    if (percentage > 90) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="h-full">
      <div className="flex items-center mb-4">
        <Activity className="w-5 h-5 text-primary" />
        <h3 className="ml-2 flex-grow text-lg font-medium">
          Service Health Monitoring
        </h3>
        <span className="text-xs text-muted-foreground">
          {Object.keys(services).length} Services
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(services).map(([serviceName, service]) => (
          <div key={serviceName} className="h-full">
            <div
              className={`h-full border-2 rounded-lg ${getStatusBorder(service.status)} ${getStatusBackground(service.status)}`}
            >
              <div className="p-4">
                <div className="flex items-center mb-2">
                  <div className="flex items-center flex-grow">
                    <div className="text-primary">
                      {getServiceIcon(serviceName)}
                    </div>
                    <h4 className="ml-2 text-base font-medium capitalize">
                      {service.name || serviceName}
                    </h4>
                  </div>
                  <div className="flex items-center space-x-1">
                    {onRefreshService && (
                      <button
                        className="p-1 hover:bg-gray-700 rounded-full"
                        onClick={() => onRefreshService(serviceName)}
                        aria-label="Refresh status"
                        title="Refresh status"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      className="p-1 hover:bg-gray-700 rounded-full"
                      onClick={() => handleExpandClick(serviceName)}
                      aria-label={expandedService === serviceName ? "Hide details" : "Show details"}
                      title={expandedService === serviceName ? "Hide details" : "Show details"}
                    >
                      {expandedService === serviceName ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center mb-2">
                  {getStatusIcon(service.status)}
                  <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(service.status)}`}>
                    {service.status.toUpperCase()}
                  </span>
                </div>

                <p className="text-sm text-gray-300 mb-3">
                  {service.description}
                </p>

                <div className="flex justify-between mb-2">
                  <span className="text-xs text-gray-400">
                    Response Time
                  </span>
                  <span className="text-xs font-medium">
                    {formatResponseTime(service.responseTime)}
                  </span>
                </div>

                <div className="flex justify-between mb-2">
                  <span className="text-xs text-gray-400">
                    Last Check
                  </span>
                  <span className="text-xs">
                    {formatTimestamp(service.lastCheck)}
                  </span>
                </div>

                {service.errorCount !== undefined && service.errorCount > 0 && (
                  <div className="flex justify-between mb-2">
                    <span className="text-xs text-red-500">
                      Recent Errors
                    </span>
                    <span className="text-xs font-medium text-red-500">
                      {service.errorCount}
                    </span>
                  </div>
                )}

                {expandedService === serviceName && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    {service.version && (
                      <div className="flex justify-between mb-2">
                        <span className="text-xs text-gray-400">
                          Version
                        </span>
                        <span className="text-xs">
                          {service.version}
                        </span>
                      </div>
                    )}

                    {service.endpoint && (
                      <div className="mb-2">
                        <span className="text-xs text-gray-400 block mb-1">
                          Endpoint
                        </span>
                        <span className="text-xs break-all">
                          {service.endpoint}
                        </span>
                      </div>
                    )}

                    {service.dependencies && service.dependencies.length > 0 && (
                      <div className="mb-3">
                        <span className="text-xs text-gray-400 block mb-1">
                          Dependencies
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {service.dependencies.map((dep) => (
                            <span
                              key={`${serviceName}-dep-${dep}`}
                              className="px-2 py-0.5 text-xs border border-gray-700 rounded-full"
                            >
                              {dep}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {service.metrics && (
                      <div className="mb-2">
                        <span className="text-xs text-gray-400 block mb-2">
                          Performance Metrics
                        </span>
                        <div className="mt-2">
                          <div className="flex justify-between mb-1">
                            <span className="text-xs">Success Rate</span>
                            <span className="text-xs font-medium">
                              {service.metrics.successRate.toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-1 mb-2">
                            <div 
                              className={`h-1 rounded-full ${getProgressColor(service.metrics.successRate)}`} 
                              style={{ width: `${service.metrics.successRate}%` }}
                              role="progressbar"
                              aria-valuenow={service.metrics.successRate}
                              aria-valuemin={0}
                              aria-valuemax={100}
                            ></div>
                          </div>
                          <div className="flex justify-between mb-1">
                            <span className="text-xs">Requests/min</span>
                            <span className="text-xs font-medium">
                              {service.metrics.requestsPerMinute}
                            </span>
                          </div>
                          <div className="flex justify-between mb-1">
                            <span className="text-xs">Uptime</span>
                            <span className="text-xs font-medium">
                              {service.metrics.uptime}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {service.recentErrors && service.recentErrors.length > 0 && (
                      <div>
                        <span className="text-xs text-red-500 block mb-1">
                          Recent Errors
                        </span>
                        <div className="max-h-24 overflow-auto">
                          {service.recentErrors.slice(0, 3).map((error) => (
                            <div key={`${serviceName}-error-${error.timestamp}-${error.error}`} className="mb-2">
                              <span className="text-xs text-red-500 block">
                                {formatTimestamp(error.timestamp)} ({error.count}x)
                              </span>
                              <span className="text-xs text-gray-400 block">
                                {error.error}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceStatusGrid;