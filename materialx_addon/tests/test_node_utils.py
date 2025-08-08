#!/usr/bin/env python3
"""
Unit Tests for Node Utilities

This module contains unit tests for the NodeUtils class and related functionality.
"""

import bpy
from typing import List
from .test_utils import BlenderTestCase
from ..utils.node_utils import NodeUtils
from ..config.node_mappings import NODE_MAPPING, is_node_supported, get_supported_node_types


class TestNodeUtilsBasic(BlenderTestCase):
    """Test basic NodeUtils functionality."""
    
    def test(self):
        """Test basic NodeUtils functionality."""
        # Test format_socket_value
        self.assertEqual(NodeUtils.format_socket_value(1.0), "1.0")
        self.assertEqual(NodeUtils.format_socket_value([1, 2, 3]), "1 2 3")
        self.assertEqual(NodeUtils.format_socket_value((0.5, 0.5, 0.5)), "0.5 0.5 0.5")
        self.assertEqual(NodeUtils.format_socket_value(None), "0")
        
        # Test is_node_supported
        self.assertTrue(NodeUtils.is_node_supported('TEX_COORD'))
        self.assertTrue(NodeUtils.is_node_supported('RGB'))
        self.assertFalse(NodeUtils.is_node_supported('EMISSION'))
        self.assertFalse(NodeUtils.is_node_supported('NONEXISTENT_NODE'))
        
        # Test get_supported_node_types
        supported_types = NodeUtils.get_supported_node_types()
        self.assertIsInstance(supported_types, list)
        self.assertIn('TEX_COORD', supported_types)
        self.assertIn('RGB', supported_types)
        self.assertNotIn('EMISSION', supported_types)


class TestNodeUtilsMapping(BlenderTestCase):
    """Test node mapping functionality."""
    
    def test(self):
        """Test node mapping functionality."""
        # Test get_node_mtlx_type
        mtlx_type, category = NodeUtils.get_node_mtlx_type('TEX_COORD')
        self.assertEqual(mtlx_type, 'texcoord')
        self.assertEqual(category, 'vector2')
        
        mtlx_type, category = NodeUtils.get_node_mtlx_type('RGB')
        self.assertEqual(mtlx_type, 'constant')
        self.assertEqual(category, 'color3')
        
        # Test get_node_output_name_robust
        output_name = NodeUtils.get_node_output_name_robust('TEX_COORD', 'Generated')
        self.assertEqual(output_name, 'out')
        
        output_name = NodeUtils.get_node_output_name_robust('RGB', 'Color')
        self.assertEqual(output_name, 'out')
        
        # Test get_node_input_name_robust
        input_name = NodeUtils.get_node_input_name_robust('MIX', 'A')
        self.assertEqual(input_name, 'fg')
        
        input_name = NodeUtils.get_node_input_name_robust('MIX', 'B')
        self.assertEqual(input_name, 'bg')
        
        # Test error cases
        self.assertRaises(ValueError, NodeUtils.get_node_mtlx_type, 'NONEXISTENT_NODE')
        self.assertRaises(ValueError, NodeUtils.get_node_output_name_robust, 'TEX_COORD', 'NONEXISTENT_OUTPUT')
        self.assertRaises(ValueError, NodeUtils.get_node_input_name_robust, 'MIX', 'NONEXISTENT_INPUT')


class TestNodeUtilsWithBlenderNodes(BlenderTestCase):
    """Test NodeUtils with actual Blender nodes."""
    
    def setUp(self):
        """Set up test environment with Blender nodes."""
        super().setUp()
        
        # Create a test material
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
        
        self.mix_node = self.node_tree.nodes.new(type='ShaderNodeMixRGB')
        self.mix_node.name = "TestMix"
        self.mix_node.location = (400, 0)
        
        # Connect nodes
        self.node_tree.links.new(self.rgb_node.outputs['Color'], self.mix_node.inputs['Color1'])
        self.node_tree.links.new(self.value_node.outputs['Value'], self.mix_node.inputs['Fac'])
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test material
        if self.material:
            bpy.data.materials.remove(self.material)
        
        super().tearDown()
    
    def test(self):
        """Test NodeUtils with actual Blender nodes."""
        # Test get_input_value_or_connection with connected input
        is_connected, value_or_connection, type_str = NodeUtils.get_input_value_or_connection(
            self.mix_node, 'Color1'
        )
        self.assertTrue(is_connected)
        self.assertEqual(value_or_connection, self.rgb_node.name)
        self.assertEqual(type_str, 'RGBA')
        
        # Test get_input_value_or_connection with unconnected input
        is_connected, value_or_connection, type_str = NodeUtils.get_input_value_or_connection(
            self.mix_node, 'Color2'
        )
        self.assertFalse(is_connected)
        self.assertIsInstance(value_or_connection, (list, tuple))
        self.assertEqual(type_str, 'RGBA')
        
        # Test get_node_inputs
        inputs = NodeUtils.get_node_inputs(self.mix_node)
        self.assertIn('Color1', inputs)
        self.assertIn('Color2', inputs)
        self.assertIn('Fac', inputs)
        
        # Test get_node_outputs
        outputs = NodeUtils.get_node_outputs(self.mix_node)
        self.assertIn('Color', outputs)
        
        # Test find_node_by_type
        found_rgb = NodeUtils.find_node_by_type(self.material, 'RGB')
        self.assertIsNotNone(found_rgb)
        self.assertEqual(found_rgb.name, "TestRGB")
        
        found_nonexistent = NodeUtils.find_node_by_type(self.material, 'EMISSION')
        self.assertIsNone(found_nonexistent)
        
        # Test find_nodes_by_type
        rgb_nodes = NodeUtils.find_nodes_by_type(self.material, 'RGB')
        self.assertEqual(len(rgb_nodes), 1)
        self.assertEqual(rgb_nodes[0].name, "TestRGB")
        
        # Test get_node_dependencies
        dependencies = NodeUtils.get_node_dependencies(self.mix_node)
        self.assertIn(self.rgb_node, dependencies)
        self.assertIn(self.value_node, dependencies)
        
        # Test get_node_dependents
        dependents = NodeUtils.get_node_dependents(self.rgb_node)
        self.assertIn(self.mix_node, dependents)


class TestNodeUtilsErrorHandling(BlenderTestCase):
    """Test NodeUtils error handling."""
    
    def test(self):
        """Test NodeUtils error handling."""
        # Test with invalid node (no inputs attribute)
        invalid_node = "not_a_node"
        self.assertRaises(AttributeError, NodeUtils.get_input_value_or_connection, 
                         invalid_node, 'some_input')
        
        # Test with valid node but invalid input name
        if bpy.data.materials:
            material = bpy.data.materials[0]
            if material.use_nodes and material.node_tree.nodes:
                node = material.node_tree.nodes[0]
                self.assertRaises(KeyError, NodeUtils.get_input_value_or_connection, 
                                 node, 'nonexistent_input')


class TestNodeMappingConfig(BlenderTestCase):
    """Test node mapping configuration."""
    
    def test(self):
        """Test node mapping configuration."""
        # Test NODE_MAPPING structure
        self.assertIsInstance(NODE_MAPPING, dict)
        self.assertGreater(len(NODE_MAPPING), 0)
        
        # Test that all entries have required keys
        for node_type, mapping in NODE_MAPPING.items():
            self.assertIn('mtlx_type', mapping)
            self.assertIn('mtlx_category', mapping)
            self.assertIsInstance(mapping['mtlx_type'], str)
            self.assertIsInstance(mapping['mtlx_category'], str)
        
        # Test is_node_supported function
        self.assertTrue(is_node_supported('TEX_COORD'))
        self.assertTrue(is_node_supported('RGB'))
        self.assertFalse(is_node_supported('EMISSION'))
        
        # Test get_supported_node_types function
        supported_types = get_supported_node_types()
        self.assertIsInstance(supported_types, list)
        self.assertGreater(len(supported_types), 0)
        self.assertIn('TEX_COORD', supported_types)
        self.assertIn('RGB', supported_types)


def create_node_utils_tests() -> List[BlenderTestCase]:
    """
    Create all NodeUtils test cases.
    
    Returns:
        List of NodeUtils test cases
    """
    return [
        TestNodeUtilsBasic("NodeUtilsBasic"),
        TestNodeUtilsMapping("NodeUtilsMapping"),
        TestNodeUtilsWithBlenderNodes("NodeUtilsWithBlenderNodes"),
        TestNodeUtilsErrorHandling("NodeUtilsErrorHandling"),
        TestNodeMappingConfig("NodeMappingConfig")
    ]
