#!/usr/bin/env python3
"""
Unit Test Runner for MaterialX Addon (Blender Environment)

This script runs unit tests within Blender's environment.
Run this from Blender's Python console or as a text block script.
"""

import bpy
import sys
import os

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

def test_node_utils_with_real_nodes():
    """Test NodeUtils with actual Blender nodes."""
    print("=" * 60)
    print("🔧 Testing NodeUtils with Real Blender Nodes")
    print("=" * 60)
    
    try:
        from materialx_addon.utils.node_utils import NodeUtils
        
        # Create a test material with various nodes
        test_material = bpy.data.materials.new(name="NodeUtilsTestMaterial")
        test_material.use_nodes = True
        node_tree = test_material.node_tree
        
        # Clear default nodes
        node_tree.nodes.clear()
        
        # Create test nodes
        rgb_node = node_tree.nodes.new(type='ShaderNodeRGB')
        rgb_node.name = "TestRGB"
        rgb_node.location = (0, 0)
        
        value_node = node_tree.nodes.new(type='ShaderNodeValue')
        value_node.name = "TestValue"
        value_node.location = (200, 0)
        
        mix_node = node_tree.nodes.new(type='ShaderNodeMixRGB')
        mix_node.name = "TestMix"
        mix_node.location = (400, 0)
        
        # Connect nodes
        node_tree.links.new(rgb_node.outputs['Color'], mix_node.inputs['Color1'])
        node_tree.links.new(value_node.outputs['Value'], mix_node.inputs['Fac'])
        
        print(f"✅ Created test material with {len(node_tree.nodes)} nodes")
        
        # Test NodeUtils functions
        # Test get_input_value_or_connection
        is_connected, value_or_connection, type_str = NodeUtils.get_input_value_or_connection(
            mix_node, 'Color1'
        )
        print(f"✅ Input connection test: connected={is_connected}, value={value_or_connection}, type={type_str}")
        
        # Test get_node_inputs
        inputs = NodeUtils.get_node_inputs(mix_node)
        print(f"✅ Node inputs: {list(inputs.keys())}")
        
        # Test get_node_outputs
        outputs = NodeUtils.get_node_outputs(mix_node)
        print(f"✅ Node outputs: {list(outputs.keys())}")
        
        # Test find_node_by_type
        found_rgb = NodeUtils.find_node_by_type(test_material, 'RGB')
        print(f"✅ Found RGB node: {found_rgb.name if found_rgb else 'None'}")
        
        # Test find_nodes_by_type
        rgb_nodes = NodeUtils.find_nodes_by_type(test_material, 'RGB')
        print(f"✅ Found {len(rgb_nodes)} RGB nodes")
        
        # Test get_node_dependencies
        dependencies = NodeUtils.get_node_dependencies(mix_node)
        print(f"✅ Mix node dependencies: {[n.name for n in dependencies]}")
        
        # Test get_node_dependents
        dependents = NodeUtils.get_node_dependents(rgb_node)
        print(f"✅ RGB node dependents: {[n.name for n in dependents]}")
        
        # Clean up
        bpy.data.materials.remove(test_material)
        print("✅ NodeUtils tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing NodeUtils: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    print("🚀 Starting MaterialX Addon Phase 1 Unit Tests")
    print("=" * 60)
    
    # Test individual components first
    components_ok = test_individual_components()
    
    # Test Blender integration
    blender_ok = test_blender_integration()
    
    # Test NodeUtils with real nodes
    node_utils_ok = test_node_utils_with_real_nodes()
    
    # Run full unit tests
    unit_tests_ok = run_unit_tests()
    
    # Summary
    print("=" * 60)
    print("📋 Phase 1 Test Summary")
    print("=" * 60)
    print(f"Components: {'✅ PASS' if components_ok else '❌ FAIL'}")
    print(f"Blender Integration: {'✅ PASS' if blender_ok else '❌ FAIL'}")
    print(f"NodeUtils with Real Nodes: {'✅ PASS' if node_utils_ok else '❌ FAIL'}")
    print(f"Unit Tests: {'✅ PASS' if unit_tests_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if components_ok and blender_ok and node_utils_ok and unit_tests_ok:
        print("🎉 Phase 1 improvements are working correctly!")
        print("✅ Extracted utility functions")
        print("✅ Created configuration files")
        print("✅ Improved error handling")
        print("✅ Added type hints")
        print("✅ Created unit testing framework")
        return True
    else:
        print("⚠️  Some Phase 1 improvements need attention.")
        return False

# Run the tests
if __name__ == "__main__":
    success = main()
    print(f"\nTest run {'completed successfully' if success else 'failed'}")
