#!/usr/bin/env python3
"""
Unit Tests for Core Components

This module contains unit tests for the core components.
"""

import bpy
import os
import tempfile
import MaterialX as mx
from typing import List
from .test_utils import BlenderTestCase
from ..core.document_manager import DocumentManager
from ..core.advanced_validator import AdvancedValidator
from ..core.type_converter import TypeConverter
from ..core.library_builder import LibraryBuilder
from ..validation.validator import MaterialXValidator
from ..utils.exceptions import MaterialXExportError


class TestDocumentManager(BlenderTestCase):
    """Test DocumentManager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.doc_manager = DocumentManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test DocumentManager functionality."""
        # Test initialization
        self.assertIsNotNone(self.doc_manager)
        self.assertIsInstance(self.doc_manager, DocumentManager)
        
        # Test document creation
        doc = self.doc_manager.create_document("test_document")
        self.assertIsNotNone(doc)
        self.assertIsInstance(doc, mx.Document)
        
        # Test document validation
        validation_result = self.doc_manager.validate_document(doc)
        self.assertIsInstance(validation_result, dict)
        self.assertIn('valid', validation_result)
        
        # Test document info
        doc_info = self.doc_manager.get_document_info("test_document")
        self.assertIsNotNone(doc_info)
        self.assertIn('version', doc_info)
        self.assertIn('created_at', doc_info)
        
        # Test document listing
        documents = self.doc_manager.list_documents()
        self.assertIsInstance(documents, list)
        self.assertIn("test_document", documents)
        
        # Test document clearing
        self.doc_manager.clear_documents()
        documents = self.doc_manager.list_documents()
        self.assertEqual(len(documents), 0)


class TestAdvancedValidator(BlenderTestCase):
    """Test AdvancedValidator functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.validator = AdvancedValidator()
        
        # Create test material
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        
        # Add some nodes
        node_tree = self.material.node_tree
        node_tree.nodes.clear()
        
        rgb_node = node_tree.nodes.new(type='ShaderNodeRGB')
        rgb_node.name = "TestRGB"
        
        principled_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.name = "TestPrincipled"
        
        # Connect nodes
        node_tree.links.new(rgb_node.outputs['Color'], principled_node.inputs['Base Color'])
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test AdvancedValidator functionality."""
        # Test initialization
        self.assertIsNotNone(self.validator)
        self.assertIsInstance(self.validator, AdvancedValidator)
        
        # Test document validation
        # Create a test MaterialX document
        doc = mx.createDocument()
        
        # Add a test material
        material = doc.addMaterial("TestMaterial")
        shader_ref = material.addShaderRef("", "standard_surface")
        
        # Add a test node
        node = doc.addNode("TestNode", "constant")
        node.addInput("in", "float").setValue(1.0)
        node.addOutput("out", "float")
        
        # Validate the document
        result = self.validator.validate_document(doc)
        self.assertIsNotNone(result)
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIn('info', result)
        self.assertIn('statistics', result)
        
        # Test validation with options
        options = {'strict_mode': True, 'check_textures': False}
        result = self.validator.validate_document(doc, options)
        self.assertIsNotNone(result)
        
        # Test validation rules
        rules = self.validator.get_validation_rules()
        self.assertIsInstance(rules, dict)


class TestTypeConverter(BlenderTestCase):
    """Test TypeConverter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.converter = TypeConverter()
    
    def test(self):
        """Test TypeConverter functionality."""
        # Test initialization
        self.assertIsNotNone(self.converter)
        self.assertIsInstance(self.converter, TypeConverter)
        
        # Test Blender to MaterialX type conversion
        blender_type = 'RGBA'
        mtlx_type = self.converter.blender_socket_to_materialx_type(blender_type)
        self.assertEqual(mtlx_type, 'color4')
        
        blender_type = 'VALUE'
        mtlx_type = self.converter.blender_socket_to_materialx_type(blender_type)
        self.assertEqual(mtlx_type, 'float')
        
        blender_type = 'VECTOR'
        mtlx_type = self.converter.blender_socket_to_materialx_type(blender_type)
        self.assertEqual(mtlx_type, 'vector3')
        
        # Test MaterialX to Blender type conversion
        mtlx_type = 'color3'
        blender_type = self.converter.materialx_type_to_blender_socket(mtlx_type)
        self.assertEqual(blender_type, 'RGB')
        
        mtlx_type = 'float'
        blender_type = self.converter.materialx_type_to_blender_socket(mtlx_type)
        self.assertEqual(blender_type, 'VALUE')
        
        # Test value conversion
        blender_value = (1.0, 0.5, 0.0, 1.0)
        mtlx_value = self.converter.convert_value(blender_value, 'color4')
        self.assertIsInstance(mtlx_value, list)
        
        blender_value = 0.5
        mtlx_value = self.converter.convert_value(blender_value, 'float')
        self.assertEqual(mtlx_value, 0.5)
        
        # Test type validation
        self.assertTrue(self.converter.validate_type_compatibility('color3', 'color4'))
        self.assertTrue(self.converter.validate_type_compatibility('float', 'integer'))
        self.assertFalse(self.converter.validate_type_compatibility('color3', 'string'))


class TestLibraryBuilder(BlenderTestCase):
    """Test LibraryBuilder functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.builder = LibraryBuilder()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test LibraryBuilder functionality."""
        # Test initialization
        self.assertIsNotNone(self.builder)
        self.assertIsInstance(self.builder, LibraryBuilder)
        
        # Test library loading
        success = self.builder.load_standard_libraries()
        self.assertIsInstance(success, bool)
        
        # Test library listing
        libraries = self.builder.list_libraries()
        self.assertIsInstance(libraries, list)
        
        # Test library retrieval
        library = self.builder.get_library("standard")
        if library:
            self.assertIsInstance(library, mx.Document)
        
        # Test node definitions
        node_defs = self.builder.get_node_definitions()
        self.assertIsInstance(node_defs, list)
        
        # Test node definition finding
        node_def = self.builder.find_node_definition("constant")
        # Note: node_def might be None if standard libraries aren't loaded
        if node_def:
            self.assertIsInstance(node_def, mx.NodeDef)


class TestMaterialXValidator(BlenderTestCase):
    """Test MaterialXValidator functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.validator = MaterialXValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test MaterialXValidator functionality."""
        # Test initialization
        self.assertIsNotNone(self.validator)
        self.assertIsInstance(self.validator, MaterialXValidator)
        
        # Test document validation
        doc = mx.createDocument()
        
        # Add a simple node
        node = doc.addNode("constant")
        node.setAttribute("value", "1.0 0.5 0.0")
        
        result = self.validator.validate_document(doc)
        self.assertIsNotNone(result)
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        
        # Test file validation
        test_file = os.path.join(self.temp_dir, "test_validation.mtlx")
        
        # Create a simple MaterialX file
        with open(test_file, 'w') as f:
            f.write('''<?xml version="1.0"?>
<materialx version="1.39">
  <constant name="test_constant" type="color3" value="1.0 0.5 0.0"/>
</materialx>''')
        
        result = self.validator.validate_file(test_file)
        self.assertIsNotNone(result)
        self.assertIn('valid', result)
        
        # Test validation options
        options = {'strict_mode': True, 'check_schema': True}
        result = self.validator.validate_document(doc, options)
        self.assertIsNotNone(result)
        
        # Test validation result structure
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)


class TestCoreIntegration(BlenderTestCase):
    """Test core components integration."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.doc_manager = DocumentManager()
        self.validator = AdvancedValidator()
        self.converter = TypeConverter()
        self.builder = LibraryBuilder()
        self.mx_validator = MaterialXValidator()
        
        # Create test material
        self.material = bpy.data.materials.new(name="IntegrationTestMaterial")
        self.material.use_nodes = True
        
        # Add nodes
        node_tree = self.material.node_tree
        node_tree.nodes.clear()
        
        rgb_node = node_tree.nodes.new(type='ShaderNodeRGB')
        rgb_node.name = "TestRGB"
        rgb_node.outputs['Color'].default_value = (1.0, 0.5, 0.0, 1.0)
        
        principled_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.name = "TestPrincipled"
        
        node_tree.links.new(rgb_node.outputs['Color'], principled_node.inputs['Base Color'])
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
        
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test core components integration."""
        # Test complete workflow
        # 1. Create document
        doc = self.doc_manager.create_document("integration_test")
        self.assertIsNotNone(doc)
        
        # 2. Add material to document
        material = self.doc_manager.add_material(doc, "TestMaterial", "standard_surface")
        self.assertIsNotNone(material)
        
        # 3. Add a test node
        node = self.doc_manager.add_node(doc, "TestNode", "constant", "color3")
        self.assertIsNotNone(node)
        
        # 4. Add inputs and outputs
        input_node = self.doc_manager.add_input(node, "in", "float", 1.0)
        output_node = self.doc_manager.add_output(node, "out", "color3")
        self.assertIsNotNone(input_node)
        self.assertIsNotNone(output_node)
        
        # 5. Validate document
        doc_validation = self.validator.validate_document(doc)
        self.assertIsNotNone(doc_validation)
        self.assertIn('valid', doc_validation)
        
        # 6. Test document info
        doc_info = self.doc_manager.get_document_info("integration_test")
        self.assertIsNotNone(doc_info)
        self.assertIn('version', doc_info)
        
        # Test error handling in integration
        # Test with invalid document creation
        self.assertRaises(Exception, 
                         self.doc_manager.create_document, None)





def create_core_tests() -> List[BlenderTestCase]:
    """Create all core component test cases."""
    return [
        TestDocumentManager("DocumentManager"),
        TestAdvancedValidator("AdvancedValidator"),
        TestTypeConverter("TypeConverter"),
        TestLibraryBuilder("LibraryBuilder"),
        TestMaterialXValidator("MaterialXValidator"),
        TestCoreIntegration("CoreIntegration"),

    ]
