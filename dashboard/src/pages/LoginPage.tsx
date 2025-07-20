import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Error as AlertCircleIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await login(username, password);
      
      if (result.success) {
        navigate(from, { replace: true });
      } else {
        setError(result.errorMessage || 'Login failed');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        px: 2,
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(123, 31, 162, 0.1) 50%, rgba(0, 0, 0, 1) 100%)'
      }}
    >
      {/* Background effects */}
      <Box
        sx={{
          position: 'absolute',
          top: 80,
          left: 80,
          width: 288,
          height: 288,
          bgcolor: 'rgba(25, 118, 210, 0.1)',
          borderRadius: '50%',
          filter: 'blur(48px)'
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: 80,
          right: 80,
          width: 384,
          height: 384,
          bgcolor: 'rgba(123, 31, 162, 0.1)',
          borderRadius: '50%',
          filter: 'blur(48px)'
        }}
      />
      
      <Box sx={{ maxWidth: 400, width: '100%', position: 'relative', zIndex: 1 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ position: 'relative', display: 'inline-block', mb: 2 }}>
            <Box
              sx={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(45deg, #1976d2, #7b1fa2)',
                borderRadius: '50%',
                filter: 'blur(8px)',
                opacity: 0.3
              }}
            />
            <ShieldIcon sx={{ fontSize: 64, color: 'primary.main', position: 'relative', zIndex: 1 }} />
          </Box>
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: 'bold',
              mb: 1,
              background: 'linear-gradient(45deg, #1976d2, #7b1fa2)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              color: 'transparent'
            }}
          >
            Reality Checker
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Admin Dashboard - Sign in to your account
          </Typography>
        </Box>
        
        <Paper
          elevation={3}
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            p: 3
          }}
        >
          {error && (
            <Alert
              severity="error"
              icon={<AlertCircleIcon />}
              sx={{
                mb: 2,
                bgcolor: 'rgba(244, 67, 54, 0.1)',
                border: '1px solid rgba(244, 67, 54, 0.5)',
                color: 'error.main'
              }}
            >
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              id="username"
              name="username"
              label="Username"
              type="text"
              autoComplete="username"
              required
              autoFocus
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your username"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(4px)',
                  '& fieldset': {
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'primary.main',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: 'text.primary',
                },
                '& .MuiOutlinedInput-input': {
                  color: 'text.primary',
                },
              }}
            />
            
            <TextField
              id="password"
              name="password"
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your password"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                  backdropFilter: 'blur(4px)',
                  '& fieldset': {
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'primary.main',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: 'text.primary',
                },
                '& .MuiOutlinedInput-input': {
                  color: 'text.primary',
                },
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading || !username || !password}
              sx={{
                background: 'linear-gradient(45deg, #1976d2, #7b1fa2)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #1565c0, #6a1b9a)',
                  transform: 'scale(1.02)',
                },
                '&:disabled': {
                  opacity: 0.5,
                  transform: 'none',
                },
                transition: 'all 0.3s ease',
                py: 1.5,
                fontWeight: 'medium'
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} color="inherit" />
                  Signing in...
                </Box>
              ) : (
                'Sign In'
              )}
            </Button>
          </Box>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Default credentials for testing:
            </Typography>
            <Paper
              sx={{
                display: 'inline-block',
                px: 2,
                py: 0.5,
                bgcolor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 1
              }}
            >
              <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                admin / admin123
              </Typography>
            </Paper>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default LoginPage;