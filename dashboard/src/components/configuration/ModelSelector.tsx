import React from 'react';
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  FormHelperText,
  SelectChangeEvent
} from '@mui/material';
import { ModelSelectorProps } from './types';

const ModelSelector: React.FC<ModelSelectorProps> = ({ value, onChange, error }) => {
  const handleChange = (event: SelectChangeEvent) => {
    onChange(event.target.value);
  };

  return (
    <FormControl fullWidth error={!!error} sx={{ mb: 2 }}>
      <InputLabel id="openai-model-label">OpenAI Model</InputLabel>
      <Select
        labelId="openai-model-label"
        id="openai-model"
        value={value}
        label="OpenAI Model"
        onChange={handleChange}
      >
        <MenuItem value="gpt-4">GPT-4</MenuItem>
        <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
        <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
      </Select>
      {error && <FormHelperText>{error}</FormHelperText>}
    </FormControl>
  );
};

export default ModelSelector;