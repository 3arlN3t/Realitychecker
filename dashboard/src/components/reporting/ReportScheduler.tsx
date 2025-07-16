import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Table,
  TableBody,
  Tooltip,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Alert
} from '@mui/material';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { format, parseISO } from 'date-fns';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import ScheduleIcon from '@mui/icons-material/Schedule';
import EmailIcon from '@mui/icons-material/Email';
import CloseIcon from '@mui/icons-material/Close';
import { ReportParameters, ScheduledReport } from './types';

interface ReportSchedulerProps {
  scheduledReports: ScheduledReport[];
  onScheduleReport: (report: Omit<ScheduledReport, 'id'>) => Promise<void>;
  onDeleteScheduledReport: (id: string) => Promise<void>;
  onEditScheduledReport: (report: ScheduledReport) => Promise<void>;
  reportParameters: ReportParameters;
}

const ReportScheduler: React.FC<ReportSchedulerProps> = ({
  scheduledReports,
  onScheduleReport,
  onDeleteScheduledReport,
  onEditScheduledReport,
  reportParameters
}) => {
  const [open, setOpen] = useState(false);
  const [editingReport, setEditingReport] = useState<ScheduledReport | null>(null);
  const [reportName, setReportName] = useState('');
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [day, setDay] = useState<number>(1);
  const [time, setTime] = useState<Date>(new Date());
  const [recipients, setRecipients] = useState<string[]>([]);
  const [newRecipient, setNewRecipient] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleOpen = () => {
    setOpen(true);
    setReportName('');
    setFrequency('weekly');
    setDay(1);
    setTime(new Date());
    setRecipients([]);
    setNewRecipient('');
    setError(null);
    setEditingReport(null);
  };

  const handleEdit = (report: ScheduledReport) => {
    setEditingReport(report);
    setReportName(report.name);
    setFrequency(report.schedule.frequency);
    setDay(report.schedule.day || 1);
    setTime(parseISO(`2023-01-01T${report.schedule.time}:00`));
    setRecipients(report.schedule.recipients);
    setNewRecipient('');
    setError(null);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleAddRecipient = () => {
    if (!newRecipient) return;
    
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newRecipient)) {
      setError('Please enter a valid email address');
      return;
    }
    
    if (recipients.includes(newRecipient)) {
      setError('This email is already added');
      return;
    }
    
    setRecipients([...recipients, newRecipient]);
    setNewRecipient('');
    setError(null);
  };

  const handleRemoveRecipient = (email: string) => {
    setRecipients(recipients.filter(r => r !== email));
  };

  const handleSave = async () => {
    if (!reportName) {
      setError('Report name is required');
      return;
    }
    
    if (recipients.length === 0) {
      setError('At least one recipient is required');
      return;
    }
    
    try {
      const formattedTime = format(time, 'HH:mm');
      
      if (editingReport) {
        await onEditScheduledReport({
          ...editingReport,
          name: reportName,
          schedule: {
            frequency,
            day: frequency !== 'daily' ? day : undefined,
            time: formattedTime,
            recipients
          }
        });
      } else {
        await onScheduleReport({
          name: reportName,
          parameters: reportParameters,
          schedule: {
            frequency,
            day: frequency !== 'daily' ? day : undefined,
            time: formattedTime,
            recipients
          }
        });
      }
      
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to schedule report');
    }
  };

  const getDayOptions = () => {
    if (frequency === 'weekly') {
      return [
        { value: 0, label: 'Sunday' },
        { value: 1, label: 'Monday' },
        { value: 2, label: 'Tuesday' },
        { value: 3, label: 'Wednesday' },
        { value: 4, label: 'Thursday' },
        { value: 5, label: 'Friday' },
        { value: 6, label: 'Saturday' }
      ];
    } else if (frequency === 'monthly') {
      return Array.from({ length: 31 }, (_, i) => ({
        value: i + 1,
        label: `${i + 1}${getDaySuffix(i + 1)}`
      }));
    }
    return [];
  };

  const getDaySuffix = (day: number): string => {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
      case 1: return 'st';
      case 2: return 'nd';
      case 3: return 'rd';
      default: return 'th';
    }
  };

  const getFrequencyText = (report: ScheduledReport): string => {
    const { frequency, day, time } = report.schedule;
    
    if (frequency === 'daily') {
      return `Daily at ${time}`;
    } else if (frequency === 'weekly') {
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      return `Weekly on ${dayNames[day || 0]} at ${time}`;
    } else {
      return `Monthly on the ${day}${getDaySuffix(day || 1)} at ${time}`;
    }
  };

  return (
    <>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Scheduled Reports
          </Typography>
          <Button 
            variant="outlined" 
            startIcon={<AddIcon />}
            onClick={handleOpen}
          >
            Schedule Report
          </Button>
        </Box>
        
        <Typography variant="body2" color="textSecondary" paragraph>
          Schedule reports to be automatically generated and emailed on a recurring basis
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        {scheduledReports.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Report Name</TableCell>
                  <TableCell>Schedule</TableCell>
                  <TableCell>Recipients</TableCell>
                  <TableCell>Next Run</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {scheduledReports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>{report.name}</TableCell>
                    <TableCell>{getFrequencyText(report)}</TableCell>
                    <TableCell>
                      {report.schedule.recipients.length > 1 ? (
                        <Tooltip title={report.schedule.recipients.join(', ')}>
                          <Typography variant="body2">
                            {report.schedule.recipients[0]} +{report.schedule.recipients.length - 1} more
                          </Typography>
                        </Tooltip>
                      ) : (
                        report.schedule.recipients[0]
                      )}
                    </TableCell>
                    <TableCell>
                      {report.next_run ? format(parseISO(report.next_run), 'MMM d, yyyy HH:mm') : 'Not scheduled'}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleEdit(report)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="error" 
                        onClick={() => onDeleteScheduledReport(report.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="textSecondary">
              No scheduled reports
            </Typography>
            <Button 
              variant="outlined" 
              startIcon={<AddIcon />}
              onClick={handleOpen}
              sx={{ mt: 2 }}
            >
              Schedule Your First Report
            </Button>
          </Box>
        )}
      </Paper>
      
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingReport ? 'Edit Scheduled Report' : 'Schedule New Report'}
          <IconButton
            aria-label="close"
            onClick={handleClose}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Report Name"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Frequency</InputLabel>
                <Select
                  value={frequency}
                  label="Frequency"
                  onChange={(e) => setFrequency(e.target.value as 'daily' | 'weekly' | 'monthly')}
                >
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {frequency !== 'daily' && (
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Day</InputLabel>
                  <Select
                    value={day}
                    label="Day"
                    onChange={(e) => setDay(Number(e.target.value))}
                  >
                    {getDayOptions().map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12} sm={frequency === 'daily' ? 12 : 6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <TimePicker
                  label="Time"
                  value={time}
                  onChange={(newTime) => newTime && setTime(newTime)}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </LocalizationProvider>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                <EmailIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: '1rem' }} />
                Recipients
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                <TextField
                  fullWidth
                  label="Email Address"
                  value={newRecipient}
                  onChange={(e) => setNewRecipient(e.target.value)}
                  placeholder="Enter email address"
                  sx={{ mr: 1 }}
                />
                <Button
                  variant="contained"
                  onClick={handleAddRecipient}
                  sx={{ height: '56px' }}
                >
                  Add
                </Button>
              </Box>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {recipients.map((email) => (
                  <Chip
                    key={email}
                    label={email}
                    onDelete={() => handleRemoveRecipient(email)}
                  />
                ))}
              </Box>
            </Grid>
            
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            {editingReport ? 'Update Schedule' : 'Schedule Report'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ReportScheduler;