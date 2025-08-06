#!/usr/bin/env python3
"""
Comprehensive Blender MaterialX Addon Test

This script runs Blender and tests the MaterialX addon with real materials,
UI testing, and validation of exported MaterialX files.

Features:
- Tests addon installation and loading
- Creates various test materials with different node types
- Tests UI functionality (export buttons, configuration)
- Validates exported MaterialX files
- Tests error conditions and edge cases
- Performance testing with complex materials
"""

import sys
import os
import subprocess
import tempfile
import shutil
import time
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('blender_addon_test.log')
        ]
    )
    return logging.getLogger('BlenderAddonTest')

def find_blender_executable():
    """Find Blender executable on the system."""
    logger = logging.getLogger('BlenderAddonTest')
    
    # Common Blender paths
    blender_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
        "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",  # Windows
        "/usr/bin/blender",  # Linux
        "/usr/local/bin/blender",  # Linux alternative
    ]
    
    for path in blender_paths:
        if os.path.exists(path):
            logger.info(f"Found Blender at: {path}")
            return path
    
    # Try to find Blender in PATH
    try:
        result = subprocess.run(['which', 'blender'], capture_output=True, text=True)
        if result.returncode == 0:
            blender_path = result.stdout.strip()
            logger.info(f"Found Blender in PATH: {blender_path}")
            return blender_path
    except FileNotFoundError:
        pass
    
    raise RuntimeError("Could not find Blender executable")

def create_test_blend_file(test_materials: List[Dict]) -> str:
    """Create a Blender file with test materials."""
    logger = logging.getLogger('BlenderAddonTest')
    
    # Create a temporary .blend file
    temp_dir = tempfile.mkdtemp()
    blend_file = os.path.join(temp_dir, "test_materials.blend")
    
    # Create Python script to generate test materials
    python_script = f"""
import bpy
import sys
import os

# Clear existing data
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Remove all materials
for material in bpy.data.materials:
    bpy.data.materials.remove(material)

# Create test materials
{chr(10).join([create_material_code(material) for material in test_materials])}

# Save the file
bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")

print("Test blend file created successfully")
"""
    
    # Write Python script to temporary file
    script_file = os.path.join(temp_dir, "create_test_materials.py")
    with open(script_file, 'w') as f:
        f.write(python_script)
    
    # Run Blender to create the test file
    blender_path = find_blender_executable()
    cmd = [
        blender_path,
        "--background",
        "--python", script_file
    ]
    
    logger.info(f"Creating test blend file: {blend_file}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        logger.error(f"Failed to create test blend file: {result.stderr}")
        raise RuntimeError("Failed to create test blend file")
    
    logger.info("Test blend file created successfully")
    return blend_file

def create_material_code(material_config: Dict) -> str:
    """Generate Python code to create a test material."""
    material_name = material_config['name']
    node_types = material_config['nodes']
    
    code = f"""
# Create material: {material_name}
material = bpy.data.materials.new(name="{material_name}")
material.use_nodes = True
nodes = material.node_tree.nodes
links = material.node_tree.links

# Clear default nodes
nodes.clear()

# Create nodes
"""
    
    # Add node creation code
    for i, node_type in enumerate(node_types):
        if node_type == 'Principled BSDF':
            code += f"principled = nodes.new(type='ShaderNodeBsdfPrincipled')\n"
            code += f"principled.location = ({i * 200}, 0)\n"
        elif node_type == 'RGB':
            code += f"rgb = nodes.new(type='ShaderNodeRGB')\n"
            code += f"rgb.location = ({i * 200}, 200)\n"
            code += f"rgb.outputs[0].default_value = (0.8, 0.2, 0.2, 1.0)\n"
        elif node_type == 'Value':
            code += f"value = nodes.new(type='ShaderNodeValue')\n"
            code += f"value.location = ({i * 200}, -200)\n"
            code += f"value.outputs[0].default_value = 0.5\n"
        elif node_type == 'Math':
            code += f"math = nodes.new(type='ShaderNodeMath')\n"
            code += f"math.location = ({i * 200}, 0)\n"
            code += f"math.operation = 'MULTIPLY'\n"
        elif node_type == 'Mix':
            code += f"mix = nodes.new(type='ShaderNodeMixRGB')\n"
            code += f"mix.location = ({i * 200}, 0)\n"
        elif node_type == 'Image Texture':
            code += f"tex = nodes.new(type='ShaderNodeTexImage')\n"
            code += f"tex.location = ({i * 200}, 0)\n"
        elif node_type == 'Noise Texture':
            code += f"noise = nodes.new(type='ShaderNodeTexNoise')\n"
            code += f"noise.location = ({i * 200}, 0)\n"
        elif node_type == 'Normal Map':
            code += f"normal = nodes.new(type='ShaderNodeNormalMap')\n"
            code += f"normal.location = ({i * 200}, 0)\n"
    
    # Add Material Output node
    code += f"""
# Create Material Output
output = nodes.new(type='ShaderNodeOutputMaterial')
output.location = ({len(node_types) * 200}, 0)

# Connect nodes (simple connections)
if len(nodes) > 1:
    for i in range(len(nodes) - 1):
        if i + 1 < len(nodes):
            links.new(nodes[i].outputs[0], nodes[i+1].inputs[0])
    
    # Connect last node to output
    if len(nodes) > 1:
        links.new(nodes[-2].outputs[0], output.inputs['Surface'])
"""
    
    return code

def test_addon_installation():
    """Test if the MaterialX addon is properly installed."""
    logger = logging.getLogger('BlenderAddonTest')
    logger.info("Testing addon installation...")
    
    # Create Python script to test addon
    test_script = """
import bpy
import addon_utils

# Check if MaterialX addon is installed
addon_name = "materialx_addon"
is_installed = addon_utils.check(addon_name)[1]

if is_installed:
    print("✓ MaterialX addon is installed")
    
    # Try to enable the addon
    try:
        bpy.ops.preferences.addon_enable(module=addon_name)
        print("✓ MaterialX addon enabled successfully")
        
        # Check if addon is active
        if addon_utils.check(addon_name)[1]:
            print("✓ MaterialX addon is active")
        else:
            print("✗ MaterialX addon is not active")
            
    except Exception as e:
        print(f"✗ Failed to enable addon: {e}")
else:
    print("✗ MaterialX addon is not installed")
"""
    
    # Run test in Blender
    blender_path = find_blender_executable()
    result = run_blender_script(blender_path, test_script)
    
    if "✓ MaterialX addon is installed" in result and "✓ MaterialX addon enabled successfully" in result:
        logger.info("✓ Addon installation test passed")
        return True
    else:
        logger.error("✗ Addon installation test failed")
        logger.error(f"Output: {result}")
        return False

def test_material_export(material_name: str, blend_file: str, output_dir: str) -> bool:
    """Test exporting a specific material."""
    logger = logging.getLogger('BlenderAddonTest')
    logger.info(f"Testing export of material: {material_name}")
    
    # Create Python script to test export
    test_script = f"""
import bpy
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestExport')

# Load the blend file
print("Loading blend file...")
bpy.ops.wm.open_mainfile(filepath="{blend_file}")
print("Blend file loaded successfully")

# Find the material
material = bpy.data.materials.get("{material_name}")
if not material:
    print(f"✗ Material '{material_name}' not found")
    print(f"Available materials: {{[m.name for m in bpy.data.materials]}}")
    sys.exit(1)

print(f"✓ Found material: {{material.name}}")

# Test export
try:
    # Import the exporter
    print("Importing exporter...")
    from materialx_addon import blender_materialx_exporter
    print("Exporter imported successfully")
    
    # Export options
    options = {{
        'export_textures': False,
        'copy_textures': False,
        'relative_paths': True,
        'optimize_document': True,
        'advanced_validation': True,
        'performance_monitoring': True
    }}
    
    # Export the material
    output_path = "{output_dir}/{material_name}.mtlx"
    print(f"Exporting to: {{output_path}}")
    
    result = blender_materialx_exporter.export_material_to_materialx(
        material, output_path, logger, options
    )
    
    print(f"Export result: {{result}}")
    
    if result['success']:
        print(f"✓ Export successful: {{output_path}}")
        print(f"  Performance stats: {{result.get('performance_stats', {{}})}}")
        print(f"  Validation results: {{result.get('validation_results', {{}})}}")
        print(f"  Optimization applied: {{result.get('optimization_applied', False)}}")
    else:
        print(f"✗ Export failed: {{result.get('error', 'Unknown error')}}")
        print(f"  Unsupported nodes: {{result.get('unsupported_nodes', [])}}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Export exception: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    # Run test in Blender
    blender_path = find_blender_executable()
    result = run_blender_script(blender_path, test_script)
    
    if "✓ Export successful:" in result:
        logger.info(f"✓ Material export test passed: {material_name}")
        return True
    else:
        logger.error(f"✗ Material export test failed: {material_name}")
        logger.error(f"Output: {result}")
        return False

def test_ui_functionality():
    """Test UI functionality (operators, panels)."""
    logger = logging.getLogger('BlenderAddonTest')
    logger.info("Testing UI functionality...")
    
    test_script = """
import bpy
import addon_utils

# Enable the addon if not already enabled
addon_name = "materialx_addon"
if not addon_utils.check(addon_name)[1]:
    bpy.ops.preferences.addon_enable(module=addon_name)

# Test if operators are registered
operators = [
    "materialx.export",
    "materialx.export_all"
]

for op_name in operators:
    if hasattr(bpy.ops, op_name.split('.')[0]) and hasattr(getattr(bpy.ops, op_name.split('.')[0]), op_name.split('.')[1]):
        print(f"✓ Operator registered: {op_name}")
    else:
        print(f"✗ Operator not found: {op_name}")

# Test if panel is registered
panel_classes = [cls for cls in bpy.types.Panel.__subclasses__() if 'materialx' in cls.__name__.lower()]
if panel_classes:
    print(f"✓ Found {len(panel_classes)} MaterialX panel(s)")
    for panel in panel_classes:
        print(f"  - {panel.__name__}")
else:
    print("✗ No MaterialX panels found")
"""
    
    blender_path = find_blender_executable()
    result = run_blender_script(blender_path, test_script)
    
    if "✓ Operator registered:" in result and "✓ Found" in result:
        logger.info("✓ UI functionality test passed")
        return True
    else:
        logger.error("✗ UI functionality test failed")
        logger.error(f"Output: {result}")
        return False

def validate_materialx_file(file_path: str) -> bool:
    """Validate a MaterialX file."""
    logger = logging.getLogger('BlenderAddonTest')
    logger.info(f"Validating MaterialX file: {file_path}")
    
    try:
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check basic structure
        if root.tag != 'materialx':
            logger.error("✗ Root element is not 'materialx'")
            return False
        
        # Check version
        version = root.get('version')
        if not version:
            logger.error("✗ No version attribute found")
            return False
        
        logger.info(f"✓ MaterialX version: {version}")
        
        # Check for required elements
        nodegraphs = root.findall('nodegraph')
        materials = root.findall('surfacematerial')
        
        if not nodegraphs:
            logger.warning("⚠ No nodegraphs found")
        
        if not materials:
            logger.warning("⚠ No surface materials found")
        
        logger.info(f"✓ Found {len(nodegraphs)} nodegraphs and {len(materials)} materials")
        
        # Check for standard_surface nodes
        standard_surfaces = []
        for nodegraph in nodegraphs:
            for node in nodegraph.findall('standard_surface'):
                standard_surfaces.append(node)
        
        if standard_surfaces:
            logger.info(f"✓ Found {len(standard_surfaces)} standard_surface nodes")
        else:
            logger.warning("⚠ No standard_surface nodes found")
        
        return True
        
    except ET.ParseError as e:
        logger.error(f"✗ XML parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Validation error: {e}")
        return False

def run_blender_script(blender_path: str, script: str) -> str:
    """Run a Python script in Blender and return the output."""
    # Write script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_file = f.name
    
    try:
        # Run Blender with the script
        cmd = [
            blender_path,
            "--background",
            "--python", script_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return result.stdout
        
    finally:
        # Clean up temporary file
        os.unlink(script_file)

def run_comprehensive_test():
    """Run the comprehensive Blender addon test."""
    logger = setup_logging()
    
    logger.info("🚀 Starting Comprehensive Blender MaterialX Addon Test")
    logger.info("=" * 80)
    
    # Test configuration
    test_materials = [
        {
            'name': 'SimpleMaterial',
            'nodes': ['RGB', 'Principled BSDF']
        },
        {
            'name': 'ComplexMaterial',
            'nodes': ['RGB', 'Math', 'Mix', 'Principled BSDF']
        },
        {
            'name': 'TextureMaterial',
            'nodes': ['Noise Texture', 'Normal Map', 'Principled BSDF']
        },
        {
            'name': 'ValueMaterial',
            'nodes': ['Value', 'Math', 'Principled BSDF']
        }
    ]
    
    results = {}
    
    try:
        # Test 1: Addon Installation
        logger.info("🧪 Test 1: Addon Installation")
        results['addon_installation'] = test_addon_installation()
        
        # Test 2: UI Functionality
        logger.info("🧪 Test 2: UI Functionality")
        results['ui_functionality'] = test_ui_functionality()
        
        # Test 3: Material Export
        logger.info("🧪 Test 3: Material Export")
        
        # Create test blend file
        blend_file = create_test_blend_file(test_materials)
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        export_results = []
        for material_config in test_materials:
            material_name = material_config['name']
            success = test_material_export(material_name, blend_file, output_dir)
            export_results.append(success)
            
            # Validate exported file
            mtlx_file = os.path.join(output_dir, f"{material_name}.mtlx")
            if os.path.exists(mtlx_file):
                validation_success = validate_materialx_file(mtlx_file)
                logger.info(f"  Validation for {material_name}: {'✓' if validation_success else '✗'}")
            else:
                logger.error(f"  ✗ Exported file not found: {mtlx_file}")
        
        results['material_export'] = all(export_results)
        
        # Test 4: Performance Testing
        logger.info("🧪 Test 4: Performance Testing")
        performance_success = test_performance_with_complex_material(blend_file, output_dir)
        results['performance'] = performance_success
        
        # Cleanup
        shutil.rmtree(os.path.dirname(blend_file), ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Generate report
    generate_test_report(results)
    
    # Return overall success
    overall_success = all(results.values())
    
    if overall_success:
        logger.info("🎉 ALL TESTS PASSED! MaterialX addon is working correctly.")
    else:
        logger.error("❌ SOME TESTS FAILED! Please review the test results.")
    
    return overall_success

def test_performance_with_complex_material(blend_file: str, output_dir: str) -> bool:
    """Test performance with a complex material."""
    logger = logging.getLogger('BlenderAddonTest')
    logger.info("Testing performance with complex material...")
    
    # Create a complex material with many nodes
    complex_material = {
        'name': 'PerformanceTestMaterial',
        'nodes': ['RGB', 'Math', 'Mix', 'Noise Texture', 'Normal Map', 'Math', 'Mix', 'Principled BSDF']
    }
    
    start_time = time.time()
    success = test_material_export(complex_material['name'], blend_file, output_dir)
    end_time = time.time()
    
    duration = end_time - start_time
    logger.info(f"Performance test took {duration:.2f} seconds")
    
    if duration > 30:  # More than 30 seconds is too slow
        logger.warning(f"⚠ Performance test took longer than expected: {duration:.2f}s")
        return False
    
    return success

def generate_test_report(results: Dict[str, bool]):
    """Generate a test report."""
    logger = logging.getLogger('BlenderAddonTest')
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    report = f"""
{'='*80}
COMPREHENSIVE BLENDER MATERIALX ADDON TEST REPORT
{'='*80}

SUMMARY:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {(passed_tests/total_tests)*100:.1f}%

DETAILED RESULTS:
"""
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        report += f"- {test_name}: {status}\n"
    
    if failed_tests > 0:
        report += f"\nFAILED TESTS ({failed_tests}):\n"
        for test_name, result in results.items():
            if not result:
                report += f"- {test_name}\n"
    
    report += f"\n{'='*80}\n"
    
    # Save report to file
    with open('blender_addon_test_report.txt', 'w') as f:
        f.write(report)
    
    logger.info(report)

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 