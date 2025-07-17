"""
Accessibility utilities for WCAG 2.1 AA compliance and inclusive design.

This module provides utilities for improving accessibility across the application,
including color contrast checking, focus management, screen reader support,
and keyboard navigation helpers.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import colorsys
import logging

from app.utils.logging import get_logger

logger = get_logger(__name__)


class ContrastLevel(Enum):
    """WCAG contrast level requirements."""
    AA_NORMAL = 4.5  # WCAG AA for normal text
    AA_LARGE = 3.0   # WCAG AA for large text (18pt+ or 14pt+ bold)
    AAA_NORMAL = 7.0 # WCAG AAA for normal text
    AAA_LARGE = 4.5  # WCAG AAA for large text


@dataclass
class ColorContrastResult:
    """Result of color contrast analysis."""
    ratio: float
    passes_aa_normal: bool
    passes_aa_large: bool
    passes_aaa_normal: bool
    passes_aaa_large: bool
    recommendation: str


@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found in content."""
    severity: str  # 'error', 'warning', 'info'
    guideline: str  # WCAG guideline reference
    description: str
    element: Optional[str] = None
    suggestion: Optional[str] = None


class AccessibilityChecker:
    """Comprehensive accessibility checker for WCAG 2.1 compliance."""
    
    def __init__(self):
        """Initialize accessibility checker."""
        self.issues: List[AccessibilityIssue] = []
        
    def check_color_contrast(self, foreground: str, background: str) -> ColorContrastResult:
        """
        Check color contrast ratio according to WCAG guidelines.
        
        Args:
            foreground: Foreground color (hex, rgb, or color name)
            background: Background color (hex, rgb, or color name)
            
        Returns:
            ColorContrastResult with analysis
        """
        try:
            # Convert colors to RGB
            fg_rgb = self._parse_color(foreground)
            bg_rgb = self._parse_color(background)
            
            # Calculate contrast ratio
            ratio = self._calculate_contrast_ratio(fg_rgb, bg_rgb)
            
            # Check against WCAG levels
            passes_aa_normal = ratio >= ContrastLevel.AA_NORMAL.value
            passes_aa_large = ratio >= ContrastLevel.AA_LARGE.value
            passes_aaa_normal = ratio >= ContrastLevel.AAA_NORMAL.value
            passes_aaa_large = ratio >= ContrastLevel.AAA_LARGE.value
            
            # Generate recommendation
            recommendation = self._generate_contrast_recommendation(
                ratio, passes_aa_normal, passes_aa_large
            )
            
            return ColorContrastResult(
                ratio=ratio,
                passes_aa_normal=passes_aa_normal,
                passes_aa_large=passes_aa_large,
                passes_aaa_normal=passes_aaa_normal,
                passes_aaa_large=passes_aaa_large,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error checking color contrast: {e}")
            return ColorContrastResult(
                ratio=0.0,
                passes_aa_normal=False,
                passes_aa_large=False,
                passes_aaa_normal=False,
                passes_aaa_large=False,
                recommendation="Unable to analyze contrast - please verify colors manually"
            )
    
    def validate_text_content(self, text: str) -> List[AccessibilityIssue]:
        """
        Validate text content for accessibility issues.
        
        Args:
            text: Text content to validate
            
        Returns:
            List of accessibility issues found
        """
        issues = []
        
        # Check for appropriate heading structure
        headings = re.findall(r'<h([1-6])[^>]*>', text, re.IGNORECASE)
        if headings:
            issues.extend(self._check_heading_structure(headings))
        
        # Check for missing alt text in images
        images = re.findall(r'<img[^>]*>', text, re.IGNORECASE)
        for img in images:
            if 'alt=' not in img.lower():
                issues.append(AccessibilityIssue(
                    severity='error',
                    guideline='WCAG 1.1.1',
                    description='Image missing alt text',
                    element=img[:50] + '...' if len(img) > 50 else img,
                    suggestion='Add meaningful alt text describing the image content'
                ))
        
        # Check for empty links
        links = re.findall(r'<a[^>]*>([^<]*)</a>', text, re.IGNORECASE)
        for link_text in links:
            if not link_text.strip():
                issues.append(AccessibilityIssue(
                    severity='error',
                    guideline='WCAG 2.4.4',
                    description='Empty link text',
                    suggestion='Provide descriptive link text that explains the link destination'
                ))
        
        # Check for generic link text
        generic_patterns = ['click here', 'read more', 'more', 'here', 'link']
        for link_text in links:
            if link_text.lower().strip() in generic_patterns:
                issues.append(AccessibilityIssue(
                    severity='warning',
                    guideline='WCAG 2.4.4',
                    description=f'Generic link text: "{link_text}"',
                    suggestion='Use descriptive link text that makes sense out of context'
                ))
        
        # Check for missing form labels
        inputs = re.findall(r'<input[^>]*>', text, re.IGNORECASE)
        for input_tag in inputs:
            if 'aria-label=' not in input_tag.lower() and 'aria-labelledby=' not in input_tag.lower():
                # Look for associated label
                input_id = re.search(r'id=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                if input_id:
                    label_pattern = f'<label[^>]*for=["\']?{input_id.group(1)}["\']?[^>]*>'
                    if not re.search(label_pattern, text, re.IGNORECASE):
                        issues.append(AccessibilityIssue(
                            severity='error',
                            guideline='WCAG 1.3.1',
                            description='Form input missing label',
                            element=input_tag[:50] + '...' if len(input_tag) > 50 else input_tag,
                            suggestion='Add a label element or aria-label attribute'
                        ))
        
        return issues
    
    def generate_focus_outline_styles(self, primary_color: str = '#1976d2') -> Dict[str, str]:
        """
        Generate WCAG-compliant focus outline styles.
        
        Args:
            primary_color: Primary color for focus indicators
            
        Returns:
            Dictionary of CSS styles for focus indicators
        """
        return {
            'outline': f'2px solid {primary_color}',
            'outline-offset': '2px',
            'border-radius': '4px',
            'box-shadow': f'0 0 0 2px rgba(25, 118, 210, 0.2)',
        }
    
    def generate_skip_navigation_html(self) -> str:
        """
        Generate HTML for skip navigation links.
        
        Returns:
            HTML string for skip navigation
        """
        return '''
        <nav aria-label="Skip links" class="skip-navigation">
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
            <a href="#search" class="skip-link">Skip to search</a>
        </nav>
        '''
    
    def create_aria_live_region_html(self) -> str:
        """
        Create ARIA live region for dynamic content announcements.
        
        Returns:
            HTML string for ARIA live region
        """
        return '''
        <div id="aria-live-polite" aria-live="polite" aria-atomic="true" class="sr-only"></div>
        <div id="aria-live-assertive" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
        '''
    
    def validate_keyboard_navigation(self, interactive_elements: List[str]) -> List[AccessibilityIssue]:
        """
        Validate keyboard navigation accessibility.
        
        Args:
            interactive_elements: List of interactive element HTML
            
        Returns:
            List of keyboard navigation issues
        """
        issues = []
        
        for element in interactive_elements:
            # Check for missing tabindex on custom interactive elements
            if any(tag in element.lower() for tag in ['<div', '<span']) and 'onclick=' in element.lower():
                if 'tabindex=' not in element.lower():
                    issues.append(AccessibilityIssue(
                        severity='error',
                        guideline='WCAG 2.1.1',
                        description='Interactive element not keyboard accessible',
                        element=element[:50] + '...' if len(element) > 50 else element,
                        suggestion='Add tabindex="0" and keyboard event handlers'
                    ))
            
            # Check for positive tabindex values (anti-pattern)
            tabindex_match = re.search(r'tabindex=["\']?(\d+)["\']?', element, re.IGNORECASE)
            if tabindex_match and int(tabindex_match.group(1)) > 0:
                issues.append(AccessibilityIssue(
                    severity='warning',
                    guideline='WCAG 2.4.3',
                    description='Positive tabindex disrupts natural tab order',
                    element=element[:50] + '...' if len(element) > 50 else element,
                    suggestion='Use tabindex="0" for focusable elements or remove tabindex'
                ))
        
        return issues
    
    def _parse_color(self, color: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple."""
        color = color.strip()
        
        # Handle hex colors
        if color.startswith('#'):
            hex_color = color[1:]
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Handle rgb() colors
        if color.startswith('rgb('):
            rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color)
            if rgb_match:
                return tuple(int(x) for x in rgb_match.groups())
        
        # Handle named colors (basic set)
        named_colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128),
        }
        
        if color.lower() in named_colors:
            return named_colors[color.lower()]
        
        # Default to black if parsing fails
        logger.warning(f"Could not parse color: {color}, defaulting to black")
        return (0, 0, 0)
    
    def _calculate_contrast_ratio(self, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two RGB colors."""
        def get_relative_luminance(rgb):
            """Calculate relative luminance according to WCAG formula."""
            r, g, b = [x / 255.0 for x in rgb]
            
            def gamma_correct(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = map(gamma_correct, [r, g, b])
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_relative_luminance(rgb1)
        lum2 = get_relative_luminance(rgb2)
        
        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _generate_contrast_recommendation(self, ratio: float, passes_aa_normal: bool, passes_aa_large: bool) -> str:
        """Generate recommendation based on contrast ratio."""
        if passes_aa_normal:
            return f"Excellent contrast ratio ({ratio:.2f}:1) - meets WCAG AA standards"
        elif passes_aa_large:
            return f"Good contrast ratio ({ratio:.2f}:1) - suitable for large text only"
        else:
            return f"Poor contrast ratio ({ratio:.2f}:1) - fails WCAG AA standards. Minimum required is 4.5:1 for normal text, 3:1 for large text"
    
    def _check_heading_structure(self, headings: List[str]) -> List[AccessibilityIssue]:
        """Check heading hierarchy for proper structure."""
        issues = []
        prev_level = 0
        
        for heading in headings:
            level = int(heading)
            
            # Check for skipped heading levels
            if level > prev_level + 1:
                issues.append(AccessibilityIssue(
                    severity='warning',
                    guideline='WCAG 1.3.1',
                    description=f'Heading hierarchy skip: h{prev_level} to h{level}',
                    suggestion='Use heading levels in sequential order (h1, h2, h3, etc.)'
                ))
            
            prev_level = level
        
        return issues


class ScreenReaderHelper:
    """Helper utilities for screen reader optimization."""
    
    @staticmethod
    def create_sr_only_text(text: str) -> str:
        """
        Create screen reader only text.
        
        Args:
            text: Text to make screen reader only
            
        Returns:
            HTML span with screen reader only styling
        """
        return f'<span class="sr-only">{text}</span>'
    
    @staticmethod
    def create_aria_label(element_type: str, description: str) -> str:
        """
        Create appropriate ARIA label for element.
        
        Args:
            element_type: Type of element (button, link, input, etc.)
            description: Description of element purpose
            
        Returns:
            ARIA label string
        """
        return f'aria-label="{element_type}: {description}"'
    
    @staticmethod
    def announce_dynamic_content(message: str, priority: str = 'polite') -> str:
        """
        Generate JavaScript to announce dynamic content changes.
        
        Args:
            message: Message to announce
            priority: ARIA live priority ('polite' or 'assertive')
            
        Returns:
            JavaScript code for announcement
        """
        return f'''
        (function() {{
            const liveRegion = document.getElementById('aria-live-{priority}');
            if (liveRegion) {{
                liveRegion.textContent = '{message}';
                setTimeout(() => liveRegion.textContent = '', 1000);
            }}
        }})();
        '''


class KeyboardNavigationHelper:
    """Helper utilities for keyboard navigation."""
    
    @staticmethod
    def create_focus_trap_js() -> str:
        """
        Generate JavaScript for focus trapping in modals.
        
        Returns:
            JavaScript code for focus trapping
        """
        return '''
        function createFocusTrap(container) {
            const focusableElements = container.querySelectorAll(
                'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            function trapFocus(e) {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            lastElement.focus();
                            e.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            firstElement.focus();
                            e.preventDefault();
                        }
                    }
                }
                if (e.key === 'Escape') {
                    container.remove();
                }
            }
            
            container.addEventListener('keydown', trapFocus);
            firstElement.focus();
            
            return function removeFocusTrap() {
                container.removeEventListener('keydown', trapFocus);
            };
        }
        '''
    
    @staticmethod
    def create_skip_link_styles() -> str:
        """
        Generate CSS for skip navigation links.
        
        Returns:
            CSS styles for skip links
        """
        return '''
        .skip-navigation {
            position: absolute;
            top: 0;
            left: 0;
            z-index: 10000;
        }
        
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            transition: top 0.2s ease;
        }
        
        .skip-link:focus {
            top: 6px;
            outline: 2px solid #1976d2;
            outline-offset: 2px;
        }
        
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        '''


# Global accessibility checker instance
_accessibility_checker: Optional[AccessibilityChecker] = None


def get_accessibility_checker() -> AccessibilityChecker:
    """Get global accessibility checker instance."""
    global _accessibility_checker
    if _accessibility_checker is None:
        _accessibility_checker = AccessibilityChecker()
    return _accessibility_checker


def validate_ui_accessibility(html_content: str, interactive_elements: List[str]) -> Dict[str, Any]:
    """
    Perform comprehensive UI accessibility validation.
    
    Args:
        html_content: HTML content to validate
        interactive_elements: List of interactive element HTML
        
    Returns:
        Dictionary with validation results
    """
    checker = get_accessibility_checker()
    
    # Validate text content
    text_issues = checker.validate_text_content(html_content)
    
    # Validate keyboard navigation
    keyboard_issues = checker.validate_keyboard_navigation(interactive_elements)
    
    # Combine all issues
    all_issues = text_issues + keyboard_issues
    
    # Categorize issues by severity
    errors = [issue for issue in all_issues if issue.severity == 'error']
    warnings = [issue for issue in all_issues if issue.severity == 'warning']
    info = [issue for issue in all_issues if issue.severity == 'info']
    
    return {
        'total_issues': len(all_issues),
        'errors': len(errors),
        'warnings': len(warnings),
        'info': len(info),
        'issues': all_issues,
        'compliance_score': max(0, 100 - (len(errors) * 10) - (len(warnings) * 5) - (len(info) * 1)),
        'recommendations': [
            'Add proper heading structure (h1-h6)',
            'Ensure all images have meaningful alt text',
            'Provide descriptive link text',
            'Add labels to all form inputs',
            'Implement keyboard navigation support',
            'Test with screen readers',
            'Verify color contrast ratios'
        ]
    }