import React from 'react';
import { 
  Box,
  Paper, 
  Typography, 
  List, 
  ListItem, 
  ListItemText,
  Chip,
  Divider
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { UserEngagementData } from './types';

interface UserEngagementMetricsProps {
  data: UserEngagementData[];
}

const UserEngagementMetrics: React.FC<UserEngagementMetricsProps> = ({ data }) => {
  // Handle empty or invalid data
  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3, height: '400px', flex: '1 1 300px', minWidth: '300px' }}>
        <Typography variant="h6" gutterBottom>
          User Behavior Insights
        </Typography>
        <Box sx={{ 
          height: '90%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column'
        }}>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            No engagement data available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            User metrics will appear here as users interact with the system
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, height: '400px', flex: '1 1 300px', minWidth: '300px' }}>
      <Typography variant="h6" gutterBottom>
        User Behavior Insights
      </Typography>
      <List>
        {data.map((item, index) => (
          <React.Fragment key={item.metric}>
            <ListItem
              secondaryAction={
                item.change !== undefined && (
                  <Chip
                    icon={item.change >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                    label={`${item.change >= 0 ? '+' : ''}${item.change}%`}
                    color={item.change >= 0 ? 'success' : 'error'}
                    size="small"
                  />
                )
              }
            >
              <ListItemText
                primary={item.metric}
                secondary={
                  <Typography 
                    variant="body1" 
                    component="span" 
                    fontWeight="bold"
                  >
                    {item.value}
                  </Typography>
                }
              />
            </ListItem>
            {index < data.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
};

export default UserEngagementMetrics;