import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, responsiveFontSizes } from '@mui/material/styles';
import { CssBaseline, useMediaQuery, Box, Snackbar, Alert } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import { QueryProvider } from './providers/QueryProvider';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AnalyticsPage from './pages/AnalyticsPage';
import MonitoringPage from './pages/MonitoringPage';
import UsersPage from './pages/UsersPage';
import ConfigurationPage from './pages/ConfigurationPage';
import ReportingPage from './pages/ReportingPage';

// Enhanced theme with accessibility and responsive design
const createAppTheme = (prefersDarkMode: boolean, prefersHighContrast: boolean) => {
  let theme = createTheme({
    palette: {
      mode: prefersDarkMode ? 'dark' : 'light',
      primary: {
        main: prefersHighContrast ? '#000080' : '#1976d2',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#dc004e',
        contrastText: '#ffffff',
      },
      background: {
        default: prefersDarkMode ? '#121212' : '#f5f5f5',
        paper: prefersDarkMode ? '#1e1e1e' : '#ffffff',
      },
      error: {
        main: prefersHighContrast ? '#cc0000' : '#d32f2f',
      },
      success: {
        main: prefersHighContrast ? '#006600' : '#2e7d32',
      },
      warning: {
        main: '#ed6c02',
      },
      info: {
        main: '#0288d1',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 600,
        lineHeight: 1.2,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        lineHeight: 1.3,
      },
      h3: {
        fontSize: '1.75rem',
        fontWeight: 500,
        lineHeight: 1.3,
      },
      h4: {
        fontSize: '1.5rem',
        fontWeight: 500,
        lineHeight: 1.4,
      },
      h5: {
        fontSize: '1.25rem',
        fontWeight: 500,
        lineHeight: 1.4,
      },
      h6: {
        fontSize: '1.1rem',
        fontWeight: 500,
        lineHeight: 1.4,
      },
      body1: {
        lineHeight: 1.6,
      },
      body2: {
        lineHeight: 1.5,
      },
    },
    shape: {
      borderRadius: 8,
    },
    spacing: 8,
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            padding: '10px 20px',
            '&:focus': {
              outline: `2px solid ${prefersHighContrast ? '#000080' : '#1976d2'}`,
              outlineOffset: '2px',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              '&:focus-within': {
                outline: `2px solid ${prefersHighContrast ? '#000080' : '#1976d2'}`,
                outlineOffset: '2px',
              },
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
            '&:focus': {
              outline: `2px solid ${prefersHighContrast ? '#000080' : '#1976d2'}`,
              outlineOffset: '2px',
            },
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            fontWeight: 600,
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 8,
          },
        },
      },
    },
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 900,
        lg: 1200,
        xl: 1536,
      },
    },
  });

  // Make theme responsive
  theme = responsiveFontSizes(theme);
  
  return theme;
};

function App() {
  // Detect user preferences for accessibility
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const prefersHighContrast = useMediaQuery('(prefers-contrast: high)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  
  // State for notifications and announcements
  const [networkStatus, setNetworkStatus] = useState<'online' | 'offline'>('online');
  const [showNetworkNotification, setShowNetworkNotification] = useState(false);
  
  // Create theme based on user preferences
  const theme = createAppTheme(prefersDarkMode, prefersHighContrast);
  
  // Monitor network status for better UX
  useEffect(() => {
    const handleOnline = () => {
      setNetworkStatus('online');
      setShowNetworkNotification(true);
    };
    
    const handleOffline = () => {
      setNetworkStatus('offline');
      setShowNetworkNotification(true);
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  // Hide loading spinner when app loads
  useEffect(() => {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
      loadingElement.style.display = 'none';
    }
  }, []);
  
  // Announce route changes for screen readers
  const announceRouteChange = (route: string) => {
    const announcementsElement = document.getElementById('announcements');
    if (announcementsElement) {
      announcementsElement.textContent = `Navigated to ${route} page`;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          // Respect user's motion preferences
          '& *': {
            animationDuration: prefersReducedMotion ? '0.01ms !important' : undefined,
            animationIterationCount: prefersReducedMotion ? '1 !important' : undefined,
            transitionDuration: prefersReducedMotion ? '0.01ms !important' : undefined,
          },
        }}
      >
        <QueryProvider>
          <AuthProvider>
            <Router>
              <Routes>
                <Route 
                  path="/login" 
                  element={
                    <Box onFocus={() => announceRouteChange('login')}>
                      <LoginPage />
                    </Box>
                  } 
                />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Box onFocus={() => announceRouteChange('dashboard')}>
                          <DashboardPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Box onFocus={() => announceRouteChange('analytics')}>
                          <AnalyticsPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/monitoring"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Box onFocus={() => announceRouteChange('monitoring')}>
                          <MonitoringPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/users"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Box onFocus={() => announceRouteChange('users')}>
                          <UsersPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Box onFocus={() => announceRouteChange('reports')}>
                          <ReportingPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/config"
                  element={
                    <ProtectedRoute requiredRole="admin">
                      <Layout>
                        <Box onFocus={() => announceRouteChange('configuration')}>
                          <ConfigurationPage />
                        </Box>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Router>
          </AuthProvider>
        </QueryProvider>
        
        {/* Network status notification */}
        <Snackbar
          open={showNetworkNotification}
          autoHideDuration={networkStatus === 'online' ? 3000 : null}
          onClose={() => setShowNetworkNotification(false)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setShowNetworkNotification(false)}
            severity={networkStatus === 'online' ? 'success' : 'warning'}
            variant="filled"
            role="alert"
            aria-live="assertive"
          >
            {networkStatus === 'online' 
              ? 'Connection restored' 
              : 'Connection lost. Some features may not work properly.'
            }
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default App;
