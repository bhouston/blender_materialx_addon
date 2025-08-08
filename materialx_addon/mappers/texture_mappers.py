#!/usr/bin/env python3
"""
Texture Node Mappers

This module provides mappers for texture nodes like image textures and procedural textures.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_mapper import BaseNodeMapper


class TextureMapper(BaseNodeMapper):
    """
    Base mapper for texture nodes.
    
    This class provides common functionality for texture node mapping.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = []
        self.materialx_node_type = "image"
        self.materialx_category = "texture2d"
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """Check if this mapper can handle the given Blender node."""
        return blender_node.type in self.supported_node_types
    
    def _add_texture_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add common texture inputs."""
        # Add texture coordinate input
        self._add_input(materialx_node, 'texcoord', 'vector2')
        
        # Add common texture parameters
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'scale', 'vector2', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Offset'):
            self._add_input(materialx_node, 'offset', 'vector2', self._get_input_value(blender_node, 'Offset'))
        
        if self._has_input(blender_node, 'Rotation'):
            self._add_input(materialx_node, 'rotation', 'float', self._get_input_value(blender_node, 'Rotation'))


class ImageTextureMapper(TextureMapper):
    """
    Mapper for Blender's Image Texture node.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = ['TEX_IMAGE']
        self.materialx_node_type = "image"
        self.materialx_category = "texture2d"
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """Map a Blender Image Texture node to MaterialX."""
        
        materialx_node = self._create_materialx_node(
            document, blender_node.name, self.materialx_node_type, self.materialx_category
        )
        
        # Add texture inputs
        self._add_texture_inputs(materialx_node, blender_node)
        
        # Add image file input if available
        if hasattr(blender_node, 'image') and blender_node.image:
            image_path = blender_node.image.filepath
            if image_path:
                # Set the file path
                materialx_node.setInputValue('file', image_path)
        
        # Add color space input
        if self._has_input(blender_node, 'Color Space'):
            color_space = self._get_input_value(blender_node, 'Color Space')
            if color_space:
                materialx_node.setInputValue('colorspace', color_space)
        
        # Add outputs
        self._add_output(materialx_node, 'out', 'color3')
        
        return materialx_node
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for Image Texture."""
        return {
            'Vector': 'texcoord',
            'Scale': 'scale',
            'Offset': 'offset',
            'Rotation': 'rotation',
            'Color Space': 'colorspace'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for Image Texture."""
        return {
            'Color': 'out',
            'Alpha': 'out'
        }


class ProceduralTextureMapper(TextureMapper):
    """
    Mapper for Blender's procedural texture nodes.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = [
            'TEX_NOISE', 'TEX_VORONOI', 'TEX_WAVE', 'TEX_MUSGRAVE',
            'TEX_BRICK', 'TEX_GRADIENT', 'CHECKER_TEXTURE', 'TEX_CHECKER'
        ]
        self.materialx_node_type = "noise2d"  # Default, will be overridden
        self.materialx_category = "texture2d"
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """Map a Blender procedural texture node to MaterialX."""
        
        # Determine MaterialX node type based on Blender node type
        materialx_type = self._get_materialx_type(blender_node.type)
        
        materialx_node = self._create_materialx_node(
            document, blender_node.name, materialx_type, self.materialx_category
        )
        
        # Add texture inputs
        self._add_texture_inputs(materialx_node, blender_node)
        
        # Add specific inputs based on node type
        if blender_node.type == 'TEX_NOISE':
            self._add_noise_inputs(materialx_node, blender_node)
        elif blender_node.type == 'TEX_VORONOI':
            self._add_voronoi_inputs(materialx_node, blender_node)
        elif blender_node.type == 'TEX_WAVE':
            self._add_wave_inputs(materialx_node, blender_node)
        elif blender_node.type == 'TEX_MUSGRAVE':
            self._add_musgrave_inputs(materialx_node, blender_node)
        elif blender_node.type == 'TEX_BRICK':
            self._add_brick_inputs(materialx_node, blender_node)
        elif blender_node.type == 'TEX_GRADIENT':
            self._add_gradient_inputs(materialx_node, blender_node)
        elif blender_node.type in ['CHECKER_TEXTURE', 'TEX_CHECKER']:
            self._add_checker_inputs(materialx_node, blender_node)
        
        # Add outputs
        self._add_output(materialx_node, 'out', 'color3')
        
        return materialx_node
    
    def _get_materialx_type(self, blender_node_type: str) -> str:
        """Get the MaterialX node type for a Blender procedural texture."""
        type_mapping = {
            'TEX_NOISE': 'noise2d',
            'TEX_VORONOI': 'voronoi2d',
            'TEX_WAVE': 'wave2d',
            'TEX_MUSGRAVE': 'musgrave2d',
            'TEX_BRICK': 'brick2d',
            'TEX_GRADIENT': 'ramp2d',
            'CHECKER_TEXTURE': 'checker2d',
            'TEX_CHECKER': 'checker2d'
        }
        return type_mapping.get(blender_node_type, 'noise2d')
    
    def _add_noise_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for noise texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'amplitude', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Detail'):
            self._add_input(materialx_node, 'octaves', 'integer', self._get_input_value(blender_node, 'Detail'))
        
        if self._has_input(blender_node, 'Roughness'):
            self._add_input(materialx_node, 'roughness', 'float', self._get_input_value(blender_node, 'Roughness'))
    
    def _add_voronoi_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for Voronoi texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'scale', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Feature'):
            feature = self._get_input_value(blender_node, 'Feature')
            if feature:
                materialx_node.setInputValue('feature', feature)
    
    def _add_wave_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for wave texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'frequency', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Distortion'):
            self._add_input(materialx_node, 'distortion', 'float', self._get_input_value(blender_node, 'Distortion'))
        
        if self._has_input(blender_node, 'Detail'):
            self._add_input(materialx_node, 'detail', 'float', self._get_input_value(blender_node, 'Detail'))
    
    def _add_musgrave_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for Musgrave texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'scale', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Detail'):
            self._add_input(materialx_node, 'octaves', 'integer', self._get_input_value(blender_node, 'Detail'))
        
        if self._has_input(blender_node, 'Dimension'):
            self._add_input(materialx_node, 'dimension', 'float', self._get_input_value(blender_node, 'Dimension'))
    
    def _add_brick_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for brick texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'scale', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Mortar Size'):
            self._add_input(materialx_node, 'mortar', 'float', self._get_input_value(blender_node, 'Mortar Size'))
        
        if self._has_input(blender_node, 'Mortar Smooth'):
            self._add_input(materialx_node, 'smooth', 'float', self._get_input_value(blender_node, 'Mortar Smooth'))
    
    def _add_gradient_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for gradient texture."""
        if self._has_input(blender_node, 'Gradient Type'):
            gradient_type = self._get_input_value(blender_node, 'Gradient Type')
            if gradient_type:
                materialx_node.setInputValue('type', gradient_type)
    
    def _add_checker_inputs(self, materialx_node: mx.Node, blender_node: bpy.types.Node):
        """Add inputs for checker texture."""
        if self._has_input(blender_node, 'Scale'):
            self._add_input(materialx_node, 'scale', 'float', self._get_input_value(blender_node, 'Scale'))
        
        if self._has_input(blender_node, 'Color1'):
            self._add_input(materialx_node, 'color1', 'color3', self._get_input_value(blender_node, 'Color1'))
        
        if self._has_input(blender_node, 'Color2'):
            self._add_input(materialx_node, 'color2', 'color3', self._get_input_value(blender_node, 'Color2'))
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for procedural textures."""
        return {
            'Vector': 'texcoord',
            'Scale': 'scale',
            'Offset': 'offset',
            'Rotation': 'rotation',
            'Detail': 'octaves',
            'Roughness': 'roughness',
            'Distortion': 'distortion',
            'Dimension': 'dimension',
            'Mortar Size': 'mortar',
            'Mortar Smooth': 'smooth',
            'Gradient Type': 'type',
            'Color1': 'color1',
            'Color2': 'color2'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for procedural textures."""
        return {
            'Color': 'out',
            'Fac': 'out'
        }
