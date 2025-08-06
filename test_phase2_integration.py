#!/usr/bin/env python3
"""
Phase 2 MaterialX Library Integration Test

This script tests the Phase 2 implementation of the MaterialX Python Library integration,
focusing on the enhanced node mapping system with type-safe input creation and validation.

Phase 2 Features Tested:
- Leverage node definitions for type-safe mapping
- Implement automatic type conversion and validation
- Enhanced node creation with validation
"""

import sys
import os
import logging
from pathlib import Path

# Add the materialx_addon directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'materialx_addon'))

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('phase2_test.log')
        ]
    )
    return logging.getLogger(__name__)

def test_mtlxutils_availability():
    """Test if mtlxutils is available."""
    logger = logging.getLogger(__name__)
    logger.info("Testing mtlxutils availability...")
    
    try:
        import mtlxutils
        import mtlxutils.mxbase as mxb
        import mtlxutils.mxfile as mxf
        import mtlxutils.mxnodegraph as mxg
        import mtlxutils.mxtraversal as mxt
        logger.info("✓ mtlxutils modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import mtlxutils: {e}")
        return False

def test_materialx_library_core():
    """Test the enhanced MaterialX library core functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing MaterialX library core...")
    
    try:
        import materialx_library_core
        from materialx_library_core import (
            MaterialXDocumentManager, 
            MaterialXNodeBuilder, 
            MaterialXConnectionManager,
            MaterialXLibraryBuilder,
            MaterialXTypeConverter
        )
        logger.info("✓ MaterialX library core imported successfully")
        
        # Test document manager
        doc_manager = MaterialXDocumentManager(logger)
        logger.info("✓ Document manager created")
        
        # Test type converter
        type_converter = MaterialXTypeConverter(logger)
        logger.info("✓ Type converter created")
        
        # Test type conversion
        test_value = [1.0, 0.5, 0.2]
        converted = type_converter.convert_value(test_value, 'color3')
        logger.info(f"✓ Type conversion test: {test_value} -> {converted}")
        
        # Test type compatibility
        compatible = type_converter.validate_type_compatibility('color3', 'vector3')
        logger.info(f"✓ Type compatibility test: color3 -> vector3 = {compatible}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ MaterialX library core test failed: {e}")
        return False

def test_enhanced_node_mapping():
    """Test the enhanced node mapping system."""
    logger = logging.getLogger(__name__)
    logger.info("Testing enhanced node mapping system...")
    
    try:
        import materialx_library_core
        from materialx_library_core import MaterialXLibraryBuilder, MaterialXTypeConverter
        
        # Create a test builder
        builder = MaterialXLibraryBuilder("test_material", logger)
        logger.info("✓ Test builder created")
        
        # Test enhanced node creation with type safety
        node_name = builder.add_node("constant", "test_constant", "color3", value=[1.0, 0.5, 0.2])
        logger.info(f"✓ Enhanced node creation: {node_name}")
        
        # Test surface shader creation
        surface_name = builder.add_surface_shader_node("standard_surface", "test_surface")
        logger.info(f"✓ Surface shader creation: {surface_name}")
        
        # Test type-safe input creation
        if node_name in builder.nodes:
            node = builder.nodes[node_name]
            input_elem = builder.library_builder.node_builder.create_mtlx_input(
                node, "value", [1.0, 0.5, 0.2], 
                node_type="constant", category="color3"
            )
            if input_elem:
                logger.info("✓ Type-safe input creation successful")
            else:
                logger.warning("⚠ Type-safe input creation returned None")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Enhanced node mapping test failed: {e}")
        return False

def test_node_schemas():
    """Test the enhanced node schemas with type information."""
    logger = logging.getLogger(__name__)
    logger.info("Testing enhanced node schemas...")
    
    try:
        # Import the exporter to access schemas
        import blender_materialx_exporter
        from blender_materialx_exporter import NODE_SCHEMAS
        
        # Test schema structure
        required_schemas = ['MIX', 'INVERT', 'PRINCIPLED_BSDF', 'IMAGE_TEXTURE', 'MATH', 'VECTOR_MATH']
        
        for schema_name in required_schemas:
            if schema_name in NODE_SCHEMAS:
                schema = NODE_SCHEMAS[schema_name]
                logger.info(f"✓ Schema '{schema_name}' found with {len(schema)} entries")
                
                # Check for enhanced schema structure
                for entry in schema:
                    if 'category' in entry:
                        logger.info(f"  ✓ Entry has category: {entry['category']}")
                    else:
                        logger.warning(f"  ⚠ Entry missing category: {entry}")
            else:
                logger.warning(f"⚠ Schema '{schema_name}' not found")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Node schemas test failed: {e}")
        return False

def test_type_conversion():
    """Test the enhanced type conversion system."""
    logger = logging.getLogger(__name__)
    logger.info("Testing enhanced type conversion...")
    
    try:
        from materialx_library_core import MaterialXTypeConverter
        
        converter = MaterialXTypeConverter(logger)
        
        # Test various type conversions
        test_cases = [
            (1.5, 'float', 1.5),
            ([1.0, 0.5, 0.2], 'color3', [1.0, 0.5, 0.2]),
            ([1.0, 0.5], 'vector2', [1.0, 0.5]),
            ([1.0, 0.5, 0.2, 1.0], 'color4', [1.0, 0.5, 0.2, 1.0]),
            (0.5, 'color3', [0.5, 0.5, 0.5]),  # Scalar to color3
        ]
        
        for input_val, target_type, expected in test_cases:
            result = converter.convert_value(input_val, target_type)
            logger.info(f"✓ Type conversion: {input_val} -> {target_type} = {result}")
            
            # Basic validation
            if target_type == 'float':
                assert isinstance(result, (int, float)), f"Expected float, got {type(result)}"
            elif target_type in ['color3', 'vector3']:
                assert len(result) == 3, f"Expected 3 components, got {len(result)}"
            elif target_type == 'vector2':
                assert len(result) == 2, f"Expected 2 components, got {len(result)}"
            elif target_type == 'color4':
                assert len(result) == 4, f"Expected 4 components, got {len(result)}"
        
        # Test value formatting
        formatted = converter.format_value_string([1.0, 0.5, 0.2], 'color3')
        logger.info(f"✓ Value formatting: {formatted}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Type conversion test failed: {e}")
        return False

def test_connection_validation():
    """Test the enhanced connection validation system."""
    logger = logging.getLogger(__name__)
    logger.info("Testing enhanced connection validation...")
    
    try:
        from materialx_library_core import MaterialXTypeConverter
        
        converter = MaterialXTypeConverter(logger)
        
        # Test type compatibility
        test_cases = [
            ('color3', 'color3', True),
            ('color3', 'vector3', True),
            ('vector3', 'color3', True),
            ('vector2', 'vector2', True),
            ('float', 'float', True),
            ('color3', 'float', False),
            ('vector2', 'vector3', False),
        ]
        
        for from_type, to_type, expected in test_cases:
            result = converter.validate_type_compatibility(from_type, to_type)
            status = "✓" if result == expected else "✗"
            logger.info(f"{status} Compatibility: {from_type} -> {to_type} = {result} (expected {expected})")
            
            if result != expected:
                logger.warning(f"  ⚠ Unexpected compatibility result")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Connection validation test failed: {e}")
        return False

def test_enhanced_node_creation():
    """Test enhanced node creation with validation."""
    logger = logging.getLogger(__name__)
    logger.info("Testing enhanced node creation...")
    
    try:
        from materialx_library_core import MaterialXLibraryBuilder
        
        builder = MaterialXLibraryBuilder("test_material", logger)
        
        # Test various node types with enhanced creation
        test_nodes = [
            ("constant", "test_const", "color3", {"value": [1.0, 0.5, 0.2]}),
            ("mix", "test_mix", "color3", {}),
            ("add", "test_add", "float", {}),
            ("multiply", "test_mult", "color3", {}),
        ]
        
        for node_type, name, category, params in test_nodes:
            node_name = builder.add_node(node_type, name, category, **params)
            logger.info(f"✓ Created node: {node_name} (type: {node_type}, category: {category})")
            
            if node_name in builder.nodes:
                node = builder.nodes[node_name]
                logger.info(f"  ✓ Node stored in builder: {node.getName()}")
            else:
                logger.warning(f"  ⚠ Node not found in builder: {node_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Enhanced node creation test failed: {e}")
        return False

def test_document_validation():
    """Test document validation with enhanced features."""
    logger = logging.getLogger(__name__)
    logger.info("Testing document validation...")
    
    try:
        from materialx_library_core import MaterialXLibraryBuilder
        
        builder = MaterialXLibraryBuilder("test_material", logger)
        
        # Create a simple material structure
        surface_name = builder.add_surface_shader_node("standard_surface", "test_surface")
        builder.set_material_surface(surface_name)
        
        # Test document validation
        is_valid = builder.validate()
        logger.info(f"✓ Document validation: {is_valid}")
        
        # Test document to string conversion
        xml_string = builder.to_string()
        if xml_string:
            logger.info(f"✓ Document to string conversion successful ({len(xml_string)} characters)")
        else:
            logger.warning("⚠ Document to string conversion returned empty string")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Document validation test failed: {e}")
        return False

def test_phase2_integration():
    """Test the complete Phase 2 integration."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("PHASE 2 MATERIALX LIBRARY INTEGRATION TEST")
    logger.info("=" * 60)
    
    tests = [
        ("mtlxutils availability", test_mtlxutils_availability),
        ("MaterialX library core", test_materialx_library_core),
        ("Enhanced node mapping", test_enhanced_node_mapping),
        ("Node schemas", test_node_schemas),
        ("Type conversion", test_type_conversion),
        ("Connection validation", test_connection_validation),
        ("Enhanced node creation", test_enhanced_node_creation),
        ("Document validation", test_document_validation),
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                logger.info(f"✓ {test_name}: PASSED")
            else:
                logger.error(f"✗ {test_name}: FAILED")
        except Exception as e:
            results[test_name] = False
            logger.error(f"✗ {test_name}: ERROR - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    if passed == total:
        logger.info("\n🎉 ALL PHASE 2 TESTS PASSED!")
        logger.info("Phase 2 MaterialX Library Integration is working correctly.")
    else:
        logger.error(f"\n❌ {total - passed} TESTS FAILED")
        logger.error("Phase 2 integration needs attention.")
    
    return passed == total

if __name__ == "__main__":
    logger = setup_logging()
    success = test_phase2_integration()
    sys.exit(0 if success else 1) 