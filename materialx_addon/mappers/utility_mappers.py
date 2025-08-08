#!/usr/bin/env python3
"""
Utility Node Mappers

This module provides mappers for utility nodes like RGB, VALUE, TEX_COORD, etc.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_mapper import BaseNodeMapper
from ..config.node_mappings import NODE_MAPPING
from ..utils.exceptions import UnsupportedNodeError


class UtilityMapper(BaseNodeMapper):
    """
    Mapper for utility nodes like RGB, VALUE, TEX_COORD, etc.
    
    This mapper handles common utility nodes that don't require complex mapping logic.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = [
            'RGB', 'VALUE', 'TEX_COORD', 'GEOMETRY', 'NEW_GEOMETRY', 'OBJECT_INFO', 'LIGHT_PATH',
            'HSV_TO_RGB', 'RGB_TO_HSV', 'LUMINANCE', 'CONTRAST', 'SATURATE', 'GAMMA',
            'SEPARATE_XYZ', 'COMBINE_XYZ', 'ROUGHNESS_ANISOTROPY', 'ARTISTIC_IOR',
            'ADD_SHADER', 'MULTIPLY_SHADER', 'MIX_SHADER', 'MIX_RGB', 'VALTORGB',
            'OUTPUT_MATERIAL', 'MIX', 'INVERT', 'SEPARATE_COLOR', 'COMBINE_COLOR',
            'NORMAL_MAP', 'BUMP', 'MAPPING', 'LAYER_WEIGHT', 'CURVE_RGB', 'CLAMP', 'MAP_RANGE'
        ]
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """Check if this mapper can handle the given Blender node."""
        return blender_node.type in self.supported_node_types
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> Any:
        """Map a Blender utility node to a MaterialX node."""
        
        # Get node mapping configuration
        node_config = NODE_MAPPING.get(blender_node.type)
        if not node_config:
            raise UnsupportedNodeError(blender_node.type, blender_node.name)
        
        materialx_type = node_config['mtlx_type']
        materialx_category = node_config['mtlx_category']
        
        # Create MaterialX node
        materialx_node = self._create_materialx_node(
            document, blender_node.name, materialx_type, materialx_category
        )
        
        # Handle specific node types
        if blender_node.type == 'RGB':
            self._map_rgb_node(blender_node, materialx_node)
        elif blender_node.type == 'VALUE':
            self._map_value_node(blender_node, materialx_node)
        elif blender_node.type == 'TEX_COORD':
            self._map_tex_coord_node(blender_node, materialx_node)
        elif blender_node.type == 'GEOMETRY':
            self._map_geometry_node(blender_node, materialx_node)
        elif blender_node.type == 'OBJECT_INFO':
            self._map_object_info_node(blender_node, materialx_node)
        elif blender_node.type == 'LIGHT_PATH':
            self._map_light_path_node(blender_node, materialx_node)
        elif blender_node.type in ['HSV_TO_RGB', 'RGB_TO_HSV']:
            self._map_color_conversion_node(blender_node, materialx_node)
        elif blender_node.type in ['LUMINANCE', 'CONTRAST', 'SATURATE', 'GAMMA']:
            self._map_color_operation_node(blender_node, materialx_node)
        elif blender_node.type in ['SEPARATE_XYZ', 'COMBINE_XYZ']:
            self._map_vector_operation_node(blender_node, materialx_node)
        elif blender_node.type in ['ROUGHNESS_ANISOTROPY', 'ARTISTIC_IOR']:
            self._map_special_utility_node(blender_node, materialx_node)
        elif blender_node.type in ['ADD_SHADER', 'MULTIPLY_SHADER']:
            self._map_shader_operation_node(blender_node, materialx_node)
        elif blender_node.type in ['MIX', 'MIX_RGB']:
            self._map_mix_node(blender_node, materialx_node)
        elif blender_node.type == 'VALTORGB':
            self._map_color_ramp_node(blender_node, materialx_node)
        elif blender_node.type == 'OUTPUT_MATERIAL':
            self._map_material_output_node(blender_node, materialx_node)
        elif blender_node.type in ['INVERT', 'SEPARATE_COLOR', 'COMBINE_COLOR']:
            self._map_color_operation_node(blender_node, materialx_node)
        elif blender_node.type in ['NORMAL_MAP', 'BUMP', 'MAPPING', 'LAYER_WEIGHT', 'CURVE_RGB', 'CLAMP', 'MAP_RANGE']:
            self._map_generic_utility_node(blender_node, materialx_node)
        else:
            # Generic mapping for other utility nodes
            self._map_generic_utility_node(blender_node, materialx_node)
        
        return materialx_node
    
    def _map_rgb_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender RGB node to MaterialX."""
        # RGB nodes are typically constants
        color_value = self._get_input_value(blender_node, 'Color')
        if color_value:
            # Add input with color value
            self._add_input(materialx_node, 'value', 'color3', value=color_value)
            # Add output
            self._add_output(materialx_node, 'out', 'color3')
        else:
            # Default white color
            self._add_input(materialx_node, 'value', 'color3', value=(1.0, 1.0, 1.0))
            self._add_output(materialx_node, 'out', 'color3')
    
    def _map_value_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender Value node to MaterialX."""
        # Value nodes are typically constants
        value = self._get_input_value(blender_node, 'Value')
        if value is not None:
            # Add input with value
            self._add_input(materialx_node, 'value', 'float', value=value)
            # Add output
            self._add_output(materialx_node, 'out', 'float')
        else:
            # Default value
            self._add_input(materialx_node, 'value', 'float', value=0.0)
            self._add_output(materialx_node, 'out', 'float')
    
    def _map_tex_coord_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender Texture Coordinate node to MaterialX."""
        # Texture coordinate nodes provide various coordinate spaces
        # Add outputs for different coordinate types
        outputs = ['Generated', 'Normal', 'UV', 'Object', 'Camera', 'Window', 'Reflection']
        for output_name in outputs:
            if self._has_output(blender_node, output_name):
                self._add_output(materialx_node, 'out', 'vector2')
    
    def _map_geometry_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map a Blender Geometry node to MaterialX."""
        # Geometry nodes provide various geometric information
        outputs = ['Position', 'Normal', 'Tangent', 'True Normal', 'Incoming', 'Parametric', 'Backfacing', 'Pointiness', 'Random Per Island']
        for output_name in outputs:
            if self._has_output(blender_node, output_name):
                if output_name in ['Position', 'Normal', 'Tangent', 'True Normal', 'Incoming']:
                    self._add_output(materialx_node, 'out', 'vector3')
                elif output_name in ['Parametric', 'Backfacing', 'Pointiness', 'Random Per Island']:
                    self._add_output(materialx_node, 'out', 'float')
    
    def _map_object_info_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map a Blender Object Info node to MaterialX."""
        # Object info nodes provide object-specific information
        outputs = ['Location', 'Rotation', 'Scale', 'Color', 'Alpha', 'Object Index', 'Material Index', 'Random']
        for output_name in outputs:
            if self._has_output(blender_node, output_name):
                if output_name in ['Location', 'Rotation', 'Scale']:
                    self._add_output(materialx_node, 'out', 'vector3')
                elif output_name in ['Color']:
                    self._add_output(materialx_node, 'out', 'color3')
                else:
                    self._add_output(materialx_node, 'out', 'float')
    
    def _map_light_path_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map a Blender Light Path node to MaterialX."""
        # Light path nodes provide rendering context information
        outputs = ['Is Camera Ray', 'Is Shadow Ray', 'Is Diffuse Ray', 'Is Glossy Ray', 'Is Singular Ray', 
                  'Is Reflection Ray', 'Is Transmission Ray', 'Ray Length', 'Ray Depth', 'Diffuse Depth', 
                  'Glossy Depth', 'Transparent Depth', 'Transmission Depth']
        for output_name in outputs:
            if self._has_output(blender_node, output_name):
                self._add_output(materialx_node, 'out', 'float')
    
    def _map_color_conversion_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map color conversion nodes (HSV_TO_RGB, RGB_TO_HSV)."""
        if blender_node.type == 'HSV_TO_RGB':
            # Add inputs for HSV
            self._add_input(materialx_node, 'h', 'float', self._get_input_value(blender_node, 'H'))
            self._add_input(materialx_node, 's', 'float', self._get_input_value(blender_node, 'S'))
            self._add_input(materialx_node, 'v', 'float', self._get_input_value(blender_node, 'V'))
            # Add output
            self._add_output(materialx_node, 'out', 'color3')
        elif blender_node.type == 'RGB_TO_HSV':
            # Add input for RGB
            self._add_input(materialx_node, 'in', 'color3', self._get_input_value(blender_node, 'Color'))
            # Add outputs for HSV
            self._add_output(materialx_node, 'h', 'float')
            self._add_output(materialx_node, 's', 'float')
            self._add_output(materialx_node, 'v', 'float')
    
    def _map_color_operation_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map color operation nodes (LUMINANCE, CONTRAST, SATURATE, GAMMA)."""
        # Add color input
        self._add_input(materialx_node, 'in', 'color3', self._get_input_value(blender_node, 'Color'))
        
        if blender_node.type == 'LUMINANCE':
            self._add_output(materialx_node, 'out', 'float')
        elif blender_node.type == 'CONTRAST':
            self._add_input(materialx_node, 'contrast', 'float', self._get_input_value(blender_node, 'Contrast'))
            self._add_input(materialx_node, 'brightness', 'float', self._get_input_value(blender_node, 'Brightness'))
            self._add_output(materialx_node, 'out', 'color3')
        elif blender_node.type == 'SATURATE':
            self._add_input(materialx_node, 'factor', 'float', self._get_input_value(blender_node, 'Factor'))
            self._add_output(materialx_node, 'out', 'color3')
        elif blender_node.type == 'GAMMA':
            self._add_input(materialx_node, 'gamma', 'float', self._get_input_value(blender_node, 'Gamma'))
            self._add_output(materialx_node, 'out', 'color3')
    
    def _map_vector_operation_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map vector operation nodes (SEPARATE_XYZ, COMBINE_XYZ)."""
        if blender_node.type == 'SEPARATE_XYZ':
            # Add vector input
            self._add_input(materialx_node, 'in', 'vector3', self._get_input_value(blender_node, 'Vector'))
            # Add outputs for X, Y, Z
            self._add_output(materialx_node, 'outr', 'float')  # X
            self._add_output(materialx_node, 'outg', 'float')  # Y
            self._add_output(materialx_node, 'outb', 'float')  # Z
        elif blender_node.type == 'COMBINE_XYZ':
            # Add inputs for X, Y, Z
            self._add_input(materialx_node, 'r', 'float', self._get_input_value(blender_node, 'X'))
            self._add_input(materialx_node, 'g', 'float', self._get_input_value(blender_node, 'Y'))
            self._add_input(materialx_node, 'b', 'float', self._get_input_value(blender_node, 'Z'))
            # Add vector output
            self._add_output(materialx_node, 'out', 'vector3')
    
    def _map_special_utility_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map special utility nodes (ROUGHNESS_ANISOTROPY, ARTISTIC_IOR)."""
        if blender_node.type == 'ROUGHNESS_ANISOTROPY':
            # Add inputs
            self._add_input(materialx_node, 'roughness', 'float', self._get_input_value(blender_node, 'Roughness'))
            self._add_input(materialx_node, 'anisotropy', 'float', self._get_input_value(blender_node, 'Anisotropy'))
            # Add outputs
            self._add_output(materialx_node, 'outr', 'float')  # Roughness X
            self._add_output(materialx_node, 'outg', 'float')  # Roughness Y
        elif blender_node.type == 'ARTISTIC_IOR':
            # Add inputs
            self._add_input(materialx_node, 'ior', 'float', self._get_input_value(blender_node, 'IOR'))
            self._add_input(materialx_node, 'extinction', 'float', self._get_input_value(blender_node, 'Extinction'))
            # Add outputs
            self._add_output(materialx_node, 'out', 'float')  # IOR
            self._add_output(materialx_node, 'out', 'float')  # Extinction
    
    def _map_shader_operation_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map shader operation nodes (ADD_SHADER, MULTIPLY_SHADER)."""
        # Add shader inputs
        self._add_input(materialx_node, 'in1', 'surface', self._get_input_value(blender_node, 'A'))
        self._add_input(materialx_node, 'in2', 'surface', self._get_input_value(blender_node, 'B'))
        # Add shader output
        self._add_output(materialx_node, 'out', 'surface')
    
    def _map_generic_utility_node(self, blender_node: bpy.types.Node, materialx_node: mx.Node):
        """Map generic utility nodes using configuration."""
        # Get input and output mappings from configuration
        input_mapping = self.get_input_mapping()
        output_mapping = self.get_output_mapping()
        
        # Add inputs
        for blender_input_name, materialx_input_name in input_mapping.items():
            if self._has_input(blender_node, blender_input_name):
                input_value = self._get_input_value(blender_node, blender_input_name)
                input_type = self._get_input_type(blender_node, blender_input_name)
                self._add_input(materialx_node, materialx_input_name, input_type, input_value)
        
        # Add outputs
        for blender_output_name, materialx_output_name in output_mapping.items():
            if self._has_output(blender_node, blender_output_name):
                output_type = self._get_output_type(blender_node, blender_output_name)
                self._add_output(materialx_node, materialx_output_name, output_type)
    
    def _get_input_type(self, blender_node: bpy.types.Node, input_name: str) -> str:
        """Get the MaterialX type for a Blender input."""
        if not self._has_input(blender_node, input_name):
            return 'float'
        
        input_socket = blender_node.inputs[input_name]
        socket_type = str(input_socket.type)
        
        # Map Blender socket types to MaterialX types
        type_mapping = {
            'RGBA': 'color3',
            'RGB': 'color3',
            'VECTOR': 'vector3',
            'VALUE': 'float',
            'INT': 'integer',
            'BOOLEAN': 'boolean'
        }
        
        return type_mapping.get(socket_type, 'float')
    
    def _get_output_type(self, blender_node: bpy.types.Node, output_name: str) -> str:
        """Get the MaterialX type for a Blender output."""
        if not self._has_output(blender_node, output_name):
            return 'float'
        
        output_socket = blender_node.outputs[output_name]
        socket_type = str(output_socket.type)
        
        # Map Blender socket types to MaterialX types
        type_mapping = {
            'RGBA': 'color3',
            'RGB': 'color3',
            'VECTOR': 'vector3',
            'VALUE': 'float',
            'INT': 'integer',
            'BOOLEAN': 'boolean'
        }
        
        return type_mapping.get(socket_type, 'float')
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for utility nodes."""
        return {
            'Color': 'in',
            'Value': 'in',
            'Vector': 'in',
            'A': 'in1',
            'B': 'in2',
            'Fac': 'mix',
            'Factor': 'factor',
            'Gamma': 'gamma',
            'Contrast': 'contrast',
            'Brightness': 'brightness',
            'H': 'h',
            'S': 's',
            'V': 'v',
            'X': 'r',
            'Y': 'g',
            'Z': 'b',
            'Roughness': 'roughness',
            'Anisotropy': 'anisotropy',
            'IOR': 'ior',
            'Extinction': 'extinction'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for utility nodes."""
        return {
            'Color': 'out',
            'Value': 'out',
            'Vector': 'out',
            'Shader': 'out',
            'h': 'h',
            's': 's',
            'v': 'v',
            'outr': 'outr',
            'outg': 'outg',
            'outb': 'outb'
        }
    
    def _map_mix_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender Mix node to MaterialX mix."""
        # Map inputs
        self._map_input(blender_node, materialx_node, 'A', 'fg')
        self._map_input(blender_node, materialx_node, 'B', 'bg')
        self._map_input(blender_node, materialx_node, 'Factor', 'mix')
        
        # Also handle alternative input names
        self._map_input(blender_node, materialx_node, 'Color1', 'fg')
        self._map_input(blender_node, materialx_node, 'Color2', 'bg')
        self._map_input(blender_node, materialx_node, 'Fac', 'mix')
        
        # Add output
        self._add_output(materialx_node, 'out', 'color3')
    
    def _map_color_ramp_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender Color Ramp node to MaterialX ramplr."""
        # Color Ramp maps to ramplr (left-to-right ramp)
        # Add input for the factor value
        self._add_input(materialx_node, 'in', 'float', value=0.5)
        
        # Add output
        self._add_output(materialx_node, 'out', 'color3')
        
        # Set default values for ramp
        self._add_input(materialx_node, 'low', 'color3', value=(0.0, 0.0, 0.0))
        self._add_input(materialx_node, 'high', 'color3', value=(1.0, 1.0, 1.0))
        
        # Try to extract ramp data from Blender node
        if hasattr(blender_node, 'color_ramp') and blender_node.color_ramp:
            # Get the first and last elements of the ramp
            elements = blender_node.color_ramp.elements
            if len(elements) >= 2:
                # First element (low)
                low_element = elements[0]
                low_color = (low_element.color[0], low_element.color[1], low_element.color[2])
                self._add_input(materialx_node, 'low', 'color3', value=low_color)
                
                # Last element (high)
                high_element = elements[-1]
                high_color = (high_element.color[0], high_element.color[1], high_element.color[2])
                self._add_input(materialx_node, 'high', 'color3', value=high_color)
    
    def _map_material_output_node(self, blender_node: bpy.types.Node, materialx_node: Any):
        """Map a Blender Material Output node to MaterialX."""
        # Material Output nodes are typically not exported to MaterialX
        # as they're Blender-specific. We'll create a simple pass-through.
        self._add_output(materialx_node, 'out', 'surfaceshader')
        
        # Map the Surface input
        self._map_input(blender_node, materialx_node, 'Surface', 'in')
    
    def _map_input(self, blender_node: bpy.types.Node, materialx_node: Any, 
                   blender_input_name: str, materialx_input_name: str):
        """Map a Blender input to a MaterialX input."""
        if self._has_input(blender_node, blender_input_name):
            input_value = self._get_input_value(blender_node, blender_input_name)
            input_type = self._get_input_type(blender_node, blender_input_name)
            self._add_input(materialx_node, materialx_input_name, input_type, input_value)
