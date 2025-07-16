import React from 'react';
import { render, screen } from '@testing-library/react';
import ConfigSection from '../ConfigSection';

describe('ConfigSection', () => {
  test('renders title correctly', () => {
    render(<ConfigSection title="Test Section">Content</ConfigSection>);
    
    expect(screen.getByText('Test Section')).toBeInTheDocument();
  });

  test('renders children content', () => {
    render(
      <ConfigSection title="Test Section">
        <div data-testid="test-content">Test Content</div>
      </ConfigSection>
    );
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});