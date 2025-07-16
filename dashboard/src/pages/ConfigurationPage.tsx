import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Alert, 
  Snackbar 
} from '@mui/material';
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

  const handleCloseSnackbar = () => {
    setSuccessMessage(null);
  };

  if (!user || user.role !== 'admin') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          You don't have permission to access this page. Admin role required.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          System Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage system settings, API configurations, and alert thresholds. Changes will take effect immediately.
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <Typography>Loading configuration...</Typography>
          </Box>
        ) : config ? (
          <ConfigurationForm 
            config={config} 
            onSave={handleSaveConfiguration}
            isLoading={saving}
          />
        ) : (
          <Alert severity="error">
            Failed to load configuration data. Please refresh the page.
          </Alert>
        )}
      </Paper>
      
      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message={successMessage}
      />
    </Container>
  );
};

export default ConfigurationPage;