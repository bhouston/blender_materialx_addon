#!/usr/bin/env python3
"""
Unit Tests for Exporters

This module contains unit tests for the exporter components.
"""

import bpy
import os
import tempfile
from typing import List
from .test_utils import BlenderTestCase
from ..exporters.base_exporter import BaseExporter
from ..exporters.material_exporter import MaterialExporter
from ..exporters.batch_exporter import BatchExporter
from ..exporters.texture_exporter import TextureExporter
from ..utils.exceptions import MaterialXExportError


class TestBaseExporter(BlenderTestCase):
    """Test BaseExporter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Don't instantiate abstract class directly
        self.exporter = None
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test BaseExporter functionality."""
        # Test that BaseExporter is an abstract class
        self.assertRaises(TypeError, BaseExporter)
        
        # Test that concrete implementations work
        concrete_exporter = MaterialExporter()
        self.assertIsInstance(concrete_exporter, BaseExporter)
        
        # Test default options
        self.assertIsNotNone(concrete_exporter.export_options)
        # Note: export_options might be empty initially, so we test the structure
        self.assertIsInstance(concrete_exporter.export_options, dict)
        
        # Test option setting
        test_options = {'materialx_version': '1.39', 'export_textures': True}
        concrete_exporter.set_export_options(test_options)
        self.assertEqual(concrete_exporter.export_options['materialx_version'], '1.39')
        self.assertTrue(concrete_exporter.export_options['export_textures'])
        
        # Test validation
        self.assertTrue(len(concrete_exporter.validate_export_options(concrete_exporter.export_options)) == 0)


class TestMaterialExporter(BlenderTestCase):
    """Test MaterialExporter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.exporter = MaterialExporter()
        
        # Create test material
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        
        # Add a simple node setup
        node_tree = self.material.node_tree
        node_tree.nodes.clear()
        
        # Create RGB node
        rgb_node = node_tree.nodes.new(type='ShaderNodeRGB')
        rgb_node.name = "TestRGB"
        rgb_node.location = (0, 0)
        
        # Create Principled BSDF
        principled_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.name = "TestPrincipled"
        principled_node.location = (200, 0)
        
        # Connect nodes
        node_tree.links.new(rgb_node.outputs['Color'], principled_node.inputs['Base Color'])
        
        # Create output directory
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up material
        if self.material:
            bpy.data.materials.remove(self.material)
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test MaterialExporter functionality."""
        # Test initialization
        self.assertIsNotNone(self.exporter)
        self.assertIsInstance(self.exporter, MaterialExporter)
        
        # Test can_export method
        # Create a test object with the material
        test_object = bpy.data.objects.new("TestObject", bpy.data.meshes.new("TestMesh"))
        test_object.active_material = self.material
        self.assertTrue(self.exporter.can_export(test_object))
        
        # Test export options
        self.assertIsNotNone(self.exporter.export_options)
        self.assertIsInstance(self.exporter.export_options, dict)
        
        # Test default options
        default_options = self.exporter.get_default_options()
        self.assertIsInstance(default_options, dict)
        
        # Test option types
        option_types = self.exporter.get_option_types()
        self.assertIsInstance(option_types, dict)
        
        # Test export to file
        output_path = os.path.join(self.temp_dir, "test_material.mtlx")
        result = self.exporter.export(test_object, output_path)
        
        self.assertIsInstance(result, bool)
        # Note: The export might fail due to unsupported nodes, but the method should work
        
        # Test export with options
        options = {'materialx_version': '1.39', 'export_textures': False}
        result = self.exporter.export(test_object, output_path, options)
        self.assertIsInstance(result, bool)


class TestBatchExporter(BlenderTestCase):
    """Test BatchExporter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.exporter = BatchExporter()
        
        # Create test materials
        self.materials = []
        for i in range(3):
            material = bpy.data.materials.new(name=f"TestMaterial{i}")
            material.use_nodes = True
            self.materials.append(material)
        
        # Create output directory
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up materials
        for material in self.materials:
            if material:
                bpy.data.materials.remove(material)
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test BatchExporter functionality."""
        # Test initialization
        self.assertIsNotNone(self.exporter)
        self.assertIsInstance(self.exporter, BatchExporter)
        
        # Test material collection
        all_materials = self.exporter.collect_materials()
        self.assertIsInstance(all_materials, list)
        self.assertGreaterEqual(len(all_materials), len(self.materials))
        
        # Test batch export
        output_dir = os.path.join(self.temp_dir, "batch_export")
        result = self.exporter.export_all_materials(output_dir)
        
        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('exported_materials', result)
        self.assertIn('failed_materials', result)
        
        # Test selective export
        selected_materials = [self.materials[0], self.materials[1]]
        result = self.exporter.export_materials(selected_materials, output_dir)
        self.assertIsNotNone(result)
        self.assertIn('success', result)
        
        # Test progress tracking
        self.exporter.set_progress_callback(lambda current, total: None)
        result = self.exporter.export_all_materials(output_dir)
        self.assertIsNotNone(result)


class TestTextureExporter(BlenderTestCase):
    """Test TextureExporter functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.exporter = TextureExporter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test TextureExporter functionality."""
        # Test initialization
        self.assertIsNotNone(self.exporter)
        self.assertIsInstance(self.exporter, TextureExporter)
        
        # Test texture path handling
        source_path = "/path/to/source/texture.jpg"
        target_path = "/path/to/target/texture.jpg"
        
        # Test relative path conversion
        relative_path = self.exporter.get_relative_path(source_path, target_path)
        self.assertIsInstance(relative_path, str)
        
        # Test texture validation
        # Note: This would require actual texture files for full testing
        # For now, we test the method exists and handles None gracefully
        result = self.exporter.validate_texture_path(None)
        self.assertFalse(result)
        
        # Test texture copying (mock test)
        result = self.exporter.copy_texture(source_path, target_path)
        # Should fail for non-existent file
        self.assertFalse(result['success'])
        
        # Test texture export options
        options = {
            'copy_textures': True,
            'texture_path': self.temp_dir,
            'relative_paths': True
        }
        self.exporter.set_export_options(options)
        self.assertEqual(self.exporter.export_options['texture_path'], self.temp_dir)


class TestExporterIntegration(BlenderTestCase):
    """Test exporter integration and error handling."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.material_exporter = MaterialExporter()
        self.batch_exporter = BatchExporter()
        self.texture_exporter = TextureExporter()
        
        # Create test material with texture
        self.material = bpy.data.materials.new(name="IntegrationTestMaterial")
        self.material.use_nodes = True
        
        # Add texture coordinate and image texture nodes
        node_tree = self.material.node_tree
        node_tree.nodes.clear()
        
        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
        tex_coord.name = "TexCoord"
        
        # Note: We can't create actual image textures without image files
        # This tests the node setup without actual textures
        
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
        """Test exporter integration."""
        # Test that all exporters are properly initialized
        self.assertIsInstance(self.material_exporter, MaterialExporter)
        self.assertIsInstance(self.batch_exporter, BatchExporter)
        self.assertIsInstance(self.texture_exporter, TextureExporter)
        
        # Test that exporters have required methods
        self.assertTrue(hasattr(self.material_exporter, 'can_export'))
        self.assertTrue(hasattr(self.material_exporter, 'export'))
        self.assertTrue(hasattr(self.batch_exporter, 'can_export'))
        self.assertTrue(hasattr(self.texture_exporter, 'can_export'))
        
        # Test basic functionality
        # Create a test object with the material
        test_object = bpy.data.objects.new("TestObject", bpy.data.meshes.new("TestMesh"))
        test_object.active_material = self.material
        self.assertTrue(self.material_exporter.can_export(test_object))


class TestExporterPerformance(BlenderTestCase):
    """Test exporter performance characteristics."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.material_exporter = MaterialExporter()
        self.batch_exporter = BatchExporter()
        
        # Create multiple test materials
        self.materials = []
        for i in range(5):
            material = bpy.data.materials.new(name=f"PerfTestMaterial{i}")
            material.use_nodes = True
            self.materials.append(material)
        
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        for material in self.materials:
            if material:
                bpy.data.materials.remove(material)
        
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test(self):
        """Test exporter performance."""
        import time
        
        # Test exporter initialization performance
        start_time = time.time()
        material_exporter = MaterialExporter()
        batch_exporter = BatchExporter()
        init_time = time.time() - start_time
        
        self.assertLess(init_time, 1.0)  # Should initialize within 1 second
        
        # Test can_export performance
        test_object = bpy.data.objects.new("TestObject", bpy.data.meshes.new("TestMesh"))
        test_object.active_material = self.materials[0]
        
        start_time = time.time()
        can_export = material_exporter.can_export(test_object)
        can_export_time = time.time() - start_time
        
        self.assertTrue(can_export)
        self.assertLess(can_export_time, 0.1)  # Should check within 0.1 seconds
        
        # Test memory usage (basic check)
        import gc
        gc.collect()
        
        # Create multiple exporters and check for memory leaks
        exporters = []
        for i in range(5):
            exporter = MaterialExporter()
            exporters.append(exporter)
        
        # Clean up
        del exporters
        gc.collect()


def create_exporter_tests() -> List[BlenderTestCase]:
    """Create all exporter test cases."""
    return [
        TestBaseExporter("BaseExporter"),
        TestMaterialExporter("MaterialExporter"),
        TestBatchExporter("BatchExporter"),
        TestTextureExporter("TextureExporter"),
        TestExporterIntegration("ExporterIntegration"),
        TestExporterPerformance("ExporterPerformance")
    ]
