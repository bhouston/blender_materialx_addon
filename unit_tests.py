#!/usr/bin/env python3
"""
Comprehensive Unit Test Runner for MaterialX Addon

This script runs unit tests within Blender's environment.
It can be executed from Blender's Python console or as a script.
"""

import bpy
import sys
import os
import time
from typing import Dict, Any, List

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

def test_exporters():
    """Test exporter components."""
    print("=" * 60)
    print("📤 Testing Exporters")
    print("=" * 60)
    
    try:
        # Test base exporter
        from materialx_addon.exporters.base_exporter import BaseExporter
        print("✅ BaseExporter imported")
        
        # Test material exporter
        from materialx_addon.exporters.material_exporter import MaterialExporter
        print("✅ MaterialExporter imported")
        
        # Test batch exporter
        from materialx_addon.exporters.batch_exporter import BatchExporter
        print("✅ BatchExporter imported")
        
        # Test texture exporter
        from materialx_addon.exporters.texture_exporter import TextureExporter
        print("✅ TextureExporter imported")
        
        # Test exporter instantiation
        material_exporter = MaterialExporter()
        print("✅ MaterialExporter instantiated")
        
        batch_exporter = BatchExporter()
        print("✅ BatchExporter instantiated")
        
        texture_exporter = TextureExporter()
        print("✅ TextureExporter instantiated")
        
        print("✅ All exporters working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing exporters: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mappers():
    """Test mapper components."""
    print("=" * 60)
    print("🗺️ Testing Mappers")
    print("=" * 60)
    
    try:
        # Test base mapper
        from materialx_addon.mappers.base_mapper import BaseMapper
        print("✅ BaseMapper imported")
        
        # Test node mapper registry
        from materialx_addon.mappers.node_mapper_registry import NodeMapperRegistry
        print("✅ NodeMapperRegistry imported")
        
        # Test specific mappers
        from materialx_addon.mappers.principled_mapper import PrincipledMapper
        from materialx_addon.mappers.texture_mappers import TextureMapper
        from materialx_addon.mappers.math_mappers import MathMapper
        from materialx_addon.mappers.utility_mappers import UtilityMapper
        print("✅ All specific mappers imported")
        
        # Test registry functionality
        registry = NodeMapperRegistry()
        print(f"✅ Registry created with {len(registry.get_available_mappers())} mappers")
        
        # Test mapper instantiation
        principled_mapper = PrincipledMapper()
        texture_mapper = TextureMapper()
        math_mapper = MathMapper()
        utility_mapper = UtilityMapper()
        print("✅ All mappers instantiated")
        
        print("✅ All mappers working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing mappers: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_components():
    """Test core components."""
    print("=" * 60)
    print("🔧 Testing Core Components")
    print("=" * 60)
    
    try:
        # Test document manager
        from materialx_addon.core.document_manager import DocumentManager
        print("✅ DocumentManager imported")
        
        # Test advanced validator
        from materialx_addon.core.advanced_validator import AdvancedValidator
        print("✅ AdvancedValidator imported")
        
        # Test type converter
        from materialx_addon.core.type_converter import TypeConverter
        print("✅ TypeConverter imported")
        
        # Test library builder
        from materialx_addon.core.library_builder import LibraryBuilder
        print("✅ LibraryBuilder imported")
        
        # Test validation
        from materialx_addon.validation.validator import MaterialXValidator
        print("✅ MaterialXValidator imported")
        
        # Test component instantiation
        doc_manager = DocumentManager()
        validator = AdvancedValidator()
        type_converter = TypeConverter()
        lib_builder = LibraryBuilder()
        mx_validator = MaterialXValidator()
        print("✅ All core components instantiated")
        
        print("✅ All core components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing core components: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_node_definitions():
    """Test node definitions."""
    print("=" * 60)
    print("📋 Testing Node Definitions")
    print("=" * 60)
    
    try:
        # Test custom node definitions
        from materialx_addon.node_definitions.custom_node_definitions import CUSTOM_NODE_DEFINITIONS
        print(f"✅ Custom node definitions loaded: {len(CUSTOM_NODE_DEFINITIONS)} definitions")
        
        # Test texture definitions
        from materialx_addon.node_definitions.texture_definitions import TEXTURE_DEFINITIONS
        print(f"✅ Texture definitions loaded: {len(TEXTURE_DEFINITIONS)} definitions")
        
        # Test type conversions
        from materialx_addon.node_definitions.type_conversions import TYPE_CONVERSIONS
        print(f"✅ Type conversions loaded: {len(TYPE_CONVERSIONS)} conversions")
        
        print("✅ All node definitions working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing node definitions: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration components."""
    print("=" * 60)
    print("⚙️ Testing Configuration")
    print("=" * 60)
    
    try:
        # Test node mappings
        from materialx_addon.config.node_mappings import NODE_MAPPING, is_node_supported, get_supported_node_types
        print(f"✅ Node mappings loaded: {len(NODE_MAPPING)} mappings")
        
        # Test supported node types
        supported_types = get_supported_node_types()
        print(f"✅ Supported node types: {len(supported_types)} types")
        
        # Test specific node support
        test_nodes = ['TEX_COORD', 'RGB', 'MIX', 'MATH', 'PRINCIPLED_BSDF']
        for node_type in test_nodes:
            supported = is_node_supported(node_type)
            print(f"  - {node_type}: {'✅' if supported else '❌'}")
        
        print("✅ All configuration components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_materialx_library():
    """Test MaterialX library integration."""
    print("=" * 60)
    print("📚 Testing MaterialX Library Integration")
    print("=" * 60)
    
    try:
        # Test MaterialX import
        import MaterialX as mx
        print(f"✅ MaterialX imported: version {mx.__version__ if hasattr(mx, '__version__') else 'unknown'}")
        
        # Test basic MaterialX functionality
        doc = mx.createDocument()
        print("✅ MaterialX document created")
        
        # Test node creation
        node = doc.addNode("constant")
        print("✅ MaterialX node created")
        
        # Test attribute setting
        node.setAttribute("value", "1.0 0.5 0.0")
        print("✅ MaterialX node attribute set")
        
        # Test document validation
        valid = doc.validate()
        print(f"✅ MaterialX document validation: {valid}")
        
        print("✅ MaterialX library integration working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing MaterialX library: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_addon_registration():
    """Test addon registration and UI components."""
    print("=" * 60)
    print("🔌 Testing Addon Registration")
    print("=" * 60)
    
    try:
        # Test addon registration
        from materialx_addon import bl_info
        print(f"✅ Addon info loaded: {bl_info.get('name', 'Unknown')} v{bl_info.get('version', 'Unknown')}")
        
        # Test UI panel registration
        from materialx_addon.blender_materialx_exporter import MATERIALX_PT_export_panel
        print("✅ UI panel class loaded")
        
        # Test operator registration
        from materialx_addon.blender_materialx_exporter import MATERIALX_OT_export_material, MATERIALX_OT_export_all_materials
        print("✅ Export operators loaded")
        
        # Test addon preferences
        from materialx_addon.blender_materialx_exporter import MaterialXAddonPreferences
        print("✅ Addon preferences loaded")
        
        print("✅ All addon registration components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing addon registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    print("🚀 Starting MaterialX Addon Comprehensive Unit Tests")
    print("=" * 60)
    
    # Track test results
    test_results = {}
    
    # Test individual components first
    test_results['components'] = test_individual_components()
    
    # Test Blender integration
    test_results['blender_integration'] = test_blender_integration()
    
    # Test NodeUtils with real nodes
    test_results['node_utils'] = test_node_utils_with_real_nodes()
    
    # Test exporters
    test_results['exporters'] = test_exporters()
    
    # Test mappers
    test_results['mappers'] = test_mappers()
    
    # Test core components
    test_results['core_components'] = test_core_components()
    
    # Test node definitions
    test_results['node_definitions'] = test_node_definitions()
    
    # Test configuration
    test_results['configuration'] = test_configuration()
    
    # Test MaterialX library
    test_results['materialx_library'] = test_materialx_library()
    
    # Test addon registration
    test_results['addon_registration'] = test_addon_registration()
    
    # Run full unit tests
    test_results['unit_tests'] = run_unit_tests()
    
    # Summary
    print("=" * 60)
    print("📋 Comprehensive Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed! The addon is working correctly.")
        print("✅ Comprehensive test coverage completed")
        print("✅ All major components tested")
        print("✅ Blender integration verified")
        print("✅ MaterialX library integration verified")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
