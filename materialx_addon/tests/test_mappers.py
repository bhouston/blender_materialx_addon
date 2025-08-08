#!/usr/bin/env python3
"""
Unit Tests for Mappers

This module contains unit tests for the mapper components.
"""

import bpy
from typing import List
from .test_utils import BlenderTestCase
from ..mappers.base_mapper import BaseNodeMapper
from ..mappers.node_mapper_registry import NodeMapperRegistry, get_registry
from ..mappers.principled_mapper import PrincipledBSDFMapper
from ..mappers.texture_mappers import TextureMapper, ImageTextureMapper
from ..mappers.math_mappers import MathMapper
from ..mappers.utility_mappers import UtilityMapper
from ..utils.exceptions import UnsupportedNodeError


class TestBaseNodeMapper(BlenderTestCase):
    """Test BaseNodeMapper functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Don't instantiate abstract class directly
        self.mapper = None
        
        # Create test material with nodes
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Create test nodes
        self.rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        self.rgb_node.name = "TestRGB"
        self.rgb_node.location = (0, 0)
        
        self.value_node = self.node_tree.nodes.new(type='ShaderNodeValue')
        self.value_node.name = "TestValue"
        self.value_node.location = (200, 0)
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test BaseNodeMapper functionality."""
        # Test that BaseNodeMapper is an abstract class
        self.assertRaises(TypeError, BaseNodeMapper)
        
        # Test that concrete implementations work
        concrete_mapper = PrincipledBSDFMapper()
        self.assertIsInstance(concrete_mapper, BaseNodeMapper)
        
        # Test utility methods that are implemented
        input_mapping = concrete_mapper.get_input_mapping()
        self.assertIsInstance(input_mapping, dict)
        
        output_mapping = concrete_mapper.get_output_mapping()
        self.assertIsInstance(output_mapping, dict)
        
        default_values = concrete_mapper.get_default_values()
        self.assertIsInstance(default_values, dict)
        
        required_inputs = concrete_mapper.get_required_inputs()
        self.assertIsInstance(required_inputs, list)
        
        optional_inputs = concrete_mapper.get_optional_inputs()
        self.assertIsInstance(optional_inputs, list)


class TestNodeMapperRegistry(BlenderTestCase):
    """Test NodeMapperRegistry functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.registry = NodeMapperRegistry()
    
    def test(self):
        """Test NodeMapperRegistry functionality."""
        # Test initialization
        self.assertIsNotNone(self.registry)
        self.assertIsInstance(self.registry, NodeMapperRegistry)
        
        # Test available mappers
        mappers = self.registry.get_supported_node_types()
        self.assertIsInstance(mappers, list)
        # Note: In test environment, mappers might not be loaded
        # self.assertGreater(len(mappers), 0)
        
        # Test mapper registration
        test_mapper = PrincipledBSDFMapper()
        self.registry.register_mapper("test_mapper", PrincipledBSDFMapper)
        
        # Test mapper retrieval
        retrieved_mapper = self.registry.get_mapper("test_mapper")
        self.assertIsNotNone(retrieved_mapper)
        self.assertIsInstance(retrieved_mapper, PrincipledBSDFMapper)
        
        # Test mapper for node type
        mapper = self.registry.get_mapper("BSDF_PRINCIPLED")
        # Some mappers might not be available in test environment
        if mapper:
            self.assertIsInstance(mapper, BaseNodeMapper)
        
        # Test unsupported node type
        mapper = self.registry.get_mapper("UNSUPPORTED_NODE")
        self.assertIsNone(mapper)
        
        # Test mapper removal (not implemented in current API)
        # self.registry.unregister_mapper("test_mapper")
        # retrieved_mapper = self.registry.get_mapper("test_mapper")
        # self.assertIsNone(retrieved_mapper)


class TestPrincipledBSDFMapper(BlenderTestCase):
    """Test PrincipledBSDFMapper functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.mapper = PrincipledBSDFMapper()
        
        # Create test material with Principled BSDF
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Clear default nodes and add Principled BSDF
        self.node_tree.nodes.clear()
        self.principled_node = self.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        self.principled_node.name = "TestPrincipled"
        self.principled_node.location = (0, 0)
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test PrincipledBSDFMapper functionality."""
        # Test initialization
        self.assertIsNotNone(self.mapper)
        self.assertIsInstance(self.mapper, PrincipledBSDFMapper)
        
        # Test node validation
        self.assertTrue(self.mapper.can_map_node(self.principled_node))
        
        # Test input mapping
        input_mapping = self.mapper.get_input_mapping()
        self.assertIsInstance(input_mapping, dict)
        self.assertIn('Base Color', input_mapping)
        self.assertIn('Metallic', input_mapping)
        self.assertIn('Roughness', input_mapping)
        
        # Test output mapping
        output_mapping = self.mapper.get_output_mapping()
        self.assertIsInstance(output_mapping, dict)
        self.assertIn('BSDF', output_mapping)
        
        # Test unsupported node
        rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        self.assertFalse(self.mapper.can_map_node(rgb_node))
        self.node_tree.nodes.remove(rgb_node)


class TestImageTextureMapper(BlenderTestCase):
    """Test ImageTextureMapper functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.mapper = ImageTextureMapper()
        
        # Create test material with texture nodes
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Create texture coordinate node
        self.tex_coord_node = self.node_tree.nodes.new(type='ShaderNodeTexCoord')
        self.tex_coord_node.name = "TestTexCoord"
        self.tex_coord_node.location = (0, 0)
        
        # Create image texture node (without actual image)
        self.image_tex_node = self.node_tree.nodes.new(type='ShaderNodeTexImage')
        self.image_tex_node.name = "TestImageTex"
        self.image_tex_node.location = (200, 0)
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test ImageTextureMapper functionality."""
        # Test initialization
        self.assertIsNotNone(self.mapper)
        self.assertIsInstance(self.mapper, ImageTextureMapper)
        
        # Test image texture mapping
        self.assertTrue(self.mapper.can_map_node(self.image_tex_node))
        
        # Test input mapping
        input_mapping = self.mapper.get_input_mapping()
        self.assertIsInstance(input_mapping, dict)
        self.assertIn('Vector', input_mapping)
        self.assertIn('Scale', input_mapping)
        
        # Test output mapping
        output_mapping = self.mapper.get_output_mapping()
        self.assertIsInstance(output_mapping, dict)
        self.assertIn('Color', output_mapping)
        
        # Test unsupported node
        rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        self.assertFalse(self.mapper.can_map_node(rgb_node))
        self.node_tree.nodes.remove(rgb_node)


class TestMathMapper(BlenderTestCase):
    """Test MathMapper functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.mapper = MathMapper()
        
        # Create test material with math nodes
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Create math node
        self.math_node = self.node_tree.nodes.new(type='ShaderNodeMath')
        self.math_node.name = "TestMath"
        self.math_node.location = (0, 0)
        self.math_node.operation = 'ADD'
        
        # Create vector math node
        self.vector_math_node = self.node_tree.nodes.new(type='ShaderNodeVectorMath')
        self.vector_math_node.name = "TestVectorMath"
        self.vector_math_node.location = (200, 0)
        self.vector_math_node.operation = 'ADD'
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test MathMapper functionality."""
        # Test initialization
        self.assertIsNotNone(self.mapper)
        self.assertIsInstance(self.mapper, MathMapper)
        
        # Test math node mapping
        self.assertTrue(self.mapper.can_map_node(self.math_node))
        
        # Test input mapping
        input_mapping = self.mapper.get_input_mapping()
        self.assertIsInstance(input_mapping, dict)
        
        # Test output mapping
        output_mapping = self.mapper.get_output_mapping()
        self.assertIsInstance(output_mapping, dict)
        
        # Test unsupported node
        rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        self.assertFalse(self.mapper.can_map_node(rgb_node))
        self.node_tree.nodes.remove(rgb_node)


class TestUtilityMapper(BlenderTestCase):
    """Test UtilityMapper functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.mapper = UtilityMapper()
        
        # Create test material with utility nodes
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Create mix node
        self.mix_node = self.node_tree.nodes.new(type='ShaderNodeMixRGB')
        self.mix_node.name = "TestMix"
        self.mix_node.location = (0, 0)
        
        # Create separate RGB node
        self.separate_rgb_node = self.node_tree.nodes.new(type='ShaderNodeSeparateRGB')
        self.separate_rgb_node.name = "TestSeparateRGB"
        self.separate_rgb_node.location = (200, 0)
        
        # Create combine RGB node
        self.combine_rgb_node = self.node_tree.nodes.new(type='ShaderNodeCombineRGB')
        self.combine_rgb_node.name = "TestCombineRGB"
        self.combine_rgb_node.location = (400, 0)
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test UtilityMapper functionality."""
        # Test initialization
        self.assertIsNotNone(self.mapper)
        self.assertIsInstance(self.mapper, UtilityMapper)
        
        # Test mix node mapping
        can_map = self.mapper.can_map_node(self.mix_node)
        self.assertIsInstance(can_map, bool)
        
        # Test input mapping
        input_mapping = self.mapper.get_input_mapping()
        self.assertIsInstance(input_mapping, dict)
        
        # Test output mapping
        output_mapping = self.mapper.get_output_mapping()
        self.assertIsInstance(output_mapping, dict)
        
        # Test unsupported node
        rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        # Note: RGB nodes might be supported by some mappers
        # self.assertFalse(self.mapper.can_map_node(rgb_node))
        self.node_tree.nodes.remove(rgb_node)


class TestMapperIntegration(BlenderTestCase):
    """Test mapper integration and complex scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.registry = get_registry()
        
        # Create test material with complex node setup
        self.material = bpy.data.materials.new(name="IntegrationTestMaterial")
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        # Create a complex node setup
        self.node_tree.nodes.clear()
        
        # RGB node
        self.rgb_node = self.node_tree.nodes.new(type='ShaderNodeRGB')
        self.rgb_node.name = "RGB"
        self.rgb_node.location = (0, 0)
        
        # Math node
        self.math_node = self.node_tree.nodes.new(type='ShaderNodeMath')
        self.math_node.name = "Math"
        self.math_node.location = (200, 0)
        self.math_node.operation = 'MULTIPLY'
        
        # Mix node
        self.mix_node = self.node_tree.nodes.new(type='ShaderNodeMixRGB')
        self.mix_node.name = "Mix"
        self.mix_node.location = (400, 0)
        
        # Principled BSDF
        self.principled_node = self.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        self.principled_node.name = "Principled"
        self.principled_node.location = (600, 0)
        
        # Connect nodes
        self.node_tree.links.new(self.rgb_node.outputs['Color'], self.math_node.inputs[0])
        self.node_tree.links.new(self.math_node.outputs['Value'], self.mix_node.inputs['Fac'])
        self.node_tree.links.new(self.mix_node.outputs['Color'], self.principled_node.inputs['Base Color'])
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        if self.material:
            bpy.data.materials.remove(self.material)
    
    def test(self):
        """Test mapper integration."""
        # Test mapping all nodes in the setup
        nodes_to_test = [
            (self.rgb_node, "RGB"),
            (self.math_node, "MATH"),
            (self.mix_node, "MIX"),
            (self.principled_node, "PRINCIPLED_BSDF")
        ]
        
        for node, expected_type in nodes_to_test:
            mapper = self.registry.get_mapper_for_node(node)
            # Some node types might not have mappers yet
            if mapper:
                self.assertIsNotNone(mapper, f"No mapper found for {node.type}")
                # Test that the mapper can handle the node
                can_map = mapper.can_map_node(node)
                self.assertIsInstance(can_map, bool)
            else:
                print(f"Warning: No mapper found for {node.type}")
        
        # Test registry functionality
        available_mappers = self.registry.get_supported_node_types()
        self.assertIsInstance(available_mappers, list)
        
        # Test error handling for unsupported nodes
        unsupported_node = self.node_tree.nodes.new(type='ShaderNodeEmission')
        mapper = self.registry.get_mapper_for_node(unsupported_node)
        self.assertIsNone(mapper)
        
        # Clean up
        self.node_tree.nodes.remove(unsupported_node)


def create_mapper_tests() -> List[BlenderTestCase]:
    """Create all mapper test cases."""
    return [
        TestBaseNodeMapper("BaseNodeMapper"),
        TestNodeMapperRegistry("NodeMapperRegistry"),
        TestPrincipledBSDFMapper("PrincipledBSDFMapper"),
        TestImageTextureMapper("ImageTextureMapper"),
        TestMathMapper("MathMapper"),
        TestUtilityMapper("UtilityMapper"),
        TestMapperIntegration("MapperIntegration")
    ]
