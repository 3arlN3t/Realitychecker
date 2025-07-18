import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { Alert, AlertTitle, Snackbar } from '@mui/material';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
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
import theme from './theme';

// Custom hook for media queries
const useMediaQuery = (query: string) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addListener(listener);
    return () => media.removeListener(listener);
  }, [matches, query]);

  return matches;
};

function App() {
  // Detect user preferences for accessibility
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  
  // State for notifications and announcements
  const [networkStatus, setNetworkStatus] = useState<'online' | 'offline'>('online');
  const [showNetworkNotification, setShowNetworkNotification] = useState(false);
  
  // Monitor network status for better UX
  useEffect(() => {
    const handleOnline = () => {
      setNetworkStatus('online');
      setShowNetworkNotification(true);
      setTimeout(() => setShowNetworkNotification(false), 3000);
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
  
  // Always apply dark mode for now to match the screenshots
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)',
        backgroundAttachment: 'fixed',
        color: '#ffffff'
      }}>
        <QueryProvider>
          <AuthProvider>
            <Router>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DashboardPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <AnalyticsPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/monitoring"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <MonitoringPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/users"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <UsersPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ReportingPage />
                      </Layout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/config"
                  element={
                    <ProtectedRoute requiredRole="admin">
                      <Layout>
                        <ConfigurationPage />
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
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert 
            severity={networkStatus === 'online' ? 'success' : 'error'}
            icon={networkStatus === 'online' ? <WifiIcon /> : <WifiOffIcon />}
          >
            <AlertTitle>{networkStatus === 'online' ? 'Connected' : 'Disconnected'}</AlertTitle>
            {networkStatus === 'online' 
              ? 'Connection restored' 
              : 'Connection lost. Some features may not work properly.'
            }
          </Alert>
        </Snackbar>
        
        {/* Screen reader announcements */}
        <div id="announcements" style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', border: 0 }} aria-live="polite" aria-atomic="true" />
      </div>
    </ThemeProvider>
  );
}

export default App;
