import React, { useState } from 'react';
import { 
  Menu, 
  Home, 
  BarChart3, 
  Users, 
  Settings, 
  Activity, 
  FileText, 
  User, 
  LogOut,
  Shield,
  X
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// drawerWidth removed as it's not used in the new layout

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  requiredRole?: 'admin' | 'analyst';
}

const navigationItems: NavigationItem[] = [
  {
    text: 'Dashboard',
    icon: <Home className="w-4 h-4" />,
    path: '/dashboard',
  },
  {
    text: 'Analytics',
    icon: <BarChart3 className="w-4 h-4" />,
    path: '/analytics',
  },
  {
    text: 'Real-time Monitoring',
    icon: <Activity className="w-4 h-4" />,
    path: '/monitoring',
  },
  {
    text: 'User Management',
    icon: <Users className="w-4 h-4" />,
    path: '/users',
  },
  {
    text: 'Reports',
    icon: <FileText className="w-4 h-4" />,
    path: '/reports',
  },
  {
    text: 'Configuration',
    icon: <Settings className="w-4 h-4" />,
    path: '/config',
    requiredRole: 'admin',
  },
];

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleProfileMenuClose();
    navigate('/login');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setMobileOpen(false);
  };

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Top header with logo */}
      <div className="fixed top-0 left-0 w-full bg-black/90 backdrop-blur-lg border-b border-gray-800/50 z-10 flex items-center px-4 py-3 shadow-lg">
        <Shield className="w-6 h-6 mr-2 text-blue-400" />
        <h2 className="text-lg font-semibold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">Reality Checker</h2>
      </div>

      {/* Navigation bar - hidden on mobile */}
      <div className="fixed top-16 left-0 right-0 bg-black/90 backdrop-blur-lg border-b border-gray-800/50 z-10 shadow-lg hidden md:block">
        <div className="flex overflow-x-auto">
          {navigationItems
            .filter(item => !item.requiredRole || item.requiredRole === user?.role)
            .map((item) => (
              <button
                key={item.text}
                type="button"
                className={`flex items-center px-4 py-3 transition-all duration-300 relative group ${
                  location.pathname === item.path 
                    ? "border-b-2 border-blue-400 text-blue-400" 
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
                onClick={() => handleNavigation(item.path)}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/10 group-hover:to-purple-500/10 transition-all duration-300 rounded"></div>
                {item.icon}
                <span className="ml-2 whitespace-nowrap relative z-10">{item.text}</span>
              </button>
            ))}
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        type="button"
        className="fixed top-4 left-4 z-20 md:hidden bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg p-2 hover:bg-white/20 transition-all duration-300"
        onClick={handleDrawerToggle}
        aria-label="Toggle menu"
        aria-expanded={mobileOpen ? "true" : "false"}
        aria-controls="mobile-navigation"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 z-50 lg:hidden bg-black bg-opacity-50"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        >
          {/* Mobile sidebar content */}
          <div 
            id="mobile-navigation"
            className="fixed inset-y-0 left-0 w-64 bg-black border-r border-gray-800"
          >
            <div className="flex items-center justify-between px-4 py-4 border-b border-gray-800">
              <div className="flex items-center">
                <Shield className="w-6 h-6 mr-2" />
                <h2 className="text-lg font-semibold">Reality Checker</h2>
              </div>
              <button
                type="button"
                className="p-1 rounded-full hover:bg-gray-800"
                onClick={() => setMobileOpen(false)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="px-2 py-4">
              {navigationItems
                .filter(item => !item.requiredRole || item.requiredRole === user?.role)
                .map((item) => (
                  <button
                    key={item.text}
                    type="button"
                    className={`flex items-center w-full px-4 py-2 my-1 rounded ${
                      location.pathname === item.path 
                        ? "bg-gray-800 text-white" 
                        : "text-gray-400 hover:bg-gray-800 hover:text-white"
                    }`}
                    onClick={() => handleNavigation(item.path)}
                  >
                    {item.icon}
                    <span className="ml-3">{item.text}</span>
                  </button>
                ))}
            </nav>
          </div>
        </div>
      )}

      {/* User info */}
      <div className="fixed top-4 right-4 z-20 flex items-center">
        <div className="text-sm mr-2 p-2 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
          <div className="font-medium">{user?.username}</div>
          <div className="text-blue-400 text-xs">{user?.role}</div>
        </div>
        <button
          type="button"
          className="p-2 rounded-full hover:bg-white/10 bg-white/5 backdrop-blur-sm border border-white/10 transition-all duration-300 hover:scale-105"
          onClick={handleProfileMenuOpen}
          aria-label="User menu"
          aria-expanded={anchorEl ? "true" : "false"}
          aria-haspopup="true"
        >
          <User className="w-5 h-5" />
        </button>
        
        {anchorEl && (
          <div 
            className="absolute right-0 top-full mt-2 w-48 bg-black/90 backdrop-blur-lg border border-gray-800/50 rounded-lg shadow-2xl z-50"
            role="menu"
            aria-orientation="vertical"
          >
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-white/10 transition-all duration-300 rounded-lg"
              role="menuitem"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="w-full pt-32 md:pt-32 pb-4 px-4 md:px-6 lg:px-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;