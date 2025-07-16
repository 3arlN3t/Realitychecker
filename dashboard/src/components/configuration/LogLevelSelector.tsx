import React from 'react';
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  FormHelperText,
  SelectChangeEvent
} from '@mui/material';
import { LogLevelSelectorProps } from './types';

const LogLevelSelector: React.FC<LogLevelSelectorProps> = ({ value, onChange, error }) => {
  const handleChange = (event: SelectChangeEvent) => {
    onChange(event.target.value);
  };

  return (
    <FormControl fullWidth error={!!error} sx={{ mb: 2 }}>
      <InputLabel id="log-level-label">Log Level</InputLabel>
      <Select
        labelId="log-level-label"
        id="log-level"
        value={value}
        label="Log Level"
        onChange={handleChange}
      >
        <MenuItem value="DEBUG">DEBUG</MenuItem>
        <MenuItem value="INFO">INFO</MenuItem>
        <MenuItem value="WARNING">WARNING</MenuItem>
        <MenuItem value="ERROR">ERROR</MenuItem>
        <MenuItem value="CRITICAL">CRITICAL</MenuItem>
      </Select>
      {error && <FormHelperText>{error}</FormHelperText>}
    </FormControl>
  );
};

export default LogLevelSelector;