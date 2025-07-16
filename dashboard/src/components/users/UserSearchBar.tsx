import React, { useState, useEffect } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Button,
  SelectChangeEvent
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { UserSearchProps } from './types';

const UserSearchBar: React.FC<UserSearchProps> = ({ onSearch, searchQuery }) => {
  const [query, setQuery] = useState(searchQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [status, setStatus] = useState('all');
  const [engagement, setEngagement] = useState('all');
  const [classification, setClassification] = useState('all');

  // Update local state when prop changes
  useEffect(() => {
    setQuery(searchQuery);
  }, [searchQuery]);

  // Handle search input change
  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  // Handle search submission
  const handleSearch = () => {
    onSearch(query);
  };

  // Handle enter key press
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  // Clear search
  const handleClearSearch = () => {
    setQuery('');
    onSearch('');
  };

  // Handle filter changes
  const handleStatusChange = (event: SelectChangeEvent) => {
    setStatus(event.target.value);
  };

  const handleEngagementChange = (event: SelectChangeEvent) => {
    setEngagement(event.target.value);
  };

  const handleClassificationChange = (event: SelectChangeEvent) => {
    setClassification(event.target.value);
  };

  // Apply filters
  const handleApplyFilters = () => {
    // In a real implementation, we would combine these filters with the search query
    // For now, we'll just use the search query
    onSearch(query);
  };

  // Reset filters
  const handleResetFilters = () => {
    setStatus('all');
    setEngagement('all');
    setClassification('all');
    setQuery('');
    onSearch('');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: showFilters ? 2 : 0 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search by phone number, date, or request count..."
          value={query}
          onChange={handleQueryChange}
          onKeyPress={handleKeyPress}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: query && (
              <InputAdornment position="end">
                <IconButton
                  aria-label="clear search"
                  onClick={handleClearSearch}
                  edge="end"
                  size="small"
                >
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        
        <Button
          variant="outlined"
          startIcon={<FilterIcon />}
          onClick={() => setShowFilters(!showFilters)}
          sx={{ ml: 2, whiteSpace: 'nowrap' }}
        >
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>
        
        <Button
          variant="contained"
          onClick={handleSearch}
          sx={{ ml: 2, whiteSpace: 'nowrap' }}
        >
          Search
        </Button>
      </Box>
      
      {showFilters && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                id="status-filter"
                value={status}
                label="Status"
                onChange={handleStatusChange}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="blocked">Blocked</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel id="engagement-filter-label">Engagement</InputLabel>
              <Select
                labelId="engagement-filter-label"
                id="engagement-filter"
                value={engagement}
                label="Engagement"
                onChange={handleEngagementChange}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel id="classification-filter-label">Classification</InputLabel>
              <Select
                labelId="classification-filter-label"
                id="classification-filter"
                value={classification}
                label="Classification"
                onChange={handleClassificationChange}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="legit">Mostly Legit</MenuItem>
                <MenuItem value="suspicious">Mostly Suspicious</MenuItem>
                <MenuItem value="scam">Mostly Scam</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={handleResetFilters}
              sx={{ mr: 1 }}
            >
              Reset
            </Button>
            <Button
              variant="contained"
              onClick={handleApplyFilters}
            >
              Apply Filters
            </Button>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default UserSearchBar;