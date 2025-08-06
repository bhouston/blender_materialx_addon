#!/usr/bin/env python3
"""
Blender MaterialX Exporter - Phase 1 & 2 MaterialX Library Integration

A Python script that exports Blender materials to MaterialX (.mtlx) format,
using the MaterialX Python library for robust and validated output.

Phase 1: Core Infrastructure Migration
- Replace XML generation with MaterialX library
- Implement library loading system
- Create MaterialX document builder

Phase 2: Node Mapping System Enhancement
- Leverage node definitions for type-safe mapping
- Implement automatic type conversion and validation
- Enhanced node creation with validation

Usage:
    import blender_materialx_exporter as mtlx_exporter
    mtlx_exporter.export_material_to_materialx(material, "output.mtlx")
"""

import bpy
import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import math

# Import the new MaterialX library core
try:
    from . import materialx_library_core
    from .materialx_library_core import MaterialXLibraryBuilder, MaterialXDocumentManager, MaterialXTypeConverter
except ImportError:
    # Fallback for direct import
    import materialx_library_core
    from materialx_library_core import MaterialXLibraryBuilder, MaterialXDocumentManager, MaterialXTypeConverter


def get_input_value_or_connection(node, input_name, exported_nodes=None) -> Tuple[bool, Any, str]:
    """
    Centralized utility to get input value or connection for a Blender node.
    Returns (is_connected, value_or_node_name, type_str)
    If connected, value_or_node_name is the MaterialX node name (from exported_nodes), not Blender node name.
    """
    if not hasattr(node, 'inputs'):
        raise AttributeError(f"Node {node} has no 'inputs' attribute")
    if input_name not in node.inputs:
        raise KeyError(f"Input '{input_name}' not found in node {node.name}")
    input_socket = node.inputs[input_name]
    if input_socket.is_linked and input_socket.links:
        from_node = input_socket.links[0].from_node
        if exported_nodes is not None and from_node in exported_nodes:
            return True, exported_nodes[from_node], str(input_socket.type)
        else:
            return True, from_node.name, str(input_socket.type)
    else:
        value = getattr(input_socket, 'default_value', None)
        return False, value, str(input_socket.type)


# Enhanced node schemas with type information for Phase 2
NODE_SCHEMAS = {
    'MIX': [
        # Support both legacy and current Blender Mix node input names
        {'blender': 'A', 'mtlx': 'fg', 'type': 'color3', 'category': 'color3'},
        {'blender': 'B', 'mtlx': 'bg', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Factor', 'mtlx': 'mix', 'type': 'float', 'category': 'color3'},
        {'blender': 'Color1', 'mtlx': 'fg', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Color2', 'mtlx': 'bg', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Fac', 'mtlx': 'mix', 'type': 'float', 'category': 'color3'},
    ],
    'INVERT': [
        {'blender': 'Color', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
    ],
    'COMBINE_COLOR': [
        {'blender': 'R', 'mtlx': 'r', 'type': 'float', 'category': 'color3'},
        {'blender': 'G', 'mtlx': 'g', 'type': 'float', 'category': 'color3'},
        {'blender': 'B', 'mtlx': 'b', 'type': 'float', 'category': 'color3'},
    ],
    'SEPARATE_COLOR': [
        {'blender': 'Color', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
    ],
    'CHECKER_TEXTURE': [
        {'blender': 'Color1', 'mtlx': 'in1', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Color2', 'mtlx': 'in2', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector2', 'category': 'color3'},
    ],
    'IMAGE_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector2', 'category': 'color3'},
        # 'file' handled separately
    ],
    'PRINCIPLED_BSDF': [
        {'blender': 'Base Color', 'mtlx': 'base_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Metallic', 'mtlx': 'metallic', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Roughness', 'mtlx': 'roughness', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Specular', 'mtlx': 'specular', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'IOR', 'mtlx': 'ior', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Transmission', 'mtlx': 'transmission', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Alpha', 'mtlx': 'opacity', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Normal', 'mtlx': 'normal', 'type': 'vector3', 'category': 'surfaceshader'},
        {'blender': 'Emission Color', 'mtlx': 'emission_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Emission Strength', 'mtlx': 'emission', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Subsurface', 'mtlx': 'subsurface', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Radius', 'mtlx': 'subsurface_radius', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Scale', 'mtlx': 'subsurface_scale', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Anisotropy', 'mtlx': 'subsurface_anisotropy', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Sheen', 'mtlx': 'sheen', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Sheen Tint', 'mtlx': 'sheen_tint', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Sheen Roughness', 'mtlx': 'sheen_roughness', 'type': 'float', 'category': 'surfaceshader'},
    ],
    'MATH': [
        {'blender': 'A', 'mtlx': 'in1', 'type': 'float', 'category': 'math'},
        {'blender': 'B', 'mtlx': 'in2', 'type': 'float', 'category': 'math'},
    ],
    'VECTOR_MATH': [
        {'blender': 'A', 'mtlx': 'in1', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'B', 'mtlx': 'in2', 'type': 'vector3', 'category': 'vector3'},
    ],
    'NOISE_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
        {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
        {'blender': 'Detail', 'mtlx': 'detail', 'type': 'float', 'category': 'color3'},
        {'blender': 'Roughness', 'mtlx': 'roughness', 'type': 'float', 'category': 'color3'},
    ],
    'GRADIENT_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
    ],
    'WAVE_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
        {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
        {'blender': 'Distortion', 'mtlx': 'distortion', 'type': 'float', 'category': 'color3'},
        {'blender': 'Detail', 'mtlx': 'detail', 'type': 'float', 'category': 'color3'},
    ],
}


class ConstantManager:
    """Manages constant nodes to avoid duplication."""
    
    def __init__(self):
        self.constants = {}  # (value, type) -> node_name
        self.constant_counter = 0
    
    def get_or_create_constant(self, builder, value, value_type):
        """Get existing constant node or create new one."""
        key = (value, value_type)
        if key not in self.constants:
            node_name = f"constant_{self.constant_counter}"
            self.constant_counter += 1
            builder.add_node("constant", node_name, value_type, value=value)
            self.constants[key] = node_name
        return self.constants[key]
    
    def should_emit_constant(self, node_name):
        """Check if constant should be emitted (has connections)."""
        return node_name in [name for name in self.constants.values()]
    
    def reset(self):
        """Reset for new material."""
        self.constants.clear()
        self.constant_counter = 0


def map_node_with_schema_enhanced(node, builder, schema, node_type, node_category, constant_manager=None, exported_nodes=None):
    """
    Enhanced node mapping using Phase 2 type-safe input creation.
    
    Args:
        node: Blender node
        builder: MaterialX builder
        schema: Node schema with type information
        node_type: MaterialX node type
        node_category: MaterialX node category
        constant_manager: Constant manager for optimization
        exported_nodes: Dictionary of exported nodes
        
    Returns:
        str: Created node name
    """
    # Create node with proper category
    node_name = builder.add_node(node_type, f"{node_type}_{node.name}", node_category)
    
    # Map inputs using enhanced type-safe method
    for entry in schema:
        blender_input = entry['blender']
        mtlx_param = entry['mtlx']
        param_type = entry['type']
        param_category = entry.get('category', node_category)
        
        try:
            is_connected, value_or_node, type_str = get_input_value_or_connection(node, blender_input, exported_nodes)
            
            if is_connected:
                # Connected input - add to nodegraph output
                builder.add_output(mtlx_param, param_type, value_or_node)
                # Connect to node input using type-safe method
                builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], mtlx_param, 
                    nodename=value_or_node,
                    node_type=node_type, category=param_category
                )
            else:
                # Constant input - use type-safe input creation
                builder.library_builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], mtlx_param, 
                    value=value_or_node,
                    node_type=node_type, category=param_category
                )
                
        except (KeyError, AttributeError):
            continue  # Input not present, skip
    
    return node_name


class MaterialXBuilder:
    """
    MaterialX document builder using Phase 2 enhanced functionality.
    
    This class provides a clean interface for building MaterialX documents
    using the enhanced MaterialX library core with type-safe operations.
    """
    
    def __init__(self, material_name: str, logger, version: str = "1.38" ):
        self.material_name = material_name
        self.logger = logger
        self.version = version
        
        # Initialize enhanced library builder
        self.library_builder = MaterialXLibraryBuilder(material_name, logger, version)
        self.document = self.library_builder.document
        self.nodes = self.library_builder.nodes
        self.connections = self.library_builder.connections
        self.node_counter = self.library_builder.node_counter
        
        # Phase 2 enhancements
        self.type_converter = MaterialXTypeConverter(logger)
        
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """Add a node using enhanced type-safe creation."""
        return self.library_builder.add_node(node_type, name, node_type_category, **params)
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """Add a connection with type validation."""
        self.library_builder.add_connection(from_node, from_output, to_node, to_input)
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """Add a surface shader node with enhanced type safety."""
        return self.library_builder.add_surface_shader_node(node_type, name, **params)
    
    def add_surface_shader_input(self, surface_node_name: str, input_name: str, input_type: str, nodegraph_name: str = None, nodename: str = None, value: str = None):
        """Add surface shader input with type-safe handling."""
        self.library_builder.add_surface_shader_input(surface_node_name, input_name, input_type, nodegraph_name, nodename, value)
    
    def add_output(self, name: str, output_type: str, nodename: str):
        """Add output with type validation."""
        self.library_builder.add_output(name, output_type, nodename)
    
    def set_material_surface(self, surface_node_name: str):
        """Set material surface with enhanced validation."""
        self.library_builder.set_material_surface(surface_node_name)
    
    def to_string(self) -> str:
        """Convert to string using enhanced library methods."""
        return self.library_builder.to_string()
    
    def write_to_file(self, filepath: str) -> bool:
        """Write to file using enhanced library methods."""
        return self.library_builder.write_to_file(filepath)
    
    def validate(self) -> bool:
        """Validate document using enhanced validation."""
        return self.library_builder.validate()
    
    def set_write_options(self, **options):
        """Set write options for the library builder."""
        if hasattr(self.library_builder, 'set_write_options'):
            self.library_builder.set_write_options(**options)
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self.library_builder, 'cleanup'):
            self.library_builder.cleanup()
    
    def optimize_document(self) -> bool:
        """Optimize the document using enhanced library methods."""
        if hasattr(self.library_builder, 'optimize_document'):
            return self.library_builder.optimize_document()
        return True  # Default to success if not available
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from the library builder."""
        if hasattr(self.library_builder, 'get_performance_stats'):
            return self.library_builder.get_performance_stats()
        return {}  # Default to empty dict if not available


class NodeMapper:
    """Enhanced node mapper using Phase 2 type-safe functionality."""
    
    @staticmethod
    def get_node_mapper(node_type: str):
        """Get the appropriate mapper for a node type."""
        mappers = {
            'BSDF_PRINCIPLED': NodeMapper.map_principled_bsdf_enhanced,
            'TEX_IMAGE': NodeMapper.map_image_texture_enhanced,
            'TEX_COORD': NodeMapper.map_tex_coord,
            'RGB': NodeMapper.map_rgb,
            'VALUE': NodeMapper.map_value,
            'NORMAL_MAP': NodeMapper.map_normal_map,
            'VECTOR_MATH': NodeMapper.map_vector_math_enhanced,
            'VECT_MATH': NodeMapper.map_vector_math_enhanced,  # Alias for Vector Math
            'MATH': NodeMapper.map_math_enhanced,
            'MIX': NodeMapper.map_mix_enhanced,
            'MIX_RGB': NodeMapper.map_mix_enhanced,  # Alias for MixRGB
            'MIX_RGB_LEGACY': NodeMapper.map_mix_enhanced,  # Alias for legacy Mix
            'INVERT': NodeMapper.map_invert_enhanced,
            'SEPARATE_COLOR': NodeMapper.map_separate_color_enhanced,
            'COMBINE_COLOR': NodeMapper.map_combine_color_enhanced,
            'BUMP': NodeMapper.map_bump,
            'TEX_CHECKER': NodeMapper.map_checker_texture_enhanced,
            'TEX_GRADIENT': NodeMapper.map_gradient_texture_enhanced,
            'TEX_NOISE': NodeMapper.map_noise_texture_enhanced,
            'MAPPING': NodeMapper.map_mapping,
            'LAYER': NodeMapper.map_layer,
            'ADD': NodeMapper.map_add,
            'MULTIPLY': NodeMapper.map_multiply,
            'ROUGHNESS_ANISOTROPY': NodeMapper.map_roughness_anisotropy,
            'ARTISTIC_IOR': NodeMapper.map_artistic_ior,
            'COLORRAMP': NodeMapper.map_color_ramp,  # New
            'VALTORGB': NodeMapper.map_color_ramp,   # Alias for ColorRamp
            'WAVE': NodeMapper.map_wave_texture_enhanced,     # New
            'WAVE_TEXTURE': NodeMapper.map_wave_texture_enhanced, # Alias
            'TEX_WAVE': NodeMapper.map_wave_texture_enhanced,     # Alias for Wave Texture
            # New color and split/merge nodes:
            'HSV_TO_RGB': NodeMapper.map_hsvtorgb,
            'RGB_TO_HSV': NodeMapper.map_rgbtohsv,
            'LUMINANCE': NodeMapper.map_luminance,
            'BRIGHT_CONTRAST': NodeMapper.map_contrast,
            'HUE_SAT': NodeMapper.map_saturate,
            'GAMMA': NodeMapper.map_gamma,
            'SEPARATE_RGB': NodeMapper.map_split_color,
            'COMBINE_RGB': NodeMapper.map_merge_color,
            'SEPARATE_XYZ': NodeMapper.map_split_vector,
            'COMBINE_XYZ': NodeMapper.map_merge_vector,
        }
        return mappers.get(node_type)
    
    @staticmethod
    def map_principled_bsdf_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced Principled BSDF mapping with type-safe input creation."""
        # Create surface shader node
        node_name = builder.add_surface_shader_node("standard_surface", f"surface_{node.name}")
        
        # Map inputs using enhanced schema with type information
        for entry in NODE_SCHEMAS['PRINCIPLED_BSDF']:
            blender_input = entry['blender']
            mtlx_param = entry['mtlx']
            param_type = entry['type']
            param_category = entry.get('category', 'surfaceshader')
            
            try:
                is_connected, value_or_node, type_str = get_input_value_or_connection(node, blender_input, exported_nodes)
                
                # Special case: skip unconnected normal/tangent inputs for standard_surface
                if mtlx_param in ("normal", "tangent") and not is_connected:
                    continue
                
                if is_connected:
                    # Connected input - add to nodegraph output and connect
                    builder.add_output(mtlx_param, param_type, value_or_node)
                    builder.add_surface_shader_input(
                        node_name, mtlx_param, param_type, 
                        nodegraph_name=builder.material_name
                    )
                else:
                    # Constant input - use type-safe input creation
                    builder.library_builder.node_builder.create_mtlx_input(
                        builder.nodes[node_name], mtlx_param, 
                        value=value_or_node,
                        node_type='standard_surface', category=param_category
                    )
                    
            except (KeyError, AttributeError):
                continue  # Input not present, skip
        
        return node_name
    
    @staticmethod
    def map_image_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced image texture mapping with type-safe input creation."""
        # Use enhanced schema-driven mapping
        node_name = map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['IMAGE_TEXTURE'], 'image', 'color3', constant_manager, exported_nodes)

        # Custom logic for file/image handling
        if node.image:
            image_path = node.image.filepath
            if image_path:
                exporter = getattr(builder, 'exporter', None)
                if exporter and image_path in exporter.texture_paths:
                    rel_path = exporter.texture_paths[image_path]
                else:
                    rel_path = os.path.basename(image_path)
                
                # Use type-safe input creation for file input
                builder.library_builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], 'file', 
                    value=rel_path,
                    node_type='image', category='color3'
                )
        
        return node_name
    
    @staticmethod
    def map_tex_coord(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Texture Coordinate node to MaterialX texcoord node."""
        node_name = builder.add_node("texcoord", f"texcoord_{node.name}", "vector2")
        return node_name
    
    @staticmethod
    def map_rgb(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map RGB node to MaterialX constant node."""
        # Get RGB values
        r = getattr(node.outputs[0], 'default_value', [1, 1, 1, 1])[0]
        g = getattr(node.outputs[0], 'default_value', [1, 1, 1, 1])[1]
        b = getattr(node.outputs[0], 'default_value', [1, 1, 1, 1])[2]
        
        # Create constant node with type-safe input creation
        node_name = builder.add_node("constant", f"rgb_{node.name}", "color3", value=[r, g, b])
        return node_name
    
    @staticmethod
    def map_value(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Value node to MaterialX constant node."""
        value = getattr(node.outputs[0], 'default_value', 0.0)
        node_name = builder.add_node("constant", f"value_{node.name}", "float", value=value)
        return node_name
    
    @staticmethod
    def map_normal_map(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Normal Map node to MaterialX normalmap node."""
        node_name = builder.add_node("normalmap", f"normalmap_{node.name}", "vector3")
        
        # Map inputs using type-safe method
        try:
            is_connected, value_or_node, type_str = get_input_value_or_connection(node, 'Color', exported_nodes)
            if is_connected:
                builder.add_connection(value_or_node, 'out', node_name, 'in')
            else:
                # Set default normal value
                builder.library_builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], 'in', 
                    value=[0.5, 0.5, 1.0],
                    node_type='normalmap', category='vector3'
                )
        except (KeyError, AttributeError):
            pass
        
        return node_name
    
    @staticmethod
    def map_vector_math_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced vector math mapping with type-safe input creation."""
        # Map operation to MaterialX node type
        operation = node.operation.lower()
        mtlx_operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'cross_product': 'crossproduct',
            'project': 'project',
            'reflect': 'reflect',
            'refract': 'refract',
            'faceforward': 'faceforward',
            'dot_product': 'dotproduct',
            'distance': 'distance',
            'length': 'length',
            'normalize': 'normalize',
            'absolute': 'absval',
            'minimum': 'min',
            'maximum': 'max',
            'floor': 'floor',
            'ceil': 'ceil',
            'fraction': 'fraction',
            'modulo': 'modulo',
            'wrap': 'wrap',
            'snap': 'snap',
            'sin': 'sin',
            'cos': 'cos',
            'tan': 'tan',
            'asin': 'asin',
            'acos': 'acos',
            'atan': 'atan',
            'atan2': 'atan2',
            'sinh': 'sinh',
            'cosh': 'cosh',
            'tanh': 'tanh',
            'log': 'ln',
            'logarithm': 'log',
            'sqrt': 'sqrt',
            'inverse_sqrt': 'inversesqrt',
            'absolute': 'absval',
            'exponent': 'exp',
            'to_radians': 'radians',
            'to_degrees': 'degrees',
            'sign': 'sign',
            'compare': 'compare',
            'smoothstep': 'smoothstep',
            'step': 'step',
            'round': 'round',
            'trunc': 'trunc',
            'fract': 'fract',
            'clamp': 'clamp',
            'mix': 'mix',
            'pingpong': 'pingpong',
            'smooth_min': 'smoothmin',
            'smooth_max': 'smoothmax',
        }
        
        mtlx_operation = mtlx_operation_map.get(operation, 'add')
        
        # Create node with enhanced type safety
        node_name = builder.add_node(mtlx_operation, f"{mtlx_operation}_{node.name}", "vector3")
        
        # Map inputs using enhanced schema
        if 'VECTOR_MATH' in NODE_SCHEMAS:
            for entry in NODE_SCHEMAS['VECTOR_MATH']:
                blender_input = entry['blender']
                mtlx_param = entry['mtlx']
                param_type = entry['type']
                param_category = entry.get('category', 'vector3')
                
                try:
                    is_connected, value_or_node, type_str = get_input_value_or_connection(node, blender_input, exported_nodes)
                    
                    if is_connected:
                        builder.add_connection(value_or_node, 'out', node_name, mtlx_param)
                    else:
                        # Set default value using type-safe method
                        default_value = [0.0, 0.0, 0.0] if blender_input == 'A' else [0.0, 0.0, 0.0]
                        builder.library_builder.node_builder.create_mtlx_input(
                            builder.nodes[node_name], mtlx_param, 
                            value=default_value,
                            node_type=mtlx_operation, category=param_category
                        )
                        
                except (KeyError, AttributeError):
                    continue
        
        return node_name
    
    @staticmethod
    def map_math_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced math mapping with type-safe input creation."""
        # Map operation to MaterialX node type
        operation = node.operation.lower()
        mtlx_operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'power': 'power',
            'logarithm': 'log',
            'sqrt': 'sqrt',
            'inverse_sqrt': 'inversesqrt',
            'absolute': 'absval',
            'exponent': 'exp',
            'minimum': 'min',
            'maximum': 'max',
            'greater_than': 'ifgreater',
            'less_than': 'ifgreater',
            'sign': 'sign',
            'compare': 'compare',
            'smoothstep': 'smoothstep',
            'step': 'step',
            'round': 'round',
            'floor': 'floor',
            'ceil': 'ceil',
            'trunc': 'trunc',
            'fract': 'fract',
            'modulo': 'modulo',
            'wrap': 'wrap',
            'snap': 'snap',
            'pingpong': 'pingpong',
            'sine': 'sin',
            'cosine': 'cos',
            'tangent': 'tan',
            'arcsine': 'asin',
            'arccosine': 'acos',
            'arctangent': 'atan',
            'arctan2': 'atan2',
            'hyperbolic_sine': 'sinh',
            'hyperbolic_cosine': 'cosh',
            'hyperbolic_tangent': 'tanh',
            'to_radians': 'radians',
            'to_degrees': 'degrees',
            'clamp': 'clamp',
            'mix': 'mix',
            'smooth_min': 'smoothmin',
            'smooth_max': 'smoothmax',
        }
        
        mtlx_operation = mtlx_operation_map.get(operation, 'add')
        
        # Create node with enhanced type safety
        node_name = builder.add_node(mtlx_operation, f"{mtlx_operation}_{node.name}", "float")
        
        # Map inputs using enhanced schema
        if 'MATH' in NODE_SCHEMAS:
            for entry in NODE_SCHEMAS['MATH']:
                blender_input = entry['blender']
                mtlx_param = entry['mtlx']
                param_type = entry['type']
                param_category = entry.get('category', 'float')
                
                try:
                    is_connected, value_or_node, type_str = get_input_value_or_connection(node, blender_input, exported_nodes)
                    
                    if is_connected:
                        builder.add_connection(value_or_node, 'out', node_name, mtlx_param)
                    else:
                        # Set default value using type-safe method
                        default_value = 0.0 if blender_input == 'A' else 0.0
                        builder.library_builder.node_builder.create_mtlx_input(
                            builder.nodes[node_name], mtlx_param, 
                            value=default_value,
                            node_type=mtlx_operation, category=param_category
                        )
                        
                except (KeyError, AttributeError):
                    continue
        
        return node_name
    
    @staticmethod
    def map_mix_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced mix mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['MIX'], 'mix', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_invert_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced invert mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['INVERT'], 'invert', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_separate_color_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced separate color mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['SEPARATE_COLOR'], 'separate3', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_combine_color_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced combine color mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['COMBINE_COLOR'], 'combine3', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_checker_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced checker texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['CHECKER_TEXTURE'], 'checkerboard', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_gradient_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced gradient texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['GRADIENT_TEXTURE'], 'ramplr', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_noise_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced noise texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['NOISE_TEXTURE'], 'fractal3d', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_wave_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced wave texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['WAVE_TEXTURE'], 'wave', 'color3', constant_manager, exported_nodes)
    
    # Legacy methods for backward compatibility
    @staticmethod
    def map_bump(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Bump node to MaterialX bump node."""
        node_name = builder.add_node("bump", f"bump_{node.name}", "vector3")
        return node_name
    
    @staticmethod
    def map_mapping(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Mapping node to MaterialX transform2d node."""
        node_name = builder.add_node("transform2d", f"mapping_{node.name}", "vector2")
        return node_name
    
    @staticmethod
    def map_layer(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Layer Weight node to MaterialX layer node."""
        node_name = builder.add_node("layer", f"layer_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_add(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Add node to MaterialX add node."""
        node_name = builder.add_node("add", f"add_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_multiply(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Multiply node to MaterialX multiply node."""
        node_name = builder.add_node("multiply", f"multiply_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_roughness_anisotropy(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Roughness Anisotropy node to MaterialX roughness_anisotropy node."""
        node_name = builder.add_node("roughness_anisotropy", f"roughness_anisotropy_{node.name}", "vector2")
        return node_name
    
    @staticmethod
    def map_artistic_ior(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Artistic IOR node to MaterialX artistic_ior node."""
        node_name = builder.add_node("artistic_ior", f"artistic_ior_{node.name}", "float")
        return node_name
    
    @staticmethod
    def map_color_ramp(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map ColorRamp node to MaterialX ramplr node."""
        node_name = builder.add_node("ramplr", f"colorramp_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_hsvtorgb(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map HSV to RGB node to MaterialX hsvtorgb node."""
        node_name = builder.add_node("hsvtorgb", f"hsvtorgb_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_rgbtohsv(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map RGB to HSV node to MaterialX rgbtohsv node."""
        node_name = builder.add_node("rgbtohsv", f"rgbtohsv_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_luminance(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Luminance node to MaterialX luminance node."""
        node_name = builder.add_node("luminance", f"luminance_{node.name}", "float")
        return node_name
    
    @staticmethod
    def map_contrast(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Bright/Contrast node to MaterialX contrast node."""
        node_name = builder.add_node("contrast", f"contrast_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_saturate(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Hue Saturation Value node to MaterialX saturate node."""
        node_name = builder.add_node("saturate", f"saturate_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_gamma(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Gamma node to MaterialX gamma node."""
        node_name = builder.add_node("gamma", f"gamma_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_split_color(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Separate RGB node to MaterialX separate3 node."""
        node_name = builder.add_node("separate3", f"split_color_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_merge_color(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Combine RGB node to MaterialX combine3 node."""
        node_name = builder.add_node("combine3", f"merge_color_{node.name}", "color3")
        return node_name
    
    @staticmethod
    def map_split_vector(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Separate XYZ node to MaterialX separate3 node."""
        node_name = builder.add_node("separate3", f"split_vector_{node.name}", "vector3")
        return node_name
    
    @staticmethod
    def map_merge_vector(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Combine XYZ node to MaterialX combine3 node."""
        node_name = builder.add_node("combine3", f"merge_vector_{node.name}", "vector3")
        return node_name


class MaterialXExporter:
    """Main MaterialX exporter class with Phase 3 enhancements."""
    
    def __init__(self, material: bpy.types.Material, output_path: str, logger, options: Dict = None):
        self.material = material
        self.output_path = Path(output_path)
        self.options = options or {}
        self.logger = logger
        
        # Default options
        self.active_uvmap = self.options.get('active_uvmap', 'UVMap')
        self.export_textures = self.options.get('export_textures', True)
        texture_path_opt = self.options.get('texture_path', '.')
        self.texture_path = (self.output_path.parent / texture_path_opt).resolve()
        self.materialx_version = self.options.get('materialx_version', '1.38')
        self.copy_textures = self.options.get('copy_textures', True)
        self.relative_paths = True  # Always use relative paths for this workflow
        self.strict_mode = options.get('strict_mode', True)  # Default to strict mode
        
        # Phase 3 enhancements
        self.optimize_document = self.options.get('optimize_document', True)
        self.advanced_validation = self.options.get('advanced_validation', True)
        self.performance_monitoring = self.options.get('performance_monitoring', True)
        
        # Internal state
        self.exported_nodes = {}
        self.texture_paths = {}
        self.builder = None
        self.unsupported_nodes = []
        self.constant_manager = ConstantManager()
        
        # Performance tracking
        self.export_start_time = None
        self.export_end_time = None

    def export(self) -> dict:
        """Export the material to MaterialX format with Phase 3 enhancements. Returns a result dict."""
        result = {
            "success": False,
            "unsupported_nodes": [],
            "output_path": str(self.output_path),
            "error": None,
            "performance_stats": {},
            "validation_results": {},
            "optimization_applied": False
        }
        
        try:
            # Start performance monitoring
            if self.performance_monitoring:
                self.export_start_time = time.time()
                self.logger.info("Starting performance monitoring for export")
            
            self.logger.info(f"Starting export of material '{self.material.name}'")
            self.logger.info(f"Output path: {self.output_path}")
            self.logger.info(f"Material uses nodes: {self.material.use_nodes}")
            self.logger.info(f"Phase 3 features: optimize={self.optimize_document}, validation={self.advanced_validation}")
            
            # Attach exporter to builder for relative path lookup
            MaterialXBuilder.exporter = self
            
            if not self.material.use_nodes:
                self.logger.info(f"Material '{self.material.name}' does not use nodes. Creating basic material.")
                ok = self._export_basic_material()
                result["success"] = ok
                return result
            
            self.constant_manager.reset() # Reset constant manager for each export
            
            # Find the Principled BSDF node
            principled_node = self._find_principled_bsdf_node()
            if not principled_node:
                self.logger.error(f"✗ No Principled BSDF node found in material '{self.material.name}'")
                self.logger.error("💡 This addon only supports materials that use Principled BSDF nodes.")
                self.logger.error("💡 Available node types in your material:")
                for node in self.material.node_tree.nodes:
                    self.logger.error(f"    - {node.name}: {node.type}")
                
                # Provide specific guidance based on what nodes are present
                node_types = [node.type for node in self.material.node_tree.nodes]
                if 'EMISSION' in node_types:
                    self.logger.error("💡 Suggestion: Replace the Emission shader with a Principled BSDF node.")
                    self.logger.error("💡 Use 'Emission Color' and 'Emission Strength' inputs on the Principled BSDF instead.")
                elif 'BSDF_DIFFUSE' in node_types or 'BSDF_GLOSSY' in node_types or 'BSDF_GLASS' in node_types:
                    self.logger.error("💡 Suggestion: Replace individual BSDF shaders with a single Principled BSDF node.")
                    self.logger.error("💡 Principled BSDF combines all these effects in one node with better control.")
                else:
                    self.logger.error("💡 Suggestion: Add a Principled BSDF node to your material and connect it to the Material Output.")
                    self.logger.error("💡 The Principled BSDF is the standard shader for physically-based rendering in Blender.")
                
                result["error"] = "No Principled BSDF node found"
                return result
            
            self.logger.info(f"Found Principled BSDF node: {principled_node.name}")
            self.builder = MaterialXBuilder(self.material.name, self.logger, self.materialx_version)
            
            # Attach exporter to builder for relative path lookup
            self.builder.exporter = self
            self.logger.info(f"Created MaterialX builder with version {self.materialx_version}")
            
            # Configure Phase 3 features
            if self.advanced_validation:
                self.builder.set_write_options(
                    skip_library_elements=True,
                    write_xinclude=False,
                    remove_layout=True,
                    format_output=True
                )
            
            self.logger.info("Starting node network export...")
            surface_node_name = self._export_node_network(principled_node)
            self.logger.info(f"Node network export completed. Surface node: {surface_node_name}")
            self.builder.set_material_surface(surface_node_name)
            
            # Phase 3: Document optimization
            if self.optimize_document:
                self.logger.info("Applying document optimization...")
                optimization_success = self.builder.optimize_document()
                result["optimization_applied"] = optimization_success
                if optimization_success:
                    self.logger.info("Document optimization completed successfully")
                else:
                    self.logger.warning("Document optimization failed")
            
            # Phase 3: Advanced validation
            if self.advanced_validation:
                self.logger.info("Performing advanced validation...")
                validation_success = self.builder.validate()
                result["validation_results"] = {
                    "valid": validation_success,
                    "details": "See log for detailed validation results"
                }
                if not validation_success:
                    self.logger.warning("Document validation failed")
            

            
            # Write the file
            self._write_file()
            
            # Phase 3: Performance statistics
            if self.performance_monitoring:
                self.export_end_time = time.time()
                export_duration = self.export_end_time - self.export_start_time
                performance_stats = self.builder.get_performance_stats()
                performance_stats['export_duration'] = export_duration
                result["performance_stats"] = performance_stats
                
                self.logger.info(f"Export completed in {export_duration:.4f} seconds")
                self.logger.info("Performance statistics:")
                for key, value in performance_stats.items():
                    self.logger.info(f"  {key}: {value}")
            
            result["success"] = True
            result["unsupported_nodes"] = self.unsupported_nodes
            
        except Exception as e:
            import traceback
            self.logger.error(f"ERROR: Failed to export material '{self.material.name}'")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error message: {str(e)}")
            self.logger.error("Full traceback:")
            traceback.print_exc()
            result["error"] = str(e)
            result["unsupported_nodes"] = self.unsupported_nodes
            if self.strict_mode:
                raise
        finally:
            # Phase 3: Cleanup
            if self.builder:
                self.builder.cleanup()
        
        return result
    
    def _export_basic_material(self) -> bool:
        """Export a basic material without nodes."""
        self.builder = MaterialXBuilder(self.material.name, self.logger, self.materialx_version)
        
        # Create a basic standard_surface shader outside the nodegraph
        surface_node = self.builder.add_surface_shader_node("standard_surface", "surface_basic")
        
        # Add inputs with values directly
        self.builder.add_surface_shader_input(
            surface_node, "base_color", "color3",
            value=str(f"{self.material.diffuse_color[0]}, {self.material.diffuse_color[1]}, {self.material.diffuse_color[2]}"))
        self.builder.add_surface_shader_input(
            surface_node, "roughness", "float",
            value=str(self.material.roughness))
        self.builder.add_surface_shader_input(
            surface_node, "metallic", "float",
            value=str(self.material.metallic))
        
        self.builder.set_material_surface(surface_node)
        self._write_file()
        return True
    
    def _find_principled_bsdf_node(self) -> Optional[bpy.types.Node]:
        """Find the Principled BSDF node in the material."""
        for node in self.material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                return node
        return None
    
    def _export_node_network(self, output_node: bpy.types.Node) -> str:
        """Export the node network starting from the output node."""
        self.logger.info(f"Building dependencies for node: {output_node.name} ({output_node.type})")
        
        # Traverse the network and build dependencies
        dependencies = self._build_dependencies(output_node)
        self.logger.info(f"Found {len(dependencies)} nodes in dependency order:")
        for i, node in enumerate(dependencies):
            self.logger.info(f"  {i+1}. {node.name} ({node.type})")
        
        # Export nodes in dependency order
        self.logger.info("Exporting nodes in dependency order...")
        for i, node in enumerate(dependencies):
            if node not in self.exported_nodes:
                self.logger.info(f"Exporting node {i+1}/{len(dependencies)}: {node.name} ({node.type})")
                try:
                    self._export_node(node)
                    self.logger.info(f"  ✓ Successfully exported {node.name}")
                except Exception as e:
                    # Don't log the error again since _export_node already logged helpful messages
                    raise
            else:
                self.logger.info(f"Skipping already exported node: {node.name}")
        
        result = self.exported_nodes[output_node]
        self.logger.info(f"Node network export completed. Final surface node: {result}")
        return result
    
    def _build_dependencies(self, output_node: bpy.types.Node) -> List[bpy.types.Node]:
        """Build a list of nodes in dependency order."""
        visited = set()
        dependencies = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            
            # Visit input nodes first
            for input_socket in node.inputs:
                if input_socket.links:
                    input_node = input_socket.links[0].from_node
                    visit(input_node)
            
            dependencies.append(node)
        
        visit(output_node)
        return dependencies
    
    def _export_node(self, node: bpy.types.Node) -> str:
        """Export a single node."""
        self.logger.info(f"  Processing node: {node.name} (type: {node.type})")
        self.logger.info(f"  *** ENTERING _export_node for {node.name} ***")
        # Get the mapper for this node type
        mapper = NodeMapper.get_node_mapper(node.type)
        if not mapper:
            self.logger.warning(f"  Warning: No mapper found for node type '{node.type}' ({node.name})")
            self.logger.warning(f"  Available mappers: {list(NodeMapper.get_node_mapper.__defaults__ or [])}")
            
            # Provide specific guidance for common unsupported node types
            if node.type == 'EMISSION':
                self.logger.error(f"  ✗ Emission shader '{node.name}' is not supported.")
                self.logger.error(f"  💡 Suggestion: Replace with Principled BSDF and use 'Emission Color' and 'Emission Strength' inputs instead.")
                self.logger.error(f"  💡 This addon only supports materials that use Principled BSDF nodes.")
            elif node.type == 'FRESNEL':
                self.logger.error(f"  ✗ Fresnel node '{node.name}' is not supported.")
                self.logger.error(f"  💡 Suggestion: Remove this node and use Principled BSDF's built-in fresnel effects via 'Specular IOR Level' and 'IOR' inputs.")
                self.logger.error(f"  💡 Principled BSDF has built-in fresnel calculations that are more accurate and efficient.")
            else:
                self.logger.error(f"  ✗ Node type '{node.type}' ({node.name}) is not supported.")
                self.logger.error(f"  💡 Suggestion: Use only supported node types or replace with equivalent Principled BSDF functionality.")
            
            if self.strict_mode:
                raise RuntimeError(f"Unsupported node type encountered: {node.type} ({node.name})")
            return self._export_unknown_node(node)
        self.logger.info(f"  Found mapper for {node.type}")
        # Build input nodes dictionary - handle duplicate input names
        input_nodes = {}
        input_nodes_by_index = {}  # Store by index for nodes with duplicate names
        for i, input_socket in enumerate(node.inputs):
            if input_socket.links:
                input_node = input_socket.links[0].from_node
                if input_node not in self.exported_nodes:
                    self._export_node(input_node)
                input_nodes[input_socket.name] = self.exported_nodes[input_node]
                input_nodes_by_index[i] = self.exported_nodes[input_node]
                self.logger.info(f"    Input {i} '{input_socket.name}' connected to {input_node.name}")
        self.logger.info(f"  Input nodes: {list(input_nodes.keys())}")
        self.logger.info(f"  Input nodes by index: {list(input_nodes_by_index.keys())}")
        self.logger.info(f"  Input nodes by index values: {input_nodes_by_index}")
        self.logger.info(f"  *** DEBUG: Node {node.name} has {len(input_nodes_by_index)} indexed inputs ***")
        # Map the node
        try:
            # Pass constant_manager to schema-driven mappers
            node_name = mapper(node, self.builder, input_nodes, input_nodes_by_index, node, self.constant_manager, self.exported_nodes)
            self.exported_nodes[node] = node_name
            self.logger.info(f"  Mapped to: {node_name}")
            return node_name
        except Exception as e:
            self.logger.error(f"  Error in mapper for {node.type}: {str(e)}")
            if self.strict_mode:
                raise
            raise
    
    def _export_unknown_node(self, node: bpy.types.Node) -> str:
        """Export an unknown node type as a placeholder and record it."""
        self.unsupported_nodes.append({
            "name": node.name,
            "type": node.type
        })
        node_name = self.builder.add_node("constant", f"unknown_{node.name}", "color3",
                                        value=[1.0, 0.0, 1.0])  # Magenta for unknown nodes
        self.exported_nodes[node] = node_name
        return node_name
    
    def _write_file(self):
        """Write the MaterialX document to file with Phase 3 enhancements."""
        try:
            self.logger.info(f"Ensuring output directory exists: {self.output_path.parent}")
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Writing MaterialX content to: {self.output_path}")
            
            # Use library-based writing with Phase 3 enhancements
            success = self.builder.write_to_file(str(self.output_path))
            if success:
                self.logger.info(f"Successfully wrote MaterialX document using library")
                

            else:
                self.logger.error("Failed to write document using library")
                raise RuntimeError("Failed to write MaterialX document")
                
        except PermissionError as e:
            self.logger.error(f"Permission error writing file: {e}")
            self.logger.error(f"Check if you have write permissions to: {self.output_path}")
            raise
        except OSError as e:
            self.logger.error(f"OS error writing file: {e}")
            self.logger.error(f"Check if the path is valid: {self.output_path}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error writing file: {e}")
            raise
    
    def _export_textures(self):
        """Export texture files."""
        if not self.export_textures:
            return
        
        # Ensure texture directory exists
        self.texture_path.mkdir(parents=True, exist_ok=True)
        
        # Find all image textures
        for node in self.material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                self._export_texture(node.image)
    
    def _export_texture(self, image: bpy.types.Image):
        """Export a single texture file."""
        if not image.filepath:
            return
        
        source_path = Path(bpy.path.abspath(image.filepath))
        if not source_path.exists():
            self.logger.warning(f"Warning: Texture file not found: {source_path}")
            return
        
        # Compute relative path from .mtlx file to texture
        rel_path = os.path.relpath(self.texture_path / source_path.name, self.output_path.parent)
        self.texture_paths[str(image.filepath)] = rel_path
        # Copy the texture (overwrite if exists)
        target_path = self.texture_path / source_path.name
        if self.copy_textures:
            try:
                shutil.copy2(source_path, target_path)
                self.logger.info(f"Copied texture: {source_path.name}")
            except Exception as e:
                self.logger.error(f"Error copying texture {source_path.name}: {str(e)}")


# Utility to robustly format Blender socket values for MaterialX XML
def format_socket_value(value):
    """
    Format a Blender socket value for MaterialX XML.
    Handles scalars, tuples, lists, and Blender's bpy_prop_array types.
    """
    # Blender's vector types can be mathutils.Vector, or bpy_prop_array, or tuple/list
    if hasattr(value, "__len__") and not isinstance(value, str):
        try:
            # Try to convert to list of floats
            return ", ".join(str(float(v)) for v in value)
        except Exception:
            return str(value)
    else:
        try:
            return str(float(value))
        except Exception:
            return str(value)


def export_material_to_materialx(material: bpy.types.Material, 
                                output_path: str, 
                                logger=None,
                                options: Dict = None) -> dict:
    """
    Export a Blender material to MaterialX format.
    Returns a dict with success, unsupported_nodes, output_path, and error (if any).
    """
    # Initialize logging
    if logger is None:
        logger = logging.getLogger(__name__)
        # Set up basic logging if not already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    logger.info("=" * 50)
    logger.info("EXPORT_MATERIAL_TO_MATERIALX: Function called")
    logger.info("=" * 50)
    logger.info(f"Material: {material.name if material else 'None'}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Options: {options}")
    try:
        exporter = MaterialXExporter(material, output_path, logger, options)
        logger.info("MaterialXExporter instance created successfully")
        result = exporter.export()
        logger.info(f"Export result: {result}")
        return result
    except Exception as e:
        import traceback
        logger.error(f"EXCEPTION in export_material_to_materialx: {type(e).__name__}: {str(e)}")
        logger.error("Full traceback:")
        traceback.print_exc()
        return {"success": False, "unsupported_nodes": [], "output_path": output_path, "error": str(e)}


def export_all_materials_to_materialx(output_directory: str, logger, options: Dict = None) -> Dict[str, bool]:
    """
    Export all materials in the current scene to MaterialX format.
    
    Args:
        output_directory: Directory to save .mtlx files
        options: Export options dictionary
    
    Returns:
        Dict[str, bool]: Dictionary mapping material names to success status
    """
    results = {}
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for material in bpy.data.materials:
        if material.users > 0:  # Only export materials that are actually used
            output_path = output_dir / f"{material.name}.mtlx"
            results[material.name] = export_material_to_materialx(material, str(output_path), logger, options)
    
    return results


# Note: Testing functions have been moved to test_blender_addon.py
# This file now focuses on the core export functionality 