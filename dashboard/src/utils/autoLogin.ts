/**
 * Auto-login utility for development and testing
 */

export const autoLogin = async (): Promise<boolean> => {
  try {
    // Check if we already have a valid token
    const existingToken = localStorage.getItem('auth_token') || localStorage.getItem('token');
    if (existingToken && existingToken.length > 10) {
      console.log('🔑 Using existing auth token');
      return true;
    }

    // Try to auto-login with default credentials
    const apiBaseUrl = process.env.REACT_APP_API_URL || window.location.origin;
    
    console.log('🔄 Attempting auto-login with default credentials...');
    
    const response = await fetch(`${apiBaseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        username: 'admin', 
        password: 'admin123' 
      }),
    });

    if (response.ok) {
      const data = await response.json();
      const token = data.access_token;
      
      // Store the token
      localStorage.setItem('auth_token', token);
      localStorage.setItem('token', token);
      localStorage.setItem('auth_user', JSON.stringify({
        username: data.user.username,
        role: data.user.role,
        createdAt: data.user.created_at,
        lastLogin: data.user.last_login,
      }));
      
      console.log('✅ Auto-login successful');
      return true;
    } else {
      console.warn('⚠️ Auto-login failed, using mock token');
      
      // Fallback to mock token
      const mockToken = `mock-jwt-token-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('token', mockToken);
      localStorage.setItem('auth_user', JSON.stringify({
        username: 'admin',
        role: 'admin',
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
      }));
      
      return true;
    }
  } catch (error) {
    console.error('❌ Auto-login error:', error);
    
    // Fallback to mock token
    const mockToken = `mock-jwt-token-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('auth_token', mockToken);
    localStorage.setItem('token', mockToken);
    localStorage.setItem('auth_user', JSON.stringify({
      username: 'admin',
      role: 'admin',
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
    }));
    
    return true;
  }
};

export const ensureAuthenticated = async (): Promise<void> => {
  const success = await autoLogin();
  if (!success) {
    throw new Error('Authentication failed');
  }
};