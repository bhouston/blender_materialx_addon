#!/usr/bin/env python3
"""
Principled BSDF Mapper

This module provides mapping for Blender's Principled BSDF shader.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_mapper import BaseNodeMapper


class PrincipledBSDFMapper(BaseNodeMapper):
    """
    Mapper for Blender's Principled BSDF shader.
    
    This mapper converts Blender's Principled BSDF to MaterialX Standard Surface.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.supported_node_types = ['BSDF_PRINCIPLED']
        self.materialx_node_type = "standard_surface"
        self.materialx_category = "surfaceshader"
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """Check if this mapper can handle the given Blender node."""
        return blender_node.type in self.supported_node_types
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """Map a Blender Principled BSDF node to MaterialX Standard Surface."""
        materialx_node = self._create_materialx_node(
            document, blender_node.name, self.materialx_node_type, self.materialx_category
        )
        
        # Add inputs with default values
        self._add_input(materialx_node, 'base_color', 'color3', value=(0.8, 0.8, 0.8))
        self._add_input(materialx_node, 'base', 'float', value=1.0)
        self._add_input(materialx_node, 'diffuse_roughness', 'float', value=0.0)
        self._add_input(materialx_node, 'metalness', 'float', value=0.0)
        self._add_input(materialx_node, 'specular', 'float', value=1.0)
        self._add_input(materialx_node, 'specular_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'specular_roughness', 'float', value=0.2)
        self._add_input(materialx_node, 'specular_IOR', 'float', value=1.5)
        self._add_input(materialx_node, 'specular_anisotropy', 'float', value=0.0)
        self._add_input(materialx_node, 'specular_rotation', 'float', value=0.0)
        self._add_input(materialx_node, 'transmission', 'float', value=0.0)
        self._add_input(materialx_node, 'transmission_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'transmission_depth', 'float', value=0.0)
        self._add_input(materialx_node, 'transmission_scatter', 'color3', value=(0.0, 0.0, 0.0))
        self._add_input(materialx_node, 'transmission_scatter_anisotropy', 'float', value=0.0)
        self._add_input(materialx_node, 'transmission_dispersion', 'float', value=0.0)
        self._add_input(materialx_node, 'transmission_extra_roughness', 'float', value=0.0)
        self._add_input(materialx_node, 'subsurface', 'float', value=0.0)
        self._add_input(materialx_node, 'subsurface_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'subsurface_radius', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'subsurface_scale', 'float', value=1.0)
        self._add_input(materialx_node, 'subsurface_anisotropy', 'float', value=0.0)
        self._add_input(materialx_node, 'sheen', 'float', value=0.0)
        self._add_input(materialx_node, 'sheen_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'sheen_roughness', 'float', value=0.3)
        self._add_input(materialx_node, 'thin_walled', 'boolean', value=False)
        self._add_input(materialx_node, 'coat', 'float', value=0.0)
        self._add_input(materialx_node, 'coat_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'coat_roughness', 'float', value=0.1)
        self._add_input(materialx_node, 'coat_anisotropy', 'float', value=0.0)
        self._add_input(materialx_node, 'coat_rotation', 'float', value=0.0)
        self._add_input(materialx_node, 'coat_IOR', 'float', value=1.5)
        self._add_input(materialx_node, 'coat_affect_color', 'float', value=0.0)
        self._add_input(materialx_node, 'coat_affect_roughness', 'float', value=0.0)
        self._add_input(materialx_node, 'thin_film_thickness', 'float', value=0.0)
        self._add_input(materialx_node, 'thin_film_IOR', 'float', value=1.5)
        self._add_input(materialx_node, 'emission', 'float', value=0.0)
        self._add_input(materialx_node, 'emission_color', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'opacity', 'color3', value=(1.0, 1.0, 1.0))
        self._add_input(materialx_node, 'normal', 'vector3', value=(0.0, 0.0, 1.0))
        self._add_input(materialx_node, 'tangent', 'vector3', value=(1.0, 0.0, 0.0))
        
        # Connect inputs from Blender node if they have values
        self._connect_blender_inputs(blender_node, materialx_node, exported_nodes)
        
        return materialx_node
    
    def _connect_blender_inputs(self, blender_node: bpy.types.Node, materialx_node: Any, 
                               exported_nodes: Dict[str, str]) -> None:
        """Connect Blender node inputs to MaterialX node inputs."""
        input_mapping = self.get_input_mapping()
        
        for blender_input_name, materialx_input_name in input_mapping.items():
            if self._has_input(blender_node, blender_input_name):
                input_socket = blender_node.inputs[blender_input_name]
                
                # If input is connected, we'll handle it in the connection phase
                if input_socket.is_linked:
                    continue
                
                # If input has a value, set it
                if hasattr(input_socket, 'default_value'):
                    value = input_socket.default_value
                    if value is not None:
                        # Convert the value to the appropriate format
                        if isinstance(value, (list, tuple)):
                            # Handle color/vector values
                            if len(value) >= 3:
                                materialx_input = materialx_node.getInput(materialx_input_name)
                                if materialx_input:
                                    materialx_input.setValueString(", ".join(str(v) for v in value[:3]))
                        else:
                            # Handle scalar values
                            materialx_input = materialx_node.getInput(materialx_input_name)
                            if materialx_input:
                                materialx_input.setValueString(str(value))
    
    def get_input_mapping(self) -> Dict[str, str]:
        """Get input mapping for Principled BSDF."""
        return {
            'Base Color': 'base_color',
            'Base': 'base',
            'Roughness': 'specular_roughness',
            'Metallic': 'metalness',
            'Specular': 'specular',
            'Specular Tint': 'specular_color',
            'IOR': 'specular_IOR',
            'Anisotropic': 'specular_anisotropy',
            'Anisotropic Rotation': 'specular_rotation',
            'Transmission': 'transmission',
            'Transmission Color': 'transmission_color',
            'Transmission Depth': 'transmission_depth',
            'Subsurface': 'subsurface',
            'Subsurface Color': 'subsurface_color',
            'Subsurface Radius': 'subsurface_radius',
            'Subsurface Scale': 'subsurface_scale',
            'Subsurface Anisotropy': 'subsurface_anisotropy',
            'Sheen': 'sheen',
            'Sheen Color': 'sheen_color',
            'Sheen Roughness': 'sheen_roughness',
            'Thin Walled': 'thin_walled',
            'Coat': 'coat',
            'Coat Color': 'coat_color',
            'Coat Roughness': 'coat_roughness',
            'Coat Anisotropy': 'coat_anisotropy',
            'Coat Rotation': 'coat_rotation',
            'Coat IOR': 'coat_IOR',
            'Coat Affect Color': 'coat_affect_color',
            'Coat Affect Roughness': 'coat_affect_roughness',
            'Thin Film Thickness': 'thin_film_thickness',
            'Thin Film IOR': 'thin_film_IOR',
            'Emission': 'emission',
            'Emission Color': 'emission_color',
            'Alpha': 'opacity',
            'Normal': 'normal',
            'Tangent': 'tangent'
        }
    
    def get_output_mapping(self) -> Dict[str, str]:
        """Get output mapping for Principled BSDF."""
        return {
            'BSDF': 'out'
        }
    
    def get_default_values(self) -> Dict[str, Any]:
        """Get default values for Principled BSDF inputs."""
        return {
            'base_color': (0.8, 0.8, 0.8),
            'base': 1.0,
            'diffuse_roughness': 0.0,
            'metalness': 0.0,
            'specular': 1.0,
            'specular_color': (1.0, 1.0, 1.0),
            'specular_roughness': 0.2,
            'specular_IOR': 1.5,
            'specular_anisotropy': 0.0,
            'specular_rotation': 0.0,
            'transmission': 0.0,
            'transmission_color': (1.0, 1.0, 1.0),
            'transmission_depth': 0.0,
            'transmission_scatter': (0.0, 0.0, 0.0),
            'transmission_scatter_anisotropy': 0.0,
            'transmission_dispersion': 0.0,
            'transmission_extra_roughness': 0.0,
            'subsurface': 0.0,
            'subsurface_color': (1.0, 1.0, 1.0),
            'subsurface_radius': (1.0, 1.0, 1.0),
            'subsurface_scale': 1.0,
            'subsurface_anisotropy': 0.0,
            'sheen': 0.0,
            'sheen_color': (1.0, 1.0, 1.0),
            'sheen_roughness': 0.3,
            'thin_walled': False,
            'coat': 0.0,
            'coat_color': (1.0, 1.0, 1.0),
            'coat_roughness': 0.1,
            'coat_anisotropy': 0.0,
            'coat_rotation': 0.0,
            'coat_IOR': 1.5,
            'coat_affect_color': 0.0,
            'coat_affect_roughness': 0.0,
            'thin_film_thickness': 0.0,
            'thin_film_IOR': 1.5,
            'emission': 0.0,
            'emission_color': (1.0, 1.0, 1.0),
            'opacity': (1.0, 1.0, 1.0),
            'normal': (0.0, 0.0, 1.0),
            'tangent': (1.0, 0.0, 0.0)
        }
