#!/usr/bin/env python3
"""
Test script for new_driver.py - Basic functionality test
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_new_driver_import():
    """Test that new_driver imports successfully"""
    try:
        import new_driver
        print("✅ new_driver.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_hybrid_report_generator():
    """Test that HybridReportGenerator can be instantiated"""
    try:
        from new_driver import HybridReportGenerator
        
        # Create instance (without Groq client for testing)
        generator = HybridReportGenerator()
        print("✅ HybridReportGenerator instantiated successfully")
        
        # Test method existence
        methods_to_check = [
            '_generate_earnings_summary',
            '_get_economic_indicators',
            '_get_ticker_headlines',
            '_get_ticker_earnings',
            '_format_complete_brief'
        ]
        
        for method in methods_to_check:
            if hasattr(generator, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ HybridReportGenerator test failed: {e}")
        return False

def test_pipeline_functions():
    """Test that pipeline orchestration functions exist"""
    try:
        import new_driver
        
        functions_to_check = [
            'run_earnings_calendar',
            'run_news_scraper',
            'run_news_csv_updater',
            'run_ticker_list_gen',
            'run_pipeline_orchestration',
            'generate_morning_brief_report'
        ]
        
        for func in functions_to_check:
            if hasattr(new_driver, func):
                print(f"✅ Function {func} exists")
            else:
                print(f"❌ Function {func} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Pipeline functions test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("TESTING NEW_DRIVER.PY")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Import
    print("\n1. Testing import...")
    if not test_new_driver_import():
        all_tests_passed = False
    
    # Test 2: HybridReportGenerator
    print("\n2. Testing HybridReportGenerator...")
    if not test_hybrid_report_generator():
        all_tests_passed = False
    
    # Test 3: Pipeline functions
    print("\n3. Testing pipeline functions...")
    if not test_pipeline_functions():
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print("new_driver.py is ready for execution!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the issues above")
    print("=" * 50)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
