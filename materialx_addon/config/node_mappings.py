#!/usr/bin/env python3
"""
MaterialX Addon Node Mappings Configuration

This module contains the mapping configuration between Blender node types
and MaterialX node types, including input/output mappings.
"""

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
            'Vector': 'texcoord',
            'Scale': 'frequency',
            'Distortion': 'distortion',
            'Detail': 'octaves',
            'Detail Scale': 'detail_frequency',
            'Detail Roughness': 'detail_amplitude',
        },
        'outputs': {
            'Fac': 'out',
            'Color': 'out',
        }
    },
    'TEX_MUSGRAVE': {
        'mtlx_type': 'musgrave',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'position',
            'Scale': 'lacunarity',
            'Detail': 'octaves',
            'Dimension': 'dimension',
        },
        'outputs': {
            'Fac': 'out',
            'Color': 'out',
        }
    },
    'TEX_BRICK': {
        'mtlx_type': 'brick',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
            'Color1': 'in1',
            'Color2': 'in2',
            'Mortar': 'mortar',
            'Scale': 'scale',
            'Mortar Size': 'mortar_thickness',
            'Mortar Smooth': 'mortar_smooth',
            'Bias': 'bias',
            'Brick Width': 'brick_width',
            'Row Height': 'row_height',
        },
        'outputs': {
            'Color': 'out',
            'Fac': 'out',
        }
    },
    'TEX_GRADIENT': {
        'mtlx_type': 'ramplr',
        'mtlx_category': 'color3',
        'inputs': {
            'Vector': 'texcoord',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'MATH': {
        'mtlx_type': 'math',
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
        'mtlx_type': 'vector_math',
        'mtlx_category': 'vector3',
        'inputs': {
            'A': 'in1',
            'B': 'in2',
        },
        'outputs': {
            'Vector': 'out',
        }
    },
    'NORMAL_MAP': {
        'mtlx_type': 'normalmap',
        'mtlx_category': 'vector3',
        'inputs': {
            'Color': 'in',
            'Strength': 'scale',
        },
        'outputs': {
            'Normal': 'out',
        }
    },
    'BUMP': {
        'mtlx_type': 'bump',
        'mtlx_category': 'vector3',
        'inputs': {
            'Height': 'in',
            'Strength': 'scale',
            'Distance': 'distance',
            'Normal': 'normal',
        },
        'outputs': {
            'Normal': 'out',
        }
    },
    'MAPPING': {
        'mtlx_type': 'place2d',
        'mtlx_category': 'vector2',
        'inputs': {
            'Vector': 'texcoord',
            'Location': 'offset',
            'Rotation': 'rotation',
            'Scale': 'scale',
        },
        'outputs': {
            'Vector': 'out',
        }
    },
    'LAYER_WEIGHT': {
        'mtlx_type': 'layer',
        'mtlx_category': 'float',
        'inputs': {
            'Blend': 'blend',
            'Normal': 'normal',
        },
        'outputs': {
            'Fresnel': 'out',
            'Facing': 'out',
        }
    },
    'ADD_SHADER': {
        'mtlx_type': 'add',
        'mtlx_category': 'surface',
        'inputs': {
            'A': 'in1',
            'B': 'in2',
        },
        'outputs': {
            'Shader': 'out',
        }
    },
    'MULTIPLY_SHADER': {
        'mtlx_type': 'multiply',
        'mtlx_category': 'surface',
        'inputs': {
            'A': 'in1',
            'B': 'in2',
        },
        'outputs': {
            'Shader': 'out',
        }
    },
    'CURVE_RGB': {
        'mtlx_type': 'ramplr',
        'mtlx_category': 'color3',
        'inputs': {
            'Fac': 'in',
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
        'mtlx_type': 'remap',
        'mtlx_category': 'float',
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
    'GEOMETRY': {
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
            'Rotation': 'out',
            'Scale': 'out',
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
    'HSV_TO_RGB': {
        'mtlx_type': 'hsvtorgb',
        'mtlx_category': 'color3',
        'inputs': {
            'H': 'h',
            'S': 's',
            'V': 'v',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'RGB_TO_HSV': {
        'mtlx_type': 'rgbtohsv',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
        },
        'outputs': {
            'H': 'h',
            'S': 's',
            'V': 'v',
        }
    },
    'LUMINANCE': {
        'mtlx_type': 'luminance',
        'mtlx_category': 'float',
        'inputs': {
            'Color': 'in',
        },
        'outputs': {
            'Value': 'out',
        }
    },
    'CONTRAST': {
        'mtlx_type': 'contrast',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
            'Contrast': 'contrast',
            'Brightness': 'brightness',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'SATURATE': {
        'mtlx_type': 'saturate',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
            'Factor': 'factor',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'GAMMA': {
        'mtlx_type': 'gamma',
        'mtlx_category': 'color3',
        'inputs': {
            'Color': 'in',
            'Gamma': 'gamma',
        },
        'outputs': {
            'Color': 'out',
        }
    },
    'SEPARATE_XYZ': {
        'mtlx_type': 'separate3',
        'mtlx_category': 'vector3',
        'inputs': {
            'Vector': 'in',
        },
        'outputs': {
            'X': 'outr',
            'Y': 'outg',
            'Z': 'outb',
        }
    },
    'COMBINE_XYZ': {
        'mtlx_type': 'combine3',
        'mtlx_category': 'vector3',
        'inputs': {
            'X': 'r',
            'Y': 'g',
            'Z': 'b',
        },
        'outputs': {
            'Vector': 'out',
        }
    },
    'ROUGHNESS_ANISOTROPY': {
        'mtlx_type': 'roughness_anisotropy',
        'mtlx_category': 'float',
        'inputs': {
            'Roughness': 'roughness',
            'Anisotropy': 'anisotropy',
        },
        'outputs': {
            'Roughness X': 'outr',
            'Roughness Y': 'outg',
        }
    },
    'ARTISTIC_IOR': {
        'mtlx_type': 'artistic_ior',
        'mtlx_category': 'float',
        'inputs': {
            'IOR': 'ior',
            'Extinction': 'extinction',
        },
        'outputs': {
            'IOR': 'out',
            'Extinction': 'out',
        }
    }
}

# Node type categories for organization
NODE_CATEGORIES = {
    'SURFACE': ['BSDF_PRINCIPLED'],
    'TEXTURE': ['TEX_COORD', 'TEX_IMAGE', 'TEX_NOISE', 'TEX_VORONOI', 'TEX_WAVE', 
                'TEX_MUSGRAVE', 'TEX_BRICK', 'TEX_GRADIENT', 'CHECKER_TEXTURE'],
    'MATH': ['MATH', 'VECTOR_MATH', 'MIX', 'MIX_RGB'],
    'UTILITY': ['INVERT', 'SEPARATE_COLOR', 'COMBINE_COLOR', 'NORMAL_MAP', 'BUMP',
                'MAPPING', 'LAYER_WEIGHT', 'CURVE_RGB', 'CLAMP', 'MAP_RANGE'],
    'COLOR': ['RGB', 'VALUE', 'HSV_TO_RGB', 'RGB_TO_HSV', 'LUMINANCE', 'CONTRAST',
              'SATURATE', 'GAMMA'],
    'GEOMETRY': ['GEOMETRY', 'OBJECT_INFO', 'LIGHT_PATH'],
    'VECTOR': ['SEPARATE_XYZ', 'COMBINE_XYZ'],
    'SPECIAL': ['ROUGHNESS_ANISOTROPY', 'ARTISTIC_IOR', 'ADD_SHADER', 'MULTIPLY_SHADER']
}

# Unsupported node types (for error reporting)
UNSUPPORTED_NODE_TYPES = [
    'EMISSION',
    'FRESNEL',
    'BSDF_DIFFUSE',
    'BSDF_GLOSSY',
    'BSDF_GLASS',
    'BSDF_TRANSPARENT',
    'BSDF_TRANSLUCENT',
    'BSDF_VELVET',
    'BSDF_TOON',
    'BSDF_HAIR',
    'BSDF_ANISOTROPIC',
    'BSDF_HAIR_PRINCIPLED',
    'BSDF_PRINCIPLED_VOLUME',
    'VOLUME_ABSORPTION',
    'VOLUME_SCATTER',
    'VOLUME_PRINCIPLED',
    'AMBIENT_OCCLUSION',
    'BEVEL',
    'DISPLACEMENT',
    'VECTOR_DISPLACEMENT',
    'SUBSURFACE_SCATTERING',
    'HOLDOUT',
    'VOLUME_INFO',
    'PARTICLE_INFO',
    'HAIR_INFO',
    'POINT_INFO',
    'VERTEX_COLOR',
    'UV_MAP',
    'TEX_ENVIRONMENT',
    'TEX_SKY',
    'TEX_IES',
    'TEX_POINT_DENSITY',
    'TEX_VOXEL_DATA',
    'TEX_WHITE_NOISE',
    'TEX_COLOR_RAMP',
    'TEX_MAGIC',
    'TEX_MARBLE',
    'TEX_WOOD',
    'TEX_STUCCI',
    'TEX_DISTANCE',
    'TEX_COORD',
    'TEX_MAPPING',
    'TEX_COMBINE',
    'TEX_SEPARATE',
    'TEX_MATH',
    'TEX_VECTOR_MATH',
    'TEX_ROTATE',
    'TEX_TRANSLATE',
    'TEX_SCALE',
    'TEX_VECTOR_ROTATE',
    'TEX_VECTOR_TRANSLATE',
    'TEX_VECTOR_SCALE',
    'TEX_VECTOR_CURVES',
    'TEX_RGB_CURVES',
    'TEX_HUE_SATURATION',
    'TEX_BRIGHT_CONTRAST',
    'TEX_GAMMA',
    'TEX_INVERT',
    'TEX_LIGHT_FALLOFF',
    'TEX_OBJECT_INFO',
    'TEX_PARTICLE_INFO',
    'TEX_HAIR_INFO',
    'TEX_POINT_INFO',
    'TEX_VERTEX_COLOR',
    'TEX_UV_MAP',
    'TEX_ENVIRONMENT',
    'TEX_SKY',
    'TEX_IES',
    'TEX_POINT_DENSITY',
    'TEX_VOXEL_DATA',
    'TEX_WHITE_NOISE',
    'TEX_COLOR_RAMP',
    'TEX_MAGIC',
    'TEX_MARBLE',
    'TEX_WOOD',
    'TEX_STUCCI',
    'TEX_DISTANCE',
    'TEX_COORD',
    'TEX_MAPPING',
    'TEX_COMBINE',
    'TEX_SEPARATE',
    'TEX_MATH',
    'TEX_VECTOR_MATH',
    'TEX_ROTATE',
    'TEX_TRANSLATE',
    'TEX_SCALE',
    'TEX_VECTOR_ROTATE',
    'TEX_VECTOR_TRANSLATE',
    'TEX_VECTOR_SCALE',
    'TEX_VECTOR_CURVES',
    'TEX_RGB_CURVES',
    'TEX_HUE_SATURATION',
    'TEX_BRIGHT_CONTRAST',
    'TEX_GAMMA',
    'TEX_INVERT',
    'TEX_LIGHT_FALLOFF',
    'TEX_OBJECT_INFO',
    'TEX_PARTICLE_INFO',
    'TEX_HAIR_INFO',
    'TEX_POINT_INFO',
    'TEX_VERTEX_COLOR',
    'TEX_UV_MAP'
]

def get_node_category(node_type: str) -> str:
    """
    Get the category for a node type.
    
    Args:
        node_type: The Blender node type
        
    Returns:
        The category name, or 'UNKNOWN' if not found
    """
    for category, node_types in NODE_CATEGORIES.items():
        if node_type in node_types:
            return category
    return 'UNKNOWN'

def is_node_supported(node_type: str) -> bool:
    """
    Check if a node type is supported.
    
    Args:
        node_type: The Blender node type
        
    Returns:
        True if supported, False otherwise
    """
    return node_type in NODE_MAPPING

def get_supported_node_types() -> list:
    """
    Get a list of all supported node types.
    
    Returns:
        List of supported node type strings
    """
    return list(NODE_MAPPING.keys())

def get_unsupported_node_types() -> list:
    """
    Get a list of all unsupported node types.
    
    Returns:
        List of unsupported node type strings
    """
    return UNSUPPORTED_NODE_TYPES.copy()
