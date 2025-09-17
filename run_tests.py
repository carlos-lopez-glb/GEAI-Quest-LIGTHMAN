#!/usr/bin/env python3
"""
LIGHTMAN Test Runner

Comprehensive test suite for the MiniTel-Lite infiltration system.
Executes all tests and generates coverage reports.

Usage:
    python run_tests.py [--coverage] [--verbose]
"""

import sys
import unittest
import argparse
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def discover_tests():
    """Discover all test modules"""
    test_dir = Path(__file__).parent / 'src' / 'tests'
    loader = unittest.TestLoader()
    
    # Discover all test files
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern='test_*.py',
        top_level_dir=str(Path(__file__).parent / 'src')
    )
    
    return suite


def run_tests_with_coverage():
    """Run tests with coverage analysis"""
    try:
        import coverage
    except ImportError:
        print("❌ Coverage module not installed. Install with: pip install coverage")
        return False
    
    # Initialize coverage
    cov = coverage.Coverage(
        source=['minitel', 'session', 'tui'],
        omit=['*/tests/*', '*/test_*']
    )
    
    cov.start()
    
    # Run tests
    suite = discover_tests()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*60)
    print("📊 COVERAGE REPORT")
    print("="*60)
    
    # Generate console report
    cov.report(show_missing=True)
    
    # Generate HTML report
    html_dir = Path(__file__).parent / 'htmlcov'
    cov.html_report(directory=str(html_dir))
    print(f"\n📄 HTML coverage report generated: {html_dir}/index.html")
    
    # Check if we meet the 80% requirement
    total_coverage = cov.report(show_missing=False)
    
    if total_coverage >= 80.0:
        print(f"✅ Coverage requirement met: {total_coverage:.1f}% >= 80%")
        return result.wasSuccessful()
    else:
        print(f"❌ Coverage requirement not met: {total_coverage:.1f}% < 80%")
        return False


def run_tests_basic(verbose=False):
    """Run tests without coverage"""
    suite = discover_tests()
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result.wasSuccessful()


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    try:
        import curses
    except ImportError:
        missing.append("curses (usually built-in on Unix systems)")
    
    try:
        import socket
        import threading
        import json
        import pathlib
    except ImportError as e:
        missing.append(f"Standard library module: {e}")
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        return False
    
    return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="LIGHTMAN Test Runner")
    parser.add_argument('--coverage', action='store_true', 
                       help='Run tests with coverage analysis')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose test output')
    
    args = parser.parse_args()
    
    print("🧪 LIGHTMAN Mission Test Suite")
    print("="*50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All dependencies available")
    
    # Run tests
    print("\n🚀 Running tests...")
    
    if args.coverage:
        success = run_tests_with_coverage()
    else:
        success = run_tests_basic(args.verbose)
    
    # Results
    print("\n" + "="*50)
    if success:
        print("✅ ALL TESTS PASSED - Mission systems operational")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Mission systems require attention")
        sys.exit(1)


if __name__ == '__main__':
    main()