#!/usr/bin/env python3
"""
Blender MaterialX Exporter - Phase 1 MaterialX Library Integration

A Python script that exports Blender materials to MaterialX (.mtlx) format,
using the MaterialX Python library for robust and validated output.

Usage:
    import blender_materialx_exporter as mtlx_exporter
    mtlx_exporter.export_material_to_materialx(material, "output.mtlx")
"""

import bpy
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import math

# Import the new MaterialX library core
try:
    from . import materialx_library_core
    from .materialx_library_core import MaterialXLibraryBuilder, MaterialXDocumentManager
except ImportError:
    # Fallback for direct import
    import materialx_library_core
    from materialx_library_core import MaterialXLibraryBuilder, MaterialXDocumentManager


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


# Declarative node schemas for generic mapping
NODE_SCHEMAS = {
    'MIX': [
        # Support both legacy and current Blender Mix node input names
        {'blender': 'A', 'mtlx': 'fg', 'type': 'color3'},
        {'blender': 'B', 'mtlx': 'bg', 'type': 'color3'},
        {'blender': 'Factor', 'mtlx': 'mix', 'type': 'float'},
        {'blender': 'Color1', 'mtlx': 'fg', 'type': 'color3'},
        {'blender': 'Color2', 'mtlx': 'bg', 'type': 'color3'},
        {'blender': 'Fac', 'mtlx': 'mix', 'type': 'float'},
    ],
    'INVERT': [
        {'blender': 'Color', 'mtlx': 'in', 'type': 'color3'},
    ],
    'COMBINE_COLOR': [
        {'blender': 'R', 'mtlx': 'r', 'type': 'float'},
        {'blender': 'G', 'mtlx': 'g', 'type': 'float'},
        {'blender': 'B', 'mtlx': 'b', 'type': 'float'},
    ],
    'SEPARATE_COLOR': [
        {'blender': 'Color', 'mtlx': 'in', 'type': 'color3'},
    ],
    'CHECKER_TEXTURE': [
        {'blender': 'Color1', 'mtlx': 'in1', 'type': 'color3'},
        {'blender': 'Color2', 'mtlx': 'in2', 'type': 'color3'},
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector2'},
    ],
    'IMAGE_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector2'},
        # 'file' handled separately
    ],
    'PRINCIPLED_BSDF': [
        {'blender': 'Base Color', 'mtlx': 'base_color', 'type': 'color3'},
        {'blender': 'Metallic', 'mtlx': 'metallic', 'type': 'float'},
        {'blender': 'Roughness', 'mtlx': 'roughness', 'type': 'float'},
        {'blender': 'Specular', 'mtlx': 'specular', 'type': 'float'},
        {'blender': 'IOR', 'mtlx': 'ior', 'type': 'float'},
        {'blender': 'Transmission', 'mtlx': 'transmission', 'type': 'float'},
        {'blender': 'Alpha', 'mtlx': 'opacity', 'type': 'float'},
        {'blender': 'Normal', 'mtlx': 'normal', 'type': 'vector3'},
        {'blender': 'Emission Color', 'mtlx': 'emission_color', 'type': 'color3'},
        {'blender': 'Emission Strength', 'mtlx': 'emission', 'type': 'float'},
        {'blender': 'Subsurface', 'mtlx': 'subsurface', 'type': 'float'},
        {'blender': 'Subsurface Radius', 'mtlx': 'subsurface_radius', 'type': 'color3'},
        {'blender': 'Subsurface Scale', 'mtlx': 'subsurface_scale', 'type': 'float'},
        {'blender': 'Subsurface Anisotropy', 'mtlx': 'subsurface_anisotropy', 'type': 'float'},
        {'blender': 'Sheen', 'mtlx': 'sheen', 'type': 'float'},
        {'blender': 'Sheen Tint', 'mtlx': 'sheen_tint', 'type': 'float'},
        {'blender': 'Sheen Roughness', 'mtlx': 'sheen_roughness', 'type': 'float'},
        {'blender': 'Clearcoat', 'mtlx': 'clearcoat', 'type': 'float'},
        {'blender': 'Clearcoat Roughness', 'mtlx': 'clearcoat_roughness', 'type': 'float'},
        {'blender': 'Clearcoat IOR', 'mtlx': 'clearcoat_ior', 'type': 'float'},
        {'blender': 'Clearcoat Normal', 'mtlx': 'clearcoat_normal', 'type': 'vector3'},
        {'blender': 'Tangent', 'mtlx': 'tangent', 'type': 'vector3'},
        {'blender': 'Anisotropic', 'mtlx': 'anisotropic', 'type': 'float'},
        {'blender': 'Anisotropic Rotation', 'mtlx': 'anisotropic_rotation', 'type': 'float'},
    ],
}


class ConstantManager:
    """
    Tracks usage of constants and deduplicates/inlines them as needed.
    """
    def __init__(self):
        self.constant_cache = {}  # value tuple -> node name
        self.usage_count = {}     # node name -> count
        self.counter = 0

    def get_or_create_constant(self, builder, value, value_type):
        key = (tuple(value) if isinstance(value, (list, tuple)) else value, value_type)
        if key in self.constant_cache:
            node_name = self.constant_cache[key]
        else:
            node_name = f"const_{value_type}_{self.counter}"
            self.counter += 1
            builder.add_node("constant", node_name, value_type, value=value)
            self.constant_cache[key] = node_name
        self.usage_count[node_name] = self.usage_count.get(node_name, 0) + 1
        return node_name

    def should_emit_constant(self, node_name):
        return self.usage_count.get(node_name, 0) > 1

    def reset(self):
        self.constant_cache.clear()
        self.usage_count.clear()
        self.counter = 0


def map_node_with_schema(node, builder, schema, node_type, node_category, constant_manager=None, exported_nodes=None):
    """
    Generic node mapping using a schema.
    - node: Blender node
    - builder: MaterialXBuilder
    - schema: list of dicts with 'blender', 'mtlx', 'type'
    - node_type: MaterialX node type (e.g., 'mix')
    - node_category: MaterialX node category/type (e.g., 'color3')
    Returns the created node name.
    """
    logger = getattr(builder, 'logger', None)
    if logger:
        logger.info(f"[map_node_with_schema] Mapping node: {getattr(node, 'name', str(node))} as type {node_type}")
    node_name = builder.add_node(node_type, f"{node_type}_{node.name}", node_category)
    for entry in schema:
        blender_input = entry['blender']
        mtlx_input = entry['mtlx']
        type_str = entry['type']
        try:
            if logger:
                logger.info(f"[map_node_with_schema]  Processing input '{blender_input}' for node '{getattr(node, 'name', str(node))}'")
            is_connected, value_or_node, input_type = get_input_value_or_connection(node, blender_input, exported_nodes)
            if logger:
                logger.info(f"[map_node_with_schema]   is_connected={is_connected}, value_or_node={value_or_node}, input_type={input_type}")
            if is_connected:
                if logger:
                    logger.info(f"[map_node_with_schema]   Adding connection: {value_or_node}.out -> {node_name}.{mtlx_input}")
                builder.add_connection(
                    value_or_node, "out",
                    node_name, mtlx_input
                )
            elif value_or_node is not None:
                if constant_manager and value_or_node is not None:
                    const_node = constant_manager.get_or_create_constant(builder, value_or_node, type_str)
                    if logger:
                        logger.info(f"[map_node_with_schema]   Using constant node: {const_node} for input '{mtlx_input}'")
                    if constant_manager.should_emit_constant(const_node):
                        builder.add_connection(const_node, "out", node_name, mtlx_input)
                    else:
                        target_node = builder.nodes[node_name]
                        input_elem = ET.SubElement(target_node, "input")
                        input_elem.set("name", mtlx_input)
                        input_elem.set("type", type_str)
                        input_elem.set("value", str(value_or_node))
                else:
                    target_node = builder.nodes[node_name]
                    input_elem = ET.SubElement(target_node, "input")
                    input_elem.set("name", mtlx_input)
                    input_elem.set("type", type_str)
                    input_elem.set("value", str(value_or_node))
        except (KeyError, AttributeError) as e:
            if logger:
                logger.warning(f"[map_node_with_schema]  Exception for input '{blender_input}' on node '{getattr(node, 'name', str(node))}': {e}")
            continue  # Input not present, skip
    if logger:
        logger.info(f"[map_node_with_schema] Finished mapping node: {getattr(node, 'name', str(node))} -> {node_name}")
    return node_name


class MaterialXBuilder:
    """Builds MaterialX XML documents using MaterialX library."""
    
    def __init__(self, material_name: str, logger, version: str = "1.38" ):
        self.material_name = material_name
        self.version = version
        self.logger = logger

        # Use the MaterialX library-based builder
        self.library_builder = MaterialXLibraryBuilder(material_name, logger, version)
        self.logger.info("Using MaterialX library-based builder")
    
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """Add a node to the nodegraph."""
        return self.library_builder.add_node(node_type, name, node_type_category, **params)
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """Add a connection between nodes using input tags with nodename."""
        self.library_builder.add_connection(from_node, from_output, to_node, to_input)
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """Add a surface shader node outside the nodegraph."""
        return self.library_builder.add_surface_shader_node(node_type, name, **params)
    
    def add_surface_shader_input(self, surface_node_name: str, input_name: str, input_type: str, nodegraph_name: str = None, nodename: str = None, value: str = None):
        """Add an input to a surface shader node."""
        self.library_builder.add_surface_shader_input(surface_node_name, input_name, input_type, nodegraph_name, nodename, value)
    
    def add_output(self, name: str, output_type: str, nodename: str):
        """Add an output node to the nodegraph."""
        self.library_builder.add_output(name, output_type, nodename)
    
    def set_material_surface(self, surface_node_name: str):
        """Set the surface shader for the material."""
        self.library_builder.set_material_surface(surface_node_name)
    

    
    def to_string(self) -> str:
        """Convert the document to a formatted XML string."""
        return self.library_builder.to_string()


class NodeMapper:
    """Maps Blender nodes to MaterialX nodes."""
    
    @staticmethod
    def get_node_mapper(node_type: str):
        """Get the appropriate mapper for a node type."""
        mappers = {
            'BSDF_PRINCIPLED': NodeMapper.map_principled_bsdf,
            'TEX_IMAGE': NodeMapper.map_image_texture,
            'TEX_COORD': NodeMapper.map_tex_coord,
            'RGB': NodeMapper.map_rgb,
            'VALUE': NodeMapper.map_value,
            'NORMAL_MAP': NodeMapper.map_normal_map,
            'VECTOR_MATH': NodeMapper.map_vector_math,
            'VECT_MATH': NodeMapper.map_vector_math,  # Alias for Vector Math
            'MATH': NodeMapper.map_math,
            'MIX': NodeMapper.map_mix,
            'MIX_RGB': NodeMapper.map_mix,  # Alias for MixRGB
            'MIX_RGB_LEGACY': NodeMapper.map_mix,  # Alias for legacy Mix
            'INVERT': NodeMapper.map_invert,
            'SEPARATE_COLOR': NodeMapper.map_separate_color,
            'COMBINE_COLOR': NodeMapper.map_combine_color,
            'BUMP': NodeMapper.map_bump,
            'TEX_CHECKER': NodeMapper.map_checker_texture,
            'TEX_GRADIENT': NodeMapper.map_gradient_texture,
            'TEX_NOISE': NodeMapper.map_noise_texture,
            'MAPPING': NodeMapper.map_mapping,
            'LAYER': NodeMapper.map_layer,
            'ADD': NodeMapper.map_add,
            'MULTIPLY': NodeMapper.map_multiply,
            'ROUGHNESS_ANISOTROPY': NodeMapper.map_roughness_anisotropy,
            'ARTISTIC_IOR': NodeMapper.map_artistic_ior,
            'COLORRAMP': NodeMapper.map_color_ramp,  # New
            'VALTORGB': NodeMapper.map_color_ramp,   # Alias for ColorRamp
            'WAVE': NodeMapper.map_wave_texture,     # New
            'WAVE_TEXTURE': NodeMapper.map_wave_texture, # Alias
            'TEX_WAVE': NodeMapper.map_wave_texture,     # Alias for Wave Texture
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
    def map_principled_bsdf(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        # Use schema-driven mapping for all standard inputs
        node_name = builder.add_surface_shader_node("standard_surface", f"surface_{node.name}")
        for entry in NODE_SCHEMAS['PRINCIPLED_BSDF']:
            blender_input = entry['blender']
            mtlx_param = entry['mtlx']
            param_type = entry['type']
            try:
                is_connected, value_or_node, type_str = get_input_value_or_connection(node, blender_input, exported_nodes)
                # Special case: skip unconnected normal/tangent inputs for standard_surface
                if mtlx_param in ("normal", "tangent") and not is_connected:
                    continue
                if is_connected:
                    builder.add_output(mtlx_param, param_type, value_or_node)
                    builder.add_surface_shader_input(
                        node_name, mtlx_param, param_type, 
                        nodegraph_name=builder.material_name
                    )
                else:
                    formatted_value = format_socket_value(value_or_node)
                    builder.add_surface_shader_input(
                        node_name, mtlx_param, param_type, 
                        value=formatted_value
                    )
            except (KeyError, AttributeError):
                continue  # Input not present, skip
        return node_name
    
    @staticmethod
    def map_image_texture(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        # Use schema-driven mapping for standard inputs
        node_name = map_node_with_schema(node, builder, NODE_SCHEMAS['IMAGE_TEXTURE'], 'image', 'color3', constant_manager, exported_nodes)

        # Custom logic for file/image handling
        if node.image:
            image_path = node.image.filepath
            if image_path:
                exporter = getattr(builder, 'exporter', None)
                if exporter and image_path in exporter.texture_paths:
                    rel_path = exporter.texture_paths[image_path]
                else:
                    rel_path = os.path.basename(image_path)
                input_elem = ET.SubElement(builder.nodes[node_name], "input")
                input_elem.set("name", "file")
                input_elem.set("type", "filename")
                input_elem.set("value", str(rel_path))
        return node_name
    
    @staticmethod
    def map_tex_coord(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Texture Coordinate node to MaterialX texcoord node."""
        node_name = builder.add_node("texcoord", f"texcoord_{node.name}", "vector2")
        return node_name
    
    @staticmethod
    def map_rgb(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map RGB node to MaterialX constant node."""
        color = [node.outputs[0].default_value[0], 
                node.outputs[0].default_value[1], 
                node.outputs[0].default_value[2]]
        node_name = builder.add_node("constant", f"rgb_{node.name}", "color3")
        input_elem = ET.SubElement(builder.nodes[node_name], "input")
        input_elem.set("name", "value")
        input_elem.set("type", "color3")
        input_elem.set("value", str(f"{color[0]}, {color[1]}, {color[2]}"))
        return node_name
    
    @staticmethod
    def map_value(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Value node to MaterialX constant node."""
        value = node.outputs[0].default_value
        node_name = builder.add_node("constant", f"value_{node.name}", "float")
        input_elem = ET.SubElement(builder.nodes[node_name], "input")
        input_elem.set("name", "value")
        input_elem.set("type", "float")
        input_elem.set("value", str(value))
        return node_name
    
    @staticmethod
    def map_normal_map(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        """Map Normal Map node to MaterialX normalmap node."""
        node_name = builder.add_node("normalmap", f"normalmap_{node.name}", "vector3")
        
        # Handle color input
        if 'Color' in input_nodes:
            builder.add_connection(
                input_nodes['Color'], "out",
                node_name, "in"
            )
        
        # Handle strength
        if 'Strength' in input_nodes:
            builder.add_connection(
                input_nodes['Strength'], "out",
                node_name, "scale"
            )
        
        return node_name
    
    @staticmethod
    def map_vector_math(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Vector Math node to MaterialX math nodes."""
        operation = getattr(node, 'operation', 'ADD').lower()
        
        # Map operations to MaterialX node types
        operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'cross_product': 'crossproduct',
            'dot_product': 'dotproduct',
            'normalize': 'normalize',
            'length': 'magnitude',
            'distance': 'distance',
            'reflect': 'reflect',
            'refract': 'refract',
            'project': 'project',
            'clamp': 'clamp',
            'floor': 'floor',
            'ceil': 'ceil',
            'modulo': 'modulo',
            'round': 'round',
            'sign': 'sign',
            'min': 'min',
            'max': 'max',
            'abs': 'abs',
        }
        
        mtlx_operation = operation_map.get(operation, 'add')
        node_name = builder.add_node(mtlx_operation, f"vector_math_{node.name}", "vector3")
        logger = getattr(builder, 'logger', None)
        for i, mtlx_input in enumerate(['in1', 'in2']):
            if i < len(node.inputs):
                socket = node.inputs[i]
                socket_name = socket.name
                is_linked = socket.is_linked and socket.links
                if logger:
                    logger.info(f"[map_vector_math] Node '{node.name}' input {i}: Blender socket name='{socket_name}', is_linked={is_linked}")
                if is_linked:
                    input_node = socket.links[0].from_node
                    if input_node in exported_nodes:
                        if logger:
                            logger.info(f"[map_vector_math]   Adding connection: {exported_nodes[input_node]}.out -> {node_name}.{mtlx_input}")
                        builder.add_connection(exported_nodes[input_node], "out", node_name, mtlx_input)
                    else:
                        if logger:
                            logger.warning(f"[map_vector_math]   Linked input_node '{input_node.name}' not in exported_nodes!")
                else:
                    default_val = getattr(socket, 'default_value', None)
                    if logger:
                        logger.info(f"[map_vector_math]   Adding constant input: {mtlx_input} = {default_val}")
                    input_elem = ET.SubElement(builder.nodes[node_name], "input")
                    input_elem.set("name", mtlx_input)
                    input_elem.set("type", "float")
                    input_elem.set("value", str(default_val))
            else:
                if logger:
                    logger.warning(f"[map_vector_math] Node '{node.name}' does not have input socket {i} for {mtlx_input}")
        return node_name
    
    @staticmethod
    def map_math(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Math node to MaterialX math nodes."""
        logger = getattr(builder, 'logger', None)
        operation = node.operation.lower()
        operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'power': 'power',
            'logarithm': 'log',
            'square_root': 'sqrt',
            'absolute': 'abs',
            'minimum': 'min',
            'maximum': 'max',
            'sine': 'sin',
            'cosine': 'cos',
            'tangent': 'tan',
            'arcsine': 'asin',
            'arccosine': 'acos',
            'arctangent': 'atan2',
            'floor': 'floor',
            'ceil': 'ceil',
            'modulo': 'modulo',
            'round': 'round',
            'sign': 'sign',
            'compare': 'compare',
            'clamp': 'clamp',
        }
        mtlx_operation = operation_map.get(operation, 'add')
        node_name = builder.add_node(mtlx_operation, f"math_{node.name}", "float")

        # Dynamically map the first two input sockets to in1 and in2
        for i, mtlx_input in enumerate(['in1', 'in2']):
            if i < len(node.inputs):
                socket = node.inputs[i]
                socket_name = socket.name
                is_linked = socket.is_linked and socket.links
                if logger:
                    logger.info(f"[map_math] Node '{node.name}' input {i}: Blender socket name='{socket_name}', is_linked={is_linked}")
                if is_linked:
                    input_node = socket.links[0].from_node
                    if input_node in exported_nodes:
                        if logger:
                            logger.info(f"[map_math]   Adding connection: {exported_nodes[input_node]}.out -> {node_name}.{mtlx_input}")
                        builder.add_connection(exported_nodes[input_node], "out", node_name, mtlx_input)
                    else:
                        if logger:
                            logger.warning(f"[map_math]   Linked input_node '{input_node.name}' not in exported_nodes!")
                else:
                    default_val = getattr(socket, 'default_value', None)
                    if logger:
                        logger.info(f"[map_math]   Adding constant input: {mtlx_input} = {default_val}")
                    input_elem = ET.SubElement(builder.nodes[node_name], "input")
                    input_elem.set("name", mtlx_input)
                    input_elem.set("type", "float")
                    input_elem.set("value", str(default_val))
            else:
                if logger:
                    logger.warning(f"[map_math] Node '{node.name}' does not have input socket {i} for {mtlx_input}")
        return node_name
    
    @staticmethod
    def map_mix(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, NODE_SCHEMAS['MIX'], 'mix', 'color3', constant_manager, exported_nodes)

    @staticmethod
    def map_invert(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, NODE_SCHEMAS['INVERT'], 'invert', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_separate_color(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Separate Color node to MaterialX separate3 node."""
        node_name = builder.add_node("separate3", f"separate_{node.name}", "float")

        # Use centralized input handling for 'Color' input
        try:
            is_connected, value_or_node, type_str = get_input_value_or_connection(node, "Color", exported_nodes)
            if is_connected:
                builder.add_connection(
                    value_or_node, "out",
                    node_name, "in"
                )
            else:
                target_node = builder.nodes[node_name]
                input_elem = ET.SubElement(target_node, "input")
                input_elem.set("name", "in")
                input_elem.set("type", type_str)
                input_elem.set("value", str(value_or_node))
        except (KeyError, AttributeError):
            pass  # Input not present, skip

        return node_name
    
    @staticmethod
    def map_combine_color(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, NODE_SCHEMAS['COMBINE_COLOR'], 'combine3', 'color3', constant_manager, exported_nodes)

    @staticmethod
    def map_bump(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, [
            {'blender': 'Height', 'mtlx': 'in', 'type': 'float'},
            {'blender': 'Strength', 'mtlx': 'scale', 'type': 'float'},
        ], 'bump', 'vector3', constant_manager, exported_nodes)

    @staticmethod
    def map_gradient_texture(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, [
            {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector2'},
        ], 'ramp', 'color3', constant_manager, exported_nodes)

    @staticmethod
    def map_noise_texture(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        # --- 1. Handle Vector input (position) ---
        position_input = None
        if 'Vector' in input_nodes:
            position_input = input_nodes['Vector']
        # --- 2. Handle Scale input (freq = 1.0 / scale) ---
        scale_is_connected, scale_value_or_node, _ = get_input_value_or_connection(node, 'Scale', exported_nodes)
        if scale_is_connected:
            # Emit divide node: freq = 1.0 / scale
            one_const = constant_manager.get_or_create_constant(builder, 1.0, 'float')
            divide_node = builder.add_node('divide', f"noise_freq_divide_{node.name}", 'float')
            builder.add_connection(one_const, 'out', divide_node, 'in1')
            builder.add_connection(scale_value_or_node, 'out', divide_node, 'in2')
            freq_input = divide_node
        else:
            scale_val = scale_value_or_node if scale_value_or_node not in (None, '') else 5.0
            freq_val = 1.0 / scale_val if scale_val != 0 else 1.0
            freq_input = constant_manager.get_or_create_constant(builder, freq_val, 'float')
        # --- 3. Handle Detail input (octaves) ---
        detail_is_connected, detail_value_or_node, _ = get_input_value_or_connection(node, 'Detail', exported_nodes)
        if detail_is_connected:
            octaves_input = detail_value_or_node
        else:
            octaves_val = detail_value_or_node if detail_value_or_node not in (None, '') else 2.0
            octaves_input = constant_manager.get_or_create_constant(builder, octaves_val, 'float')
        # --- 4. Handle Roughness input (diminish = 1.0 - roughness) ---
        rough_is_connected, rough_value_or_node, _ = get_input_value_or_connection(node, 'Roughness', exported_nodes)
        if rough_is_connected:
            one_const = constant_manager.get_or_create_constant(builder, 1.0, 'float')
            subtract_node = builder.add_node('subtract', f"noise_diminish_subtract_{node.name}", 'float')
            builder.add_connection(one_const, 'out', subtract_node, 'in1')
            builder.add_connection(rough_value_or_node, 'out', subtract_node, 'in2')
            diminish_input = subtract_node
        else:
            rough_val = rough_value_or_node if rough_value_or_node not in (None, '') else 0.5
            diminish_val = 1.0 - rough_val
            diminish_input = constant_manager.get_or_create_constant(builder, diminish_val, 'float')
        # --- 5. Handle Lacunarity input ---
        lac_is_connected, lac_value_or_node, _ = get_input_value_or_connection(node, 'Lacunarity', exported_nodes)
        if lac_is_connected:
            lacunarity_input = lac_value_or_node
        else:
            lacunarity_val = lac_value_or_node if lac_value_or_node not in (None, '') else 2.0
            lacunarity_input = constant_manager.get_or_create_constant(builder, lacunarity_val, 'float')
        # --- 6. Handle Distortion input (jitter) ---
        dist_is_connected, dist_value_or_node, _ = get_input_value_or_connection(node, 'Distortion', exported_nodes)
        if dist_is_connected:
            jitter_input = dist_value_or_node
        else:
            jitter_val = dist_value_or_node if dist_value_or_node not in (None, '') else 0.0
            jitter_input = constant_manager.get_or_create_constant(builder, jitter_val, 'float')
        # --- 7. Create unifiednoise3d node and connect all inputs ---
        node_name = builder.add_node('unifiednoise3d', f"unifiednoise3d_{node.name}", 'float')
        # Connect position
        if position_input:
            builder.add_connection(position_input, 'out', node_name, 'position')
        # Connect freq
        builder.add_connection(freq_input, 'out', node_name, 'freq')
        # Connect octaves
        builder.add_connection(octaves_input, 'out', node_name, 'octaves')
        # Connect diminish
        builder.add_connection(diminish_input, 'out', node_name, 'diminish')
        # Connect lacunarity
        builder.add_connection(lacunarity_input, 'out', node_name, 'lacunarity')
        # Connect jitter
        builder.add_connection(jitter_input, 'out', node_name, 'jitter')
        return node_name
    
    @staticmethod
    def map_mapping(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Mapping node to MaterialX place2d node."""
        node_name = builder.add_node("place2d", f"mapping_{node.name}", "vector2")
        # Set pivot, translate, rotate, scale as <input> elements if available
        for pname in ["pivot", "translate", "rotate", "scale"]:
            val = getattr(node, pname, None)
            if val is not None:
                input_elem = ET.SubElement(builder.nodes[node_name], "input")
                input_elem.set("name", pname)
                input_elem.set("type", builder._get_param_type(val))
                input_elem.set("value", str(builder._format_value(val)))
        return node_name
    
    @staticmethod
    def map_layer(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Layer node to MaterialX layer node for vertical layering of BSDFs."""
        node_name = builder.add_node("layer", f"layer_{node.name}", "bsdf")
        
        # Handle top BSDF
        if 'Top' in input_nodes:
            builder.add_connection(
                input_nodes['Top'], "out",
                node_name, "top"
            )
        
        # Handle base BSDF
        if 'Base' in input_nodes:
            builder.add_connection(
                input_nodes['Base'], "out",
                node_name, "base"
            )
        
        return node_name
    
    @staticmethod
    def map_add(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        node_name = builder.add_node("add", f"add_{node.name}", "bsdf")
        logger = getattr(builder, 'logger', None)
        for i, mtlx_input in enumerate(['in1', 'in2']):
            if i < len(node.inputs):
                socket = node.inputs[i]
                socket_name = socket.name
                is_linked = socket.is_linked and socket.links
                if logger:
                    logger.info(f"[map_add] Node '{node.name}' input {i}: Blender socket name='{socket_name}', is_linked={is_linked}")
                if is_linked:
                    input_node = socket.links[0].from_node
                    if input_node in exported_nodes:
                        if logger:
                            logger.info(f"[map_add]   Adding connection: {exported_nodes[input_node]}.out -> {node_name}.{mtlx_input}")
                        builder.add_connection(exported_nodes[input_node], "out", node_name, mtlx_input)
                    else:
                        if logger:
                            logger.warning(f"[map_add]   Linked input_node '{input_node.name}' not in exported_nodes!")
                else:
                    default_val = getattr(socket, 'default_value', None)
                    if logger:
                        logger.info(f"[map_add]   Adding constant input: {mtlx_input} = {default_val}")
                    input_elem = ET.SubElement(builder.nodes[node_name], "input")
                    input_elem.set("name", mtlx_input)
                    input_elem.set("type", "float")
                    input_elem.set("value", str(default_val))
            else:
                if logger:
                    logger.warning(f"[map_add] Node '{node.name}' does not have input socket {i} for {mtlx_input}")
        return node_name
    
    @staticmethod
    def map_multiply(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Multiply node to MaterialX multiply node for distribution functions."""
        node_name = builder.add_node("multiply", f"multiply_{node.name}", "bsdf")
        for blender_input, mtlx_input in [("A", "in1"), ("B", "in2")]:
            if blender_input in input_nodes:
                builder.add_connection(input_nodes[blender_input], "out", node_name, mtlx_input)
            else:
                if blender_node is not None:
                    idx = [i for i, inp in enumerate(blender_node.inputs) if inp.name == blender_input]
                    if idx:
                        default_val = blender_node.inputs[idx[0]].default_value
                        input_elem = ET.SubElement(builder.nodes[node_name], "input")
                        input_elem.set("name", mtlx_input)
                        if isinstance(default_val, (float, int)):
                            input_elem.set("type", "float")
                            input_elem.set("value", str(default_val))
                        elif hasattr(default_val, "__len__") and len(default_val) == 4:
                            input_elem.set("type", "color3")
                            input_elem.set("value", str(f"{default_val[0]}, {default_val[1]}, {default_val[2]}"))
        return node_name
    
    @staticmethod
    def map_roughness_anisotropy(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Roughness Anisotropy node to MaterialX roughness_anisotropy utility node."""
        node_name = builder.add_node("roughness_anisotropy", f"roughness_anisotropy_{node.name}", "vector2")
        
        # Handle roughness input
        if 'Roughness' in input_nodes:
            builder.add_connection(
                input_nodes['Roughness'], "out",
                node_name, "roughness"
            )
        
        # Handle anisotropy input
        if 'Anisotropy' in input_nodes:
            builder.add_connection(
                input_nodes['Anisotropy'], "out",
                node_name, "anisotropy"
            )
        
        return node_name
    
    @staticmethod
    def map_artistic_ior(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map Artistic IOR node to MaterialX artistic_ior utility node."""
        node_name = builder.add_node("artistic_ior", f"artistic_ior_{node.name}", "vector3")
        
        # Handle reflectivity input
        if 'Reflectivity' in input_nodes:
            builder.add_connection(
                input_nodes['Reflectivity'], "out",
                node_name, "reflectivity"
            )
        
        # Handle edge color input
        if 'Edge Color' in input_nodes:
            builder.add_connection(
                input_nodes['Edge Color'], "out",
                node_name, "edge_color"
            )
        
        return node_name

    @staticmethod
    def map_color_ramp(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Map ColorRamp node to MaterialX ramp4 node."""
        node_name = builder.add_node("ramp4", f"color_ramp_{node.name}", "color3")
        ramp = getattr(node, 'color_ramp', None)
        # Set ramp4 corners as valuetl, valuetr, valuebl, valuebr
        if ramp and len(ramp.elements) >= 4:
            # Assume: 0=tl, 1=tr, 2=bl, 3=br (user may want to customize mapping)
            names = ["valuetl", "valuetr", "valuebl", "valuebr"]
            for i, elem in enumerate(ramp.elements[:4]):
                color = elem.color[:3]
                input_elem = ET.SubElement(builder.nodes[node_name], "input")
                input_elem.set("name", names[i])
                input_elem.set("type", "color3")
                input_elem.set("value", str(f"{color[0]}, {color[1]}, {color[2]}"))
        # Connect texcoord if available
        if 'Vector' in input_nodes:
            builder.add_connection(input_nodes['Vector'], "out", node_name, "texcoord")
        return node_name

    @staticmethod
    def map_wave_texture(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Approximate Wave Texture node using MaterialX nodes (sin, add, etc.)."""
        # Approximate: sin(frequency * (x + y) + phase)
        # 1. Add x and y (from input or texcoord)
        # 2. Multiply by scale
        # 3. Add phase
        # 4. Pass through sin
        #
        # For now, just create a sin node with a placeholder input
        # (A more accurate mapping would require more node logic)
        #
        # Get input (Vector or UV)
        if 'Vector' in input_nodes:
            input_node = input_nodes['Vector']
        else:
            input_node = None
        # Add a multiply node for scale
        mult_node = builder.add_node("multiply", f"wave_mult_{node.name}", "float")
        if input_node:
            builder.add_connection(input_node, "out", mult_node, "in1")
        # Set scale as in2 (as <input> element, not as attribute)
        scale = getattr(node, 'scale', 1.0)
        input_elem = ET.SubElement(builder.nodes[mult_node], "input")
        input_elem.set("name", "in2")
        input_elem.set("type", "float")
        input_elem.set("value", str(scale))
        # Add a sin node
        sin_node = builder.add_node("sin", f"wave_sin_{node.name}", "float")
        builder.add_connection(mult_node, "out", sin_node, "in")
        return sin_node

    @staticmethod
    def map_checker_texture(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        return map_node_with_schema(node, builder, NODE_SCHEMAS['CHECKER_TEXTURE'], 'checker', 'color3', constant_manager, exported_nodes)

    @staticmethod
    def map_hsvtorgb(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("hsvtorgb", f"hsvtorgb_{node.name}", "color3")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        return node_name

    @staticmethod
    def map_rgbtohsv(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("rgbtohsv", f"rgbtohsv_{node.name}", "color3")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        return node_name

    @staticmethod
    def map_luminance(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("luminance", f"luminance_{node.name}", "float")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        return node_name

    @staticmethod
    def map_contrast(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("contrast", f"contrast_{node.name}", "color3")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        if 'Contrast' in input_nodes:
            builder.add_connection(input_nodes['Contrast'], "out", node_name, "amount")
        return node_name

    @staticmethod
    def map_saturate(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("saturate", f"saturate_{node.name}", "color3")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        if 'Saturation' in input_nodes:
            builder.add_connection(input_nodes['Saturation'], "out", node_name, "amount")
        return node_name

    @staticmethod
    def map_gamma(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("gamma", f"gamma_{node.name}", "color3")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        if 'Gamma' in input_nodes:
            builder.add_connection(input_nodes['Gamma'], "out", node_name, "amount")
        return node_name

    @staticmethod
    def map_split_color(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("separate3", f"split_color_{node.name}", "float")
        if 'Color' in input_nodes:
            builder.add_connection(input_nodes['Color'], "out", node_name, "in")
        return node_name

    @staticmethod
    def map_merge_color(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("combine3", f"merge_color_{node.name}", "color3")
        for c, mtlx_input in zip(['R', 'G', 'B'], ['r', 'g', 'b']):
            if c in input_nodes:
                builder.add_connection(input_nodes[c], "out", node_name, mtlx_input)
        return node_name

    @staticmethod
    def map_split_vector(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("separate3", f"split_vector_{node.name}", "float")
        if 'Vector' in input_nodes:
            builder.add_connection(input_nodes['Vector'], "out", node_name, "in")
        return node_name

    @staticmethod
    def map_merge_vector(node, builder, input_nodes, input_nodes_by_index=None, blender_node=None, constant_manager=None, exported_nodes=None):
        node_name = builder.add_node("combine3", f"merge_vector_{node.name}", "vector3")
        for c, mtlx_input in zip(['X', 'Y', 'Z'], ['in1', 'in2', 'in3']):
            if c in input_nodes:
                builder.add_connection(input_nodes[c], "out", node_name, mtlx_input)
        return node_name


class MaterialXExporter:
    """Main MaterialX exporter class."""
    
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
        self.strict_mode = True  # Always strict mode
        # Internal state
        self.exported_nodes = {}
        self.texture_paths = {}
        self.builder = None
        self.unsupported_nodes = []
        self.constant_manager = ConstantManager()

    def export(self) -> dict:
        """Export the material to MaterialX format. Returns a result dict."""
        result = {
            "success": False,
            "unsupported_nodes": [],
            "output_path": str(self.output_path),
            "error": None,
        }
        try:
            self.logger.info(f"Starting export of material '{self.material.name}'")
            self.logger.info(f"Output path: {self.output_path}")
            self.logger.info(f"Material uses nodes: {self.material.use_nodes}")
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
                self.logger.info(f"No Principled BSDF node found in material '{self.material.name}'")
                self.logger.info("Available node types:")
                for node in self.material.node_tree.nodes:
                    self.logger.info(f"  - {node.name}: {node.type}")
                result["error"] = "No Principled BSDF node found"
                return result
            self.logger.info(f"Found Principled BSDF node: {principled_node.name}")
            self.builder = MaterialXBuilder(self.material.name, self.logger, self.materialx_version)
            # Attach exporter to builder for relative path lookup
            self.builder.exporter = self
            self.logger.info(f"Created MaterialX builder with version {self.materialx_version}")
            self.logger.info("Starting node network export...")
            surface_node_name = self._export_node_network(principled_node)
            self.logger.info(f"Node network export completed. Surface node: {surface_node_name}")
            self.builder.set_material_surface(surface_node_name)
            self._write_file()
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
                    self.logger.error(f"  ✗ Failed to export {node.name}: {str(e)}")
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
            if self.strict_mode:
                raise RuntimeError(f"Unsupported node type encountered in strict mode: {node.type} ({node.name})")
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
        """Write the MaterialX document to file."""
        try:
            self.logger.info(f"Ensuring output directory exists: {self.output_path.parent}")
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Writing MaterialX content to: {self.output_path}")
            
            # Use library-based writing
            success = self.builder.library_builder.write_to_file(str(self.output_path))
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
                                logger,
                                options: Dict = None) -> dict:
    """
    Export a Blender material to MaterialX format.
    Returns a dict with success, unsupported_nodes, output_path, and error (if any).
    """
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


# Example usage and testing functions
def create_test_material():
    """Create a test material for demonstration."""
    # Create a new material
    material = bpy.data.materials.new(name="TestMaterial")
    material.use_nodes = True
    
    # Get the node tree
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Create RGB node for base color
    rgb = nodes.new(type='ShaderNodeRGB')
    rgb.location = (-300, 0)
    rgb.outputs[0].default_value = (0.8, 0.2, 0.2, 1.0)  # Red color
    
    # Create Value node for roughness
    roughness = nodes.new(type='ShaderNodeValue')
    roughness.location = (-300, -200)
    roughness.outputs[0].default_value = 0.5
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes
    links.new(rgb.outputs[0], principled.inputs['Base Color'])
    links.new(roughness.outputs[0], principled.inputs['Roughness'])
    links.new(principled.outputs[0], output.inputs['Surface'])
    
    return material


def test_export():
    """Test the MaterialX exporter with a simple material."""
    # Create test material
    material = create_test_material()
    
    # Export options
    options = {
        'active_uvmap': 'UVMap',
        'export_textures': False,
        'materialx_version': '1.38',
        'relative_paths': True,
    }
    
    # Export the material
    success = export_material_to_materialx(material, "test_material.mtlx", options)
    
    if success["success"]:
        logger.info("Test export successful!")
        # Clean up test material
        bpy.data.materials.remove(material)
    else:
        logger.error("Test export failed!")
        logger.error(f"Unsupported nodes: {success['unsupported_nodes']}")


if __name__ == "__main__":
    # This will run when the script is executed directly
    test_export() 