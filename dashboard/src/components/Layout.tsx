import React, { useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
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

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-6 py-4 border-b">
        <Shield className="w-6 h-6 mr-2 text-primary" />
        <h2 className="text-lg font-semibold">Reality Checker</h2>
      </div>
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navigationItems
          .filter(item => !item.requiredRole || item.requiredRole === user?.role)
          .map((item) => (
            <Button
              key={item.text}
              variant={location.pathname === item.path ? "default" : "ghost"}
              className="w-full justify-start"
              onClick={() => handleNavigation(item.path)}
            >
              {item.icon}
              <span className="ml-2">{item.text}</span>
            </Button>
          ))}
      </nav>
    </div>
  );

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 z-50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        >
          <div className="fixed inset-y-0 left-0 w-64 bg-background border-r shadow-lg">
            <div className="flex items-center justify-between px-4 py-4 border-b">
              <div className="flex items-center">
                <Shield className="w-6 h-6 mr-2 text-primary" />
                <h2 className="text-lg font-semibold">Reality Checker</h2>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <nav className="px-4 py-4 space-y-2">
              {navigationItems
                .filter(item => !item.requiredRole || item.requiredRole === user?.role)
                .map((item) => (
                  <Button
                    key={item.text}
                    variant={location.pathname === item.path ? "default" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => handleNavigation(item.path)}
                  >
                    {item.icon}
                    <span className="ml-2">{item.text}</span>
                  </Button>
                ))}
            </nav>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:flex-col lg:w-64 lg:border-r lg:bg-background">
        {sidebarContent}
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-background border-b">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden mr-2"
              onClick={handleDrawerToggle}
            >
              <Menu className="w-4 h-4" />
            </Button>
            <h1 className="text-xl font-semibold">Admin Dashboard</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">{user?.username}</span>
              <Badge variant="outline">{user?.role}</Badge>
            </div>
            
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleProfileMenuOpen}
                className="relative"
              >
                <User className="w-4 h-4" />
              </Button>
              
              {anchorEl && (
                <div className="absolute right-0 mt-2 w-48 bg-background border rounded-md shadow-lg z-50">
                  <div className="py-1">
                    <button
                      onClick={handleLogout}
                      className="flex items-center w-full px-4 py-2 text-sm text-left hover:bg-muted"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;