import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ReportTemplates from '../ReportTemplates';
import { ReportTemplate } from '../types';

describe('ReportTemplates Component', () => {
  const mockTemplates: ReportTemplate[] = [
    {
      id: '1',
      name: 'Monthly Usage Summary',
      description: 'Overview of system usage for the past month',
      report_type: 'usage_summary',
      default_parameters: {
        export_format: 'pdf'
      },
      icon: 'bar_chart'
    },
    {
      id: '2',
      name: 'Classification Breakdown',
      description: 'Detailed analysis of job ad classifications',
      report_type: 'classification_analysis',
      default_parameters: {
        export_format: 'xlsx'
      },
      icon: 'pie_chart'
    }
  ];
  
  const mockOnUseTemplate = jest.fn();
  const mockOnEditTemplate = jest.fn();
  const mockOnDeleteTemplate = jest.fn();
  const mockOnCreateTemplate = jest.fn();
  
  beforeEach(() => {
    mockOnUseTemplate.mockReset();
    mockOnEditTemplate.mockReset();
    mockOnDeleteTemplate.mockReset();
    mockOnCreateTemplate.mockReset();
  });

  test('renders templates correctly', () => {
    render(
      <ReportTemplates 
        templates={mockTemplates} 
        onUseTemplate={mockOnUseTemplate} 
      />
    );
    
    expect(screen.getByText('Report Templates')).toBeInTheDocument();
    expect(screen.getByText('Monthly Usage Summary')).toBeInTheDocument();
    expect(screen.getByText('Classification Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Overview of system usage for the past month')).toBeInTheDocument();
    expect(screen.getByText('Detailed analysis of job ad classifications')).toBeInTheDocument();
  });

  test('shows empty state when no templates are available', () => {
    render(
      <ReportTemplates 
        templates={[]} 
        onUseTemplate={mockOnUseTemplate} 
      />
    );
    
    expect(screen.getByText('No report templates available')).toBeInTheDocument();
  });

  test('calls onUseTemplate when Use Template button is clicked', () => {
    render(
      <ReportTemplates 
        templates={mockTemplates} 
        onUseTemplate={mockOnUseTemplate} 
      />
    );
    
    const useTemplateButtons = screen.getAllByText('Use Template');
    fireEvent.click(useTemplateButtons[0]);
    
    expect(mockOnUseTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnUseTemplate).toHaveBeenCalledWith(mockTemplates[0]);
  });

  test('shows edit and delete buttons when handlers are provided', () => {
    render(
      <ReportTemplates 
        templates={mockTemplates} 
        onUseTemplate={mockOnUseTemplate}
        onEditTemplate={mockOnEditTemplate}
        onDeleteTemplate={mockOnDeleteTemplate}
      />
    );
    
    // Check for edit and delete buttons (they contain SVG icons)
    const editButtons = document.querySelectorAll('[data-testid="EditIcon"]');
    const deleteButtons = document.querySelectorAll('[data-testid="DeleteIcon"]');
    
    expect(editButtons.length).toBe(2);
    expect(deleteButtons.length).toBe(2);
  });

  test('shows create template button when handler is provided', () => {
    render(
      <ReportTemplates 
        templates={mockTemplates} 
        onUseTemplate={mockOnUseTemplate}
        onCreateTemplate={mockOnCreateTemplate}
      />
    );
    
    const createButton = screen.getByText('Create Template');
    expect(createButton).toBeInTheDocument();
    
    fireEvent.click(createButton);
    expect(mockOnCreateTemplate).toHaveBeenCalledTimes(1);
  });

  test('shows create first template button in empty state when handler is provided', () => {
    render(
      <ReportTemplates 
        templates={[]} 
        onUseTemplate={mockOnUseTemplate}
        onCreateTemplate={mockOnCreateTemplate}
      />
    );
    
    const createButton = screen.getByText('Create Your First Template');
    expect(createButton).toBeInTheDocument();
    
    fireEvent.click(createButton);
    expect(mockOnCreateTemplate).toHaveBeenCalledTimes(1);
  });
});