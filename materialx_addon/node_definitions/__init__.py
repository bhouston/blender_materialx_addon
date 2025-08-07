#!/usr/bin/env python3
"""
Node Definitions Package

This package contains node definition modules for the MaterialX addon.
"""

from .custom_node_definitions import CustomNodeDefinitionManager, get_custom_node_type, is_custom_node_type
from .type_conversions import TYPE_CONVERSION_CONFIGS
from .texture_definitions import TextureDefinitionManager

__all__ = [
    'CustomNodeDefinitionManager',
    'get_custom_node_type', 
    'is_custom_node_type',
    'TYPE_CONVERSION_CONFIGS',
    'TextureDefinitionManager'
]
