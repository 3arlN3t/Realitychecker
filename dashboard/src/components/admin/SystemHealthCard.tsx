import React from 'react';
import {
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info
} from 'lucide-react';

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  uptime: string;
  lastUpdated: string;
  services: {
    openai: ServiceStatus;
    twilio: ServiceStatus;
    database: ServiceStatus;
    webhook: ServiceStatus;
  };
  memoryUsage: number; // percentage
  cpuUsage: number; // percentage
}

export interface ServiceStatus {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  responseTime?: number; // in ms
  lastCheck: string;
  errorCount?: number;
}

interface SystemHealthCardProps {
  health: SystemHealth;
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
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

  const getProgressColor = (percentage: number) => {
    if (percentage < 70) return 'bg-green-500';
    if (percentage < 85) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="h-full">
      <div className="flex items-center mb-4">
        {getStatusIcon(health.status)}
        <h3 className="ml-2 flex-grow text-lg font-medium">
          System Health
        </h3>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(health.status)}`}>
          {health.status.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-400">
            Uptime
          </p>
          <p className="text-lg font-medium text-green-500">
            {health.uptime}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-400">
            Last Updated
          </p>
          <p className="text-sm">
            {health.lastUpdated}
          </p>
        </div>
      </div>

      <div className="mt-6">
        <h4 className="text-sm font-medium mb-2">
          Resource Usage
        </h4>
        
        <div className="mb-4">
          <div className="flex justify-between mb-1">
            <span className="text-sm">Memory</span>
            <span className="text-sm">{health.memoryUsage}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${getProgressColor(health.memoryUsage)}`} 
              style={{ width: `${health.memoryUsage}%` }}
              role="progressbar"
              aria-valuenow={health.memoryUsage}
              aria-valuemin={0}
              aria-valuemax={100}
            ></div>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex justify-between mb-1">
            <span className="text-sm">CPU</span>
            <span className="text-sm">{health.cpuUsage}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${getProgressColor(health.cpuUsage)}`} 
              style={{ width: `${health.cpuUsage}%` }}
              role="progressbar"
              aria-valuenow={health.cpuUsage}
              aria-valuemin={0}
              aria-valuemax={100}
            ></div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <h4 className="text-sm font-medium mb-2">
          Service Status
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {Object.entries(health.services).map(([serviceName, service]) => (
            <div
              key={serviceName}
              className={`flex items-center p-2 border rounded ${
                service.status === 'healthy' 
                  ? 'bg-green-500/5 border-green-500/20' 
                  : service.status === 'warning'
                  ? 'bg-yellow-500/5 border-yellow-500/20'
                  : service.status === 'critical'
                  ? 'bg-red-500/5 border-red-500/20'
                  : 'bg-gray-500/5 border-gray-500/20'
              }`}
            >
              {getStatusIcon(service.status)}
              <div className="ml-2 min-w-0">
                <p className="text-xs capitalize">
                  {serviceName}
                </p>
                {service.responseTime && (
                  <p className="text-xs text-gray-400">
                    {service.responseTime}ms
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SystemHealthCard;