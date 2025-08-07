#!/usr/bin/env python3
"""
Type Conversion Definitions

This module contains configurations for MaterialX type conversion nodes.
"""

from typing import Dict, Any

# Configuration for type conversion definitions
TYPE_CONVERSION_CONFIGS: Dict[str, Dict[str, Any]] = {
    "convert_vector3_to_vector2": {
        "input_type": "vector3",
        "output_type": "vector2",
        "description": "Convert vector3 to vector2 by extracting X,Y components",
        "input_description": "Input vector3",
        "output_description": "Output vector2 (X,Y components)",
        "implementation": {
            "separate_node": {"type": "separate3", "name": "separate_input"},
            "combine_node": {"type": "combine2", "name": "combine_xy"},
            "combine_inputs": ["outx", "outy"]
        }
    },
    "convert_vector2_to_vector3": {
        "input_type": "vector2",
        "output_type": "vector3",
        "description": "Convert vector2 to vector3 by adding Z=0",
        "input_description": "Input vector2",
        "output_description": "Output vector3 (X,Y,0)",
        "implementation": {
            "separate_node": {"type": "separate2", "name": "separate_input"},
            "combine_node": {"type": "combine3", "name": "combine_xyz"},
            "combine_inputs": ["outx", "outy", "0"]
        }
    },
    "convert_color3_to_vector2": {
        "input_type": "color3",
        "output_type": "vector2",
        "description": "Convert color3 to vector2 by extracting R,G components",
        "input_description": "Input color3",
        "output_description": "Output vector2 (R,G components)",
        "implementation": {
            "separate_node": {"type": "separate3", "name": "separate_input"},
            "combine_node": {"type": "combine2", "name": "combine_rg"},
            "combine_inputs": ["outx", "outy"]
        }
    },
    "convert_vector4_to_vector3": {
        "input_type": "vector4",
        "output_type": "vector3",
        "description": "Convert vector4 to vector3 by extracting X,Y,Z components",
        "input_description": "Input vector4",
        "output_description": "Output vector3 (X,Y,Z components)",
        "implementation": {
            "separate_node": {"type": "separate4", "name": "separate_input"},
            "combine_node": {"type": "combine3", "name": "combine_xyz"},
            "combine_inputs": ["outx", "outy", "outz"]
        }
    },
    "convert_vector3_to_vector4": {
        "input_type": "vector3",
        "output_type": "vector4",
        "description": "Convert vector3 to vector4 by adding W=1",
        "input_description": "Input vector3",
        "output_description": "Output vector4 (X,Y,Z,1)",
        "implementation": {
            "separate_node": {"type": "separate3", "name": "separate_input"},
            "combine_node": {"type": "combine4", "name": "combine_xyzw"},
            "combine_inputs": ["outx", "outy", "outz", "1"]
        }
    },
    "convert_color4_to_color3": {
        "input_type": "color4",
        "output_type": "color3",
        "description": "Convert color4 to color3 by extracting R,G,B components",
        "input_description": "Input color4",
        "output_description": "Output color3 (R,G,B components)",
        "implementation": {
            "separate_node": {"type": "separate4", "name": "separate_input"},
            "combine_node": {"type": "combine3", "name": "combine_rgb"},
            "combine_inputs": ["outx", "outy", "outz"]
        }
    },
    "convert_color3_to_color4": {
        "input_type": "color3",
        "output_type": "color4",
        "description": "Convert color3 to color4 by adding A=1",
        "input_description": "Input color3",
        "output_description": "Output color4 (R,G,B,1)",
        "implementation": {
            "separate_node": {"type": "separate3", "name": "separate_input"},
            "combine_node": {"type": "combine4", "name": "combine_rgba"},
            "combine_inputs": ["outx", "outy", "outz", "1"]
        }
    }
}
