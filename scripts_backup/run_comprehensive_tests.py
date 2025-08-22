#!/usr/bin/env python3
"""
Comprehensive test runner for Reality Checker WhatsApp Bot.

This script runs the complete test suite including unit tests, integration tests,
performance tests, and end-to-end tests with proper reporting.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Run comprehensive test suite."""
    print("Reality Checker WhatsApp Bot - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("app").exists() or not Path("tests").exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Test categories to run
    test_categories = [
        {
            "name": "Unit Tests - Data Models",
            "command": "python3 -m pytest tests/test_data_models.py -v --tb=short",
            "required": True
        },
        {
            "name": "Unit Tests - Services",
            "command": "python3 -m pytest tests/test_openai_analysis.py tests/test_twilio_response.py tests/test_pdf_processing.py -v --tb=short",
            "required": True
        },
        {
            "name": "Integration Tests - External Services",
            "command": "python3 -m pytest tests/test_integration.py -v --tb=short",
            "required": True
        },
        {
            "name": "Performance Tests - Concurrent Processing",
            "command": "python3 -m pytest tests/test_performance.py::TestAsyncServicePerformance -v --tb=short",
            "required": False
        },
        {
            "name": "Test Fixtures Validation",
            "command": "python3 -c \"from tests.fixtures.job_ad_samples import JobAdFixtures; from tests.fixtures.pdf_samples import PDFFixtures; print('Fixtures loaded successfully')\"",
            "required": True
        },
        {
            "name": "Security Tests",
            "command": "python3 -m pytest tests/test_security.py -v --tb=short",
            "required": True
        },
        {
            "name": "Error Handling Tests",
            "command": "python3 -m pytest tests/test_error_handling.py -v --tb=short",
            "required": True
        }
    ]
    
    # Track results
    results = []
    total_tests = len(test_categories)
    passed_tests = 0
    
    # Run each test category
    for i, test_category in enumerate(test_categories, 1):
        print(f"\n[{i}/{total_tests}] {test_category['name']}")
        
        success = run_command(test_category['command'], test_category['name'])
        results.append({
            'name': test_category['name'],
            'success': success,
            'required': test_category['required']
        })
        
        if success:
            passed_tests += 1
            print(f"✅ {test_category['name']} - PASSED")
        else:
            print(f"❌ {test_category['name']} - FAILED")
            if test_category['required']:
                print(f"⚠️  This is a required test category!")
    
    # Summary report
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    print(f"Total test categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        required = "(Required)" if result['required'] else "(Optional)"
        print(f"  {status} {result['name']} {required}")
    
    # Check for critical failures
    required_failures = [r for r in results if not r['success'] and r['required']]
    if required_failures:
        print(f"\n⚠️  CRITICAL: {len(required_failures)} required test categories failed!")
        print("The following required tests must pass:")
        for failure in required_failures:
            print(f"  - {failure['name']}")
        return False
    
    print(f"\n🎉 Comprehensive test suite completed successfully!")
    print(f"All required tests passed. Optional test failures (if any) can be addressed separately.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)