import React from 'react';
import { 
  TextField, 
  FormControl, 
  FormHelperText,
  InputAdornment
} from '@mui/material';
import { PDFSizeInputProps } from './types';

const PDFSizeInput: React.FC<PDFSizeInputProps> = ({ value, onChange, error }) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(event.target.value, 10);
    if (!isNaN(newValue) && newValue >= 1) {
      onChange(newValue);
    }
  };

  return (
    <FormControl fullWidth error={!!error} sx={{ mb: 2 }}>
      <TextField
        id="pdf-size-limit"
        label="PDF Size Limit"
        type="number"
        value={value}
        onChange={handleChange}
        InputProps={{
          endAdornment: <InputAdornment position="end">MB</InputAdornment>,
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

export default PDFSizeInput;