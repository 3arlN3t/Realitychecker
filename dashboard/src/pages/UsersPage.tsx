import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Paper
} from '@mui/material';
import {
  People as UsersIcon,
  Search as SearchIcon,
  PersonAdd as UserCheckIcon,
  PersonOff as UserXIcon
} from '@mui/icons-material';
import UserTable from '../components/users/UserTable';
import UserSearchBar from '../components/users/UserSearchBar';
import UserInteractionModal from '../components/users/UserInteractionModal';
import { UserDetails, UserInteraction } from '../components/users/types';

// Sample user data generator
const generateSampleUsers = (count: number): UserDetails[] => {
  const users: UserDetails[] = [];
  
  for (let i = 0; i < count; i++) {
    const phoneNumber = `+1${Math.floor(Math.random() * 9000000000) + 1000000000}`;
    const firstInteraction = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000);
    const lastInteraction = new Date(
      Math.max(
        firstInteraction.getTime(),
        Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000
      )
    );
    
    const totalRequests = Math.floor(Math.random() * 20) + 1;
    const blocked = Math.random() < 0.05; // 5% chance of being blocked
    
    // Generate interaction history
    const interactions: UserInteraction[] = [];
    for (let j = 0; j < totalRequests; j++) {
      const timestamp = new Date(
        firstInteraction.getTime() + 
        (lastInteraction.getTime() - firstInteraction.getTime()) * (j / totalRequests)
      );
      
      const messageType = Math.random() > 0.3 ? 'text' : 'pdf';
      let classification: 'Legit' | 'Suspicious' | 'Likely Scam' = 'Legit';
      if (Math.random() <= 0.7) {
        classification = Math.random() > 0.5 ? 'Suspicious' : 'Likely Scam';
      }
      
      interactions.push({
        id: `int-${i}-${j}`,
        timestamp: timestamp.toISOString(),
        messageType,
        content: messageType === 'text' 
          ? 'Job posting content...' 
          : 'PDF document content...',
        analysisResult: Math.random() > 0.1 ? {
          trustScore: Math.floor(Math.random() * 100),
          classification,
          reasons: [
            'Reason 1 for classification',
            'Reason 2 for classification',
            'Reason 3 for classification'
          ]
        } : undefined,
        responseTime: Math.random() * 3 + 0.5,
        error: Math.random() > 0.9 ? 'Error processing request' : undefined
      });
    }
    
    users.push({
      id: `user-${i}`,
      phoneNumber,
      firstInteraction: firstInteraction.toISOString(),
      lastInteraction: lastInteraction.toISOString(),
      totalRequests,
      blocked,
      interactionHistory: interactions,
      engagementScore: Math.floor(Math.random() * 100),
      averageResponseTime: Math.random() * 2 + 0.5,
      mostFrequentHour: Math.floor(Math.random() * 24)
    });
  }
  
  return users;
};

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<UserDetails[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserDetails[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserDetails | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Load sample data
  useEffect(() => {
    const sampleUsers = generateSampleUsers(50);
    setUsers(sampleUsers);
    setFilteredUsers(sampleUsers);
  }, []);
  
  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(0);
    
    if (!query.trim()) {
      setFilteredUsers(users);
      return;
    }
    
    const filtered = users.filter(user => 
      user.phoneNumber.includes(query) ||
      new Date(user.lastInteraction).toLocaleDateString().includes(query) ||
      user.totalRequests.toString().includes(query)
    );
    
    setFilteredUsers(filtered);
  };
  
  // Handle user blocking/unblocking
  const handleBlockUser = (userId: string) => {
    setUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, blocked: true } : user
      )
    );
    
    setFilteredUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, blocked: true } : user
      )
    );
  };
  
  const handleUnblockUser = (userId: string) => {
    setUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, blocked: false } : user
      )
    );
    
    setFilteredUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === userId ? { ...user, blocked: false } : user
      )
    );
  };
  
  // Handle user selection for modal
  const handleUserSelect = (user: UserDetails) => {
    setSelectedUser(user);
    setIsModalOpen(true);
  };
  
  // Handle pagination
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };
  
  const handleRowsPerPageChange = (newRowsPerPage: number) => {
    setRowsPerPage(newRowsPerPage);
    setCurrentPage(0);
  };
  
  // Calculate stats
  const totalUsers = users.length;
  const activeUsers = users.filter(user => !user.blocked).length;
  const blockedUsers = users.filter(user => user.blocked).length;
  const avgEngagement = users.reduce((sum, user) => sum + user.engagementScore, 0) / users.length || 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Enhanced Header Section */}
      <Paper
        elevation={3}
        sx={{
          position: 'relative',
          overflow: 'hidden',
          borderRadius: 3,
          background: 'linear-gradient(135deg, #7b1fa2 0%, #e91e63 50%, #f44336 100%)',
          p: 4,
          mb: 3,
          color: 'white'
        }}
      >
        <Box sx={{ position: 'absolute', inset: 0, bgcolor: 'rgba(0,0,0,0.1)' }} />
        <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(4px)',
                mr: 2
              }}
            >
              <UsersIcon sx={{ fontSize: 32 }} />
            </Box>
            <Box>
              <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                User Management
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Manage users and track interactions
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={<UserCheckIcon />}
              label={`${activeUsers} Active`}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(4px)'
              }}
            />
            <Chip
              icon={<UsersIcon />}
              label={`${totalUsers} Total Users`}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)'
              }}
            />
          </Box>
        </Box>
      </Paper>

      {/* User Stats Overview */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, gap: 2, mb: 3 }}>
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Total Users</Typography>
                <UsersIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {totalUsers}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Registered users
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Active Users</Typography>
                <UserCheckIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ color: 'success.main', mb: 0.5 }}>
              {activeUsers}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Not blocked
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Blocked Users</Typography>
                <UserXIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ color: 'error.main', mb: 0.5 }}>
              {blockedUsers}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Restricted access
            </Typography>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle2">Avg Engagement</Typography>
                <SearchIcon color="action" fontSize="small" />
              </Box>
            }
            sx={{ pb: 1 }}
          />
          <CardContent sx={{ pt: 0 }}>
            <Typography variant="h4" sx={{ mb: 0.5 }}>
              {avgEngagement.toFixed(0)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Engagement score
            </Typography>
          </CardContent>
        </Card>
      </Box>
      
      {/* Search Bar */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SearchIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Search Users</Typography>
            </Box>
          }
          subheader="Find users by phone number, date, or request count"
        />
        <CardContent>
          <UserSearchBar 
            onSearch={handleSearch} 
            searchQuery={searchQuery}
          />
        </CardContent>
      </Card>
      
      {/* User Table */}
      <Card>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <UsersIcon sx={{ mr: 1 }} />
              <Typography variant="h6">User Directory</Typography>
              {searchQuery && (
                <Chip
                  label={`${filteredUsers.length} results`}
                  color="secondary"
                  size="small"
                />
              )}
            </Box>
          }
          subheader="Manage WhatsApp users and view their interaction history"
        />
        <CardContent>
          <UserTable 
            users={filteredUsers}
            onBlockUser={handleBlockUser}
            onUnblockUser={handleUnblockUser}
            onUserSelect={handleUserSelect}
            page={currentPage}
            rowsPerPage={rowsPerPage}
            onPageChange={handlePageChange}
            onRowsPerPageChange={handleRowsPerPageChange}
          />
        </CardContent>
      </Card>
      
      <UserInteractionModal 
        user={selectedUser}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </Box>
  );
};

export default UsersPage;