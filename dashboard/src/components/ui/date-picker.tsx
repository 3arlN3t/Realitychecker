import React from 'react';
import { Input } from './input';
import { Label } from './label';
import { CalendarIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface DatePickerProps {
  id: string;
  label: string;
  value: Date;
  onChange: (date: Date) => void;
  min?: Date;
  max?: Date;
  className?: string;
}

export function DatePicker({
  id,
  label,
  value,
  onChange,
  min,
  max,
  className,
}: DatePickerProps) {
  // Format date as YYYY-MM-DD for the input
  const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Format date for display
  const formatDateForDisplay = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value);
    if (!isNaN(newDate.getTime())) {
      onChange(newDate);
    }
  };

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          type="date"
          id={id}
          value={formatDateForInput(value)}
          onChange={handleChange}
          min={min ? formatDateForInput(min) : undefined}
          max={max ? formatDateForInput(max) : undefined}
          className="pr-10"
        />
        <CalendarIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
      </div>
      <p className="text-xs text-muted-foreground">
        {formatDateForDisplay(value)}
      </p>
    </div>
  );
}