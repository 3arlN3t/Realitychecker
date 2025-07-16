import React from 'react';
import { 
  TextField, 
  FormControl, 
  FormHelperText,
  InputAdornment
} from '@mui/material';
import { RateLimitInputProps } from './types';

const RateLimitInput: React.FC<RateLimitInputProps> = ({ value, onChange, error }) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(event.target.value, 10);
    if (!isNaN(newValue) && newValue >= 1) {
      onChange(newValue);
    }
  };

  return (
    <FormControl fullWidth error={!!error} sx={{ mb: 2 }}>
      <TextField
        id="rate-limit"
        label="Rate Limit"
        type="number"
        value={value}
        onChange={handleChange}
        InputProps={{
          endAdornment: <InputAdornment position="end">requests/minute</InputAdornment>,
        }}
        inputProps={{
          min: 1,
          step: 1
        }}
      />
      {error && <FormHelperText>{error}</FormHelperText>}
    </FormControl>
  );
};

export default RateLimitInput;