#!/usr/bin/env python3
"""
Node Mapper Registry

This module provides a registry-based system for managing node mappers,
allowing for automatic discovery and registration of mappers.
"""

from typing import Dict, List, Optional, Type, Any
import bpy
import MaterialX as mx
from .base_mapper import BaseNodeMapper
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import NodeMappingError, UnsupportedNodeError


class NodeMapperRegistry:
    """
    Registry for managing node mappers.
    
    This class provides a centralized registry for all node mappers,
    allowing for automatic discovery and registration of mappers.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the node mapper registry.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger("NodeMapperRegistry")
        self._mappers: Dict[str, Type[BaseNodeMapper]] = {}
        self._mapper_instances: Dict[str, BaseNodeMapper] = {}
        self._node_type_mapping: Dict[str, str] = {}
        self._initialized = False
    
    def register_mapper(self, node_type: str, mapper_class: Type[BaseNodeMapper]):
        """
        Register a mapper for a specific node type.
        
        Args:
            node_type: The Blender node type to register
            mapper_class: The mapper class to register
        """
        self._mappers[node_type] = mapper_class
        self.logger.debug(f"Registered mapper for node type: {node_type} -> {mapper_class.__name__}")
    
    def register_mappers(self, mappers: Dict[str, Type[BaseNodeMapper]]):
        """
        Register multiple mappers at once.
        
        Args:
            mappers: Dictionary mapping node types to mapper classes
        """
        for node_type, mapper_class in mappers.items():
            self.register_mapper(node_type, mapper_class)
    
    def get_mapper(self, node_type: str) -> Optional[BaseNodeMapper]:
        """
        Get a mapper instance for a node type.
        
        Args:
            node_type: The Blender node type
            
        Returns:
            Mapper instance if found, None otherwise
        """
        if node_type not in self._mapper_instances:
            if node_type in self._mappers:
                mapper_class = self._mappers[node_type]
                self._mapper_instances[node_type] = mapper_class(self.logger)
            else:
                return None
        
        return self._mapper_instances[node_type]
    
    def get_mapper_for_node(self, blender_node: bpy.types.Node) -> Optional[BaseNodeMapper]:
        """
        Get the appropriate mapper for a Blender node.
        
        Args:
            blender_node: The Blender node
            
        Returns:
            Mapper instance if found, None otherwise
        """
        # First try direct node type mapping
        mapper = self.get_mapper(blender_node.type)
        if mapper and mapper.can_map_node(blender_node):
            return mapper
        
        # Try to find a mapper that can handle this node
        for node_type, mapper_instance in self._mapper_instances.items():
            if mapper_instance.can_map_node(blender_node):
                return mapper_instance
        
        return None
    
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """
        Check if a Blender node can be mapped.
        
        Args:
            blender_node: The Blender node to check
            
        Returns:
            True if the node can be mapped, False otherwise
        """
        return self.get_mapper_for_node(blender_node) is not None
    
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document,
                 exported_nodes: Dict[str, str]) -> mx.Node:
        """
        Map a Blender node to a MaterialX node.
        
        Args:
            blender_node: The Blender node to map
            document: The MaterialX document to add the node to
            exported_nodes: Dictionary of already exported nodes
            
        Returns:
            The created MaterialX node
            
        Raises:
            UnsupportedNodeError: If no mapper is found for the node
            NodeMappingError: If mapping fails
        """
        mapper = self.get_mapper_for_node(blender_node)
        if not mapper:
            raise UnsupportedNodeError(blender_node.type, blender_node.name)
        
        try:
            return mapper.map_node(blender_node, document, exported_nodes)
        except Exception as e:
            if isinstance(e, (UnsupportedNodeError, NodeMappingError)):
                raise
            raise NodeMappingError(blender_node.type, blender_node.name, "mapping", e)
    
    def get_supported_node_types(self) -> List[str]:
        """
        Get a list of all supported node types.
        
        Returns:
            List of supported node type strings
        """
        return list(self._mappers.keys())
    
    def get_mapper_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered mappers.
        
        Returns:
            Dictionary containing mapper information
        """
        info = {}
        for node_type, mapper_class in self._mappers.items():
            mapper_instance = self.get_mapper(node_type)
            info[node_type] = {
                'class_name': mapper_class.__name__,
                'supported_types': mapper_instance.supported_node_types if mapper_instance else [],
                'materialx_type': mapper_instance.materialx_node_type if mapper_instance else '',
                'materialx_category': mapper_instance.materialx_category if mapper_instance else '',
                'input_mapping': mapper_instance.get_input_mapping() if mapper_instance else {},
                'output_mapping': mapper_instance.get_output_mapping() if mapper_instance else {},
                'required_inputs': mapper_instance.get_required_inputs() if mapper_instance else [],
                'optional_inputs': mapper_instance.get_optional_inputs() if mapper_instance else []
            }
        return info
    
    def validate_node(self, blender_node: bpy.types.Node) -> List[str]:
        """
        Validate a Blender node using the appropriate mapper.
        
        Args:
            blender_node: The Blender node to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        mapper = self.get_mapper_for_node(blender_node)
        if not mapper:
            return [f"No mapper found for node type: {blender_node.type}"]
        
        return mapper.validate_node(blender_node)
    
    def initialize_default_mappers(self):
        """
        Initialize the registry with default mappers.
        
        This method should be called after all mapper classes are imported
        to register the default mappers.
        """
        if self._initialized:
            return
        
        self.logger.info("Initializing default node mappers...")
        
        # Import and register default mappers
        try:
            from .principled_mapper import PrincipledBSDFMapper
            from .texture_mappers import TextureMapper, ImageTextureMapper, ProceduralTextureMapper
            from .math_mappers import MathMapper, VectorMathMapper
            from .utility_mappers import UtilityMapper
            
            # Register mappers
            default_mappers = {
                'BSDF_PRINCIPLED': PrincipledBSDFMapper,
                'TEX_IMAGE': ImageTextureMapper,
                'TEX_NOISE': ProceduralTextureMapper,
                'TEX_VORONOI': ProceduralTextureMapper,
                'TEX_WAVE': ProceduralTextureMapper,
                'TEX_MUSGRAVE': ProceduralTextureMapper,
                'TEX_BRICK': ProceduralTextureMapper,
                'TEX_GRADIENT': ProceduralTextureMapper,
                'CHECKER_TEXTURE': ProceduralTextureMapper,
                'MATH': MathMapper,
                'VECTOR_MATH': VectorMathMapper,
                'MIX': UtilityMapper,
                'MIX_RGB': UtilityMapper,
                'INVERT': UtilityMapper,
                'SEPARATE_COLOR': UtilityMapper,
                'COMBINE_COLOR': UtilityMapper,
                'NORMAL_MAP': UtilityMapper,
                'BUMP': UtilityMapper,
                'MAPPING': UtilityMapper,
                'LAYER_WEIGHT': UtilityMapper,
                'CURVE_RGB': UtilityMapper,
                'CLAMP': UtilityMapper,
                'MAP_RANGE': UtilityMapper,
                'GEOMETRY': UtilityMapper,
                'OBJECT_INFO': UtilityMapper,
                'LIGHT_PATH': UtilityMapper,
                'HSV_TO_RGB': UtilityMapper,
                'RGB_TO_HSV': UtilityMapper,
                'LUMINANCE': UtilityMapper,
                'CONTRAST': UtilityMapper,
                'SATURATE': UtilityMapper,
                'GAMMA': UtilityMapper,
                'SEPARATE_XYZ': UtilityMapper,
                'COMBINE_XYZ': UtilityMapper,
                'ROUGHNESS_ANISOTROPY': UtilityMapper,
                'ARTISTIC_IOR': UtilityMapper,
                'ADD_SHADER': UtilityMapper,
                'MULTIPLY_SHADER': UtilityMapper,
                'TEX_COORD': UtilityMapper,
                'RGB': UtilityMapper,
                'VALUE': UtilityMapper
            }
            
            self.register_mappers(default_mappers)
            self.logger.info(f"Registered {len(default_mappers)} default mappers")
            
        except ImportError as e:
            self.logger.warning(f"Could not import some default mappers: {e}")
        
        self._initialized = True
    
    def clear_mappers(self):
        """Clear all registered mappers."""
        self._mappers.clear()
        self._mapper_instances.clear()
        self._node_type_mapping.clear()
        self._initialized = False
        self.logger.debug("Cleared all mappers")
    
    def get_mapper_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the registry.
        
        Returns:
            Dictionary containing registry statistics
        """
        return {
            'total_mappers': len(self._mappers),
            'mapper_instances': len(self._mapper_instances),
            'supported_node_types': len(self.get_supported_node_types()),
            'initialized': self._initialized
        }


# Global registry instance
_global_registry: Optional[NodeMapperRegistry] = None


def get_registry() -> NodeMapperRegistry:
    """
    Get the global node mapper registry instance.
    
    Returns:
        Global NodeMapperRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = NodeMapperRegistry()
        _global_registry.initialize_default_mappers()
    return _global_registry


def register_mapper(node_type: str, mapper_class: Type[BaseNodeMapper]):
    """
    Register a mapper with the global registry.
    
    Args:
        node_type: The Blender node type to register
        mapper_class: The mapper class to register
    """
    registry = get_registry()
    registry.register_mapper(node_type, mapper_class)


def get_mapper(node_type: str) -> Optional[BaseNodeMapper]:
    """
    Get a mapper from the global registry.
    
    Args:
        node_type: The Blender node type
        
    Returns:
        Mapper instance if found, None otherwise
    """
    registry = get_registry()
    return registry.get_mapper(node_type)


def can_map_node(blender_node: bpy.types.Node) -> bool:
    """
    Check if a Blender node can be mapped using the global registry.
    
    Args:
        blender_node: The Blender node to check
        
    Returns:
        True if the node can be mapped, False otherwise
    """
    registry = get_registry()
    return registry.can_map_node(blender_node)


def map_node(blender_node: bpy.types.Node, document: mx.Document,
             exported_nodes: Dict[str, str]) -> mx.Node:
    """
    Map a Blender node to a MaterialX node using the global registry.
    
    Args:
        blender_node: The Blender node to map
        document: The MaterialX document to add the node to
        exported_nodes: Dictionary of already exported nodes
        
    Returns:
        The created MaterialX node
        
    Raises:
        UnsupportedNodeError: If no mapper is found for the node
        NodeMappingError: If mapping fails
    """
    registry = get_registry()
    return registry.map_node(blender_node, document, exported_nodes)
