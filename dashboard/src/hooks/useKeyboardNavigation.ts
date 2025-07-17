/**
 * Custom hook for keyboard navigation and shortcuts in Reality Checker Dashboard.
 * 
 * Provides comprehensive keyboard navigation support including:
 * - Global keyboard shortcuts
 * - Focus management
 * - Accessibility navigation
 * - Command palette integration
 */

import { useEffect, useCallback, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  metaKey?: boolean;
  action: () => void;
  description: string;
  category: string;
  disabled?: boolean;
}

export interface FocusableElement {
  element: HTMLElement;
  priority: number;
  group?: string;
}

interface UseKeyboardNavigationOptions {
  enableGlobalShortcuts?: boolean;
  enableFocusTrapping?: boolean;
  enableArrowNavigation?: boolean;
  announceNavigation?: boolean;
}

interface NavigationState {
  currentFocusIndex: number;
  focusableElements: FocusableElement[];
  shortcutsEnabled: boolean;
  commandPaletteOpen: boolean;
}

export const useKeyboardNavigation = (options: UseKeyboardNavigationOptions = {}) => {
  const {
    enableGlobalShortcuts = true,
    enableFocusTrapping = false,
    enableArrowNavigation = true,
    announceNavigation = true
  } = options;

  const navigate = useNavigate();
  const location = useLocation();
  
  const [navigationState, setNavigationState] = useState<NavigationState>({
    currentFocusIndex: -1,
    focusableElements: [],
    shortcutsEnabled: true,
    commandPaletteOpen: false
  });

  const focusTrapRef = useRef<HTMLElement | null>(null);
  const shortcutsRef = useRef<KeyboardShortcut[]>([]);

  // Default keyboard shortcuts
  const defaultShortcuts: KeyboardShortcut[] = [
    // Navigation shortcuts
    {
      key: 'd',
      altKey: true,
      action: () => navigate('/dashboard'),
      description: 'Go to Dashboard',
      category: 'Navigation'
    },
    {
      key: 'a',
      altKey: true,
      action: () => navigate('/analytics'),
      description: 'Go to Analytics',
      category: 'Navigation'
    },
    {
      key: 'm',
      altKey: true,
      action: () => navigate('/monitoring'),
      description: 'Go to Monitoring',
      category: 'Navigation'
    },
    {
      key: 'u',
      altKey: true,
      action: () => navigate('/users'),
      description: 'Go to Users',
      category: 'Navigation'
    },
    {
      key: 'r',
      altKey: true,
      action: () => navigate('/reports'),
      description: 'Go to Reports',
      category: 'Navigation'
    },
    {
      key: 'c',
      altKey: true,
      action: () => navigate('/config'),
      description: 'Go to Configuration',
      category: 'Navigation'
    },
    
    // Action shortcuts
    {
      key: 'k',
      ctrlKey: true,
      action: () => toggleCommandPalette(),
      description: 'Open Command Palette',
      category: 'Actions'
    },
    {
      key: 'k',
      metaKey: true,
      action: () => toggleCommandPalette(),
      description: 'Open Command Palette (Mac)',
      category: 'Actions'
    },
    {
      key: 'h',
      altKey: true,
      action: () => showHelpDialog(),
      description: 'Show Help',
      category: 'Actions'
    },
    {
      key: 'f',
      ctrlKey: true,
      action: () => focusSearch(),
      description: 'Focus Search',
      category: 'Actions'
    },
    {
      key: 'f',
      metaKey: true,
      action: () => focusSearch(),
      description: 'Focus Search (Mac)',
      category: 'Actions'
    },
    {
      key: 'n',
      ctrlKey: true,
      action: () => createNew(),
      description: 'Create New',
      category: 'Actions'
    },
    {
      key: 'r',
      ctrlKey: true,
      action: () => refresh(),
      description: 'Refresh Page',
      category: 'Actions'
    },
    
    // Accessibility shortcuts
    {
      key: 'Tab',
      action: () => handleTabNavigation(),
      description: 'Navigate to next element',
      category: 'Accessibility'
    },
    {
      key: 'Tab',
      shiftKey: true,
      action: () => handleShiftTabNavigation(),
      description: 'Navigate to previous element',
      category: 'Accessibility'
    },
    {
      key: 'Escape',
      action: () => handleEscape(),
      description: 'Close dialog/modal or cancel action',
      category: 'Accessibility'
    },
    {
      key: 'Enter',
      action: () => handleEnter(),
      description: 'Activate focused element',
      category: 'Accessibility'
    },
    {
      key: ' ',
      action: () => handleSpace(),
      description: 'Activate focused element',
      category: 'Accessibility'
    }
  ];

  // Initialize shortcuts
  useEffect(() => {
    shortcutsRef.current = [...defaultShortcuts];
  }, []);

  // Global keyboard event handler
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!navigationState.shortcutsEnabled || !enableGlobalShortcuts) return;

    // Check for shortcut matches
    const matchingShortcut = shortcutsRef.current.find(shortcut => {
      if (shortcut.disabled) return false;
      
      return (
        shortcut.key.toLowerCase() === event.key.toLowerCase() &&
        !!shortcut.ctrlKey === event.ctrlKey &&
        !!shortcut.altKey === event.altKey &&
        !!shortcut.shiftKey === event.shiftKey &&
        !!shortcut.metaKey === event.metaKey
      );
    });

    if (matchingShortcut) {
      event.preventDefault();
      event.stopPropagation();
      matchingShortcut.action();
      
      if (announceNavigation) {
        announceToScreenReader(`Executed: ${matchingShortcut.description}`);
      }
    }

    // Handle arrow navigation
    if (enableArrowNavigation && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
      handleArrowNavigation(event);
    }
  }, [navigationState.shortcutsEnabled, enableGlobalShortcuts, enableArrowNavigation, announceNavigation]);

  // Attach global keyboard event listener
  useEffect(() => {
    if (enableGlobalShortcuts) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, enableGlobalShortcuts]);

  // Update focusable elements when DOM changes
  const updateFocusableElements = useCallback(() => {
    const container = focusTrapRef.current || document.body;
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'textarea:not([disabled])',
      'select:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      'details summary',
      '[contenteditable="true"]'
    ].join(', ');

    const elements = Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
    
    const focusableElements: FocusableElement[] = elements.map((element, index) => {
      // Determine priority based on element type and role
      let priority = 0;
      if (element.getAttribute('role') === 'main') priority = 10;
      else if (element.tagName === 'BUTTON' && element.classList.contains('primary')) priority = 8;
      else if (element.tagName === 'INPUT') priority = 7;
      else if (element.tagName === 'BUTTON') priority = 6;
      else if (element.tagName === 'A') priority = 5;
      else priority = index;

      return {
        element,
        priority,
        group: element.dataset.focusGroup
      };
    });

    // Sort by priority (higher priority first)
    focusableElements.sort((a, b) => b.priority - a.priority);

    setNavigationState(prev => ({
      ...prev,
      focusableElements
    }));
  }, []);

  // Update focusable elements on mount and route change
  useEffect(() => {
    updateFocusableElements();
    
    // Use MutationObserver to detect DOM changes
    const observer = new MutationObserver(updateFocusableElements);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled', 'tabindex', 'aria-hidden']
    });

    return () => observer.disconnect();
  }, [location.pathname, updateFocusableElements]);

  // Command palette toggle
  const toggleCommandPalette = useCallback(() => {
    setNavigationState(prev => ({
      ...prev,
      commandPaletteOpen: !prev.commandPaletteOpen
    }));
    
    if (announceNavigation) {
      announceToScreenReader(navigationState.commandPaletteOpen ? 'Command palette closed' : 'Command palette opened');
    }
  }, [navigationState.commandPaletteOpen, announceNavigation]);

  // Navigation action handlers
  const showHelpDialog = useCallback(() => {
    // Trigger help dialog
    const helpEvent = new CustomEvent('show-help-dialog');
    document.dispatchEvent(helpEvent);
    
    if (announceNavigation) {
      announceToScreenReader('Help dialog opened');
    }
  }, [announceNavigation]);

  const focusSearch = useCallback(() => {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]') as HTMLInputElement;
    if (searchInput) {
      searchInput.focus();
      if (announceNavigation) {
        announceToScreenReader('Search field focused');
      }
    }
  }, [announceNavigation]);

  const createNew = useCallback(() => {
    // Look for "New" or "Add" buttons
    const newButton = document.querySelector('button[aria-label*="new" i], button[aria-label*="add" i], button[aria-label*="create" i]') as HTMLButtonElement;
    if (newButton) {
      newButton.click();
      if (announceNavigation) {
        announceToScreenReader('Create new action triggered');
      }
    }
  }, [announceNavigation]);

  const refresh = useCallback(() => {
    window.location.reload();
  }, []);

  // Tab navigation handlers
  const handleTabNavigation = useCallback(() => {
    if (enableFocusTrapping && focusTrapRef.current) {
      const { focusableElements, currentFocusIndex } = navigationState;
      if (focusableElements.length === 0) return;

      const nextIndex = (currentFocusIndex + 1) % focusableElements.length;
      const nextElement = focusableElements[nextIndex];
      
      if (nextElement) {
        nextElement.element.focus();
        setNavigationState(prev => ({ ...prev, currentFocusIndex: nextIndex }));
        
        if (announceNavigation) {
          announceToScreenReader(`Focused: ${getElementDescription(nextElement.element)}`);
        }
      }
    }
  }, [enableFocusTrapping, navigationState, announceNavigation]);

  const handleShiftTabNavigation = useCallback(() => {
    if (enableFocusTrapping && focusTrapRef.current) {
      const { focusableElements, currentFocusIndex } = navigationState;
      if (focusableElements.length === 0) return;

      const prevIndex = currentFocusIndex <= 0 ? focusableElements.length - 1 : currentFocusIndex - 1;
      const prevElement = focusableElements[prevIndex];
      
      if (prevElement) {
        prevElement.element.focus();
        setNavigationState(prev => ({ ...prev, currentFocusIndex: prevIndex }));
        
        if (announceNavigation) {
          announceToScreenReader(`Focused: ${getElementDescription(prevElement.element)}`);
        }
      }
    }
  }, [enableFocusTrapping, navigationState, announceNavigation]);

  // Arrow navigation handler
  const handleArrowNavigation = useCallback((event: KeyboardEvent) => {
    const activeElement = document.activeElement as HTMLElement;
    if (!activeElement) return;

    // Check if we're in a grid or list context
    const gridContainer = activeElement.closest('[role="grid"], [role="listbox"], [role="menu"]');
    if (!gridContainer) return;

    event.preventDefault();

    const items = Array.from(gridContainer.querySelectorAll('[role="gridcell"], [role="option"], [role="menuitem"]')) as HTMLElement[];
    const currentIndex = items.indexOf(activeElement);
    
    if (currentIndex === -1) return;

    let targetIndex = currentIndex;
    const columns = parseInt(gridContainer.getAttribute('aria-colcount') || '1');

    switch (event.key) {
      case 'ArrowUp':
        targetIndex = Math.max(0, currentIndex - columns);
        break;
      case 'ArrowDown':
        targetIndex = Math.min(items.length - 1, currentIndex + columns);
        break;
      case 'ArrowLeft':
        targetIndex = Math.max(0, currentIndex - 1);
        break;
      case 'ArrowRight':
        targetIndex = Math.min(items.length - 1, currentIndex + 1);
        break;
    }

    if (targetIndex !== currentIndex) {
      items[targetIndex]?.focus();
      
      if (announceNavigation) {
        announceToScreenReader(`Moved to: ${getElementDescription(items[targetIndex])}`);
      }
    }
  }, [announceNavigation]);

  // Common key handlers
  const handleEscape = useCallback(() => {
    // Close any open modals or dialogs
    const modal = document.querySelector('[role="dialog"][aria-modal="true"]') as HTMLElement;
    if (modal) {
      const closeButton = modal.querySelector('button[aria-label*="close" i]') as HTMLButtonElement;
      if (closeButton) {
        closeButton.click();
        if (announceNavigation) {
          announceToScreenReader('Dialog closed');
        }
        return;
      }
    }

    // Close command palette if open
    if (navigationState.commandPaletteOpen) {
      toggleCommandPalette();
      return;
    }

    // Clear any selections or reset state
    const clearEvent = new CustomEvent('keyboard-escape');
    document.dispatchEvent(clearEvent);
  }, [navigationState.commandPaletteOpen, toggleCommandPalette, announceNavigation]);

  const handleEnter = useCallback(() => {
    const activeElement = document.activeElement as HTMLElement;
    if (!activeElement) return;

    // Activate the focused element
    if (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button') {
      activeElement.click();
    } else if (activeElement.tagName === 'A') {
      activeElement.click();
    } else if (activeElement.getAttribute('role') === 'menuitem') {
      activeElement.click();
    }
  }, []);

  const handleSpace = useCallback(() => {
    const activeElement = document.activeElement as HTMLElement;
    if (!activeElement) return;

    // Only handle space for certain elements (not inputs)
    if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') return;

    if (activeElement.tagName === 'BUTTON' || activeElement.getAttribute('role') === 'button') {
      activeElement.click();
    }
  }, []);

  // Utility functions
  const announceToScreenReader = useCallback((message: string) => {
    const announcer = document.getElementById('announcements') || 
                     document.querySelector('[aria-live="polite"]') ||
                     document.querySelector('[aria-live="assertive"]');
    
    if (announcer) {
      announcer.textContent = message;
      setTimeout(() => {
        announcer.textContent = '';
      }, 1000);
    }
  }, []);

  const getElementDescription = useCallback((element: HTMLElement): string => {
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel;

    const ariaLabelledBy = element.getAttribute('aria-labelledby');
    if (ariaLabelledBy) {
      const labelElement = document.getElementById(ariaLabelledBy);
      if (labelElement) return labelElement.textContent || '';
    }

    const textContent = element.textContent?.trim();
    if (textContent) return textContent;

    const tagName = element.tagName.toLowerCase();
    const type = element.getAttribute('type');
    
    return type ? `${tagName} ${type}` : tagName;
  }, []);

  // Focus management functions
  const setFocusTrap = useCallback((element: HTMLElement | null) => {
    focusTrapRef.current = element;
    updateFocusableElements();
  }, [updateFocusableElements]);

  const moveFocus = useCallback((direction: 'next' | 'previous' | 'first' | 'last') => {
    const { focusableElements } = navigationState;
    if (focusableElements.length === 0) return;

    let targetIndex = 0;
    
    switch (direction) {
      case 'first':
        targetIndex = 0;
        break;
      case 'last':
        targetIndex = focusableElements.length - 1;
        break;
      case 'next':
        targetIndex = (navigationState.currentFocusIndex + 1) % focusableElements.length;
        break;
      case 'previous':
        targetIndex = navigationState.currentFocusIndex <= 0 ? 
                     focusableElements.length - 1 : 
                     navigationState.currentFocusIndex - 1;
        break;
    }

    const targetElement = focusableElements[targetIndex];
    if (targetElement) {
      targetElement.element.focus();
      setNavigationState(prev => ({ ...prev, currentFocusIndex: targetIndex }));
      
      if (announceNavigation) {
        announceToScreenReader(`Moved focus ${direction}: ${getElementDescription(targetElement.element)}`);
      }
    }
  }, [navigationState, announceNavigation, getElementDescription]);

  const addShortcut = useCallback((shortcut: KeyboardShortcut) => {
    shortcutsRef.current.push(shortcut);
  }, []);

  const removeShortcut = useCallback((key: string, modifiers?: Partial<Pick<KeyboardShortcut, 'ctrlKey' | 'altKey' | 'shiftKey' | 'metaKey'>>) => {
    shortcutsRef.current = shortcutsRef.current.filter(shortcut => {
      if (shortcut.key !== key) return true;
      
      if (modifiers) {
        return !(
          !!shortcut.ctrlKey === !!modifiers.ctrlKey &&
          !!shortcut.altKey === !!modifiers.altKey &&
          !!shortcut.shiftKey === !!modifiers.shiftKey &&
          !!shortcut.metaKey === !!modifiers.metaKey
        );
      }
      
      return false;
    });
  }, []);

  const toggleShortcuts = useCallback((enabled: boolean) => {
    setNavigationState(prev => ({ ...prev, shortcutsEnabled: enabled }));
  }, []);

  const getShortcutsByCategory = useCallback(() => {
    const categories: Record<string, KeyboardShortcut[]> = {};
    
    shortcutsRef.current.forEach(shortcut => {
      if (!categories[shortcut.category]) {
        categories[shortcut.category] = [];
      }
      categories[shortcut.category].push(shortcut);
    });
    
    return categories;
  }, []);

  return {
    // State
    navigationState,
    
    // Focus management
    setFocusTrap,
    moveFocus,
    updateFocusableElements,
    
    // Shortcut management
    addShortcut,
    removeShortcut,
    toggleShortcuts,
    getShortcutsByCategory,
    
    // Command palette
    toggleCommandPalette,
    
    // Utilities
    announceToScreenReader,
    
    // Refs for external use
    focusTrapRef
  };
};

export default useKeyboardNavigation;