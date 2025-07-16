import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import UserSearchBar from '../UserSearchBar';

describe('UserSearchBar Component', () => {
  const mockOnSearch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders search input correctly', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="" />);
    
    // Check if search input is rendered
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    expect(searchInput).toBeInTheDocument();
  });

  test('updates search query when typing', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="" />);
    
    // Find search input and type in it
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    fireEvent.change(searchInput, { target: { value: '+1234567890' } });
    
    // Check if the input value is updated
    expect(searchInput).toHaveValue('+1234567890');
  });

  test('calls onSearch when search button is clicked', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="" />);
    
    // Find search input and type in it
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    fireEvent.change(searchInput, { target: { value: '+1234567890' } });
    
    // Find and click the search button
    const searchButton = screen.getByText('Search');
    fireEvent.click(searchButton);
    
    // Check if onSearch was called with the correct query
    expect(mockOnSearch).toHaveBeenCalledWith('+1234567890');
  });

  test('calls onSearch when Enter key is pressed', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="" />);
    
    // Find search input, type in it, and press Enter
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    fireEvent.change(searchInput, { target: { value: '+1234567890' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    // Check if onSearch was called with the correct query
    expect(mockOnSearch).toHaveBeenCalledWith('+1234567890');
  });

  test('clears search query when clear button is clicked', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="+1234567890" />);
    
    // Find and click the clear button
    const clearButton = screen.getByLabelText('clear search');
    fireEvent.click(clearButton);
    
    // Check if onSearch was called with empty string
    expect(mockOnSearch).toHaveBeenCalledWith('');
    
    // Check if the input value is cleared
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    expect(searchInput).toHaveValue('');
  });

  test('toggles filter section when filter button is clicked', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="" />);
    
    // Initially, filter section should not be visible
    expect(screen.queryByText('Status')).not.toBeInTheDocument();
    
    // Find and click the filter button
    const filterButton = screen.getByText('Show Filters');
    fireEvent.click(filterButton);
    
    // Now filter section should be visible
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Engagement')).toBeInTheDocument();
    expect(screen.getByText('Classification')).toBeInTheDocument();
    
    // Click the filter button again to hide filters
    const hideFilterButton = screen.getByText('Hide Filters');
    fireEvent.click(hideFilterButton);
    
    // Filter section should be hidden again
    expect(screen.queryByText('Status')).not.toBeInTheDocument();
  });

  test('applies filters when Apply Filters button is clicked', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="+1234567890" />);
    
    // Show filters
    const filterButton = screen.getByText('Show Filters');
    fireEvent.click(filterButton);
    
    // Select filter values
    const statusSelect = screen.getByLabelText('Status');
    fireEvent.mouseDown(statusSelect);
    const blockedOption = screen.getByText('Blocked');
    fireEvent.click(blockedOption);
    
    // Click Apply Filters button
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);
    
    // Check if onSearch was called with the current query
    expect(mockOnSearch).toHaveBeenCalledWith('+1234567890');
  });

  test('resets filters when Reset button is clicked', () => {
    render(<UserSearchBar onSearch={mockOnSearch} searchQuery="+1234567890" />);
    
    // Show filters
    const filterButton = screen.getByText('Show Filters');
    fireEvent.click(filterButton);
    
    // Click Reset button
    const resetButton = screen.getByText('Reset');
    fireEvent.click(resetButton);
    
    // Check if onSearch was called with empty string
    expect(mockOnSearch).toHaveBeenCalledWith('');
    
    // Check if the input value is cleared
    const searchInput = screen.getByPlaceholderText('Search by phone number, date, or request count...');
    expect(searchInput).toHaveValue('');
  });
});