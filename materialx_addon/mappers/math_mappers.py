#!/usr/bin/env python3
"""
Math Node Mappers

This module provides mappers for mathematical operation nodes.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_mapper import BaseNodeMapper


class MathMapper(BaseNodeMapper):
    """
    Mapper for Blender's Math node.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = ['MATH']
        self.materialx_node_type = "add"  # Default, will be overridden
        self.materialx_category = "math"
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """Check if this mapper can handle the given Blender node."""
        return blender_node.type in self.supported_node_types
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """Map a Blender Math node to MaterialX."""
        
        # Determine MaterialX node type based on operation
        materialx_type = self._get_materialx_type(blender_node)
        
        materialx_node = self._create_materialx_node(
            document, blender_node.name, materialx_type, self.materialx_category
        )
        
        # Add inputs
        self._add_input(materialx_node, 'in1', 'float', self._get_input_value(blender_node, 'A'))
        self._add_input(materialx_node, 'in2', 'float', self._get_input_value(blender_node, 'B'))
        
        # Add output
        self._add_output(materialx_node, 'out', 'float')
        
        return materialx_node
    
    def _get_materialx_type(self, blender_node: bpy.types.Node) -> str:
        """Get the MaterialX node type based on the math operation."""
        operation = blender_node.operation
        
        type_mapping = {
            'ADD': 'add',
            'SUBTRACT': 'subtract',
            'MULTIPLY': 'multiply',
            'DIVIDE': 'divide',
            'POWER': 'power',
            'LOGARITHM': 'log',
            'SQRT': 'sqrt',
            'ABSOLUTE': 'abs',
            'MINIMUM': 'min',
            'MAXIMUM': 'max',
            'GREATER_THAN': 'ifgreater',
            'LESS_THAN': 'ifgreater',
            'SIGN': 'sign',
            'COMPARE': 'ifgreater',
            'SMOOTH_MIN': 'smoothmin',
            'SMOOTH_MAX': 'smoothmax',
            'ROUND': 'round',
            'FLOOR': 'floor',
            'CEIL': 'ceil',
            'TRUNC': 'trunc',
            'FRACT': 'fract',
            'MODULO': 'modulo',
            'WRAP': 'wrap',
            'SNAP': 'snap',
            'PINGPONG': 'pingpong',
            'SINE': 'sin',
            'COSINE': 'cos',
            'TANGENT': 'tan',
            'ARCSINE': 'asin',
            'ARCCOSINE': 'acos',
            'ARCTANGENT': 'atan',
            'ARCTAN2': 'atan2',
            'SINH': 'sinh',
            'COSH': 'cosh',
            'TANH': 'tanh',
            'RADIANS': 'radians',
            'DEGREES': 'degrees'
        }
        
        return type_mapping.get(operation, 'add')
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for Math node."""
        return {
            'A': 'in1',
            'B': 'in2'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for Math node."""
        return {
            'Value': 'out'
        }


class VectorMathMapper(BaseNodeMapper):
    """
    Mapper for Blender's Vector Math node.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = ['VECTOR_MATH']
        self.materialx_node_type = "add"  # Default, will be overridden
        self.materialx_category = "math"
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """Check if this mapper can handle the given Blender node."""
        return blender_node.type in self.supported_node_types
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """Map a Blender Vector Math node to MaterialX."""
        
        # Determine MaterialX node type based on operation
        materialx_type = self._get_materialx_type(blender_node)
        
        materialx_node = self._create_materialx_node(
            document, blender_node.name, materialx_type, self.materialx_category
        )
        
        # Add inputs
        self._add_input(materialx_node, 'in1', 'vector3', self._get_input_value(blender_node, 'A'))
        self._add_input(materialx_node, 'in2', 'vector3', self._get_input_value(blender_node, 'B'))
        
        # Add outputs based on operation
        operation = blender_node.operation
        if operation in ['DOT_PRODUCT', 'CROSS_PRODUCT']:
            # These operations produce scalar outputs
            self._add_output(materialx_node, 'out', 'float')
        else:
            # Most operations produce vector outputs
            self._add_output(materialx_node, 'out', 'vector3')
        
        return materialx_node
    
    def _get_materialx_type(self, blender_node: bpy.types.Node) -> str:
        """Get the MaterialX node type based on the vector math operation."""
        operation = blender_node.operation
        
        type_mapping = {
            'ADD': 'add',
            'SUBTRACT': 'subtract',
            'MULTIPLY': 'multiply',
            'DIVIDE': 'divide',
            'CROSS_PRODUCT': 'crossproduct',
            'PROJECT': 'project',
            'REFLECT': 'reflect',
            'REFRACT': 'refract',
            'FACEFORWARD': 'faceforward',
            'DOT_PRODUCT': 'dotproduct',
            'DISTANCE': 'distance',
            'LENGTH': 'length',
            'SCALE': 'scale',
            'NORMALIZE': 'normalize',
            'SNAP': 'snap',
            'FLOOR': 'floor',
            'CEIL': 'ceil',
            'MODULO': 'modulo',
            'FRACTION': 'fraction',
            'ABSOLUTE': 'abs',
            'MINIMUM': 'min',
            'MAXIMUM': 'max',
            'WRAP': 'wrap',
            'SINE': 'sin',
            'COSINE': 'cos',
            'TANGENT': 'tan'
        }
        
        return type_mapping.get(operation, 'add')
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for Vector Math node."""
        return {
            'A': 'in1',
            'B': 'in2'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for Vector Math node."""
        return {
            'Vector': 'out',
            'Value': 'out'
        }
