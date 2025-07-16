import React from 'react';
import { ToggleButtonGroup, ToggleButton, Box, Typography } from '@mui/material';
import { PeriodType } from './types';

interface PeriodSelectorProps {
  period: PeriodType;
  onChange: (period: PeriodType) => void;
}

const PeriodSelector: React.FC<PeriodSelectorProps> = ({ period, onChange }) => {
  const handleChange = (
    _event: React.MouseEvent<HTMLElement>,
    newPeriod: PeriodType | null
  ) => {
    if (newPeriod !== null) {
      onChange(newPeriod);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
      <Typography variant="body1" sx={{ mr: 2 }}>
        Time Period:
      </Typography>
      <ToggleButtonGroup
        value={period}
        exclusive
        onChange={handleChange}
        aria-label="time period"
        size="small"
      >
        <ToggleButton value="day" aria-label="day">
          Day
        </ToggleButton>
        <ToggleButton value="week" aria-label="week">
          Week
        </ToggleButton>
        <ToggleButton value="month" aria-label="month">
          Month
        </ToggleButton>
        <ToggleButton value="year" aria-label="year">
          Year
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

export default PeriodSelector;