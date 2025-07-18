import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Settings, Shield, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
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

  // Removed handleCloseSnackbar as we're using shadcn/ui Alert instead of Snackbar

  if (!user || user.role !== 'admin') {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <Shield className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to access this page. Admin role required.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
          <p className="text-muted-foreground">
            Manage system settings, API configurations, and alert thresholds. Changes will take effect immediately.
          </p>
        </div>
        <Badge variant="outline">
          <Settings className="w-4 h-4 mr-1" />
          Admin Only
        </Badge>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {successMessage && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      )}
      
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Configuration Settings
          </CardTitle>
          <CardDescription>
            Configure system parameters and operational settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin mr-2" />
              <span>Loading configuration...</span>
            </div>
          ) : config ? (
            <ConfigurationForm 
              config={config} 
              onSave={handleSaveConfiguration}
              isLoading={saving}
            />
          ) : (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Failed to load configuration data. Please refresh the page.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ConfigurationPage;