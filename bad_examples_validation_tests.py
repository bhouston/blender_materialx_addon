#!/usr/bin/env python3
"""
Bad MaterialX Examples Validation Tests

This script validates all intentionally bad MaterialX files in the BadExamples folder
to ensure our validator correctly catches various types of errors.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def create_blender_validation_script():
    """Create a temporary Python script to run validation tests in Blender."""
    test_script = '''
import bpy
import sys
import os
from pathlib import Path

# Add the addon directory to the path
addon_dir = r"{addon_dir}"
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

def run_bad_examples_validation_tests():
    """Run validation tests on bad MaterialX files."""
    try:
        # Import the validator
        from materialx_addon.validation.validator import MaterialXValidator
        
        print("=" * 80)
        print("🧪 Running Bad MaterialX Examples Validation Tests")
        print("=" * 80)
        
        # Initialize validator
        validator = MaterialXValidator()
        
        # Load standard libraries
        if not validator.load_standard_libraries():
            print("❌ Failed to load standard MaterialX libraries")
            return False
        
        # Get bad example files
        bad_examples_dir = Path(r"{bad_examples_dir}")
        mtlx_files = list(bad_examples_dir.glob("*.mtlx"))
        
        if not mtlx_files:
            print(f"❌ No .mtlx files found in {{bad_examples_dir}}")
            return False
        
        print(f"📁 Found {{len(mtlx_files)}} bad MaterialX example files")
        print()
        
        # Track results
        total_files = len(mtlx_files)
        correctly_failed_files = 0
        incorrectly_passed_files = 0
        files_with_expected_errors = []
        files_with_unexpected_errors = []
        
        # Expected error patterns for each file
        expected_errors = {{
            "bad_standard_surface_node.mtlx": ["Invalid standard_surface node"],
            "bad_no_surface_shader.mtlx": ["No standard_surface elements found"],
            "bad_material_no_shader_connection.mtlx": ["has no surfaceshader input connection"],
            "bad_material_wrong_shader_type.mtlx": ["connected to non-standard_surface element"],
            "bad_material_nonexistent_shader.mtlx": ["references non-existent surface shader"],
            "bad_disconnected_nodes.mtlx": ["has no values or connections", "has no file or connections"],
            "bad_texture_no_texcoord.mtlx": ["missing texcoord input"],
            "bad_invalid_xml.mtlx": ["Failed to load file"]  # Should fail to load
        }}
        
        # Validate each file
        for mtlx_file in sorted(mtlx_files):
            print(f"🔍 Validating: {{mtlx_file.name}}")
            
            try:
                # Validate the file
                results = validator.validate_file(str(mtlx_file), verbose=False)
                
                # Check if this file should have failed
                expected_error_patterns = expected_errors.get(mtlx_file.name, [])
                
                if expected_error_patterns:
                    # This file should have failed - check if it did
                    found_expected_error = False
                    for error in results['errors']:
                        for pattern in expected_error_patterns:
                            if pattern in error:
                                found_expected_error = True
                                break
                        if found_expected_error:
                            break
                    
                    if found_expected_error:
                        print(f"  ✅ CORRECTLY FAILED - Found expected error")
                        correctly_failed_files += 1
                        files_with_expected_errors.append((mtlx_file.name, results['errors']))
                    else:
                        print(f"  ❌ INCORRECTLY PASSED - Should have failed")
                        incorrectly_passed_files += 1
                        files_with_unexpected_errors.append((mtlx_file.name, results['errors']))
                else:
                    # This file should have passed - check if it did
                    if results['valid'] and not results['errors']:
                        print(f"  ✅ CORRECTLY PASSED")
                        correctly_failed_files += 1
                    else:
                        print(f"  ❌ INCORRECTLY FAILED - Should have passed")
                        incorrectly_passed_files += 1
                        files_with_unexpected_errors.append((mtlx_file.name, results['errors']))
                        
            except Exception as e:
                # Check if this was expected to fail to load
                if "Failed to load file" in expected_errors.get(mtlx_file.name, []):
                    print(f"  ✅ CORRECTLY FAILED TO LOAD - {{str(e)}}")
                    correctly_failed_files += 1
                    files_with_expected_errors.append((mtlx_file.name, [f"Load error: {{str(e)}}"]))
                else:
                    print(f"  ❌ UNEXPECTED ERROR - {{str(e)}}")
                    incorrectly_passed_files += 1
                    files_with_unexpected_errors.append((mtlx_file.name, [f"Unexpected error: {{str(e)}}"]))
        
        # Print summary
        print()
        print("=" * 80)
        print("📊 Bad Examples Validation Test Results")
        print("=" * 80)
        print(f"Total Files: {{total_files}}")
        print(f"Correctly Failed: {{correctly_failed_files}}")
        print(f"Incorrectly Passed: {{incorrectly_passed_files}}")
        print(f"Success Rate: {{correctly_failed_files/total_files:.1%}}")
        print()
        
        if files_with_expected_errors:
            print("✅ Files with Expected Errors (Good!):")
            for filename, errors in files_with_expected_errors[:3]:  # Show first 3
                print(f"  {{filename}}: {{len(errors)}} errors")
            if len(files_with_expected_errors) > 3:
                print(f"  ... and {{len(files_with_expected_errors) - 3}} more files")
            print()
        
        if files_with_unexpected_errors:
            print("❌ Files with Unexpected Errors (Bad!):")
            for filename, errors in files_with_unexpected_errors:
                print(f"  {{filename}}:")
                for error in errors[:2]:  # Show first 2 errors
                    print(f"    - {{error}}")
                if len(errors) > 2:
                    print(f"    ... and {{len(errors) - 2}} more errors")
                print()
        
        # Determine overall success
        success = incorrectly_passed_files == 0
        
        if success:
            print("✅ All bad examples correctly identified as invalid!")
        else:
            print(f"❌ {{incorrectly_passed_files}} bad examples incorrectly passed validation")
            print("   This indicates issues with the validator that need to be fixed.")
        
        print("=" * 80)
        
        return success
        
    except Exception as e:
        print(f"❌ Error running bad examples validation tests: {{e}}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_bad_examples_validation_tests()
    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)
'''
    
    # Get the absolute paths
    addon_dir = os.path.abspath("materialx_addon")
    bad_examples_dir = os.path.abspath("MaterialX_Reference/BadExamples")
    
    # Create temporary script
    script_content = test_script.format(addon_dir=addon_dir, bad_examples_dir=bad_examples_dir)
    
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
    """Run the bad examples validation tests in Blender."""
    # Find Blender executable
    blender_path = find_blender_executable()
    if not blender_path:
        print("❌ Could not find Blender executable")
        print("Please ensure Blender is installed and accessible")
        return False
    
    print(f"🎬 Found Blender at: {{blender_path}}")
    
    # Create test script
    test_script_path = create_blender_validation_script()
    print(f"📝 Created test script: {{test_script_path}}")
    
    try:
        # Run Blender in background mode with our test script
        cmd = [
            blender_path,
            "--background",  # Run in background mode
            "--python", test_script_path
        ]
        
        print("🚀 Starting Blender and running bad examples validation tests...")
        print("   This may take a moment...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print("✅ Bad examples validation tests completed successfully")
        else:
            print(f"❌ Bad examples validation tests failed (exit code: {{result.returncode}})")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Test execution timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {{e}}")
        return False
    finally:
        # Clean up temporary script
        try:
            os.unlink(test_script_path)
        except:
            pass

def main():
    """Main entry point."""
    print("🧪 Bad MaterialX Examples Validation Test Runner")
    print("=" * 50)
    
    # Check if bad examples directory exists
    bad_examples_dir = "MaterialX_Reference/BadExamples"
    if not os.path.exists(bad_examples_dir):
        print(f"❌ Bad examples directory not found: {{bad_examples_dir}}")
        print("Please ensure the MaterialX_Reference/BadExamples directory exists")
        return 1
    
    # Check if addon directory exists
    addon_dir = "materialx_addon"
    if not os.path.exists(addon_dir):
        print(f"❌ Addon directory not found: {{addon_dir}}")
        print("Please run this script from the project root directory")
        return 1
    
    # Run tests
    success = run_validation_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
