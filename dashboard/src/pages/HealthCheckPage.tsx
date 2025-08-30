import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Button,
  Alert,
  Chip,
  Divider,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  HealthAndSafety as HealthIcon,
  Refresh as RefreshIcon,
  Api as ApiIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { HealthCheckAPI } from '../lib/api';

interface HealthEndpoint {
  name: string;
  path: string;
  description: string;
  method: 'GET' | 'POST';
}

const healthEndpoints: HealthEndpoint[] = [
  {
    name: 'Basic Health Check',
    path: '/api/health',
    description: 'Simple health status endpoint',
    method: 'GET'
  },
  {
    name: 'Detailed Health Check',
    path: '/api/health/detailed',
    description: 'Comprehensive system health with service status',
    method: 'GET'
  },
  {
    name: 'Service Status',
    path: '/api/health/services',
    description: 'Individual service health status',
    method: 'GET'
  },
  {
    name: 'Database Health',
    path: '/api/health/database',
    description: 'Database connectivity and performance',
    method: 'GET'
  },
  {
    name: 'External APIs Health',
    path: '/api/health/external',
    description: 'OpenAI, Twilio, and other external service status',
    method: 'GET'
  }
];

const HealthCheckPage: React.FC = () => {
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [testingAll, setTestingAll] = useState(false);

  const testEndpoint = async (endpoint: HealthEndpoint) => {
    const key = endpoint.path;
    setLoading(prev => ({ ...prev, [key]: true }));
    
    try {
      let result: any;
      switch (endpoint.path) {
        case '/api/health':
          result = await HealthCheckAPI.getBasicHealth();
          break;
        case '/api/health/detailed':
          result = await HealthCheckAPI.getDetailedHealth();
          break;
        case '/api/health/services':
          result = await HealthCheckAPI.getServicesHealth();
          break;
        case '/api/health/database':
          result = await HealthCheckAPI.getDatabaseHealth();
          break;
        case '/api/health/external':
          result = await HealthCheckAPI.getExternalHealth();
          break;
        default:
          throw new Error('Unknown endpoint');
      }
      
      setTestResults(prev => ({
        ...prev,
        [key]: { success: true, data: result, timestamp: new Date() }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [key]: { 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date()
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const testAllEndpoints = async () => {
    try {
      setTestingAll(true);
      setGlobalError(null);
      // Test endpoints in parallel for better performance
      const promises = healthEndpoints.map(endpoint => testEndpoint(endpoint));
      await Promise.allSettled(promises);
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : 'Failed to test endpoints');
    } finally {
      setTestingAll(false);
    }
  };

  const getStatusIcon = (result: any) => {
    if (!result) return <ApiIcon color="action" />;
    if (result.success) return <CheckCircleIcon color="success" />;
    return <ErrorIcon color="error" />;
  };

  const getStatusColor = (result: any): 'success' | 'error' | 'default' => {
    if (!result) return 'default';
    return result.success ? 'success' : 'error';
  };

  const formatJson = (data: any) => {
    return JSON.stringify(data, null, 2);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <HealthIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Health Check Endpoints
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={testingAll ? <CircularProgress size={16} /> : <RefreshIcon />}
          onClick={testAllEndpoints}
          disabled={testingAll || Object.values(loading).some(Boolean)}
        >
          {testingAll ? 'Testing...' : 'Test All Endpoints'}
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Use these endpoints to monitor system health and diagnose issues. 
          Click "Test" to make a live API call and see the response.
        </Typography>
      </Alert>

      {globalError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Global Error: {globalError}
          </Typography>
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {healthEndpoints.map((endpoint) => {
          const result = testResults[endpoint.path];
          const isLoading = loading[endpoint.path];
          
          return (
            <Box key={endpoint.path}>
              <Card>
                <CardHeader
                  avatar={getStatusIcon(result)}
                  title={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6">{endpoint.name}</Typography>
                      <Chip 
                        label={endpoint.method} 
                        size="small" 
                        color="primary" 
                        variant="outlined" 
                      />
                      <Chip
                        label={result ? (result.success ? 'SUCCESS' : 'ERROR') : 'UNTESTED'}
                        size="small"
                        color={getStatusColor(result)}
                      />
                    </Box>
                  }
                  subheader={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {endpoint.description}
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.875rem', mt: 0.5 }}>
                        {endpoint.method} {endpoint.path}
                      </Typography>
                    </Box>
                  }
                  action={
                    <Tooltip title="Test this endpoint">
                      <IconButton
                        onClick={() => testEndpoint(endpoint)}
                        disabled={isLoading}
                        color="primary"
                      >
                        {isLoading ? <CircularProgress size={20} /> : <RefreshIcon />}
                      </IconButton>
                    </Tooltip>
                  }
                />
                
                {result && (
                  <CardContent>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                        <TimelineIcon sx={{ mr: 1, fontSize: 16 }} />
                        Response Details
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Tested at: {result.timestamp.toLocaleString()}
                      </Typography>
                    </Box>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    {result.success ? (
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                          <CodeIcon sx={{ mr: 1, fontSize: 16 }} />
                          Response Data
                        </Typography>
                        <Paper 
                          sx={{ 
                            p: 2, 
                            bgcolor: 'grey.50', 
                            border: '1px solid', 
                            borderColor: 'grey.200',
                            maxHeight: 400,
                            overflow: 'auto'
                          }}
                        >
                          <pre style={{ 
                            margin: 0, 
                            fontSize: '0.75rem', 
                            fontFamily: 'monospace',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}>
                            {formatJson(result.data)}
                          </pre>
                        </Paper>
                      </Box>
                    ) : (
                      <Box>
                        <Alert severity="error">
                          <Typography variant="subtitle2">Error Details</Typography>
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            {result.error}
                          </Typography>
                        </Alert>
                      </Box>
                    )}
                  </CardContent>
                )}
              </Card>
            </Box>
          );
        })}
      </Box>

      <Box sx={{ mt: 4 }}>
        <Card>
          <CardHeader
            title="API Documentation"
            subheader="Health check endpoint specifications"
          />
          <CardContent>
            <Typography variant="body2" paragraph>
              The health check endpoints provide different levels of system monitoring:
            </Typography>
            <Box component="ul" sx={{ pl: 2 }}>
              <li>
                <Typography variant="body2">
                  <strong>Basic Health:</strong> Simple up/down status for quick monitoring
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>Detailed Health:</strong> Comprehensive system status including resource usage
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>Service Status:</strong> Individual service health (OpenAI, Twilio, Database, etc.)
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>Database Health:</strong> Database connectivity and performance metrics
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>External APIs:</strong> Status of third-party service integrations
                </Typography>
              </li>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default HealthCheckPage;