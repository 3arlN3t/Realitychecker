/**
 * Keyboard Shortcuts component for Reality Checker Dashboard.
 * 
 * Displays available keyboard shortcuts organized by category with search
 * and accessibility features.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
  Divider,
  Paper
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  Keyboard as KeyboardIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material';
import { useKeyboardNavigation, KeyboardShortcut } from '../hooks/useKeyboardNavigation';

interface KeyboardShortcutsProps {
  open: boolean;
  onClose: () => void;
}

interface ShortcutDisplayProps {
  shortcut: KeyboardShortcut;
}

const ShortcutDisplay: React.FC<ShortcutDisplayProps> = ({ shortcut }) => {
  const formatShortcut = (shortcut: KeyboardShortcut): string => {
    const parts: string[] = [];
    
    // Add modifiers in standard order
    if (shortcut.ctrlKey || shortcut.metaKey) {
      parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
    }
    if (shortcut.altKey) {
      parts.push(navigator.platform.includes('Mac') ? '⌥' : 'Alt');
    }
    if (shortcut.shiftKey) {
      parts.push('⇧');
    }
    
    // Add the main key
    let keyDisplay = shortcut.key;
    
    // Special key formatting
    const specialKeys: Record<string, string> = {
      ' ': 'Space',
      'ArrowUp': '↑',
      'ArrowDown': '↓',
      'ArrowLeft': '←',
      'ArrowRight': '→',
      'Enter': '↵',
      'Escape': 'Esc',
      'Tab': '⇥',
      'Backspace': '⌫',
      'Delete': '⌦'
    };
    
    if (specialKeys[keyDisplay]) {
      keyDisplay = specialKeys[keyDisplay];
    } else {
      keyDisplay = keyDisplay.toUpperCase();
    }
    
    parts.push(keyDisplay);
    
    return parts.join(' + ');
  };

  return (
    <Box 
      component="kbd"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        px: 1,
        py: 0.5,
        backgroundColor: 'grey.100',
        border: '1px solid',
        borderColor: 'grey.300',
        borderRadius: 1,
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        fontWeight: 'bold',
        color: 'text.primary',
        minWidth: 'auto',
        whiteSpace: 'nowrap'
      }}
      role="text"
      aria-label={`Keyboard shortcut: ${formatShortcut(shortcut)}`}
    >
      {formatShortcut(shortcut)}
    </Box>
  );
};

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({ open, onClose }) => {
  const { getShortcutsByCategory } = useKeyboardNavigation();
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['Navigation']);

  // Get shortcuts organized by category
  const shortcutsByCategory = useMemo(() => {
    return getShortcutsByCategory();
  }, [getShortcutsByCategory]);

  // Filter shortcuts based on search term
  const filteredShortcuts = useMemo(() => {
    if (!searchTerm.trim()) return shortcutsByCategory;

    const filtered: Record<string, KeyboardShortcut[]> = {};
    const searchLower = searchTerm.toLowerCase();

    Object.entries(shortcutsByCategory).forEach(([category, shortcuts]) => {
      const matchingShortcuts = shortcuts.filter(shortcut => 
        shortcut.description.toLowerCase().includes(searchLower) ||
        shortcut.key.toLowerCase().includes(searchLower) ||
        category.toLowerCase().includes(searchLower)
      );

      if (matchingShortcuts.length > 0) {
        filtered[category] = matchingShortcuts;
      }
    });

    return filtered;
  }, [shortcutsByCategory, searchTerm]);

  // Expand all categories when searching
  useEffect(() => {
    if (searchTerm.trim()) {
      setExpandedCategories(Object.keys(filteredShortcuts));
    } else {
      setExpandedCategories(['Navigation']);
    }
  }, [searchTerm, filteredShortcuts]);

  const handleCategoryToggle = (category: string) => {
    setExpandedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const categoryOrder = ['Navigation', 'Actions', 'Accessibility', 'Editing', 'View'];
  const sortedCategories = Object.keys(filteredShortcuts).sort((a, b) => {
    const indexA = categoryOrder.indexOf(a);
    const indexB = categoryOrder.indexOf(b);
    
    if (indexA === -1 && indexB === -1) return a.localeCompare(b);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    
    return indexA - indexB;
  });

  const totalShortcuts = Object.values(filteredShortcuts).reduce((sum, shortcuts) => sum + shortcuts.length, 0);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="keyboard-shortcuts-title"
      aria-describedby="keyboard-shortcuts-description"
    >
      <DialogTitle id="keyboard-shortcuts-title">
        <Box display="flex" alignItems="center" gap={1}>
          <KeyboardIcon />
          <Typography variant="h6" component="span">
            Keyboard Shortcuts
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Typography 
          id="keyboard-shortcuts-description" 
          variant="body2" 
          color="text.secondary" 
          sx={{ mb: 3 }}
        >
          Use these keyboard shortcuts to navigate and interact with the Reality Checker Dashboard efficiently.
          {totalShortcuts > 0 && ` ${totalShortcuts} shortcuts available.`}
        </Typography>

        {/* Search Field */}
        <TextField
          fullWidth
          placeholder="Search shortcuts..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            )
          }}
          sx={{ mb: 3 }}
          aria-label="Search keyboard shortcuts"
        />

        {/* Quick Access Tips */}
        <Paper 
          variant="outlined" 
          sx={{ p: 2, mb: 3, backgroundColor: 'primary.50' }}
        >
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            💡 Quick Tips
          </Typography>
          <Typography variant="body2">
            • Press <ShortcutDisplay shortcut={{ key: 'k', ctrlKey: true, action: () => {}, description: '', category: '' }} /> to open the command palette
            • Use <ShortcutDisplay shortcut={{ key: 'Tab', action: () => {}, description: '', category: '' }} /> to navigate between elements
            • Press <ShortcutDisplay shortcut={{ key: 'Escape', action: () => {}, description: '', category: '' }} /> to close dialogs or cancel actions
          </Typography>
        </Paper>

        {/* Shortcuts by Category */}
        <Box>
          {sortedCategories.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                No shortcuts found matching "{searchTerm}"
              </Typography>
              <Button 
                onClick={() => setSearchTerm('')}
                sx={{ mt: 2 }}
              >
                Clear Search
              </Button>
            </Box>
          ) : (
            sortedCategories.map(category => (
              <Accordion
                key={category}
                expanded={expandedCategories.includes(category)}
                onChange={() => handleCategoryToggle(category)}
                sx={{ mb: 1 }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`${category}-shortcuts-content`}
                  id={`${category}-shortcuts-header`}
                >
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    <Typography variant="h6" component="h3">
                      {category}
                    </Typography>
                    <Chip 
                      label={filteredShortcuts[category].length} 
                      size="small" 
                      color="primary" 
                      variant="outlined"
                    />
                  </Box>
                </AccordionSummary>

                <AccordionDetails>
                  <List dense>
                    {filteredShortcuts[category].map((shortcut, index) => (
                      <React.Fragment key={`${category}-${index}`}>
                        {index > 0 && <Divider component="li" />}
                        <ListItem
                          sx={{
                            py: 1.5,
                            '&:hover': {
                              backgroundColor: 'action.hover'
                            }
                          }}
                        >
                          <ListItemText
                            primary={
                              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                {shortcut.description}
                              </Typography>
                            }
                            secondary={
                              shortcut.disabled ? (
                                <Typography variant="body2" color="text.disabled">
                                  Currently disabled
                                </Typography>
                              ) : undefined
                            }
                          />
                          <ListItemSecondaryAction>
                            <ShortcutDisplay shortcut={shortcut} />
                          </ListItemSecondaryAction>
                        </ListItem>
                      </React.Fragment>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>

        {/* Additional Information */}
        <Box mt={4}>
          <Typography variant="h6" gutterBottom>
            Accessibility Features
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            This application supports full keyboard navigation and screen reader compatibility.
            All interactive elements can be accessed using the Tab key, and actions can be
            triggered using Enter or Space keys.
          </Typography>
          
          <Typography variant="body2" color="text.secondary">
            For additional accessibility options, visit the Configuration page or contact
            your system administrator.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} variant="contained" autoFocus>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default KeyboardShortcuts;