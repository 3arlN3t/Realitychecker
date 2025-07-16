import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper } from '@mui/material';
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
      const classification = Math.random() > 0.7 ? 'Legit' : 
                            Math.random() > 0.5 ? 'Suspicious' : 'Likely Scam';
      
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
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        User Management
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <UserSearchBar 
          onSearch={handleSearch} 
          searchQuery={searchQuery}
        />
      </Paper>
      
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
      
      <UserInteractionModal 
        user={selectedUser}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </Box>
  );
};

export default UsersPage;