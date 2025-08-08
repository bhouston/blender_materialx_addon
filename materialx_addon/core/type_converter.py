#!/usr/bin/env python3
"""
MaterialX Type Converter

This module provides type conversion utilities for converting between
Blender types and MaterialX types.
"""

from typing import Dict, List, Optional, Any, Union
import bpy
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import TypeConversionError


class TypeConverter:
    """
    Converter for handling type conversions between Blender and MaterialX.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the type converter.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger("TypeConverter")
        
        # Type mapping from Blender socket types to MaterialX types
        self.blender_to_materialx_types = {
            'RGBA': 'color4',
            'RGB': 'color3',
            'VECTOR': 'vector3',
            'VALUE': 'float',
            'INT': 'integer',
            'BOOLEAN': 'boolean',
            'STRING': 'string',
            'SHADER': 'surface',
            'CUSTOM': 'float'  # Default for custom types
        }
        
        # Type mapping from MaterialX types to Blender socket types
        self.materialx_to_blender_types = {
            'color4': 'RGBA',
            'color3': 'RGB',
            'vector3': 'VECTOR',
            'vector2': 'VECTOR',
            'float': 'VALUE',
            'integer': 'INT',
            'boolean': 'BOOLEAN',
            'string': 'STRING',
            'surface': 'SHADER',
            'filename': 'STRING'
        }
    
    def blender_socket_to_materialx_type(self, socket_type: str) -> str:
        """
        Convert a Blender socket type to MaterialX type.
        
        Args:
            socket_type: Blender socket type string
            
        Returns:
            MaterialX type string
        """
        return self.blender_to_materialx_types.get(socket_type, 'float')
    
    def materialx_type_to_blender_socket(self, materialx_type: str) -> str:
        """
        Convert a MaterialX type to Blender socket type.
        
        Args:
            materialx_type: MaterialX type string
            
        Returns:
            Blender socket type string
        """
        return self.materialx_to_blender_types.get(materialx_type, 'VALUE')
    
    def convert_value(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the specified MaterialX type.
        
        Args:
            value: The value to convert
            target_type: Target MaterialX type
            
        Returns:
            Converted value
            
        Raises:
            TypeConversionError: If conversion fails
        """
        try:
            if target_type == 'color3':
                return self._convert_to_color3(value)
            elif target_type == 'color4':
                return self._convert_to_color4(value)
            elif target_type == 'vector3':
                return self._convert_to_vector3(value)
            elif target_type == 'vector2':
                return self._convert_to_vector2(value)
            elif target_type == 'float':
                return self._convert_to_float(value)
            elif target_type == 'integer':
                return self._convert_to_integer(value)
            elif target_type == 'boolean':
                return self._convert_to_boolean(value)
            elif target_type == 'string':
                return self._convert_to_string(value)
            else:
                self.logger.warning(f"Unknown target type: {target_type}, using float")
                return self._convert_to_float(value)
                
        except Exception as e:
            raise TypeConversionError(value, target_type, e)
    
    def _convert_to_color3(self, value: Any) -> List[float]:
        """Convert value to color3 (3-component color)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 3:
                return [float(value[0]), float(value[1]), float(value[2])]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0])]
        elif isinstance(value, (int, float)):
            v = float(value)
            return [v, v, v]
        elif hasattr(value, 'r') and hasattr(value, 'g') and hasattr(value, 'b'):
            return [float(value.r), float(value.g), float(value.b)]
        
        # Default to white
        return [1.0, 1.0, 1.0]
    
    def _convert_to_color4(self, value: Any) -> List[float]:
        """Convert value to color4 (4-component color with alpha)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 4:
                return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
            elif len(value) == 3:
                return [float(value[0]), float(value[1]), float(value[2]), 1.0]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0]), 1.0]
        elif isinstance(value, (int, float)):
            v = float(value)
            return [v, v, v, 1.0]
        elif hasattr(value, 'r') and hasattr(value, 'g') and hasattr(value, 'b'):
            alpha = getattr(value, 'a', 1.0)
            return [float(value.r), float(value.g), float(value.b), float(alpha)]
        
        # Default to white with full alpha
        return [1.0, 1.0, 1.0, 1.0]
    
    def _convert_to_vector3(self, value: Any) -> List[float]:
        """Convert value to vector3 (3-component vector)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 3:
                return [float(value[0]), float(value[1]), float(value[2])]
            elif len(value) == 2:
                return [float(value[0]), float(value[1]), 0.0]
            elif len(value) == 1:
                return [float(value[0]), 0.0, 0.0]
        elif isinstance(value, (int, float)):
            v = float(value)
            return [v, v, v]
        elif hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            return [float(value.x), float(value.y), float(value.z)]
        
        # Default to zero vector
        return [0.0, 0.0, 0.0]
    
    def _convert_to_vector2(self, value: Any) -> List[float]:
        """Convert value to vector2 (2-component vector)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 2:
                return [float(value[0]), float(value[1])]
            elif len(value) == 1:
                return [float(value[0]), 0.0]
        elif isinstance(value, (int, float)):
            v = float(value)
            return [v, v]
        elif hasattr(value, 'x') and hasattr(value, 'y'):
            return [float(value.x), float(value.y)]
        
        # Default to zero vector
        return [0.0, 0.0]
    
    def _convert_to_float(self, value: Any) -> float:
        """Convert value to float."""
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                return float(value[0])
            else:
                return 0.0
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _convert_to_integer(self, value: Any) -> int:
        """Convert value to integer."""
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                return int(value[0])
            else:
                return 0
        elif isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return 0
        
        return 0
    
    def _convert_to_boolean(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(value, (list, tuple)):
            return len(value) > 0 and any(self._convert_to_boolean(v) for v in value)
        
        return False
    
    def _convert_to_string(self, value: Any) -> str:
        """Convert value to string."""
        if isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        else:
            return str(value)
    
    def format_value_for_materialx(self, value: Any, materialx_type: str) -> str:
        """
        Format a value as a string for MaterialX.
        
        Args:
            value: The value to format
            materialx_type: MaterialX type
            
        Returns:
            Formatted string value
        """
        try:
            converted_value = self.convert_value(value, materialx_type)
            
            if materialx_type in ['color3', 'color4', 'vector2', 'vector3']:
                return " ".join(str(v) for v in converted_value)
            else:
                return str(converted_value)
                
        except Exception as e:
            self.logger.error(f"Failed to format value {value} for type {materialx_type}: {e}")
            return "0"
    
    def get_socket_type(self, blender_socket: bpy.types.NodeSocket) -> str:
        """
        Get the MaterialX type for a Blender socket.
        
        Args:
            blender_socket: Blender node socket
            
        Returns:
            MaterialX type string
        """
        socket_type = str(blender_socket.type)
        return self.blender_socket_to_materialx_type(socket_type)
    
    def validate_type_compatibility(self, source_type: str, target_type: str) -> bool:
        """
        Validate if two types are compatible for connection.
        
        Args:
            source_type: Source MaterialX type
            target_type: Target MaterialX type
            
        Returns:
            True if types are compatible, False otherwise
        """
        # Direct match
        if source_type == target_type:
            return True
        
        # Special compatibility rules
        compatibility_rules = {
            'color3': ['color4', 'vector3'],
            'color4': ['color3'],
            'vector3': ['color3', 'vector2'],
            'vector2': ['vector3'],
            'float': ['integer'],
            'integer': ['float']
        }
        
        # Check if source type can be converted to target type
        if source_type in compatibility_rules:
            return target_type in compatibility_rules[source_type]
        
        return False
    
    def get_default_value(self, materialx_type: str) -> Any:
        """
        Get the default value for a MaterialX type.
        
        Args:
            materialx_type: MaterialX type
            
        Returns:
            Default value for the type
        """
        defaults = {
            'color3': [0.0, 0.0, 0.0],
            'color4': [0.0, 0.0, 0.0, 1.0],
            'vector2': [0.0, 0.0],
            'vector3': [0.0, 0.0, 0.0],
            'float': 0.0,
            'integer': 0,
            'boolean': False,
            'string': '',
            'surface': None,
            'filename': ''
        }
        
        return defaults.get(materialx_type, 0.0)
