import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  FormControlLabel, 
  Switch, 
  CircularProgress 
} from '@mui/material';
import { ConfigurationFormProps, SystemConfiguration } from './types';
import ConfigSection from './ConfigSection';
import ModelSelector from './ModelSelector';
import RateLimitInput from './RateLimitInput';
import PDFSizeInput from './PDFSizeInput';
import LogLevelSelector from './LogLevelSelector';
import AlertThresholdSettings from './AlertThresholdSettings';

const ConfigurationForm: React.FC<ConfigurationFormProps> = ({ 
  config, 
  onSave,
  isLoading = false
}) => {
  const [formData, setFormData] = useState<SystemConfiguration>(config);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleModelChange = (value: string) => {
    setFormData(prev => ({ ...prev, openaiModel: value }));
    if (errors.openaiModel) {
      setErrors(prev => ({ ...prev, openaiModel: '' }));
    }
  };

  const handleRateLimitChange = (value: number) => {
    setFormData(prev => ({ ...prev, rateLimitPerMinute: value }));
    if (errors.rateLimitPerMinute) {
      setErrors(prev => ({ ...prev, rateLimitPerMinute: '' }));
    }
  };

  const handlePdfSizeChange = (value: number) => {
    setFormData(prev => ({ ...prev, maxPdfSizeMb: value }));
    if (errors.maxPdfSizeMb) {
      setErrors(prev => ({ ...prev, maxPdfSizeMb: '' }));
    }
  };

  const handleLogLevelChange = (value: string) => {
    setFormData(prev => ({ ...prev, logLevel: value }));
    if (errors.logLevel) {
      setErrors(prev => ({ ...prev, logLevel: '' }));
    }
  };

  const handleWebhookValidationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, webhookValidation: event.target.checked }));
  };

  const handleAlertThresholdsChange = (thresholds: SystemConfiguration['alertThresholds']) => {
    setFormData(prev => ({ ...prev, alertThresholds: thresholds }));
    
    // Clear any threshold errors
    const newErrors = { ...errors };
    delete newErrors.errorRate;
    delete newErrors.responseTime;
    delete newErrors.cpuUsage;
    delete newErrors.memoryUsage;
    setErrors(newErrors);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.openaiModel) {
      newErrors.openaiModel = 'OpenAI model is required';
    }
    
    if (formData.rateLimitPerMinute <= 0) {
      newErrors.rateLimitPerMinute = 'Rate limit must be greater than 0';
    }
    
    if (formData.maxPdfSizeMb <= 0) {
      newErrors.maxPdfSizeMb = 'PDF size limit must be greater than 0';
    }
    
    if (!formData.logLevel) {
      newErrors.logLevel = 'Log level is required';
    }
    
    if (formData.alertThresholds.errorRate < 0 || formData.alertThresholds.errorRate > 100) {
      newErrors.errorRate = 'Error rate must be between 0 and 100';
    }
    
    if (formData.alertThresholds.responseTime < 0) {
      newErrors.responseTime = 'Response time must be greater than or equal to 0';
    }
    
    if (formData.alertThresholds.cpuUsage < 0 || formData.alertThresholds.cpuUsage > 100) {
      newErrors.cpuUsage = 'CPU usage must be between 0 and 100';
    }
    
    if (formData.alertThresholds.memoryUsage < 0 || formData.alertThresholds.memoryUsage > 100) {
      newErrors.memoryUsage = 'Memory usage must be between 0 and 100';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    
    if (validateForm()) {
      onSave(formData);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      <ConfigSection title="OpenAI Settings">
        <ModelSelector 
          value={formData.openaiModel} 
          onChange={handleModelChange}
          error={errors.openaiModel}
        />
      </ConfigSection>
      
      <ConfigSection title="API Settings">
        <RateLimitInput 
          value={formData.rateLimitPerMinute} 
          onChange={handleRateLimitChange}
          error={errors.rateLimitPerMinute}
        />
        <FormControlLabel
          control={
            <Switch 
              checked={formData.webhookValidation} 
              onChange={handleWebhookValidationChange}
              name="webhookValidation"
            />
          }
          label="Enable Webhook Signature Validation"
        />
      </ConfigSection>
      
      <ConfigSection title="System Settings">
        <PDFSizeInput 
          value={formData.maxPdfSizeMb} 
          onChange={handlePdfSizeChange}
          error={errors.maxPdfSizeMb}
        />
        <LogLevelSelector 
          value={formData.logLevel} 
          onChange={handleLogLevelChange}
          error={errors.logLevel}
        />
      </ConfigSection>
      
      <ConfigSection title="Monitoring Settings">
        <AlertThresholdSettings 
          thresholds={formData.alertThresholds}
          onChange={handleAlertThresholdsChange}
          errors={{
            errorRate: errors.errorRate,
            responseTime: errors.responseTime,
            cpuUsage: errors.cpuUsage,
            memoryUsage: errors.memoryUsage
          }}
        />
      </ConfigSection>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button 
          type="submit" 
          variant="contained" 
          color="primary" 
          disabled={isLoading}
          sx={{ minWidth: 120 }}
        >
          {isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
        </Button>
      </Box>
    </Box>
  );
};

export default ConfigurationForm;