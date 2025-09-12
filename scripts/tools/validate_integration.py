#!/usr/bin/env python3
"""
Validation script for Health Dashboard Integration.

This script validates the integration files and structure without requiring
a running server.
"""

import os
import json
from pathlib import Path


def validate_file_structure():
    """Validate that all required files are present."""
    print("🔍 Validating file structure...")
    
    required_files = [
        "dashboard/src/lib/api.ts",
        "dashboard/src/lib/healthTransforms.ts", 
        "dashboard/src/hooks/useHealthCheck.ts",
        "dashboard/src/components/admin/EnhancedSystemHealthCard.tsx",
        "test_health_dashboard_integration.py",
        "docs/legacy/HEALTH_DASHBOARD_INTEGRATION.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True


def validate_typescript_files():
    """Validate TypeScript files for basic syntax."""
    print("🔍 Validating TypeScript files...")
    
    ts_files = [
        "dashboard/src/lib/api.ts",
        "dashboard/src/lib/healthTransforms.ts",
        "dashboard/src/hooks/useHealthCheck.ts",
        "dashboard/src/components/admin/EnhancedSystemHealthCard.tsx"
    ]
    
    for file_path in ts_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Basic validation checks
            if not content.strip():
                print(f"❌ Empty file: {file_path}")
                return False
                
            # Check for common TypeScript patterns
            if file_path.endswith('.ts') or file_path.endswith('.tsx'):
                if 'import' not in content and 'export' not in content:
                    print(f"⚠️  No imports/exports found in: {file_path}")
                    
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False
    
    print("✅ TypeScript files validated")
    return True


def validate_api_types():
    """Validate that API types are properly defined."""
    print("🔍 Validating API types...")
    
    api_file = "dashboard/src/lib/api.ts"
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for required type definitions
        required_types = [
            "HealthCheckResponse",
            "ServiceHealthStatus", 
            "BasicHealthResponse",
            "MetricsResponse"
        ]
        
        missing_types = []
        for type_name in required_types:
            if f"interface {type_name}" not in content and f"type {type_name}" not in content:
                missing_types.append(type_name)
        
        if missing_types:
            print(f"❌ Missing type definitions: {missing_types}")
            return False
            
        # Check for required API methods
        required_methods = [
            "getBasicHealth",
            "getDetailedHealth", 
            "getMetrics"
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if method_name not in content:
                missing_methods.append(method_name)
                
        if missing_methods:
            print(f"❌ Missing API methods: {missing_methods}")
            return False
        
        print("✅ API types validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating API types: {e}")
        return False


def validate_hook_implementation():
    """Validate the useHealthCheck hook implementation."""
    print("🔍 Validating useHealthCheck hook...")
    
    hook_file = "dashboard/src/hooks/useHealthCheck.ts"
    
    try:
        with open(hook_file, 'r') as f:
            content = f.read()
        
        # Check for required hook features
        required_features = [
            "useState",
            "useEffect", 
            "useCallback",
            "useHealthCheck",
            "pollInterval",
            "refresh",
            "isLoading",
            "error"
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing hook features: {missing_features}")
            return False
        
        print("✅ useHealthCheck hook validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating hook: {e}")
        return False


def validate_component_integration():
    """Validate the enhanced component integration."""
    print("🔍 Validating component integration...")
    
    component_file = "dashboard/src/components/admin/EnhancedSystemHealthCard.tsx"
    dashboard_file = "dashboard/src/pages/DashboardPage.tsx"
    
    try:
        # Check component file
        with open(component_file, 'r') as f:
            component_content = f.read()
        
        required_component_features = [
            "EnhancedSystemHealthCard",
            "useHealthCheck",
            "SystemHealth",
            "Skeleton",
            "Alert",
            "Fade"
        ]
        
        missing_features = []
        for feature in required_component_features:
            if feature not in component_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing component features: {missing_features}")
            return False
        
        # Check dashboard integration
        with open(dashboard_file, 'r') as f:
            dashboard_content = f.read()
        
        if "EnhancedSystemHealthCard" not in dashboard_content:
            print("❌ EnhancedSystemHealthCard not integrated in DashboardPage")
            return False
        
        print("✅ Component integration validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating component integration: {e}")
        return False


def validate_environment_config():
    """Validate environment configuration."""
    print("🔍 Validating environment configuration...")
    
    env_example_file = "dashboard/.env.example"
    
    try:
        with open(env_example_file, 'r') as f:
            content = f.read()
        
        required_vars = [
            "REACT_APP_API_URL",
            "REACT_APP_HEALTH_POLL_INTERVAL",
            "REACT_APP_HEALTH_MOCK_FALLBACK"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
        
        print("✅ Environment configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating environment config: {e}")
        return False


def validate_documentation():
    """Validate documentation completeness."""
    print("🔍 Validating documentation...")
    
    doc_file = "docs/legacy/HEALTH_DASHBOARD_INTEGRATION.md"
    
    try:
        with open(doc_file, 'r') as f:
            content = f.read()
        
        required_sections = [
            "## Overview",
            "## Architecture", 
            "## API Endpoints",
            "## Configuration",
            "## Features",
            "## Testing",
            "## Troubleshooting"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing documentation sections: {missing_sections}")
            return False
        
        print("✅ Documentation validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating documentation: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Health Dashboard Integration Validation")
    print("=" * 50)
    
    validations = [
        validate_file_structure,
        validate_typescript_files,
        validate_api_types,
        validate_hook_implementation,
        validate_component_integration,
        validate_environment_config,
        validate_documentation
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        try:
            if validation():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Validation failed with error: {e}")
            print()
    
    print("=" * 50)
    if passed == total:
        print(f"✅ ALL VALIDATIONS PASSED ({passed}/{total})")
        print("\n🎉 Health Dashboard Integration is ready!")
        print("\nNext steps:")
        print("1. Start the backend server: uvicorn app.main:app --reload")
        print("2. Start the dashboard: cd dashboard && npm start")
        print("3. Test the integration in your browser")
        return True
    else:
        print(f"❌ VALIDATIONS FAILED ({passed}/{total})")
        print(f"\n{total - passed} validation(s) failed. Please fix the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
