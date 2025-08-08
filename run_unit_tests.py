#!/usr/bin/env python3
"""
Unit Test Runner for MaterialX Addon

This script runs unit tests within Blender's environment.
It can be executed from Blender's Python console or as a script.
"""

import bpy
import sys
import os

# Add the addon directory to the path
addon_dir = os.path.join(os.path.dirname(__file__), 'materialx_addon')
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

def run_unit_tests():
    """Run all unit tests for the MaterialX addon."""
    try:
        # Import the test runner
        from materialx_addon.tests.test_utils import run_all_tests
        
        print("=" * 60)
        print("🧪 Running MaterialX Addon Unit Tests")
        print("=" * 60)
        
        # Run the tests
        results = run_all_tests()
        
        print("=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {results['success_rate']:.1%}")
        print(f"Total Duration: {results['total_duration']:.3f}s")
        print(f"Average Duration: {results['average_duration']:.3f}s")
        print("=" * 60)
        
        if results['failed'] > 0:
            print("❌ Some tests failed!")
            return False
        else:
            print("✅ All tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components in isolation."""
    print("=" * 60)
    print("🔧 Testing Individual Components")
    print("=" * 60)
    
    try:
        # Test constants
        from materialx_addon.utils.constants import MATERIALX_VERSION, DEFAULT_EXPORT_OPTIONS
        print(f"✅ Constants loaded: MaterialX version {MATERIALX_VERSION}")
        
        # Test exceptions
        from materialx_addon.utils.exceptions import MaterialXExportError, UnsupportedNodeError
        print("✅ Exceptions loaded")
        
        # Test node utils
        from materialx_addon.utils.node_utils import NodeUtils
        print("✅ NodeUtils loaded")
        
        # Test logging
        from materialx_addon.utils.logging_utils import MaterialXLogger
        logger = MaterialXLogger("TestLogger")
        logger.info("Test log message")
        print("✅ Logging utilities working")
        
        # Test performance monitoring
        from materialx_addon.utils.performance import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.start_timer("test")
        monitor.end_timer("test")
        print("✅ Performance monitoring working")
        
        # Test node mappings
        from materialx_addon.config.node_mappings import NODE_MAPPING, is_node_supported
        print(f"✅ Node mappings loaded: {len(NODE_MAPPING)} mappings")
        
        # Test specific node support
        print(f"  - TEX_COORD supported: {is_node_supported('TEX_COORD')}")
        print(f"  - RGB supported: {is_node_supported('RGB')}")
        print(f"  - EMISSION supported: {is_node_supported('EMISSION')}")
        
        print("✅ All individual components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_blender_integration():
    """Test integration with Blender's environment."""
    print("=" * 60)
    print("🎨 Testing Blender Integration")
    print("=" * 60)
    
    try:
        # Test that we can access Blender's data
        print(f"✅ Blender version: {bpy.app.version_string}")
        print(f"✅ Materials in scene: {len(bpy.data.materials)}")
        print(f"✅ Objects in scene: {len(bpy.data.objects)}")
        
        # Test creating a test material
        test_material = bpy.data.materials.new(name="UnitTestMaterial")
        test_material.use_nodes = True
        print(f"✅ Created test material: {test_material.name}")
        
        # Test NodeUtils with Blender nodes
        from materialx_addon.utils.node_utils import NodeUtils
        
        # Find a node in the material
        if test_material.node_tree and test_material.node_tree.nodes:
            node = test_material.node_tree.nodes[0]
            print(f"✅ Found node: {node.name} ({node.type})")
            
            # Test node utilities
            outputs = NodeUtils.get_node_outputs(node)
            print(f"✅ Node outputs: {list(outputs.keys())}")
        
        # Clean up
        bpy.data.materials.remove(test_material)
        print("✅ Blender integration working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Blender integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    print("🚀 Starting MaterialX Addon Unit Tests")
    print("=" * 60)
    
    # Test individual components first
    components_ok = test_individual_components()
    
    # Test Blender integration
    blender_ok = test_blender_integration()
    
    # Run full unit tests
    unit_tests_ok = run_unit_tests()
    
    # Summary
    print("=" * 60)
    print("📋 Final Summary")
    print("=" * 60)
    print(f"Components: {'✅ PASS' if components_ok else '❌ FAIL'}")
    print(f"Blender Integration: {'✅ PASS' if blender_ok else '❌ FAIL'}")
    print(f"Unit Tests: {'✅ PASS' if unit_tests_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if components_ok and blender_ok and unit_tests_ok:
        print("🎉 All tests passed! The addon is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
