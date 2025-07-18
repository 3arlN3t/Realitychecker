import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
import { Alert, AlertDescription } from './components/ui/alert';
// Badge import removed as it's not used
import { Wifi, WifiOff } from 'lucide-react';

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
  
  // Apply dark mode class to document
  useEffect(() => {
    if (prefersDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [prefersDarkMode]);

  return (
    <div className={`min-h-screen bg-background text-foreground ${prefersReducedMotion ? 'motion-reduce' : ''}`}>
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
      {showNetworkNotification && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
          <Alert variant={networkStatus === 'offline' ? 'destructive' : 'default'}>
            {networkStatus === 'online' ? (
              <Wifi className="h-4 w-4" />
            ) : (
              <WifiOff className="h-4 w-4" />
            )}
            <AlertDescription>
              {networkStatus === 'online' 
                ? 'Connection restored' 
                : 'Connection lost. Some features may not work properly.'
              }
            </AlertDescription>
          </Alert>
        </div>
      )}
      
      {/* Screen reader announcements */}
      <div id="announcements" className="sr-only" aria-live="polite" aria-atomic="true" />
    </div>
  );
}

export default App;
