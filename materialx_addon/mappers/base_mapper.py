#!/usr/bin/env python3
"""
Base Node Mapper

This module provides the base class for all node mappers in the MaterialX addon.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import bpy
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import NodeMappingError, UnsupportedNodeError
from ..utils.node_utils import NodeUtils


class BaseNodeMapper(ABC):
    """
    Abstract base class for all node mappers.
    
    This class defines the interface that all node mappers must implement
    for converting Blender nodes to MaterialX nodes.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the base mapper.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger(f"Mapper.{self.__class__.__name__}")
        self.supported_node_types: List[str] = []
        self.materialx_node_type: str = ""
        self.materialx_category: str = ""
        
    @abstractmethod
    def can_map_node(self, blender_node: bpy.types.Node) -> bool:
        """
        Check if this mapper can handle the given Blender node.
        
        Args:
            blender_node: The Blender node to check
            
        Returns:
            True if this mapper can handle the node, False otherwise
        """
        pass
    
    @abstractmethod
    def map_node(self, blender_node: bpy.types.Node, document: mx.Document, 
                 exported_nodes: Dict[str, str]) -> Any:
        """
        Map a Blender node to a MaterialX node.
        
        Args:
            blender_node: The Blender node to map
            document: The MaterialX document to add the node to
            exported_nodes: Dictionary of already exported nodes
            
        Returns:
            The created MaterialX node
            
        Raises:
            NodeMappingError: If mapping fails
            UnsupportedNodeError: If node type is not supported
        """
        pass
    
    def get_input_mapping(self) -> Dict[str, str]:
        """
        Get the input mapping for this node type.
        
        Returns:
            Dictionary mapping Blender input names to MaterialX input names
        """
        return {}
    
    def get_output_mapping(self) -> Dict[str, str]:
        """
        Get the output mapping for this node type.
        
        Returns:
            Dictionary mapping Blender output names to MaterialX output names
        """
        return {}
    
    def get_default_values(self) -> Dict[str, Any]:
        """
        Get default values for this node type.
        
        Returns:
            Dictionary of default values for node inputs
        """
        return {}
    
    def validate_node(self, blender_node: bpy.types.Node) -> List[str]:
        """
        Validate a Blender node before mapping.
        
        Args:
            blender_node: The Blender node to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check if node type is supported
        if not self.can_map_node(blender_node):
            errors.append(f"Node type '{blender_node.type}' is not supported by {self.__class__.__name__}")
        
        # Check for required inputs
        required_inputs = self.get_required_inputs()
        for input_name in required_inputs:
            if not self._has_input(blender_node, input_name):
                errors.append(f"Required input '{input_name}' not found on node '{blender_node.name}'")
        
        return errors
    
    def get_required_inputs(self) -> List[str]:
        """
        Get list of required inputs for this node type.
        
        Returns:
            List of required input names
        """
        return []
    
    def get_optional_inputs(self) -> List[str]:
        """
        Get list of optional inputs for this node type.
        
        Returns:
            List of optional input names
        """
        return []
    
    def _has_input(self, blender_node: bpy.types.Node, input_name: str) -> bool:
        """
        Check if a Blender node has a specific input.
        
        Args:
            blender_node: The Blender node
            input_name: The input name to check
            
        Returns:
            True if the input exists, False otherwise
        """
        return input_name in blender_node.inputs
    
    def _has_output(self, blender_node: bpy.types.Node, output_name: str) -> bool:
        """
        Check if a Blender node has a specific output.
        
        Args:
            blender_node: The Blender node
            output_name: The output name to check
            
        Returns:
            True if the output exists, False otherwise
        """
        return output_name in blender_node.outputs
    
    def _get_input_value(self, blender_node: bpy.types.Node, input_name: str) -> Any:
        """
        Get the value of a Blender node input.
        
        Args:
            blender_node: The Blender node
            input_name: The input name
            
        Returns:
            The input value
        """
        if not self._has_input(blender_node, input_name):
            return None
        
        input_socket = blender_node.inputs[input_name]
        default_value = getattr(input_socket, 'default_value', None)
        
        # Handle Blender array values properly
        if default_value is not None:
            if hasattr(default_value, '__len__') and not isinstance(default_value, str):
                # Convert Blender arrays to Python lists
                try:
                    if len(default_value) == 3:
                        return [float(default_value[0]), float(default_value[1]), float(default_value[2])]
                    elif len(default_value) == 4:
                        return [float(default_value[0]), float(default_value[1]), float(default_value[2]), float(default_value[3])]
                    elif len(default_value) == 2:
                        return [float(default_value[0]), float(default_value[1])]
                    else:
                        return [float(v) for v in default_value]
                except (TypeError, ValueError, IndexError):
                    # If conversion fails, return as is
                    return default_value
            else:
                # Single value
                try:
                    return float(default_value)
                except (TypeError, ValueError):
                    return default_value
        
        return default_value
    
    def _get_input_connection(self, blender_node: bpy.types.Node, input_name: str,
                             exported_nodes: Dict[str, str]) -> Optional[str]:
        """
        Get the MaterialX node name that an input is connected to.
        
        Args:
            blender_node: The Blender node
            input_name: The input name
            exported_nodes: Dictionary of already exported nodes
            
        Returns:
            MaterialX node name if connected, None otherwise
        """
        if not self._has_input(blender_node, input_name):
            return None
        
        input_socket = blender_node.inputs[input_name]
        if not input_socket.is_linked or not input_socket.links:
            return None
        
        from_node = input_socket.links[0].from_node
        return exported_nodes.get(from_node.name)
    
    def _create_materialx_node(self, document: mx.Document, node_name: str, 
                              node_type: str, category: str) -> Any:
        """
        Create a MaterialX node in the document.
        
        Args:
            document: The MaterialX document
            node_name: Name for the node
            node_type: Type of the node
            category: Category of the node
            
        Returns:
            The created MaterialX node
            
        Raises:
            NodeMappingError: If node creation fails
        """
        try:
            # Generate a proper MaterialX node name based on the node type
            materialx_name = self._generate_materialx_node_name(node_name, node_type)
            unique_name = self._get_unique_node_name(document, materialx_name, node_type)
            
            node = document.addNode(unique_name, node_type, category)
            self.logger.debug(f"Created MaterialX node: {unique_name} ({node_type})")
            return node
        except Exception as e:
            raise NodeMappingError(node_type, node_name, "node_creation", e)
    
    def _generate_materialx_node_name(self, blender_name: str, materialx_type: str) -> str:
        """
        Generate a proper MaterialX node name based on the node type.
        
        Args:
            blender_name: Original Blender node name
            materialx_type: MaterialX node type
            
        Returns:
            Proper MaterialX node name
        """
        # Sanitize the Blender name for MaterialX
        sanitized_blender_name = blender_name.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '_')
        
        # For surface shaders, use a simpler naming scheme to avoid conflicts
        if materialx_type == "standard_surface":
            return f"surface_{sanitized_blender_name}"
        
        # For other nodes, include the type for clarity
        return f"{materialx_type}_{sanitized_blender_name}"
    
    def _get_unique_node_name(self, document: mx.Document, base_name: str, node_type: str) -> str:
        """
        Get a unique node name for the document.
        
        Args:
            document: The MaterialX document
            base_name: Base name for the node
            node_type: Type of the node
            
        Returns:
            Unique node name
        """
        # Start with the base name
        name = base_name
        counter = 1
        
        # Check if name exists and generate unique name
        while document.getNode(name):
            name = f"{base_name}_{counter}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                name = f"{node_type}_{counter}"
                break
        
        return name
    
    def _add_input(self, materialx_node: Any, input_name: str, input_type: str,
                   value: Optional[Any] = None) -> Any:
        """
        Add an input to a MaterialX node.
        
        Args:
            materialx_node: The MaterialX node
            input_name: Name for the input
            input_type: Type of the input
            value: Optional default value
            
        Returns:
            The created MaterialX input
            
        Raises:
            NodeMappingError: If input creation fails
        """
        try:
            # Check if input already exists
            existing_input = materialx_node.getInput(input_name)
            if existing_input:
                self.logger.debug(f"Input {input_name} already exists on {materialx_node.getName()}")
                return existing_input
            
            input_port = materialx_node.addInput(input_name, input_type)
            
            if value is not None:
                # Handle different value types properly
                if isinstance(value, (list, tuple)):
                    # For arrays (like colors), join with commas
                    if len(value) <= 4:  # color3, color4, vector2, vector3, vector4
                        input_port.setValueString(", ".join(str(v) for v in value))
                    else:
                        input_port.setValueString(" ".join(str(v) for v in value))
                elif hasattr(value, '__str__') and '<bpy_' in str(value):
                    # Handle Blender array objects that haven't been properly converted
                    self.logger.warning(f"Unconverted Blender value: {value}")
                    # Set a default value based on the input type
                    if input_type == 'color3':
                        input_port.setValueString("0.5, 0.5, 0.5")
                    elif input_type == 'color4':
                        input_port.setValueString("0.5, 0.5, 0.5, 1.0")
                    elif input_type == 'vector3':
                        input_port.setValueString("0.0, 0.0, 0.0")
                    elif input_type == 'vector2':
                        input_port.setValueString("0.0, 0.0")
                    else:
                        input_port.setValueString("0.0")
                else:
                    # Handle boolean values properly
                    if input_type == 'boolean':
                        input_port.setValueString(str(value).lower())
                    else:
                        input_port.setValueString(str(value))
            
            self.logger.debug(f"Added input to {materialx_node.getName()}: {input_name} ({input_type})")
            return input_port
        except Exception as e:
            raise NodeMappingError(materialx_node.getType(), materialx_node.getName(), "input_creation", e)
    
    def _add_output(self, materialx_node: Any, output_name: str, 
                    output_type: str) -> Any:
        """
        Add an output to a MaterialX node.
        
        Args:
            materialx_node: The MaterialX node
            output_name: Name for the output
            output_type: Type of the output
            
        Returns:
            The created MaterialX output
            
        Raises:
            NodeMappingError: If output creation fails
        """
        try:
            # Check if output already exists
            existing_output = materialx_node.getOutput(output_name)
            if existing_output:
                self.logger.debug(f"Output {output_name} already exists on {materialx_node.getName()}")
                return existing_output
            
            output_port = materialx_node.addOutput(output_name, output_type)
            self.logger.debug(f"Added output to {materialx_node.getName()}: {output_name} ({output_type})")
            return output_port
        except Exception as e:
            raise NodeMappingError(materialx_node.getType(), materialx_node.getName(), "output_creation", e)
    
    def _connect_nodes(self, from_node: Any, from_output: str,
                      to_node: Any, to_input: str) -> bool:
        """
        Connect two MaterialX nodes.
        
        Args:
            from_node: Source node
            from_output: Source output name
            to_node: Target node
            to_input: Target input name
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            output_port = from_node.getOutput(from_output)
            input_port = to_node.getInput(to_input)
            
            if not output_port:
                self.logger.warning(f"Output '{from_output}' not found on node '{from_node.getName()}'")
                return False
            
            if not input_port:
                self.logger.warning(f"Input '{to_input}' not found on node '{to_node.getName()}'")
                return False
            
            input_port.setConnectedOutput(output_port)
            self.logger.debug(f"Connected {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect nodes: {e}")
            return False
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for MaterialX.
        
        Args:
            value: The value to format
            
        Returns:
            Formatted string representation
        """
        return NodeUtils.format_socket_value(value)
    
    def _get_materialx_input_name(self, blender_input_name: str) -> str:
        """
        Get the MaterialX input name for a Blender input name.
        
        Args:
            blender_input_name: The Blender input name
            
        Returns:
            The MaterialX input name
        """
        input_mapping = self.get_input_mapping()
        return input_mapping.get(blender_input_name, blender_input_name)
    
    def _get_materialx_output_name(self, blender_output_name: str) -> str:
        """
        Get the MaterialX output name for a Blender output name.
        
        Args:
            blender_output_name: The Blender output name
            
        Returns:
            The MaterialX output name
        """
        output_mapping = self.get_output_mapping()
        return output_mapping.get(blender_output_name, blender_output_name)
