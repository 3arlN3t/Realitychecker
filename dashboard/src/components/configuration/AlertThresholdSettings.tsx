import React from 'react';
import { 
  Grid, 
  TextField, 
  Typography, 
  InputAdornment,
  FormHelperText
} from '@mui/material';
import { AlertThresholdSettingsProps } from './types';

const AlertThresholdSettings: React.FC<AlertThresholdSettingsProps> = ({ 
  thresholds, 
  onChange,
  errors = {}
}) => {
  const handleChange = (field: keyof typeof thresholds) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(event.target.value);
    if (!isNaN(newValue) && newValue >= 0) {
      onChange({
        ...thresholds,
        [field]: newValue
      });
    }
  };

  return (
    <div>
      <Typography variant="subtitle1" gutterBottom>
        Alert Thresholds
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="error-rate-threshold"
            label="Error Rate Threshold"
            type="number"
            value={thresholds.errorRate}
            onChange={handleChange('errorRate')}
            error={!!errors.errorRate}
            helperText={errors.errorRate}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{
              min: 0,
              step: 0.1
            }}
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="response-time-threshold"
            label="Response Time Threshold"
            type="number"
            value={thresholds.responseTime}
            onChange={handleChange('responseTime')}
            error={!!errors.responseTime}
            helperText={errors.responseTime}
            InputProps={{
              endAdornment: <InputAdornment position="end">sec</InputAdornment>,
            }}
            inputProps={{
              min: 0,
              step: 0.1
            }}
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="cpu-usage-threshold"
            label="CPU Usage Threshold"
            type="number"
            value={thresholds.cpuUsage}
            onChange={handleChange('cpuUsage')}
            error={!!errors.cpuUsage}
            helperText={errors.cpuUsage}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{
              min: 0,
              max: 100,
              step: 1
            }}
            sx={{ mb: 2 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="memory-usage-threshold"
            label="Memory Usage Threshold"
            type="number"
            value={thresholds.memoryUsage}
            onChange={handleChange('memoryUsage')}
            error={!!errors.memoryUsage}
            helperText={errors.memoryUsage}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{
              min: 0,
              max: 100,
              step: 1
            }}
            sx={{ mb: 2 }}
          />
        </Grid>
      </Grid>
    </div>
  );
};

export default AlertThresholdSettings;