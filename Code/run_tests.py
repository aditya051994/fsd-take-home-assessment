#!/usr/bin/env python
"""
Comprehensive test runner for Event Sync Service
Runs all unit and integration tests with detailed reporting
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def print_section(text):
    """Print formatted section"""
    print("\n" + "-"*80)
    print(f"  {text}")
    print("-"*80 + "\n")


def run_tests():
    """Run all tests and generate report"""
    print_header("EVENT SYNC SERVICE - COMPREHENSIVE TEST SUITE")
    
    print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {Path.cwd()}")
    
    test_dirs = [
        ("Unit Tests - Reconciler", ["tests/test_reconciler.py", "-v", "--tb=short"]),
        ("Integration Tests - API", ["tests/test_main.py", "-v", "--tb=short"]),
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for test_name, pytest_args in test_dirs:
        print_section(test_name)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest"] + pytest_args,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr)
            
            results[test_name] = result.returncode == 0
            
            # Parse output for counts
            stdout = result.stdout
            if "passed" in stdout:
                # Extract test counts from pytest output
                import re
                match = re.search(r'(\d+) passed', stdout)
                if match:
                    total_passed += int(match.group(1))
                match = re.search(r'(\d+) failed', stdout)
                if match:
                    total_failed += int(match.group(1))
                match = re.search(r'(\d+) skipped', stdout)
                if match:
                    total_skipped += int(match.group(1))
        
        except subprocess.TimeoutExpired:
            print(f"❌ Tests timed out!")
            results[test_name] = False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            results[test_name] = False
    
    # Print summary
    print_header("TEST SUMMARY")
    
    print(f"Total Passed:  {total_passed} ✅")
    print(f"Total Failed:  {total_failed} ❌")
    print(f"Total Skipped: {total_skipped} ⊘")
    print()
    
    print("Test Suites:")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print()
    
    all_passed = all(results.values())
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Please review the output above")
        return 1


def print_test_info():
    """Print information about tests"""
    print_header("TEST COVERAGE INFORMATION")
    
    coverage_info = {
        "Unit Tests (test_reconciler.py)": [
            "✓ Date normalization (5 tests)",
            "✓ DateTime extraction (4 tests)",
            "✓ String similarity scoring (5 tests)",
            "✓ Time overlap detection (4 tests)",
            "✓ Client matching (3 tests)",
            "✓ Conflict detection (4 tests)",
            "✓ Full reconciliation (3 tests)",
            "✓ Real data reconciliation (4 tests)",
            "Total: 32 unit tests"
        ],
        "Integration Tests (test_main.py)": [
            "✓ Health check endpoint (2 tests)",
            "✓ Summary endpoint (4 tests)",
            "✓ Meetings list endpoint (6 tests)",
            "✓ Meeting detail endpoint (2 tests)",
            "✓ Conflicts endpoint (3 tests)",
            "✓ Statistics endpoint (3 tests)",
            "✓ Raw data endpoints (2 tests)",
            "✓ Grouping endpoints (2 tests)",
            "✓ Error handling (2 tests)",
            "✓ CORS headers (1 test)",
            "✓ Response formats (2 tests)",
            "✓ Data consistency (3 tests)",
            "Total: 32 integration tests"
        ]
    }
    
    for category, tests in coverage_info.items():
        print(f"\n{category}")
        for test in tests:
            print(f"  {test}")
    
    print()
    print("Total Test Cases: 64")
    print()


if __name__ == "__main__":
    print_test_info()
    exit_code = run_tests()
    print_header("TEST RUN COMPLETE")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(exit_code)
