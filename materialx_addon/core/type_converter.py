#!/usr/bin/env python3
"""
MaterialX Type Converter

This module provides type conversion functionality for MaterialX.
"""

import logging
from typing import Dict, List, Optional, Any


class MaterialXTypeConverter:
    """
    Handles type conversion and validation for MaterialX inputs and outputs.
    
    This class provides:
    - Automatic type conversion between Blender and MaterialX types
    - Type validation and compatibility checking
    - Value formatting for different MaterialX types
    """
    
    def __init__(self, logger):
        self.logger = logger
        
        # Type compatibility mapping
        self.type_compatibility = {
            'color3': ['color3', 'vector3', 'vector2'],  # color3 can convert to vector2 (extract first two components)
            'vector3': ['vector3', 'color3'],
            'vector2': ['vector2', 'vector3'],  # vector2 can convert to vector3 (add Z=0)
            'vector4': ['vector4', 'color4'],
            'color4': ['color4', 'vector4'],
            'float': ['float'],
            'filename': ['filename'],
            'string': ['string'],
            'integer': ['integer'],
            'boolean': ['boolean']
        }
        
        # Blender to MaterialX type mapping
        self.blender_to_mtlx_types = {
            'RGBA': 'color4',
            'RGB': 'color3',
            'VECTOR': 'vector3',
            'VECTOR_2D': 'vector2',
            'VALUE': 'float',
            'INT': 'integer',
            'BOOLEAN': 'boolean',
            'STRING': 'string'
        }
    
    def convert_blender_type(self, blender_type: str) -> str:
        """
        Convert a Blender socket type to MaterialX type.
        
        Args:
            blender_type: The Blender socket type
            
        Returns:
            str: The corresponding MaterialX type
        """
        return self.blender_to_mtlx_types.get(blender_type, 'color3')
    
    def validate_type_compatibility(self, from_type: str, to_type: str) -> bool:
        """
        Validate if a type conversion is compatible.
        
        Args:
            from_type: The source type
            to_type: The target type
            
        Returns:
            bool: True if conversion is compatible
        """
        # Direct match
        if from_type == to_type:
            return True
        
        # Check compatibility mapping
        if from_type in self.type_compatibility:
            compatible_types = self.type_compatibility[from_type]
            if to_type in compatible_types:
                return True
        
        # Special cases for specific conversions mentioned in corrections plan
        if from_type == 'vector2' and to_type == 'vector3':
            return True  # texcoord -> fractal3d position
        if from_type == 'color3' and to_type == 'vector2':
            return True  # mix -> ramp texcoord
        if from_type == 'color3' and to_type == 'vector3':
            return True  # mix -> normalmap default
        
        # Legacy special cases
        if from_type == 'color3' and to_type == 'vector3':
            return True
        if from_type == 'vector3' and to_type == 'color3':
            return True
        if from_type == 'color4' and to_type == 'vector4':
            return True
        if from_type == 'vector4' and to_type == 'color4':
            return True
        
        self.logger.warning(f"Type incompatibility: {from_type} -> {to_type}")
        return False
    
    def convert_value(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the target MaterialX type.
        
        Args:
            value: The value to convert
            target_type: The target MaterialX type
            
        Returns:
            Any: The converted value
        """
        if value is None:
            return None
        
        try:
            if target_type == 'color3':
                return self._convert_to_color3(value)
            elif target_type == 'color4':
                return self._convert_to_color4(value)
            elif target_type == 'vector2':
                return self._convert_to_vector2(value)
            elif target_type == 'vector3':
                return self._convert_to_vector3(value)
            elif target_type == 'vector4':
                return self._convert_to_vector4(value)
            elif target_type == 'float':
                return self._convert_to_float(value)
            elif target_type == 'integer':
                return self._convert_to_integer(value)
            elif target_type == 'boolean':
                return self._convert_to_boolean(value)
            elif target_type == 'string':
                return str(value)
            elif target_type == 'filename':
                return str(value)
            else:
                self.logger.warning(f"Unknown target type: {target_type}")
                return value
                
        except Exception as e:
            self.logger.error(f"Error converting value {value} to {target_type}: {str(e)}")
            return value
    
    def _convert_to_color3(self, value) -> List[float]:
        """Convert value to color3 (3-component color)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 3:
                return [float(value[0]), float(value[1]), float(value[2])]
            elif len(value) == 2:
                return [float(value[0]), float(value[1]), 0.0]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0])]
        elif isinstance(value, (int, float)):
            return [float(value), float(value), float(value)]
        return [0.0, 0.0, 0.0]
    
    def _convert_to_color4(self, value) -> List[float]:
        """Convert value to color4 (4-component color)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 4:
                return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
            elif len(value) == 3:
                return [float(value[0]), float(value[1]), float(value[2]), 1.0]
            elif len(value) == 2:
                return [float(value[0]), float(value[1]), 0.0, 1.0]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0]), 1.0]
        elif isinstance(value, (int, float)):
            return [float(value), float(value), float(value), 1.0]
        return [0.0, 0.0, 0.0, 1.0]
    
    def _convert_to_vector2(self, value) -> List[float]:
        """Convert value to vector2 (2-component vector)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 2:
                return [float(value[0]), float(value[1])]
            elif len(value) == 1:
                return [float(value[0]), float(value[0])]
        elif isinstance(value, (int, float)):
            return [float(value), float(value)]
        return [0.0, 0.0]
    
    def _convert_to_vector3(self, value) -> List[float]:
        """Convert value to vector3 (3-component vector)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 3:
                return [float(value[0]), float(value[1]), float(value[2])]
            elif len(value) == 2:
                return [float(value[0]), float(value[1]), 0.0]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0])]
        elif isinstance(value, (int, float)):
            return [float(value), float(value), float(value)]
        return [0.0, 0.0, 0.0]
    
    def _convert_to_vector4(self, value) -> List[float]:
        """Convert value to vector4 (4-component vector)."""
        if isinstance(value, (list, tuple)):
            if len(value) >= 4:
                return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
            elif len(value) == 3:
                return [float(value[0]), float(value[1]), float(value[2]), 1.0]
            elif len(value) == 2:
                return [float(value[0]), float(value[1]), 0.0, 1.0]
            elif len(value) == 1:
                return [float(value[0]), float(value[0]), float(value[0]), 1.0]
        elif isinstance(value, (int, float)):
            return [float(value), float(value), float(value), 1.0]
        return [0.0, 0.0, 0.0, 1.0]
    
    def _convert_to_float(self, value) -> float:
        """Convert value to float."""
        if isinstance(value, (list, tuple)) and len(value) > 0:
            return float(value[0])
        return float(value)
    
    def _convert_to_integer(self, value) -> int:
        """Convert value to integer."""
        if isinstance(value, (list, tuple)) and len(value) > 0:
            return int(value[0])
        return int(value)
    
    def _convert_to_boolean(self, value) -> bool:
        """Convert value to boolean."""
        if isinstance(value, (list, tuple)) and len(value) > 0:
            return bool(value[0])
        return bool(value)
    
    def format_value_string(self, value: Any, value_type: str) -> str:
        """
        Format a value as a string for MaterialX.
        
        Args:
            value: The value to format
            value_type: The MaterialX type
            
        Returns:
            str: The formatted value string
        """
        if value is None:
            return ""
        
        try:
            if value_type in ['color3', 'color4', 'vector2', 'vector3', 'vector4']:
                if isinstance(value, (list, tuple)):
                    return ",".join(str(float(v)) for v in value)
                else:
                    return str(float(value))
            elif value_type == 'float':
                return str(float(value))
            elif value_type == 'integer':
                return str(int(value))
            elif value_type == 'boolean':
                return str(bool(value)).lower()
            elif value_type in ['string', 'filename']:
                return str(value)
            else:
                return str(value)
                
        except Exception as e:
            self.logger.error(f"Error formatting value {value} as {value_type}: {str(e)}")
            return str(value)
