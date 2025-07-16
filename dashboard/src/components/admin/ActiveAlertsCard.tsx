import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Badge,
  Collapse,
  Button,
  Tooltip,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon,
} from '@mui/icons-material';

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
  // Remove unused variables to fix ESLint warnings
  // const theme = useTheme();
  // const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'success':
        return <SuccessIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: string) => {
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
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Badge badgeContent={activeAlerts.length} color="error">
            <NotificationsIcon color="primary" />
          </Badge>
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            Active Alerts
          </Typography>
          {criticalAlerts.length > 0 && (
            <Chip
              label={`${criticalAlerts.length} Critical`}
              color="error"
              size="small"
              variant="filled"
            />
          )}
        </Box>

        {activeAlerts.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <NotificationsOffIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
            <Typography variant="h6" color="success.main" gutterBottom>
              All Clear!
            </Typography>
            <Typography variant="body2" color="textSecondary">
              No active alerts at this time
            </Typography>
          </Box>
        ) : (
          <>
            <List dense sx={{ maxHeight: 400, overflow: 'auto' }}>
              {displayedAlerts.map((alert) => (
                <React.Fragment key={alert.id}>
                  <ListItem
                    sx={{
                      border: 1,
                      borderColor: alert.severity === 'critical' ? 'error.main' : 'divider',
                      borderRadius: 1,
                      mb: 1,
                      bgcolor: alert.severity === 'critical' ? 'error.light' : 'background.paper',
                      opacity: alert.severity === 'critical' ? 0.1 : 1,
                    }}
                  >
                    <ListItemIcon>
                      {getAlertIcon(alert.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="subtitle2" component="span">
                            {alert.title}
                          </Typography>
                          <Chip
                            label={alert.severity.toUpperCase()}
                            color={getSeverityColor(alert.severity) as any}
                            size="small"
                            variant="outlined"
                          />
                          {alert.actionRequired && (
                            <Chip
                              label="ACTION REQUIRED"
                              color="warning"
                              size="small"
                              variant="filled"
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {alert.message}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                            <Typography variant="caption" color="textSecondary">
                              {alert.source} • {formatTimestamp(alert.timestamp)}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {alert.details && (
                          <Tooltip title="View details">
                            <IconButton
                              size="small"
                              onClick={() => handleExpandClick(alert.id)}
                            >
                              {expanded === alert.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          </Tooltip>
                        )}
                        {onAcknowledgeAlert && (
                          <Tooltip title="Acknowledge">
                            <IconButton
                              size="small"
                              onClick={() => onAcknowledgeAlert(alert.id)}
                              color="success"
                            >
                              <SuccessIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {onDismissAlert && (
                          <Tooltip title="Dismiss">
                            <IconButton
                              size="small"
                              onClick={() => onDismissAlert(alert.id)}
                              color="error"
                            >
                              <CloseIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {alert.details && (
                    <Collapse in={expanded === alert.id} timeout="auto" unmountOnExit>
                      <Box sx={{ ml: 4, mr: 2, mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="body2" color="textSecondary">
                          <strong>Details:</strong>
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                          {alert.details}
                        </Typography>
                      </Box>
                    </Collapse>
                  )}
                </React.Fragment>
              ))}
            </List>

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
              <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="caption" color="textSecondary">
                  {activeAlerts.length} active alert{activeAlerts.length !== 1 ? 's' : ''} • 
                  {criticalAlerts.length} critical • 
                  {alerts.filter(a => a.acknowledged).length} acknowledged
                </Typography>
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ActiveAlertsCard;