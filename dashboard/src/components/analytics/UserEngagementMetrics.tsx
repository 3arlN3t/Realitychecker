import React from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
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