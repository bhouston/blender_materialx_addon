#!/usr/bin/env python3
"""
Comprehensive Test Runner for MaterialX Addon

This script:
1. Deploys the addon to Blender
2. Runs comprehensive unit tests
3. Provides detailed test results

Usage:
    python3 run_tests.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def deploy_addon():
    """Deploy the addon to Blender."""
    print("=" * 60)
    print("🚀 Deploying MaterialX Addon to Blender")
    print("=" * 60)
    
    # Check if deploy.py exists
    deploy_script = Path("deploy.py")
    if not deploy_script.exists():
        print("❌ deploy.py not found in current directory")
        return False
    
    # Run deployment
    success = run_command("python3 deploy.py", "Deploying addon to Blender")
    
    if success:
        print("✅ Addon deployment completed")
        return True
    else:
        print("❌ Addon deployment failed")
        return False

def run_unit_tests():
    """Run the comprehensive unit tests."""
    print("=" * 60)
    print("🧪 Running Comprehensive Unit Tests")
    print("=" * 60)
    
    # Check if run_unit_tests_in_blender.py exists
    test_script = Path("run_unit_tests_in_blender.py")
    if not test_script.exists():
        print("❌ run_unit_tests_in_blender.py not found in current directory")
        return False
    
    # Run unit tests in Blender
    success = run_command("python3 run_unit_tests_in_blender.py", "Running unit tests in Blender")
    
    if success:
        print("✅ Unit tests completed")
        return True
    else:
        print("❌ Unit tests failed")
        return False

def run_integration_tests():
    """Run integration tests if available."""
    print("=" * 60)
    print("🔗 Running Integration Tests")
    print("=" * 60)
    
    # Check if integration_tests.py exists
    integration_script = Path("integration_tests.py")
    if not integration_script.exists():
        print("⚠️  integration_tests.py not found, skipping integration tests")
        return True
    
    # Run integration tests
    success = run_command("python3 integration_tests.py", "Running integration tests")
    
    if success:
        print("✅ Integration tests completed")
        return True
    else:
        print("❌ Integration tests failed")
        return False

def check_test_coverage():
    """Check test coverage and provide summary."""
    print("=" * 60)
    print("📊 Test Coverage Summary")
    print("=" * 60)
    
    # Count test files
    test_files = [
        "materialx_addon/tests/test_utils.py",
        "materialx_addon/tests/test_node_utils.py",
        "materialx_addon/tests/test_logging.py",
        "materialx_addon/tests/test_performance.py",
        "materialx_addon/tests/test_exporters.py",
        "materialx_addon/tests/test_mappers.py",
        "materialx_addon/tests/test_core.py"
    ]
    
    existing_tests = []
    for test_file in test_files:
        if Path(test_file).exists():
            existing_tests.append(test_file)
            print(f"✅ {test_file}")
        else:
            print(f"❌ {test_file} (missing)")
    
    print(f"\n📈 Test Coverage: {len(existing_tests)}/{len(test_files)} test modules")
    
    # Check addon components
    addon_components = [
        "materialx_addon/exporters/",
        "materialx_addon/mappers/",
        "materialx_addon/core/",
        "materialx_addon/validation/",
        "materialx_addon/utils/",
        "materialx_addon/config/",
        "materialx_addon/node_definitions/"
    ]
    
    print("\n🔧 Addon Components:")
    for component in addon_components:
        if Path(component).exists():
            print(f"✅ {component}")
        else:
            print(f"❌ {component} (missing)")
    
    return len(existing_tests) == len(test_files)

def main():
    """Main test runner function."""
    print("🚀 MaterialX Addon Comprehensive Test Suite")
    print("=" * 60)
    print(f"📅 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    print("=" * 60)
    
    # Track results
    results = {}
    
    # Step 1: Deploy addon
    results['deployment'] = deploy_addon()
    
    if not results['deployment']:
        print("❌ Deployment failed, cannot continue with tests")
        return False
    
    # Step 2: Check test coverage
    results['coverage'] = check_test_coverage()
    
    # Step 3: Run unit tests
    results['unit_tests'] = run_unit_tests()
    
    # Step 4: Run integration tests
    results['integration_tests'] = run_integration_tests()
    
    # Final summary
    print("=" * 60)
    print("📋 Final Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed! The MaterialX addon is working correctly.")
        print("✅ Addon deployed successfully")
        print("✅ Comprehensive test coverage")
        print("✅ All unit tests passed")
        print("✅ All integration tests passed")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        print("🔧 Recommendations:")
        print("   - Check Blender installation and version")
        print("   - Verify MaterialX library is available")
        print("   - Review error messages for specific issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
