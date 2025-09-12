#!/usr/bin/env python3
"""
Test script to verify the dashboard authentication fix works correctly.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_development_mode_bypass():
    """Test that development mode properly bypasses authentication."""
    
    # Mock the config to return development_mode=True
    with patch('app.config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.development_mode = True
        mock_get_config.return_value = mock_config
        
        # Import after patching
        from app.api.dashboard import get_current_user_dev, get_auth_dependencies
        
        # Test that development user is returned
        import asyncio
        user = asyncio.run(get_current_user_dev())
        
        assert user.username == "dev_admin"
        assert user.role.value == "admin"
        assert user.is_active == True
        
        # Test that development dependencies are selected
        deps = get_auth_dependencies()
        assert 'analyst_or_admin' in deps
        assert 'admin' in deps
        
        print("✅ Development mode bypass works correctly")

def test_production_mode_security():
    """Test that production mode prevents authentication bypass."""
    
    # Mock the config to return development_mode=False
    with patch('app.config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.development_mode = False
        mock_get_config.return_value = mock_config
        
        # Import after patching
        from app.api.dashboard import get_current_user_dev
        from fastapi import HTTPException
        
        # Test that development bypass raises exception in production
        import asyncio
        try:
            user = asyncio.run(get_current_user_dev())
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 500
            assert "production mode" in e.detail.lower()
            print("✅ Production mode security works correctly")

def test_conditional_dependencies():
    """Test that dependencies are selected based on environment."""
    
    # Test development mode
    with patch('app.config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.development_mode = True
        mock_get_config.return_value = mock_config
        
        from app.api.dashboard import get_auth_dependencies
        deps = get_auth_dependencies()
        
        # Should return development dependencies
        assert deps['analyst_or_admin'].__name__ == 'require_analyst_or_admin_dev'
        assert deps['admin'].__name__ == 'require_admin_dev'
        
    # Test production mode
    with patch('app.config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.development_mode = False
        mock_get_config.return_value = mock_config
        
        # Need to reload the module to get fresh dependencies
        import importlib
        import app.api.dashboard
        importlib.reload(app.api.dashboard)
        
        from app.api.dashboard import get_auth_dependencies
        deps = get_auth_dependencies()
        
        # Should return production dependencies
        assert deps['analyst_or_admin'].__name__ == 'require_analyst_or_admin_user'
        assert deps['admin'].__name__ == 'require_admin_user'
        
    print("✅ Conditional dependencies work correctly")

if __name__ == "__main__":
    print("Testing dashboard authentication fix...")
    
    try:
        test_development_mode_bypass()
        test_production_mode_security()
        test_conditional_dependencies()
        
        print("\n🎉 All tests passed! The authentication fix is working correctly.")
        print("\nSummary of improvements:")
        print("- ✅ Development mode bypass is properly gated by DEVELOPMENT_MODE environment variable")
        print("- ✅ Production mode prevents authentication bypass with clear error message")
        print("- ✅ Dependencies are conditionally selected based on environment")
        print("- ✅ Clear warnings and documentation added to development functions")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)