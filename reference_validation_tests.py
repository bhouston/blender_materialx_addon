#!/usr/bin/env python3
"""
Reference MaterialX Validation Tests

This script validates all reference MaterialX files in the StandardSurface folder
to ensure our validator is working correctly with known good files.

The test runs within Blender's environment since the validator uses the MaterialX
Python library which is only available in Blender.
"""

import os
import sys
import subprocess
import tempfile
import glob
from pathlib import Path

def create_blender_validation_script():
    """Create a temporary Python script to run validation tests in Blender."""
    test_script = '''
import bpy
import sys
import os
import glob
from pathlib import Path

# Add the addon directory to the path
addon_dir = r"{addon_dir}"
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

def run_reference_validation_tests():
    """Run validation tests on reference MaterialX files."""
    try:
        # Import the validator
        from materialx_addon.validation.validator import MaterialXValidator
        
        print("=" * 80)
        print("🧪 Running Reference MaterialX Validation Tests")
        print("=" * 80)
        
        # Initialize validator
        validator = MaterialXValidator()
        
        # Load standard libraries
        if not validator.load_standard_libraries():
            print("❌ Failed to load standard MaterialX libraries")
            return False
        
        # Get reference files
        reference_dir = Path(r"{reference_dir}")
        mtlx_files = list(reference_dir.glob("*.mtlx"))
        
        if not mtlx_files:
            print(f"❌ No .mtlx files found in {reference_dir}")
            return False
        
        print(f"📁 Found {{len(mtlx_files)}} reference MaterialX files")
        print()
        
        # Track results
        total_files = len(mtlx_files)
        passed_files = 0
        failed_files = 0
        files_with_errors = []
        files_with_warnings = []
        
        # Validate each file
        for mtlx_file in sorted(mtlx_files):
            print(f"🔍 Validating: {{mtlx_file.name}}")
            
            try:
                # Validate the file
                results = validator.validate_file(str(mtlx_file), verbose=False)
                
                # Check results
                if results['valid']:
                    if results['errors']:
                        print(f"  ❌ FAILED - {{len(results['errors'])}} errors")
                        failed_files += 1
                        files_with_errors.append((mtlx_file.name, results['errors']))
                    else:
                        print(f"  ✅ PASSED - {{len(results['warnings'])}} warnings")
                        passed_files += 1
                        if results['warnings']:
                            files_with_warnings.append((mtlx_file.name, results['warnings']))
                else:
                    print(f"  ❌ FAILED - Document validation failed")
                    failed_files += 1
                    files_with_errors.append((mtlx_file.name, results['errors']))
                    
            except Exception as e:
                print(f"  ❌ ERROR - {{str(e)}}")
                failed_files += 1
                files_with_errors.append((mtlx_file.name, [f"Exception: {{str(e)}}"]))
        
        # Print summary
        print()
        print("=" * 80)
        print("📊 Reference Validation Test Results")
        print("=" * 80)
        print(f"Total Files: {{total_files}}")
        print(f"Passed: {{passed_files}}")
        print(f"Failed: {{failed_files}}")
        print(f"Success Rate: {{passed_files/total_files:.1%}}")
        print()
        
        if files_with_errors:
            print("❌ Files with Errors:")
            for filename, errors in files_with_errors:
                print(f"  {{filename}}:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"    - {{error}}")
                if len(errors) > 3:
                    print(f"    ... and {{len(errors) - 3}} more errors")
                print()
        
        if files_with_warnings:
            print("⚠️  Files with Warnings (these are OK):")
            for filename, warnings in files_with_warnings[:5]:  # Show first 5 files
                print(f"  {{filename}}: {{len(warnings)}} warnings")
            if len(files_with_warnings) > 5:
                print(f"  ... and {{len(files_with_warnings) - 5}} more files with warnings")
            print()
        
        # Determine overall success
        success = failed_files == 0
        
        if success:
            print("✅ All reference files passed validation!")
        else:
            print(f"❌ {{failed_files}} reference files failed validation")
            print("   This indicates issues with the validator that need to be fixed.")
        
        print("=" * 80)
        
        return success
        
    except Exception as e:
        print(f"❌ Error running validation tests: {{e}}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_reference_validation_tests()
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)
'''
    
    # Get the absolute paths
    addon_dir = os.path.abspath("materialx_addon")
    reference_dir = os.path.abspath("MaterialX_Reference/StandardSurface")
    
    # Create temporary script
    script_content = test_script.format(addon_dir=addon_dir, reference_dir=reference_dir)
    
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

def run_validation_tests():
    """Run the reference validation tests in Blender."""
    # Find Blender executable
    blender_path = find_blender_executable()
    if not blender_path:
        print("❌ Could not find Blender executable")
        print("Please ensure Blender is installed and accessible")
        return False
    
    print(f"🎬 Found Blender at: {blender_path}")
    
    # Create test script
    test_script_path = create_blender_validation_script()
    print(f"📝 Created test script: {test_script_path}")
    
    try:
        # Run Blender in background mode with our test script
        cmd = [
            blender_path,
            "--background",  # Run in background mode
            "--python", test_script_path
        ]
        
        print("🚀 Starting Blender and running validation tests...")
        print("   This may take a moment...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print("✅ Reference validation tests completed successfully")
        else:
            print(f"❌ Reference validation tests failed (exit code: {result.returncode})")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False
    finally:
        # Clean up temporary script
        try:
            os.unlink(test_script_path)
        except:
            pass

def main():
    """Main entry point."""
    print("🧪 MaterialX Reference Validation Test Runner")
    print("=" * 50)
    
    # Check if reference directory exists
    reference_dir = "MaterialX_Reference/StandardSurface"
    if not os.path.exists(reference_dir):
        print(f"❌ Reference directory not found: {reference_dir}")
        print("Please ensure the MaterialX_Reference/StandardSurface directory exists")
        return 1
    
    # Check if addon directory exists
    addon_dir = "materialx_addon"
    if not os.path.exists(addon_dir):
        print(f"❌ Addon directory not found: {addon_dir}")
        print("Please run this script from the project root directory")
        return 1
    
    # Run tests
    success = run_validation_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
