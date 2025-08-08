#!/usr/bin/env python3
"""
Unit Test Runner for MaterialX Addon (Blender Environment)

This script runs unit tests within Blender's environment by launching Blender
in background mode and executing the test suite.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def create_blender_test_script():
    """Create a temporary Python script to run tests in Blender."""
    test_script = '''
import bpy
import sys
import os

# Add the addon directory to the path
addon_dir = r"{addon_dir}"
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

def run_unit_tests_in_blender():
    """Run unit tests within Blender environment."""
    try:
        # Import and run tests
        from materialx_addon.tests import run_all_tests
        
        print("=" * 60)
        print("🧪 Running MaterialX Addon Unit Tests in Blender")
        print("=" * 60)
        
        # Run the tests
        results = run_all_tests()
        
        print("=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {{results['total_tests']}}")
        print(f"Passed: {{results['passed']}}")
        print(f"Failed: {{results['failed']}}")
        print(f"Success Rate: {{results['success_rate']:.1%}}")
        print(f"Total Duration: {{results['total_duration']:.3f}}s")
        print(f"Average Duration: {{results['average_duration']:.3f}}s")
        print("=" * 60)
        
        if results['failed'] > 0:
            print("❌ Some tests failed!")
            return False
        else:
            print("✅ All tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Error running tests: {{e}}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_unit_tests_in_blender()
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)
'''
    
    # Get the absolute path to the addon directory
    addon_dir = os.path.abspath("materialx_addon")
    
    # Create temporary script
    script_content = test_script.format(addon_dir=addon_dir)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        return f.name

def find_blender_executable():
    """Find the Blender executable."""
    # Common Blender paths
    blender_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
        "/Applications/Blender 4.5.app/Contents/MacOS/Blender",
        "/Applications/Blender 4.4.app/Contents/MacOS/Blender",
        "/Applications/Blender 4.3.app/Contents/MacOS/Blender",
        "/Applications/Blender 4.2.app/Contents/MacOS/Blender",
        "/Applications/Blender 4.1.app/Contents/MacOS/Blender",
        "/Applications/Blender 4.0.app/Contents/MacOS/Blender",
    ]
    
    for path in blender_paths:
        if os.path.exists(path):
            return path
    
    # Try to find via PATH
    try:
        result = subprocess.run(['which', 'blender'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def run_unit_tests():
    """Run unit tests within Blender environment."""
    print("🚀 Running MaterialX Addon Unit Tests in Blender")
    print("=" * 60)
    
    # Find Blender executable
    blender_path = find_blender_executable()
    if not blender_path:
        print("❌ Blender executable not found!")
        print("Please ensure Blender is installed and accessible.")
        return False
    
    print(f"✅ Found Blender at: {blender_path}")
    
    # Create test script
    test_script_path = create_blender_test_script()
    print(f"✅ Created test script: {test_script_path}")
    
    try:
        # Run Blender in background mode with the test script
        cmd = [
            blender_path,
            "--background",  # Run in background mode
            "--python", test_script_path,  # Execute our test script
            "--",  # End Blender arguments
        ]
        
        print(f"🔄 Running: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print output
        if result.stdout:
            print("📤 Output:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Errors/Warnings:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print("✅ Unit tests completed successfully!")
            return True
        else:
            print(f"❌ Unit tests failed with exit code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Unit tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False
    finally:
        # Clean up temporary script
        try:
            os.unlink(test_script_path)
        except:
            pass

def main():
    """Main function."""
    success = run_unit_tests()
    
    if success:
        print("🎉 All unit tests passed!")
    else:
        print("⚠️  Unit tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
