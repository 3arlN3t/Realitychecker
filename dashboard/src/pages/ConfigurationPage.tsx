import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Alert,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Shield as ShieldIcon,
  Warning as AlertTriangleIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import ConfigurationForm from '../components/configuration/ConfigurationForm';
import { SystemConfiguration } from '../components/configuration/types';
import { useAuth } from '../contexts/AuthContext';

// Mock API function to get configuration
const fetchConfiguration = async (): Promise<SystemConfiguration> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Return mock data
  return {
    openaiModel: 'gpt-4',
    maxPdfSizeMb: 10,
    rateLimitPerMinute: 60,
    webhookValidation: true,
    logLevel: 'INFO',
    alertThresholds: {
      errorRate: 5,
      responseTime: 3,
      cpuUsage: 80,
      memoryUsage: 85
    }
  };
};

// Mock API function to update configuration
const updateConfiguration = async (config: SystemConfiguration): Promise<boolean> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Simulate success (in a real app, this would send the data to the backend)
  console.log('Configuration updated:', config);
  return true;
};

const ConfigurationPage: React.FC = () => {
  const { user } = useAuth();
  const [config, setConfig] = useState<SystemConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const loadConfiguration = async () => {
      try {
        setLoading(true);
        const data = await fetchConfiguration();
        setConfig(data);
        setError(null);
      } catch (err) {
        setError('Failed to load configuration. Please try again.');
        console.error('Error loading configuration:', err);
      } finally {
        setLoading(false);
      }
    };

    loadConfiguration();
  }, []);

  const handleSaveConfiguration = async (updatedConfig: SystemConfiguration) => {
    try {
      setSaving(true);
      setError(null);
      
      const success = await updateConfiguration(updatedConfig);
      
      if (success) {
        setConfig(updatedConfig);
        setSuccessMessage('Configuration saved successfully!');
      } else {
        setError('Failed to save configuration. Please try again.');
      }
    } catch (err) {
      setError('An error occurred while saving. Please try again.');
      console.error('Error saving configuration:', err);
    } finally {
      setSaving(false);
    }
  };

  if (!user || user.role !== 'admin') {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" icon={<ShieldIcon />}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>Access Denied</Typography>
          You don't have permission to access this page. Admin role required.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            System Configuration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage system settings, API configurations, and alert thresholds. Changes will take effect immediately.
          </Typography>
        </Box>
        <Chip
          icon={<SettingsIcon />}
          label="Admin Only"
          variant="outlined"
          color="primary"
        />
      </Box>
      
      {error && (
        <Alert severity="error" icon={<AlertTriangleIcon />} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}
      
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SettingsIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Configuration Settings</Typography>
            </Box>
          }
          subheader="Configure system parameters and operational settings"
        />
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
              <CircularProgress size={32} sx={{ mr: 2 }} />
              <Typography>Loading configuration...</Typography>
            </Box>
          ) : config ? (
            <ConfigurationForm 
              config={config} 
              onSave={handleSaveConfiguration}
              isLoading={saving}
            />
          ) : (
            <Alert severity="error" icon={<AlertTriangleIcon />}>
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>Configuration Error</Typography>
              Failed to load configuration data. Please refresh the page.
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ConfigurationPage;