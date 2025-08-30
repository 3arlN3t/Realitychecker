import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  IconButton,
  Button,
  Collapse,
  Badge,
  Divider
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  NotificationsActive as NotificationsActiveIcon,
  NotificationsOff as NotificationsOffIcon,
} from '@mui/icons-material';
import { Alert } from '../../types/dashboard';

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
        return <ErrorIcon fontSize="small" color="error" />;
      case 'warning':
        return <WarningIcon fontSize="small" color="warning" />;
      case 'success':
        return <CheckCircleIcon fontSize="small" color="success" />;
      default:
        return <InfoIcon fontSize="small" color="info" />;
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'default' => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'default';
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
    <Box sx={{ height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box sx={{ position: 'relative' }}>
          <Badge badgeContent={activeAlerts.length} color="error">
            <NotificationsActiveIcon color="primary" />
          </Badge>
        </Box>
        <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
          Active Alerts
        </Typography>
        {criticalAlerts.length > 0 && (
          <Chip
            label={`${criticalAlerts.length} Critical`}
            color="error"
            size="small"
          />
        )}
      </Box>

      {activeAlerts.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <NotificationsOffIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
          <Typography variant="h6" color="success.main" sx={{ mb: 0.5 }}>
            All Clear!
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No active alerts at this time
          </Typography>
        </Box>
      ) : (
        <>
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            {displayedAlerts.map((alert) => (
              <Paper
                key={alert.id}
                elevation={0}
                sx={{
                  mb: 1,
                  border: 1,
                  borderColor: alert.severity === 'critical' ? 'error.main' : 'divider',
                  bgcolor: alert.severity === 'critical' ? 'error.main' : 'background.paper',
                  opacity: alert.severity === 'critical' ? 0.1 : 0.05,
                  borderRadius: 1,
                  overflow: 'hidden'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', p: 1.5 }}>
                  <Box sx={{ mr: 1.5, mt: 0.5 }}>
                    {getAlertIcon(alert.type)}
                  </Box>
                  <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 0.5, alignItems: 'center' }}>
                      <Typography variant="subtitle2">
                        {alert.title}
                      </Typography>
                      <Chip
                        label={alert.severity.toUpperCase()}
                        color={getSeverityColor(alert.severity)}
                        size="small"
                      />
                      {alert.actionRequired && (
                        <Chip
                          label="ACTION REQUIRED"
                          color="warning"
                          size="small"
                        />
                      )}
                    </Box>
                    <Typography variant="body2">
                      {alert.message}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {alert.source} • {formatTimestamp(alert.timestamp)}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                    {alert.details && (
                      <IconButton
                        size="small"
                        onClick={() => handleExpandClick(alert.id)}
                        aria-label={expanded === alert.id ? "Hide details" : "Show details"}
                        title={expanded === alert.id ? "Hide details" : "Show details"}
                      >
                        {expanded === alert.id ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                      </IconButton>
                    )}
                    {onAcknowledgeAlert && (
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => onAcknowledgeAlert(alert.id)}
                        aria-label="Acknowledge alert"
                        title="Acknowledge alert"
                      >
                        <CheckCircleIcon fontSize="small" />
                      </IconButton>
                    )}
                    {onDismissAlert && (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => onDismissAlert(alert.id)}
                        aria-label="Dismiss alert"
                        title="Dismiss alert"
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                </Box>
                {alert.details && expanded === alert.id && (
                  <Collapse in={expanded === alert.id}>
                    <Box sx={{ ml: 5, mr: 2, mb: 1.5, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                        Details:
                      </Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {alert.details}
                      </Typography>
                    </Box>
                  </Collapse>
                )}
              </Paper>
            ))}
          </Box>

          {activeAlerts.length > maxDisplayed && (
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? 'Show Less' : `Show All (${activeAlerts.length})`}
              </Button>
            </Box>
          )}

          {activeAlerts.length > 0 && (
            <Box sx={{ mt: 2, pt: 1.5, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''} • 
                {criticalAlerts.length} critical • 
                {alerts.filter(a => a.acknowledged).length} acknowledged
              </Typography>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default ActiveAlertsCard;