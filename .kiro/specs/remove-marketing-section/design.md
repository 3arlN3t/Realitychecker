# Design Document

## Overview

This design outlines the removal of the "AI-Powered Job Scam Detection" marketing section from the user interface. The section currently appears in the `direct_test.html` template and contains promotional content including a hero title, subtitle, and statistics grid that doesn't serve a functional purpose in the application.

## Architecture

The marketing section removal involves:
- **Template Layer**: Removing HTML elements from `templates/direct_test.html`
- **Styling Layer**: Removing associated CSS styles that are no longer needed
- **Layout Adjustment**: Ensuring proper spacing and visual hierarchy after removal

## Components and Interfaces

### Affected Files

1. **templates/direct_test.html**
   - Contains the hero section HTML structure
   - Includes embedded CSS styles for the marketing section
   - Location: Lines ~508-530 (hero section HTML) and lines ~83-130 (CSS styles)

2. **CSS Styles to Remove**
   - `.hero-section` - Main container styling
   - `.hero-title` - Title styling with gradient effect
   - `.hero-subtitle` - Subtitle text styling
   - `.stats-grid` - Grid layout for statistics
   - `.stat-card` - Individual statistic card styling
   - `.stat-number` - Large number display
   - `.stat-label` - Label text under numbers

### HTML Structure to Remove

```html
<section class="hero-section">
    <h1 class="hero-title">AI-Powered Job Scam Detection</h1>
    <p class="hero-subtitle">
        Protect yourself from fraudulent job postings with our advanced AI analysis. 
        Get instant trust scores and detailed risk assessments for any job advertisement.
    </p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-number">97.3%</span>
            <div class="stat-label">Detection Accuracy</div>
        </div>
        <!-- Additional stat cards -->
    </div>
</section>
```

## Data Models

No data models are affected by this change as it's purely a UI modification.

## Error Handling

### Potential Issues
1. **Layout Disruption**: Removing the section might affect spacing
2. **CSS Conflicts**: Unused CSS might remain and cause conflicts
3. **Visual Hierarchy**: The remaining content needs proper visual balance

### Mitigation Strategies
1. **Gradual Removal**: Remove HTML first, then clean up CSS
2. **Visual Testing**: Verify layout integrity after removal
3. **CSS Cleanup**: Remove all associated styles to prevent conflicts

## Testing Strategy

### Manual Testing
1. **Visual Verification**: Ensure the marketing section is completely removed
2. **Layout Testing**: Verify proper spacing and alignment of remaining elements
3. **Responsive Testing**: Check layout on different screen sizes
4. **Cross-browser Testing**: Ensure consistent appearance across browsers

### Test Cases
1. **Removal Verification**: Marketing section should not be visible
2. **Layout Integrity**: Analysis results should display properly
3. **Spacing Consistency**: No awkward gaps or overlapping elements
4. **Functionality Preservation**: All existing functionality should work unchanged

### Acceptance Criteria Validation
- Verify no "AI-Powered Job Scam Detection" text appears
- Confirm analysis details are prominently displayed
- Ensure proper visual hierarchy is maintained
- Validate clean code with no unused references