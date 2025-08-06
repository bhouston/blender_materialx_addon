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
    print("MaterialX library core imported successfully")
except ImportError as e:
    print(f"Failed to import MaterialX library core: {e}")
    # Fallback for direct import
    import materialx_library_core
    from materialx_library_core import MaterialXLibraryBuilder, MaterialXDocumentManager, MaterialXTypeConverter
    print("MaterialX library core imported via fallback")


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


def get_node_output_name_robust(blender_node_type: str, blender_output_name: str) -> str:
    """
    Get the MaterialX output name for a Blender node output using explicit mapping.
    
    Args:
        blender_node_type: The Blender node type (e.g., 'TEX_COORD', 'MIX')
        blender_output_name: The Blender output name (e.g., 'Generated', 'Result')
        
    Returns:
        str: The MaterialX output name
        
    Raises:
        ValueError: If no explicit mapping is found
    """
    if blender_node_type in NODE_MAPPING:
        node_mapping = NODE_MAPPING[blender_node_type]
        if 'outputs' in node_mapping:
            outputs_mapping = node_mapping['outputs']
            if blender_output_name in outputs_mapping:
                return outputs_mapping[blender_output_name]
            else:
                raise ValueError(f"No explicit mapping found for output '{blender_output_name}' in node type '{blender_node_type}'. Available outputs: {list(outputs_mapping.keys())}")
        else:
            raise ValueError(f"No outputs mapping found for node type '{blender_node_type}'")
    else:
        raise ValueError(f"No explicit mapping found for node type '{blender_node_type}'. Available node types: {list(NODE_MAPPING.keys())}")


def get_node_input_name_robust(blender_node_type: str, blender_input_name: str) -> str:
    """
    Get the MaterialX input name for a Blender node input using explicit mapping.
    
    Args:
        blender_node_type: The Blender node type (e.g., 'MIX', 'NOISE_TEXTURE')
        blender_input_name: The Blender input name (e.g., 'A', 'Vector')
        
    Returns:
        str: The MaterialX input name
        
    Raises:
        ValueError: If no explicit mapping is found
    """
    if blender_node_type in NODE_MAPPING:
        node_mapping = NODE_MAPPING[blender_node_type]
        if 'inputs' in node_mapping:
            inputs_mapping = node_mapping['inputs']
            if blender_input_name in inputs_mapping:
                return inputs_mapping[blender_input_name]
            else:
                raise ValueError(f"No explicit mapping found for input '{blender_input_name}' in node type '{blender_node_type}'. Available inputs: {list(inputs_mapping.keys())}")
        else:
            raise ValueError(f"No inputs mapping found for node type '{blender_node_type}'")
    else:
        raise ValueError(f"No explicit mapping found for node type '{blender_node_type}'. Available node types: {list(NODE_MAPPING.keys())}")


def get_node_mtlx_type(blender_node_type: str) -> Tuple[str, str]:
    """
    Get the MaterialX node type and category for a Blender node type.
    
    Args:
        blender_node_type: The Blender node type
        
    Returns:
        Tuple[str, str]: (MaterialX node type, MaterialX category)
        
    Raises:
        ValueError: If no explicit mapping is found
    """
    if blender_node_type in NODE_MAPPING:
        node_mapping = NODE_MAPPING[blender_node_type]
        return node_mapping['mtlx_type'], node_mapping['mtlx_category']
    else:
        raise ValueError(f"No explicit mapping found for node type '{blender_node_type}'. Available node types: {list(NODE_MAPPING.keys())}")


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
        # Core surface properties
        {'blender': 'Base Color', 'mtlx': 'base_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Metallic', 'mtlx': 'metalness', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Roughness', 'mtlx': 'specular_roughness', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Specular', 'mtlx': 'specular', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Specular Tint', 'mtlx': 'specular_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'IOR', 'mtlx': 'specular_IOR', 'type': 'float', 'category': 'surfaceshader'},
        
        # Transmission properties
        {'blender': 'Transmission', 'mtlx': 'transmission', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Transmission Color', 'mtlx': 'transmission_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Transmission Depth', 'mtlx': 'transmission_depth', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Transmission Scatter', 'mtlx': 'transmission_scatter', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Transmission Scatter Anisotropy', 'mtlx': 'transmission_scatter_anisotropy', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Transmission Dispersion', 'mtlx': 'transmission_dispersion', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Transmission Extra Roughness', 'mtlx': 'transmission_extra_roughness', 'type': 'float', 'category': 'surfaceshader'},
        
        # Opacity
        {'blender': 'Alpha', 'mtlx': 'opacity', 'type': 'float', 'category': 'surfaceshader'},
        
        # Normal mapping
        {'blender': 'Normal', 'mtlx': 'normal', 'type': 'vector3', 'category': 'surfaceshader'},
        {'blender': 'Tangent', 'mtlx': 'tangent', 'type': 'vector3', 'category': 'surfaceshader'},
        
        # Emission properties
        {'blender': 'Emission Color', 'mtlx': 'emission_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Emission Strength', 'mtlx': 'emission', 'type': 'float', 'category': 'surfaceshader'},
        
        # Subsurface properties
        {'blender': 'Subsurface', 'mtlx': 'subsurface', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Color', 'mtlx': 'subsurface_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Radius', 'mtlx': 'subsurface_radius', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Scale', 'mtlx': 'subsurface_scale', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Subsurface Anisotropy', 'mtlx': 'subsurface_anisotropy', 'type': 'float', 'category': 'surfaceshader'},
        
        # Sheen properties
        {'blender': 'Sheen', 'mtlx': 'sheen', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Sheen Color', 'mtlx': 'sheen_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Sheen Tint', 'mtlx': 'sheen_tint', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Sheen Roughness', 'mtlx': 'sheen_roughness', 'type': 'float', 'category': 'surfaceshader'},
        
        # Coat properties
        {'blender': 'Coat', 'mtlx': 'coat', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Coat Color', 'mtlx': 'coat_color', 'type': 'color3', 'category': 'surfaceshader'},
        {'blender': 'Coat Roughness', 'mtlx': 'coat_roughness', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Coat IOR', 'mtlx': 'coat_IOR', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Coat Normal', 'mtlx': 'coat_normal', 'type': 'vector3', 'category': 'surfaceshader'},
        
        # Anisotropy properties
        {'blender': 'Anisotropic', 'mtlx': 'anisotropic', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Anisotropic Rotation', 'mtlx': 'anisotropic_rotation', 'type': 'float', 'category': 'surfaceshader'},
        {'blender': 'Anisotropic Direction', 'mtlx': 'anisotropic_direction', 'type': 'vector3', 'category': 'surfaceshader'},
        
        # Base properties (should be included for completeness)
        {'blender': 'Base', 'mtlx': 'base', 'type': 'float', 'category': 'surfaceshader'},
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
    'VORONOI_TEXTURE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
        {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
        {'blender': 'Detail', 'mtlx': 'detail', 'type': 'float', 'category': 'color3'},
    ],
    'CURVE_RGB': [
        {'blender': 'Color', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
    ],
    'CLAMP': [
        {'blender': 'Value', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Min', 'mtlx': 'low', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Max', 'mtlx': 'high', 'type': 'color3', 'category': 'color3'},
    ],
    'MAP_RANGE': [
        {'blender': 'Value', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
        {'blender': 'From Min', 'mtlx': 'inlow', 'type': 'color3', 'category': 'color3'},
        {'blender': 'From Max', 'mtlx': 'inhigh', 'type': 'color3', 'category': 'color3'},
        {'blender': 'To Min', 'mtlx': 'outlow', 'type': 'color3', 'category': 'color3'},
        {'blender': 'To Max', 'mtlx': 'outhigh', 'type': 'color3', 'category': 'color3'},
    ],
    'VALTORGB': [
        {'blender': 'Fac', 'mtlx': 'in', 'type': 'float', 'category': 'color3'},
    ],

    'TEX_MUSGRAVE': [
        {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
        {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
        {'blender': 'Detail', 'mtlx': 'detail', 'type': 'float', 'category': 'color3'},
        {'blender': 'Dimension', 'mtlx': 'dimension', 'type': 'float', 'category': 'color3'},
        {'blender': 'Lacunarity', 'mtlx': 'lacunarity', 'type': 'float', 'category': 'color3'},
    ],
    # New utility nodes
    'NEW_GEOMETRY': [
        {'blender': 'Position', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Normal', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Tangent', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'True Normal', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Incoming', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Parametric', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Backfacing', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Pointiness', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Random Per Island', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
    ],
    'OBJECT_INFO': [
        {'blender': 'Location', 'mtlx': 'out', 'type': 'vector3', 'category': 'vector3'},
        {'blender': 'Color', 'mtlx': 'out', 'type': 'color3', 'category': 'color3'},
        {'blender': 'Alpha', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Object Index', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Material Index', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Random', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
    ],
    'LIGHT_PATH': [
        {'blender': 'Is Camera Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Shadow Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Diffuse Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Glossy Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Singular Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Reflection Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Is Transmission Ray', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Ray Length', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Ray Depth', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Diffuse Depth', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Glossy Depth', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Transparent Depth', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
        {'blender': 'Transmission Depth', 'mtlx': 'out', 'type': 'float', 'category': 'float'},
    ],
}

# Robust Blender-to-MaterialX node mapping with explicit input/output relationships
NODE_MAPPING = {
    'TEX_COORD': {
        'mtlx_type': 'texcoord',
        'mtlx_category': 'vector2',
        'outputs': {
            'Generated': 'out',
            'Normal': 'out',
            'UV': 'out',
            'Object': 'out',
            'Camera': 'out',
            'Window': 'out',
            'Reflection': 'out',
        }
    },
    'RGB': {
        'mtlx_type': 'constant',
        'mtlx_category': 'color3',
        'outputs': {
            'Color': 'out',
        }
    },
    'VALUE': {
        'mtlx_type': 'constant',
        'mtlx_category': 'float',
        'outputs': {
            'Value': 'out',
        }
    },
    'MIX': {
        'mtlx_type': 'mix',
        'mtlx_category': 'color3',
        'inputs': {
            'A': 'fg',
            'B': 'bg',
            'Factor': 'mix',
            'Color1': 'fg',
            'Color2': 'bg',
            'Fac': 'mix',
        },
        'outputs': {
            'Result': 'out',
        }
    },
    'MIX_RGB': {
        'mtlx_type': 'mix',
        'mtlx_category': 'color3',
        'inputs': {
            'Color1': 'fg',
            'Color2': 'bg',
            'Fac': 'mix',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'INVERT': {
        'mtlx_type': 'invert',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'SEPARATE_COLOR': {
        'mtlx_type': 'separate3',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
        },
        'outputs': {
            'R': 'outr',
            'G': 'outg',
            'B': 'outb',
        }
    },
    'COMBINE_COLOR': {
        'mtlx_type': 'combine3',
        'mtlx_category': 'color3',
        'inputs': {
            'R': 'r',
            'G': 'g',
            'B': 'b',
        },
        'outputs': {
            'Image': 'out',
        }
    },
    'CHECKER_TEXTURE': {
        'mtlx_type': 'checkerboard',
        'mtlx_category': 'color3',
        'inputs': {
            'Color1': 'in1',
            'Color2': 'in2',
            'Vector': 'texcoord',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'TEX_NOISE': {
        'mtlx_type': 'fractal3d',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'position',
            'Scale': 'lacunarity',
            'Detail': 'octaves',
            'Roughness': 'diminish',
        },
        'outputs': {
            'Fac': 'out',
            'Color': 'out',
        }
    },
    'TEX_VORONOI': {
        'mtlx_type': 'voronoi',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'position',
            'Scale': 'scale',
            'Detail': 'detail',
        },
        'outputs': {
            'Distance': 'out',
            'Color': 'out',
        }
    },
    'TEX_WAVE': {
        'mtlx_type': 'wave',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'position',
            'Scale': 'scale',
            'Distortion': 'distortion',
            'Detail': 'detail',
        },
        'outputs': {
            'Fac': 'out',
            'Color': 'out',
        }
    },
    'TEX_CHECKER': {
        'mtlx_type': 'checkerboard',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
            'Color1': 'in1',
            'Color2': 'in2',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'CURVE_RGB': {
        'mtlx_type': 'curve',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'CLAMP': {
        'mtlx_type': 'clamp',
        'mtlx_category': 'color3',
        'inputs': {
            'Value': 'in',
            'Min': 'low',
            'Max': 'high',
        },
        'outputs': {
            'Result': 'out',
        }
    },
    'MAP_RANGE': {
        'mtlx_type': 'maprange',
        'mtlx_category': 'color3',
        'inputs': {
            'Value': 'in',
            'From Min': 'inlow',
            'From Max': 'inhigh',
            'To Min': 'outlow',
            'To Max': 'outhigh',
        },
        'outputs': {
            'Result': 'out',
        }
    },
    'GRADIENT_TEXTURE': {
        'mtlx_type': 'ramplr',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'WAVE_TEXTURE': {
        'mtlx_type': 'wave',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
            'Scale': 'scale',
            'Distortion': 'distortion',
            'Detail': 'detail',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'NORMAL_MAP': {
        'mtlx_type': 'normalmap',
        'mtlx_category': 'vector3',
        'inputs': {
            'Color': 'default',
        },
        'outputs': {
            'Normal': 'out',
        }
    },
    'VALTORGB': {
        'mtlx_type': 'ramplr',
        'mtlx_category': 'color3',
        'inputs': {
            'Fac': 'texcoord',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'BUMP': {
        'mtlx_type': 'bump',
        'mtlx_category': 'vector3',
        'inputs': {
            'Height': 'in',
        },
        'outputs': {
            'Normal': 'out',
        }
    },
    'MAPPING': {
        'mtlx_type': 'transform2d',
        'mtlx_category': 'vector2',
        'inputs': {
            'Vector': 'in',
        },
        'outputs': {
            'Vector': 'out',
        }
    },
    'MATH': {
        'mtlx_type': 'add',  # Will be overridden by operation
        'mtlx_category': 'float',
        'inputs': {
            'A': 'in1',
            'B': 'in2',
        },
        'outputs': {
            'Value': 'out',
        }
    },
    'VECTOR_MATH': {
        'mtlx_type': 'add',  # Will be overridden by operation
        'mtlx_category': 'vector3',
        'inputs': {
            'A': 'in1',
            'B': 'in2',
        },
        'outputs': {
            'Vector': 'out',
        }
    },
    'IMAGE_TEXTURE': {
        'mtlx_type': 'image',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'BSDF_PRINCIPLED': {
        'mtlx_type': 'standard_surface',
        'mtlx_category': 'surfaceshader',
        'inputs': {
            'Base Color': 'base_color',
            'Metallic': 'metallic',
            'Roughness': 'roughness',
            'Specular': 'specular',
            'IOR': 'ior',
            'Transmission': 'transmission',
            'Alpha': 'opacity',
            'Normal': 'normal',
            'Emission Color': 'emission_color',
            'Emission Strength': 'emission',
            'Subsurface': 'subsurface',
            'Subsurface Radius': 'subsurface_radius',
            'Subsurface Scale': 'subsurface_scale',
            'Subsurface Anisotropy': 'subsurface_anisotropy',
            'Sheen': 'sheen',
            'Sheen Tint': 'sheen_tint',
            'Sheen Roughness': 'sheen_roughness',
        },
        'outputs': {
            'BSDF': 'out',
        }
    },

    'TEX_MUSGRAVE': {
        'mtlx_type': 'musgrave',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
            'Scale': 'scale',
            'Detail': 'detail',
            'Dimension': 'dimension',
            'Lacunarity': 'lacunarity',
        },
        'outputs': {
            'Fac': 'out',
            'Color': 'out',
        }
    },
    # New utility nodes
    'NEW_GEOMETRY': {
        'mtlx_type': 'position',
        'mtlx_category': 'vector3',
        'outputs': {
            'Position': 'out',
            'Normal': 'out',
            'Tangent': 'out',
            'True Normal': 'out',
            'Incoming': 'out',
            'Parametric': 'out',
            'Backfacing': 'out',
            'Pointiness': 'out',
            'Random Per Island': 'out',
        }
    },
    'OBJECT_INFO': {
        'mtlx_type': 'constant',
        'mtlx_category': 'vector3',
        'outputs': {
            'Location': 'out',
            'Color': 'out',
            'Alpha': 'out',
            'Object Index': 'out',
            'Material Index': 'out',
            'Random': 'out',
        }
    },
    'LIGHT_PATH': {
        'mtlx_type': 'constant',
        'mtlx_category': 'float',
        'outputs': {
            'Is Camera Ray': 'out',
            'Is Shadow Ray': 'out',
            'Is Diffuse Ray': 'out',
            'Is Glossy Ray': 'out',
            'Is Singular Ray': 'out',
            'Is Reflection Ray': 'out',
            'Is Transmission Ray': 'out',
            'Ray Length': 'out',
            'Ray Depth': 'out',
            'Diffuse Depth': 'out',
            'Glossy Depth': 'out',
            'Transparent Depth': 'out',
            'Transmission Depth': 'out',
        }
    },
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
                # Connected input - use robust connection mapping
                # Get the source node type and output name
                source_node_type = None
                source_output_name = None
                if exported_nodes:
                    # Find the source node by looking up the MaterialX node name
                    for node_obj, node_name_in_exported in exported_nodes.items():
                        if node_name_in_exported == value_or_node:
                            source_node_type = node_obj.type
                            # Get the output name from the source node's output socket
                            for output_socket in node_obj.outputs:
                                if output_socket.links:
                                    for link in output_socket.links:
                                        if link.to_node == node and link.to_socket.name == blender_input:
                                            source_output_name = output_socket.name
                                            break
                                    if source_output_name:
                                        break
                            break
                
                # Get the correct output name using robust mapping
                if source_node_type and source_output_name:
                    output_name = get_node_output_name_robust(source_node_type, source_output_name)
                else:
                    # Fallback to default output name
                    output_name = 'out'
                
                # Get the correct input name using robust mapping
                correct_input_name = get_node_input_name_robust(node.type, blender_input)
                print(f"DEBUG: Robust mapping - node type: {node.type}, blender input: {blender_input}, mtlx param: {mtlx_param}, correct input: {correct_input_name}")
                
                builder.add_connection(value_or_node, output_name, node_name, correct_input_name)
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
    
    def __init__(self, material_name: str, logger, version: str = "1.39" ):
        self.material_name = material_name
        self.logger = logger
        self.version = version
        
        self.logger.info(f"MaterialXBuilder: Initializing with version {version}")
        
        # Initialize enhanced library builder
        self.library_builder = MaterialXLibraryBuilder(material_name, logger, version)
        self.document = self.library_builder.document
        self.nodes = self.library_builder.nodes
        self.connections = self.library_builder.connections
        self.node_counter = self.library_builder.node_counter
        
        self.logger.info(f"MaterialXBuilder: Library builder initialized, document has {len(self.document.getNodeDefs())} node definitions")
        
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
    
    def get_node_output_name(self, node_type: str, node_category: str = None) -> str:
        """
        Get the default output name for a given node type by looking up the actual MaterialX node definition.
        
        Args:
            node_type: The MaterialX node type
            node_category: The node category
            
        Returns:
            str: The default output name for the node type
        """
        try:
            # Get the node definition from the MaterialX library
            node_def = self.library_builder.document_manager.get_node_definition(node_type, node_category)
            
            if node_def:
                # Get all outputs from the node definition
                outputs = node_def.getOutputs()
                
                if outputs:
                    # Return the first output name (most nodes have a single output)
                    first_output = outputs[0]
                    output_name = first_output.getName()
                    self.logger.debug(f"Found output '{output_name}' for node type '{node_type}'")
                    return output_name
                else:
                    self.logger.warning(f"No outputs found for node type '{node_type}'")
            else:
                self.logger.warning(f"No node definition found for '{node_type}' (category: {node_category})")
                
        except Exception as e:
            self.logger.error(f"Error getting output name for node type '{node_type}': {str(e)}")
        
        # Fallback to common output names if lookup fails
        fallback_names = {
            'separate3': 'outr',  # separate3 has outr, outg, outb
            'split3': 'out1',     # split3 has out1, out2, out3
            'split2': 'out1',     # split2 has out1, out2
        }
        
        return fallback_names.get(node_type, 'out')


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
            'TEX_VORONOI': NodeMapper.map_voronoi_texture_enhanced,
            'CURVE_RGB': NodeMapper.map_curve_rgb_enhanced,
            'CLAMP': NodeMapper.map_clamp_enhanced,
            'MAP_RANGE': NodeMapper.map_map_range_enhanced,
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

            'TEX_MUSGRAVE': NodeMapper.map_musgrave_texture_enhanced,
            # New utility nodes
            'NEW_GEOMETRY': NodeMapper.map_geometry_info_enhanced,
            'OBJECT_INFO': NodeMapper.map_object_info_enhanced,
            'LIGHT_PATH': NodeMapper.map_light_path_enhanced,
        }
        return mappers.get(node_type)
    
    @staticmethod
    def map_principled_bsdf_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced Principled BSDF mapping with type-safe input creation."""
        # Create surface shader node
        node_name = builder.add_surface_shader_node("standard_surface", f"surface_{node.name}")
        
        # Default values for essential standard surface parameters
        default_values = {
            'base': 1.0,
            'specular': 1.0,
            'specular_color': [1.0, 1.0, 1.0],
            'specular_roughness': 0.5,
            'specular_IOR': 1.5,
            'metalness': 0.0,
            'transmission': 0.0,
            'transmission_color': [1.0, 1.0, 1.0],
            'transmission_depth': 0.0,
            'transmission_scatter': [0.0, 0.0, 0.0],
            'transmission_scatter_anisotropy': 0.0,
            'transmission_dispersion': 0.0,
            'transmission_extra_roughness': 0.0,
            'opacity': [1.0, 1.0, 1.0],
            'emission': 0.0,
            'emission_color': [1.0, 1.0, 1.0],
            'subsurface': 0.0,
            'subsurface_color': [1.0, 1.0, 1.0],
            'subsurface_radius': [1.0, 0.2, 0.1],
            'subsurface_scale': 0.05,
            'subsurface_anisotropy': 0.0,
            'sheen': 0.0,
            'sheen_color': [1.0, 1.0, 1.0],
            'sheen_tint': 1.0,
            'sheen_roughness': 0.5,
            'coat': 0.0,
            'coat_color': [1.0, 1.0, 1.0],
            'coat_roughness': 0.1,
            'coat_IOR': 1.5,
            'anisotropic': 0.0,
            'anisotropic_rotation': 0.0,
            'anisotropic_direction': [0.0, 1.0, 0.0],
        }
        
        # Essential parameters that should always be included (with default values)
        essential_params = {
            'base': 1.0,
            'specular': 1.0,
            'specular_roughness': 0.5
        }
        
        # First, add essential parameters that should always be present
        for mtlx_param, default_value in essential_params.items():
            builder.library_builder.node_builder.create_mtlx_input(
                builder.nodes[node_name], mtlx_param, 
                value=default_value,
                node_type='standard_surface', category='surfaceshader'
            )
        
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
                
                # Skip essential parameters that we already added
                if mtlx_param in essential_params:
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
                    # Handle different value types properly
                    if param_type == 'float':
                        # For float inputs, extract the first component if it's a vector/color
                        if isinstance(value_or_node, (list, tuple)) and len(value_or_node) > 0:
                            value_or_node = value_or_node[0]
                        # Use default if no value provided
                        if value_or_node is None:
                            value_or_node = default_values.get(mtlx_param, 0.0)
                    elif param_type == 'color3':
                        # For color3 inputs, ensure we have 3 components
                        if isinstance(value_or_node, (list, tuple)):
                            if len(value_or_node) >= 3:
                                value_or_node = value_or_node[:3]
                            else:
                                # Pad with zeros if not enough components
                                value_or_node = list(value_or_node) + [0.0] * (3 - len(value_or_node))
                        # Use default if no value provided
                        if value_or_node is None:
                            value_or_node = default_values.get(mtlx_param, [1.0, 1.0, 1.0])
                    elif param_type == 'vector3':
                        # For vector3 inputs, ensure we have 3 components
                        if isinstance(value_or_node, (list, tuple)):
                            if len(value_or_node) >= 3:
                                value_or_node = value_or_node[:3]
                            else:
                                # Pad with zeros if not enough components
                                value_or_node = list(value_or_node) + [0.0] * (3 - len(value_or_node))
                        # Use default if no value provided
                        if value_or_node is None:
                            value_or_node = default_values.get(mtlx_param, [0.0, 0.0, 0.0])
                    
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
                # Get the correct output name from the source node using robust mapping
                source_node_type = None
                source_output_name = None
                if exported_nodes:
                    for node_obj, node_name_in_exported in exported_nodes.items():
                        if node_name_in_exported == value_or_node:
                            source_node_type = node_obj.type
                            # Get the output name from the source node's output socket
                            for output_socket in node_obj.outputs:
                                if output_socket.links:
                                    for link in output_socket.links:
                                        if link.to_node == node and link.to_socket.name == 'Color':
                                            source_output_name = output_socket.name
                                            break
                                    if source_output_name:
                                        break
                            break
                
                # Get the correct output name using robust mapping
                if source_node_type and source_output_name:
                    output_name = get_node_output_name_robust(source_node_type, source_output_name)
                else:
                    # Fallback to default output name
                    output_name = 'out'
                
                # Get the correct input name using robust mapping
                correct_input_name = get_node_input_name_robust(node.type, 'Color')
                print(f"DEBUG: Normal map robust mapping - node type: {node.type}, blender input: Color, correct input: {correct_input_name}")
                
                builder.add_connection(value_or_node, output_name, node_name, correct_input_name)
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
                        # Get the correct output name from the source node
                        source_node_type = None
                        if exported_nodes:
                            for node_obj, node_name_in_exported in exported_nodes.items():
                                if node_name_in_exported == value_or_node:
                                    source_node_type = node_obj.type
                                    break
                        
                        # Map Blender node type to MaterialX node type
                        blender_to_mtlx_type = {
                            'TEX_COORD': 'texcoord',
                            'RGB': 'constant',
                            'VALUE': 'constant',
                            'MIX': 'mix',
                            'INVERT': 'invert',
                            'SEPARATE_COLOR': 'separate3',
                            'COMBINE_COLOR': 'combine3',
                            'CHECKER_TEXTURE': 'checkerboard',
                            'GRADIENT_TEXTURE': 'ramplr',
                            'NOISE_TEXTURE': 'fractal3d',
                            'WAVE_TEXTURE': 'wave',
                            'NORMAL_MAP': 'normalmap',
                            'BUMP': 'bump',
                            'MAPPING': 'transform2d',
                            'LAYER_WEIGHT': 'layer',
                            'MATH': 'add',
                            'VECTOR_MATH': 'add',
                            'IMAGE_TEXTURE': 'image',
                            'BSDF_PRINCIPLED': 'standard_surface',
                        }
                        
                        mtlx_source_type = blender_to_mtlx_type.get(source_node_type, 'constant')
                        output_name = builder.get_node_output_name(mtlx_source_type)
                        
                        builder.add_connection(value_or_node, output_name, node_name, mtlx_param)
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
                        # Get the correct output name from the source node
                        source_node_type = None
                        if exported_nodes:
                            for node_obj, node_name_in_exported in exported_nodes.items():
                                if node_name_in_exported == value_or_node:
                                    source_node_type = node_obj.type
                                    break
                        
                        # Map Blender node type to MaterialX node type
                        blender_to_mtlx_type = {
                            'TEX_COORD': 'texcoord',
                            'RGB': 'constant',
                            'VALUE': 'constant',
                            'MIX': 'mix',
                            'INVERT': 'invert',
                            'SEPARATE_COLOR': 'separate3',
                            'COMBINE_COLOR': 'combine3',
                            'CHECKER_TEXTURE': 'checkerboard',
                            'GRADIENT_TEXTURE': 'ramplr',
                            'NOISE_TEXTURE': 'fractal3d',
                            'WAVE_TEXTURE': 'wave',
                            'NORMAL_MAP': 'normalmap',
                            'BUMP': 'bump',
                            'MAPPING': 'transform2d',
                            'LAYER_WEIGHT': 'layer',
                            'MATH': 'add',
                            'VECTOR_MATH': 'add',
                            'IMAGE_TEXTURE': 'image',
                            'BSDF_PRINCIPLED': 'standard_surface',
                        }
                        
                        mtlx_source_type = blender_to_mtlx_type.get(source_node_type, 'constant')
                        output_name = builder.get_node_output_name(mtlx_source_type)
                        
                        builder.add_connection(value_or_node, output_name, node_name, mtlx_param)
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
    
    @staticmethod
    def map_voronoi_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced voronoi texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['VORONOI_TEXTURE'], 'voronoi', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_curve_rgb_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced RGB curves mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['CURVE_RGB'], 'curve', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_clamp_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced clamp mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['CLAMP'], 'clamp', 'color3', constant_manager, exported_nodes)
    
    @staticmethod
    def map_map_range_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced map range mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['MAP_RANGE'], 'maprange', 'color3', constant_manager, exported_nodes)
    
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
        """Map ColorRamp node to MaterialX ramp node."""
        # Create ramp node with proper type - use color4 since ramp outputs color4
        node_name = builder.add_node("ramp", f"colorramp_{node.name}", "color4")
        
        # Extract Color Ramp data from Blender node
        if hasattr(node, 'color_ramp'):
            ramp = node.color_ramp
            
            # Set interpolation type
            interpolation_map = {
                'LINEAR': 0,
                'CONSTANT': 2,
                'EASING': 1,
                'CARDINAL': 1,
                'B_SPLINE': 1
            }
            interpolation = interpolation_map.get(ramp.interpolation, 1)
            
            # Get the number of elements (control points)
            num_elements = len(ramp.elements)
            num_intervals = max(2, num_elements - 1)  # At least 2 intervals
            
            # Set basic ramp properties
            builder.library_builder.node_builder.create_mtlx_input(
                builder.nodes[node_name], 'interpolation', 
                value=interpolation,
                node_type='ramp', category='color4'
            )
            
            builder.library_builder.node_builder.create_mtlx_input(
                builder.nodes[node_name], 'num_intervals', 
                value=num_intervals,
                node_type='ramp', category='color4'
            )
            
            # Map control points (up to 10 supported by MaterialX)
            for i in range(min(num_elements, 10)):
                element = ramp.elements[i]
                
                # Set interval position
                interval_name = f'interval{i+1}' if i > 0 else 'interval1'
                builder.library_builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], interval_name, 
                    value=element.position,
                    node_type='ramp', category='color4'
                )
                
                # Set color (convert to color4)
                color_name = f'color{i+1}' if i > 0 else 'color1'
                color_value = [element.color[0], element.color[1], element.color[2], element.alpha]
                builder.library_builder.node_builder.create_mtlx_input(
                    builder.nodes[node_name], color_name, 
                    value=color_value,
                    node_type='ramp', category='color4'
                )
        
        # Connect input if available
        try:
            is_connected, value_or_node, type_str = get_input_value_or_connection(node, 'Fac', exported_nodes)
            if is_connected:
                # Connect to texcoord input
                builder.add_connection(value_or_node, 'out', node_name, 'texcoord')
        except (KeyError, AttributeError):
            pass
        
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



    @staticmethod
    def map_musgrave_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced musgrave texture mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['TEX_MUSGRAVE'], 'musgrave', 'color3', constant_manager, exported_nodes)

    # New utility node mappers
    @staticmethod
    def map_geometry_info_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced geometry info mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['NEW_GEOMETRY'], 'position', 'vector3', constant_manager, exported_nodes)

    @staticmethod
    def map_object_info_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced object info mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['OBJECT_INFO'], 'constant', 'vector3', constant_manager, exported_nodes)

    @staticmethod
    def map_light_path_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced light path mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['LIGHT_PATH'], 'constant', 'float', constant_manager, exported_nodes)


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
        self.materialx_version = self.options.get('materialx_version', '1.39')
        self.copy_textures = self.options.get('copy_textures', True)
        self.relative_paths = True  # Always use relative paths for this workflow
        self.strict_mode = options.get('strict_mode', True)  # Default to strict mode
        self.logger.info(f"Strict mode setting: {self.strict_mode}")
        
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
                
                # Check for unsupported nodes and record them
                node_types = []
                for node in self.material.node_tree.nodes:
                    node_types.append(node.type)
                    self.logger.error(f"    - {node.name}: {node.type}")
                    
                    # Check if this is an unsupported node type
                    if node.type in ['EMISSION', 'FRESNEL']:
                        self.unsupported_nodes.append({
                            "name": node.name,
                            "type": node.type
                        })
                
                # Provide specific guidance based on what nodes are present
                if 'EMISSION' in node_types:
                    self.logger.error("💡 Suggestion: Replace the Emission shader with a Principled BSDF node.")
                    self.logger.error("💡 Use 'Emission Color' and 'Emission Strength' inputs on the Principled BSDF instead.")
                elif 'BSDF_DIFFUSE' in node_types or 'BSDF_GLOSSY' in node_types or 'BSDF_GLASS' in node_types:
                    self.logger.error("💡 Suggestion: Replace individual BSDF shaders with a single Principled BSDF node.")
                    self.logger.error("💡 Principled BSDF combines all these effects in one node with better control.")
                else:
                    self.logger.error("💡 Suggestion: Add a Principled BSDF node to your material and connect it to the Material Output.")
                    self.logger.error("💡 The Principled BSDF is the standard shader for physically-based rendering in Blender.")
                
                # Check if we should continue despite unsupported nodes
                print(f"DEBUG: Checking strict mode: {self.strict_mode}")
                self.logger.info(f"Checking strict mode: {self.strict_mode}")
                if self.strict_mode:
                    print("DEBUG: Strict mode enabled - failing export")
                    self.logger.info("Strict mode enabled - failing export")
                    result["error"] = "No Principled BSDF node found"
                    result["unsupported_nodes"] = self.unsupported_nodes
                    return result
                else:
                    # Continue with a basic material export
                    print("DEBUG: Strict mode disabled - continuing export")
                    self.logger.warning("⚠ Continuing export despite unsupported nodes...")
                    return self._export_basic_material()
            
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
    
    def _export_basic_material(self) -> dict:
        """Export a basic material without nodes."""
        self.logger.info("Creating basic MaterialX document for unsupported material...")
        self.logger.info(f"Strict mode in _export_basic_material: {self.strict_mode}")
        
        self.builder = MaterialXBuilder(self.material.name, self.logger, self.materialx_version)
        self.builder.exporter = self
        
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
        
        # Return success result with unsupported nodes info
        result = {
            "success": True,
            "unsupported_nodes": self.unsupported_nodes,
            "output_path": str(self.output_path),
            "warning": "Material exported with basic surface due to unsupported nodes"
        }
        
        return result
    
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
        # MaterialX expects forward-slash paths. Build a relative path and
        # then normalise to POSIX style so it is portable across OSes.
        rel_path = os.path.relpath(self.texture_path / source_path.name, self.output_path.parent).replace(os.sep, '/')
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
    logger.info(f"Options type: {type(options)}")
    if options:
        logger.info(f"strict_mode in options: {options.get('strict_mode', 'NOT_FOUND')}")
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