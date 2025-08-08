#!/usr/bin/env python3
"""
Simple Test Runner for Blender Python Console

This script can be run directly in Blender's Python console for quick testing.
It provides a simple interface to run unit tests without external dependencies.

Usage in Blender Python Console:
    exec(open('/path/to/blender_test_runner.py').read())
"""

import bpy
import sys
import os

def run_quick_tests():
    """Run a quick test suite in Blender."""
    print("🚀 Quick MaterialX Addon Tests")
    print("=" * 50)
    
    # Test basic imports
    try:
        from materialx_addon.utils.constants import MATERIALX_VERSION
        print(f"✅ MaterialX version: {MATERIALX_VERSION}")
    except Exception as e:
        print(f"❌ Failed to import constants: {e}")
        return False
    
    try:
        from materialx_addon.utils.node_utils import NodeUtils
        print("✅ NodeUtils imported")
    except Exception as e:
        print(f"❌ Failed to import NodeUtils: {e}")
        return False
    
    try:
        from materialx_addon.config.node_mappings import NODE_MAPPING
        print(f"✅ Node mappings loaded: {len(NODE_MAPPING)} mappings")
    except Exception as e:
        print(f"❌ Failed to import node mappings: {e}")
        return False
    
    # Test Blender integration
    try:
        print(f"✅ Blender version: {bpy.app.version_string}")
        print(f"✅ Materials in scene: {len(bpy.data.materials)}")
    except Exception as e:
        print(f"❌ Blender integration failed: {e}")
        return False
    
    # Test MaterialX library
    try:
        import MaterialX as mx
        doc = mx.createDocument()
        print("✅ MaterialX library working")
    except Exception as e:
        print(f"❌ MaterialX library failed: {e}")
        return False
    
    # Test creating a simple material
    try:
        test_material = bpy.data.materials.new(name="QuickTestMaterial")
        test_material.use_nodes = True
        print("✅ Test material created")
        
        # Clean up
        bpy.data.materials.remove(test_material)
        print("✅ Test material cleaned up")
    except Exception as e:
        print(f"❌ Material creation failed: {e}")
        return False
    
    print("=" * 50)
    print("✅ Quick tests completed successfully!")
    return True

def run_full_tests():
    """Run the full test suite if available."""
    print("🧪 Running Full Test Suite")
    print("=" * 50)
    
    try:
        from materialx_addon.tests import run_all_tests
        results = run_all_tests()
        
        print(f"📊 Results: {results['passed']}/{results['total_tests']} tests passed")
        print(f"⏱️  Duration: {results['total_duration']:.3f}s")
        
        if results['failed'] > 0:
            print("❌ Some tests failed")
            return False
        else:
            print("✅ All tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Full test suite failed: {e}")
        return False

def test_specific_component(component_name):
    """Test a specific component."""
    print(f"🔧 Testing {component_name}")
    print("=" * 50)
    
    try:
        if component_name == "exporters":
            from materialx_addon.exporters.material_exporter import MaterialExporter
            exporter = MaterialExporter()
            print("✅ MaterialExporter created")
            
        elif component_name == "mappers":
            from materialx_addon.mappers.node_mapper_registry import NodeMapperRegistry
            registry = NodeMapperRegistry()
            print(f"✅ NodeMapperRegistry created with {len(registry.get_available_mappers())} mappers")
            
        elif component_name == "core":
            from materialx_addon.core.document_manager import DocumentManager
            doc_manager = DocumentManager()
            doc = doc_manager.create_document()
            print("✅ DocumentManager and document created")
            
        elif component_name == "validation":
            from materialx_addon.validation.validator import MaterialXValidator
            validator = MaterialXValidator()
            print("✅ MaterialXValidator created")
            
        else:
            print(f"❌ Unknown component: {component_name}")
            return False
            
        print(f"✅ {component_name} test completed")
        return True
        
    except Exception as e:
        print(f"❌ {component_name} test failed: {e}")
        return False

def main():
    """Main test runner for Blender console."""
    print("🎯 MaterialX Addon Test Runner")
    print("=" * 50)
    print("Available commands:")
    print("  run_quick_tests()     - Run basic functionality tests")
    print("  run_full_tests()      - Run complete test suite")
    print("  test_specific_component('exporters')  - Test exporters")
    print("  test_specific_component('mappers')    - Test mappers")
    print("  test_specific_component('core')       - Test core components")
    print("  test_specific_component('validation') - Test validation")
    print("=" * 50)
    
    # Run quick tests by default
    success = run_quick_tests()
    
    if success:
        print("\n💡 Try running 'run_full_tests()' for comprehensive testing")
    
    return success

# Run quick tests when script is executed
if __name__ == "__main__":
    main()
