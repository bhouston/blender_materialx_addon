#!/usr/bin/env python3
"""
MaterialX Addon Node Utilities

This module contains utility functions for common node operations used
throughout the MaterialX addon.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
import bpy
from .exceptions import NodeMappingError, UnsupportedNodeError


class NodeUtils:
    """
    Utility class for common node operations.
    
    This class provides static methods for common operations on Blender nodes
    that are used throughout the MaterialX export process.
    """
    
    @staticmethod
    def get_input_value_or_connection(
        node: Any, 
        input_name: str, 
        exported_nodes: Optional[Dict] = None
    ) -> Tuple[bool, Any, str]:
        """
        Get input value or connection for a Blender node.
        
        Args:
            node: The Blender node to get input from
            input_name: Name of the input socket
            exported_nodes: Dictionary of already exported nodes for connection lookup
            
        Returns:
            Tuple of (is_connected, value_or_node_name, type_str)
            - is_connected: True if input is connected to another node
            - value_or_node_name: The MaterialX node name if connected, or the value if not
            - type_str: The socket type as a string
            
        Raises:
            AttributeError: If node has no 'inputs' attribute
            KeyError: If input_name is not found in node inputs
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
    
    @staticmethod
    def format_socket_value(value: Any) -> str:
        """
        Format a socket value for MaterialX.
        
        Args:
            value: The value to format (can be single value, list, or tuple)
            
        Returns:
            Formatted string representation of the value
        """
        if value is None:
            return "0"
        
        if isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        
        return str(value)
    
    @staticmethod
    def get_node_output_name_robust(blender_node_type: str, blender_output_name: str) -> str:
        """
        Get the MaterialX output name for a Blender node output using explicit mapping.
        
        Args:
            blender_node_type: The Blender node type (e.g., 'TEX_COORD', 'MIX')
            blender_output_name: The Blender output name (e.g., 'Generated', 'Result')
            
        Returns:
            The MaterialX output name
            
        Raises:
            ValueError: If no explicit mapping is found
        """
        from ..config.node_mappings import NODE_MAPPING
        
        if blender_node_type in NODE_MAPPING:
            node_mapping = NODE_MAPPING[blender_node_type]
            if 'outputs' in node_mapping:
                outputs_mapping = node_mapping['outputs']
                if blender_output_name in outputs_mapping:
                    return outputs_mapping[blender_output_name]
                else:
                    available_outputs = list(outputs_mapping.keys())
                    raise ValueError(
                        f"No explicit mapping found for output '{blender_output_name}' "
                        f"in node type '{blender_node_type}'. "
                        f"Available outputs: {available_outputs}"
                    )
            else:
                raise ValueError(f"No outputs mapping found for node type '{blender_node_type}'")
        else:
            available_types = list(NODE_MAPPING.keys())
            raise ValueError(
                f"No explicit mapping found for node type '{blender_node_type}'. "
                f"Available node types: {available_types}"
            )
    
    @staticmethod
    def get_node_input_name_robust(blender_node_type: str, blender_input_name: str) -> str:
        """
        Get the MaterialX input name for a Blender node input using explicit mapping.
        
        Args:
            blender_node_type: The Blender node type (e.g., 'MIX', 'NOISE_TEXTURE')
            blender_input_name: The Blender input name (e.g., 'A', 'Vector')
            
        Returns:
            The MaterialX input name
            
        Raises:
            ValueError: If no explicit mapping is found
        """
        from ..config.node_mappings import NODE_MAPPING
        
        if blender_node_type in NODE_MAPPING:
            node_mapping = NODE_MAPPING[blender_node_type]
            if 'inputs' in node_mapping:
                inputs_mapping = node_mapping['inputs']
                if blender_input_name in inputs_mapping:
                    return inputs_mapping[blender_input_name]
                else:
                    available_inputs = list(inputs_mapping.keys())
                    raise ValueError(
                        f"No explicit mapping found for input '{blender_input_name}' "
                        f"in node type '{blender_node_type}'. "
                        f"Available inputs: {available_inputs}"
                    )
            else:
                raise ValueError(f"No inputs mapping found for node type '{blender_node_type}'")
        else:
            available_types = list(NODE_MAPPING.keys())
            raise ValueError(
                f"No explicit mapping found for node type '{blender_node_type}'. "
                f"Available node types: {available_types}"
            )
    
    @staticmethod
    def get_node_mtlx_type(blender_node_type: str) -> Tuple[str, str]:
        """
        Get the MaterialX type and category for a Blender node type.
        
        Args:
            blender_node_type: The Blender node type
            
        Returns:
            Tuple of (materialx_type, materialx_category)
            
        Raises:
            ValueError: If no mapping is found for the node type
        """
        from ..config.node_mappings import NODE_MAPPING
        
        if blender_node_type in NODE_MAPPING:
            node_mapping = NODE_MAPPING[blender_node_type]
            return node_mapping['mtlx_type'], node_mapping['mtlx_category']
        else:
            available_types = list(NODE_MAPPING.keys())
            raise ValueError(
                f"No explicit mapping found for node type '{blender_node_type}'. "
                f"Available node types: {available_types}"
            )
    
    @staticmethod
    def is_node_supported(blender_node_type: str) -> bool:
        """
        Check if a Blender node type is supported by the exporter.
        
        Args:
            blender_node_type: The Blender node type to check
            
        Returns:
            True if the node type is supported, False otherwise
        """
        from ..config.node_mappings import NODE_MAPPING
        return blender_node_type in NODE_MAPPING
    
    @staticmethod
    def get_supported_node_types() -> List[str]:
        """
        Get a list of all supported Blender node types.
        
        Returns:
            List of supported node type strings
        """
        from ..config.node_mappings import NODE_MAPPING
        return list(NODE_MAPPING.keys())
    
    @staticmethod
    def get_node_inputs(node: Any) -> Dict[str, Any]:
        """
        Get all inputs for a node with their values and connections.
        
        Args:
            node: The Blender node
            
        Returns:
            Dictionary mapping input names to their values or connections
        """
        inputs = {}
        for input_name in node.inputs.keys():
            try:
                is_connected, value_or_connection, type_str = NodeUtils.get_input_value_or_connection(
                    node, input_name
                )
                inputs[input_name] = {
                    'is_connected': is_connected,
                    'value_or_connection': value_or_connection,
                    'type': type_str
                }
            except (KeyError, AttributeError) as e:
                # Skip inputs that can't be accessed
                continue
        
        return inputs
    
    @staticmethod
    def get_node_outputs(node: Any) -> Dict[str, str]:
        """
        Get all outputs for a node.
        
        Args:
            node: The Blender node
            
        Returns:
            Dictionary mapping output names to their types
        """
        outputs = {}
        for output_name in node.outputs.keys():
            output_socket = node.outputs[output_name]
            outputs[output_name] = str(output_socket.type)
        
        return outputs
    
    @staticmethod
    def find_node_by_type(material: bpy.types.Material, node_type: str) -> Optional[Any]:
        """
        Find a node of a specific type in a material.
        
        Args:
            material: The Blender material to search in
            node_type: The type of node to find
            
        Returns:
            The first node of the specified type, or None if not found
        """
        if not material.use_nodes or not material.node_tree:
            return None
        
        for node in material.node_tree.nodes:
            if node.type == node_type:
                return node
        
        return None
    
    @staticmethod
    def find_nodes_by_type(material: bpy.types.Material, node_type: str) -> List[Any]:
        """
        Find all nodes of a specific type in a material.
        
        Args:
            material: The Blender material to search in
            node_type: The type of node to find
            
        Returns:
            List of all nodes of the specified type
        """
        if not material.use_nodes or not material.node_tree:
            return []
        
        return [node for node in material.node_tree.nodes if node.type == node_type]
    
    @staticmethod
    def get_node_dependencies(node: Any) -> List[Any]:
        """
        Get all nodes that this node depends on (connected inputs).
        
        Args:
            node: The Blender node
            
        Returns:
            List of nodes that this node depends on
        """
        dependencies = []
        
        for input_socket in node.inputs:
            if input_socket.is_linked:
                for link in input_socket.links:
                    dependencies.append(link.from_node)
        
        return dependencies
    
    @staticmethod
    def get_node_dependents(node: Any) -> List[Any]:
        """
        Get all nodes that depend on this node (connected outputs).
        
        Args:
            node: The Blender node
            
        Returns:
            List of nodes that depend on this node
        """
        dependents = []
        
        for output_socket in node.outputs:
            if output_socket.is_linked:
                for link in output_socket.links:
                    dependents.append(link.to_node)
        
        return dependents
    
    @staticmethod
    def validate_node_connections(node: Any) -> List[str]:
        """
        Validate that a node has all required connections.
        
        Args:
            node: The Blender node to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for required inputs that are not connected
        for input_socket in node.inputs:
            if hasattr(input_socket, 'is_required') and input_socket.is_required:
                if not input_socket.is_linked and not input_socket.default_value:
                    errors.append(f"Required input '{input_socket.name}' is not connected or has no default value")
        
        return errors
