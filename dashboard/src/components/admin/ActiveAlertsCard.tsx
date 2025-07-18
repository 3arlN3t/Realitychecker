import React, { useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  X,
  ChevronDown,
  ChevronUp,
  Bell,
  BellOff,
} from 'lucide-react';

export interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  source: string; // e.g., 'OpenAI', 'Twilio', 'System'
  severity: 'low' | 'medium' | 'high' | 'critical';
  acknowledged: boolean;
  details?: string;
  actionRequired?: boolean;
}

interface ActiveAlertsCardProps {
  alerts: Alert[];
  onAcknowledgeAlert?: (alertId: string) => void;
  onDismissAlert?: (alertId: string) => void;
  maxDisplayed?: number;
}

const ActiveAlertsCard: React.FC<ActiveAlertsCardProps> = ({
  alerts,
  onAcknowledgeAlert,
  onDismissAlert,
  maxDisplayed = 5,
}) => {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'high':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'medium':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleExpandClick = (alertId: string) => {
    setExpanded(expanded === alertId ? null : alertId);
  };

  const activeAlerts = alerts.filter(alert => !alert.acknowledged);
  const criticalAlerts = activeAlerts.filter(alert => alert.severity === 'critical');
  const displayedAlerts = showAll ? activeAlerts : activeAlerts.slice(0, maxDisplayed);

  return (
    <div className="h-full">
      <div className="flex items-center mb-4">
        <div className="relative">
          <Bell className="w-5 h-5 text-primary" />
          {activeAlerts.length > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs flex items-center justify-center rounded-full">
              {activeAlerts.length}
            </span>
          )}
        </div>
        <h3 className="ml-2 flex-grow text-lg font-medium">
          Active Alerts
        </h3>
        {criticalAlerts.length > 0 && (
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-500/10 text-red-500 border border-red-500/20">
            {criticalAlerts.length} Critical
          </span>
        )}
      </div>

      {activeAlerts.length === 0 ? (
        <div className="text-center py-8">
          <BellOff className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-green-500 mb-1">
            All Clear!
          </h4>
          <p className="text-sm text-gray-400">
            No active alerts at this time
          </p>
        </div>
      ) : (
        <>
          <div className="max-h-96 overflow-auto">
            {displayedAlerts.map((alert) => (
              <React.Fragment key={alert.id}>
                <div
                  className={`border rounded mb-2 ${
                    alert.severity === 'critical' 
                      ? 'border-red-500 bg-red-500/5' 
                      : 'border-gray-700 bg-gray-900'
                  }`}
                >
                  <div className="flex items-start p-3">
                    <div className="mr-3 mt-0.5">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-grow min-w-0">
                      <div className="flex items-center flex-wrap gap-2 mb-1">
                        <h4 className="text-sm font-medium">
                          {alert.title}
                        </h4>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        {alert.actionRequired && (
                          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">
                            ACTION REQUIRED
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-300">
                        {alert.message}
                      </p>
                      <div className="flex justify-between mt-1">
                        <span className="text-xs text-gray-400">
                          {alert.source} • {formatTimestamp(alert.timestamp)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center ml-2">
                      {alert.details && (
                        <button
                          className="p-1 hover:bg-gray-800 rounded-full"
                          onClick={() => handleExpandClick(alert.id)}
                          aria-label={expanded === alert.id ? "Hide details" : "Show details"}
                          title={expanded === alert.id ? "Hide details" : "Show details"}
                        >
                          {expanded === alert.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      )}
                      {onAcknowledgeAlert && (
                        <button
                          className="p-1 hover:bg-gray-800 rounded-full text-green-500"
                          onClick={() => onAcknowledgeAlert(alert.id)}
                          aria-label="Acknowledge alert"
                          title="Acknowledge alert"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                      )}
                      {onDismissAlert && (
                        <button
                          className="p-1 hover:bg-gray-800 rounded-full text-red-500"
                          onClick={() => onDismissAlert(alert.id)}
                          aria-label="Dismiss alert"
                          title="Dismiss alert"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  {alert.details && expanded === alert.id && (
                    <div className="ml-10 mr-4 mb-3 p-3 bg-gray-800 rounded">
                      <p className="text-sm text-gray-300 font-medium mb-1">
                        Details:
                      </p>
                      <p className="text-sm text-gray-300 whitespace-pre-wrap">
                        {alert.details}
                      </p>
                    </div>
                  )}
                </div>
              </React.Fragment>
            ))}
          </div>

          {activeAlerts.length > maxDisplayed && (
            <div className="text-center mt-4">
              <button
                className="px-3 py-1 text-sm border border-gray-600 rounded hover:bg-gray-800"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Show Less' : `Show All (${activeAlerts.length})`}
              </button>
            </div>
          )}

          {activeAlerts.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-400">
                {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''} • 
                {criticalAlerts.length} critical • 
                {alerts.filter(a => a.acknowledged).length} acknowledged
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ActiveAlertsCard;