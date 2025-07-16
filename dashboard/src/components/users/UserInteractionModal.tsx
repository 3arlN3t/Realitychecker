import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  Divider,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  IconButton
} from '@mui/material';
import {
  Close as CloseIcon,
  AccessTime as TimeIcon,
  CalendarToday as CalendarIcon,
  Message as MessageIcon,
  Description as PdfIcon,
  CheckCircleOutline as LegitIcon,
  ErrorOutline as ScamIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Timeline as TimelineIcon,
  ShowChart as ChartIcon
} from '@mui/icons-material';
import { UserInteractionModalProps, UserInteraction } from './types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`user-tabpanel-${index}`}
      aria-labelledby={`user-tab-${index}`}
      {...other}
      style={{ maxHeight: '60vh', overflowY: 'auto' }}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const UserInteractionModal: React.FC<UserInteractionModalProps> = ({
  user,
  open,
  onClose
}) => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (!user) {
    return null;
  }

  // Format phone number for display
  const formatPhoneNumber = (phoneNumber: string) => {
    if (phoneNumber.length === 12 && phoneNumber.startsWith('+1')) {
      return `+1 (${phoneNumber.substring(2, 5)}) ${phoneNumber.substring(5, 8)}-${phoneNumber.substring(8)}`;
    }
    return phoneNumber;
  };

  // Get classification color
  const getClassificationColor = (classification?: string) => {
    if (!classification) return 'default';
    switch (classification) {
      case 'Legit': return 'success';
      case 'Suspicious': return 'warning';
      case 'Likely Scam': return 'error';
      default: return 'default';
    }
  };

  // Get classification icon
  const getClassificationIcon = (classification?: string) => {
    if (!classification) return null;
    switch (classification) {
      case 'Legit': return <LegitIcon fontSize="small" />;
      case 'Suspicious': return <WarningIcon fontSize="small" />;
      case 'Likely Scam': return <ScamIcon fontSize="small" />;
      default: return null;
    }
  };

  // Calculate statistics
  const calculateStats = () => {
    const interactions = user.interactionHistory;
    
    // Count by message type
    const textCount = interactions.filter(i => i.messageType === 'text').length;
    const pdfCount = interactions.filter(i => i.messageType === 'pdf').length;
    
    // Count by classification
    const legitCount = interactions.filter(i => i.analysisResult?.classification === 'Legit').length;
    const suspiciousCount = interactions.filter(i => i.analysisResult?.classification === 'Suspicious').length;
    const scamCount = interactions.filter(i => i.analysisResult?.classification === 'Likely Scam').length;
    const errorCount = interactions.filter(i => i.error).length;
    
    // Average response time
    const avgResponseTime = interactions.reduce((sum, i) => sum + i.responseTime, 0) / interactions.length;
    
    // Activity by hour of day
    const hourCounts = Array(24).fill(0);
    interactions.forEach(i => {
      const hour = new Date(i.timestamp).getHours();
      hourCounts[hour]++;
    });
    const peakHour = hourCounts.indexOf(Math.max(...hourCounts));
    
    return {
      textCount,
      pdfCount,
      legitCount,
      suspiciousCount,
      scamCount,
      errorCount,
      avgResponseTime,
      peakHour,
      hourCounts
    };
  };

  const stats = calculateStats();

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="user-interaction-dialog-title"
    >
      <DialogTitle id="user-interaction-dialog-title">
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            User Details: {formatPhoneNumber(user.phoneNumber)}
          </Typography>
          <IconButton aria-label="close" onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <Divider />
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="user tabs">
          <Tab label="Overview" id="user-tab-0" aria-controls="user-tabpanel-0" />
          <Tab label="Interaction History" id="user-tab-1" aria-controls="user-tabpanel-1" />
          <Tab label="Analytics" id="user-tab-2" aria-controls="user-tabpanel-2" />
        </Tabs>
      </Box>
      
      <DialogContent dividers sx={{ p: 0 }}>
        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>User Information</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">First Interaction:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {new Date(user.firstInteraction).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">Last Interaction:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {new Date(user.lastInteraction).toLocaleString()}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <MessageIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">Total Requests:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {user.totalRequests}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimeIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">Average Response Time:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {user.averageResponseTime.toFixed(2)}s
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimelineIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">Engagement Score:</Typography>
                    <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        {user.engagementScore}/100
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={user.engagementScore}
                        sx={{ width: 60, height: 8, borderRadius: 5 }}
                        color={
                          user.engagementScore >= 70 ? 'success' :
                          user.engagementScore >= 40 ? 'warning' : 'error'
                        }
                      />
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <ChartIcon sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">Most Active Hour:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {user.mostFrequentHour}:00 - {user.mostFrequentHour + 1}:00
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Status:</Typography>
                    <Box sx={{ ml: 'auto' }}>
                      <Chip
                        label={user.blocked ? 'Blocked' : 'Active'}
                        color={user.blocked ? 'error' : 'success'}
                        size="small"
                      />
                    </Box>
                  </Box>
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Interaction Summary</Typography>
                
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                        <Typography variant="body2" color="text.secondary">Text Messages</Typography>
                        <Typography variant="h6">{stats.textCount}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                        <Typography variant="body2" color="text.secondary">PDF Uploads</Typography>
                        <Typography variant="h6">{stats.pdfCount}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                
                <Typography variant="subtitle2" gutterBottom>Classification Breakdown</Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <LegitIcon color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2">Legitimate:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {stats.legitCount} ({Math.round(stats.legitCount / user.totalRequests * 100) || 0}%)
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <WarningIcon color="warning" sx={{ mr: 1 }} />
                    <Typography variant="body2">Suspicious:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {stats.suspiciousCount} ({Math.round(stats.suspiciousCount / user.totalRequests * 100) || 0}%)
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <ScamIcon color="error" sx={{ mr: 1 }} />
                    <Typography variant="body2">Likely Scam:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {stats.scamCount} ({Math.round(stats.scamCount / user.totalRequests * 100) || 0}%)
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <ErrorIcon color="error" sx={{ mr: 1 }} />
                    <Typography variant="body2">Errors:</Typography>
                    <Typography variant="body2" sx={{ ml: 'auto' }}>
                      {stats.errorCount} ({Math.round(stats.errorCount / user.totalRequests * 100) || 0}%)
                    </Typography>
                  </Box>
                </Box>
                
                <Typography variant="subtitle2" gutterBottom>Response Time</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TimeIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography variant="body2">Average:</Typography>
                  <Typography variant="body2" sx={{ ml: 'auto' }}>
                    {stats.avgResponseTime.toFixed(2)}s
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Interaction History Tab */}
        <TabPanel value={tabValue} index={1}>
          <TableContainer component={Paper}>
            <Table aria-label="interaction history table">
              <TableHead>
                <TableRow>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Classification</TableCell>
                  <TableCell>Trust Score</TableCell>
                  <TableCell>Response Time</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {user.interactionHistory
                  .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                  .map((interaction) => (
                    <TableRow
                      key={interaction.id}
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell component="th" scope="row">
                        {new Date(interaction.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {interaction.messageType === 'text' ? (
                            <MessageIcon fontSize="small" sx={{ mr: 0.5 }} />
                          ) : (
                            <PdfIcon fontSize="small" sx={{ mr: 0.5 }} />
                          )}
                          {interaction.messageType === 'text' ? 'Text' : 'PDF'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {interaction.analysisResult ? (
                          <Chip
                            icon={getClassificationIcon(interaction.analysisResult.classification)}
                            label={interaction.analysisResult.classification}
                            color={getClassificationColor(interaction.analysisResult.classification) as any}
                            size="small"
                          />
                        ) : (
                          <Chip label="N/A" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        {interaction.analysisResult ? (
                          `${interaction.analysisResult.trustScore}/100`
                        ) : (
                          'N/A'
                        )}
                      </TableCell>
                      <TableCell>{interaction.responseTime.toFixed(2)}s</TableCell>
                      <TableCell>
                        {interaction.error ? (
                          <Chip
                            icon={<ErrorIcon fontSize="small" />}
                            label="Error"
                            color="error"
                            size="small"
                          />
                        ) : (
                          <Chip label="Success" color="success" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
        
        {/* Analytics Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>User Behavior Insights</Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>Activity Pattern</Typography>
                        <Typography variant="body2" paragraph>
                          This user is most active during {user.mostFrequentHour}:00 - {user.mostFrequentHour + 1}:00 hours.
                          {user.engagementScore > 70 && ' They show a high level of engagement with the service.'}
                          {user.engagementScore > 40 && user.engagementScore <= 70 && ' They show a moderate level of engagement with the service.'}
                          {user.engagementScore <= 40 && ' They show a low level of engagement with the service.'}
                        </Typography>
                        
                        <Typography variant="body2" paragraph>
                          {user.totalRequests > 10 ? 'Regular user' : 'Occasional user'} with an average of {(user.totalRequests / (
                            (new Date(user.lastInteraction).getTime() - new Date(user.firstInteraction).getTime()) / (1000 * 60 * 60 * 24) + 1
                          )).toFixed(2)} requests per day since first interaction.
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>Content Analysis</Typography>
                        <Typography variant="body2" paragraph>
                          {stats.legitCount > stats.suspiciousCount + stats.scamCount ? 
                            'This user primarily submits legitimate job postings for verification.' :
                            stats.scamCount > stats.legitCount + stats.suspiciousCount ?
                            'This user frequently encounters suspicious or scam job postings.' :
                            'This user submits a mix of legitimate and suspicious job postings.'
                          }
                        </Typography>
                        
                        <Typography variant="body2">
                          {stats.pdfCount > stats.textCount ? 
                            'Prefers to upload PDF documents rather than text.' :
                            stats.textCount > stats.pdfCount ?
                            'Prefers to send text messages rather than PDFs.' :
                            'Uses both text and PDF uploads equally.'
                          }
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>Recommendations</Typography>
                        <Typography variant="body2" paragraph>
                          {user.engagementScore > 70 ? 
                            'High-value user who could be targeted for feedback on new features.' :
                            user.engagementScore > 40 ?
                            'Regular user who might benefit from tips on how to get the most out of the service.' :
                            'Occasional user who might need re-engagement messaging or tutorials.'
                          }
                        </Typography>
                        
                        {stats.errorCount > 0 && (
                          <Typography variant="body2" color="error">
                            User has experienced {stats.errorCount} errors. Consider reaching out to ensure they are not having technical difficulties.
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserInteractionModal;