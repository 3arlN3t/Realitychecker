import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography
} from '@mui/material';
import {
  Block as BlockIcon,
  CheckCircle as UnblockIcon,
  Visibility as ViewIcon,
  Warning as WarningIcon,
  CheckCircleOutline as LegitIcon,
  ErrorOutline as ScamIcon
} from '@mui/icons-material';
import { UserTableProps, UserDetails } from './types';

const UserTable: React.FC<UserTableProps> = ({
  users,
  onBlockUser,
  onUnblockUser,
  onUserSelect,
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange
}) => {
  // Calculate user engagement level based on score
  const getUserEngagementLevel = (score: number): { label: string; color: 'success' | 'warning' | 'error' | 'default' } => {
    if (score >= 70) return { label: 'High', color: 'success' };
    if (score >= 40) return { label: 'Medium', color: 'warning' };
    return { label: 'Low', color: 'error' };
  };

  // Get the most common classification from user's interaction history
  const getMostCommonClassification = (user: UserDetails) => {
    const classifications = user.interactionHistory
      .filter(interaction => interaction.analysisResult)
      .map(interaction => interaction.analysisResult!.classification);
    
    if (classifications.length === 0) return null;
    
    const counts: Record<string, number> = {};
    let maxCount = 0;
    let mostCommon = '';
    
    classifications.forEach(classification => {
      counts[classification] = (counts[classification] || 0) + 1;
      if (counts[classification] > maxCount) {
        maxCount = counts[classification];
        mostCommon = classification;
      }
    });
    
    return mostCommon;
  };

  // Format phone number for display
  const formatPhoneNumber = (phoneNumber: string) => {
    // Simple formatting for display purposes
    if (phoneNumber.length === 12 && phoneNumber.startsWith('+1')) {
      return `+1 (${phoneNumber.substring(2, 5)}) ${phoneNumber.substring(5, 8)}-${phoneNumber.substring(8)}`;
    }
    return phoneNumber;
  };

  // Handle page change
  const handleChangePage = (_event: unknown, newPage: number) => {
    onPageChange(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    onRowsPerPageChange(parseInt(event.target.value, 10));
  };

  // Calculate pagination
  const paginatedUsers = users.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader aria-label="user management table">
          <TableHead>
            <TableRow>
              <TableCell>Phone Number</TableCell>
              <TableCell>Last Interaction</TableCell>
              <TableCell align="center">Total Requests</TableCell>
              <TableCell align="center">Engagement</TableCell>
              <TableCell align="center">Common Classification</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedUsers.length > 0 ? (
              paginatedUsers.map((user) => {
                const engagementLevel = getUserEngagementLevel(user.engagementScore);
                const commonClassification = getMostCommonClassification(user);
                
                return (
                  <TableRow
                    key={user.id}
                    hover
                    sx={{
                      '&:last-child td, &:last-child th': { border: 0 },
                      backgroundColor: user.blocked ? 'rgba(244, 67, 54, 0.08)' : 'inherit',
                    }}
                  >
                    <TableCell component="th" scope="row">
                      {formatPhoneNumber(user.phoneNumber)}
                    </TableCell>
                    <TableCell>
                      {new Date(user.lastInteraction).toLocaleString()}
                    </TableCell>
                    <TableCell align="center">{user.totalRequests}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={engagementLevel.label}
                        color={engagementLevel.color}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      {commonClassification ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {commonClassification === 'Legit' && (
                            <LegitIcon fontSize="small" color="success" sx={{ mr: 0.5 }} />
                          )}
                          {commonClassification === 'Suspicious' && (
                            <WarningIcon fontSize="small" color="warning" sx={{ mr: 0.5 }} />
                          )}
                          {commonClassification === 'Likely Scam' && (
                            <ScamIcon fontSize="small" color="error" sx={{ mr: 0.5 }} />
                          )}
                          {commonClassification}
                        </Box>
                      ) : (
                        'N/A'
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={user.blocked ? 'Blocked' : 'Active'}
                        color={user.blocked ? 'error' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Tooltip title="View Interactions">
                          <IconButton
                            size="small"
                            onClick={() => onUserSelect(user)}
                            color="primary"
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        
                        {user.blocked ? (
                          <Tooltip title="Unblock User">
                            <IconButton
                              size="small"
                              onClick={() => onUnblockUser(user.id)}
                              color="success"
                            >
                              <UnblockIcon />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Block User">
                            <IconButton
                              size="small"
                              onClick={() => onBlockUser(user.id)}
                              color="error"
                            >
                              <BlockIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body1" sx={{ py: 2 }}>
                    No users found matching your search criteria
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={users.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
};

export default UserTable;