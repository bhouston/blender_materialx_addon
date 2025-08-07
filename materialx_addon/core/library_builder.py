#!/usr/bin/env python3
"""
MaterialX Library Builder

This module provides the main library builder functionality for MaterialX.
"""

import MaterialX as mx
import logging
from typing import Dict, List, Optional, Any
from .document_manager import MaterialXDocumentManager
from .type_converter import MaterialXTypeConverter
from ..node_definitions import CustomNodeDefinitionManager


class MaterialXLibraryBuilder:
    """
    Main MaterialX library builder for creating and managing MaterialX documents.
    
    This class provides:
    - Document creation and management
    - Node addition and connection
    - Surface shader management
    - Document validation and optimization
    - Performance monitoring
    """
    
    def __init__(self, material_name: str, logger, version: str = "1.39"):
        """
        Initialize the MaterialX library builder.
        
        Args:
            material_name: Name of the material being built
            logger: Logger instance
            version: MaterialX version to use
        """
        self.material_name = material_name
        self.logger = logger
        self.version = version
        
        # Initialize managers
        self.document_manager = MaterialXDocumentManager(logger, version)
        self.type_converter = MaterialXTypeConverter(logger)
        
        # Document and node tracking
        self.document = None
        self.nodegraph = None
        self.surface_shader = None
        self.material = None
        
        # Node tracking
        self.nodes = {}
        self.connections = []
        self.node_counter = 0
        
        # Node builder for creating inputs with proper type handling
        self.node_builder = NodeBuilder(self.logger)
        
        # Performance tracking removed
        
        # Initialize document
        self._initialize_document()
    
    def _initialize_document(self):
        """Initialize the MaterialX document."""
        try:
            self.document = self.document_manager.create_document()
            
            # Create main nodegraph
            self.nodegraph = self.document.addNodeGraph(f"{self.material_name}_graph")
            self.nodegraph.setAttribute("description", f"Node graph for {self.material_name}")
            
            # Create material
            self.material = self.document.addMaterial(self.material_name)
            self.material.setAttribute("description", f"Material: {self.material_name}")
            
            self.logger.info(f"Initialized MaterialX document for {self.material_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MaterialX document: {str(e)}")
            raise
    
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """
        Add a node to the document.
        
        Args:
            node_type: The MaterialX node type
            name: The node name
            node_type_category: Optional category for the node
            **params: Additional parameters for the node
            
        Returns:
            str: The node name
        """
        try:
            # Check if it's a custom node type
            if self._is_custom_node_type(node_type):
                return self._add_custom_node(node_type, name, **params)
            
            # Create standard node
            node = self.nodegraph.addNode(node_type, name)
            
            # Set node definition if available
            nodedef = self.document_manager.get_node_definition(node_type, node_type_category)
            if nodedef:
                node.setNodeDefString(nodedef.getName())
            
            # Set parameters
            for param_name, param_value in params.items():
                if param_value is not None:
                    input_elem = node.addInput(param_name, "float")  # Default type
                    if isinstance(param_value, (list, tuple)):
                        input_elem.setValueString(",".join(str(v) for v in param_value))
                    else:
                        input_elem.setValueString(str(param_value))
            
            self.nodes[name] = node
            self.node_counter += 1
            self.logger.debug(f"Added node: {name} of type {node_type}")
            return name
            
        except Exception as e:
            self.logger.error(f"Failed to add node {name} of type {node_type}: {str(e)}")
            raise
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """
        Add a surface shader node.
        
        Args:
            node_type: The surface shader node type
            name: The node name
            **params: Additional parameters
            
        Returns:
            str: The node name
        """
        try:
            node_name = self.add_node(node_type, name, **params)
            self.surface_shader = self.nodes[node_name]
            
            # Connect to material using the new MaterialX 1.38+ API
            # The material should reference the shader node directly
            # No need for separate shader reference in new API
            
            self.logger.info(f"Added surface shader: {name} of type {node_type}")
            return node_name
            
        except Exception as e:
            self.logger.error(f"Failed to add surface shader {name}: {str(e)}")
            raise
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """
        Add a connection between nodes.
        
        Args:
            from_node: Source node name
            from_output: Source output name
            to_node: Target node name
            to_input: Target input name
        """
        try:
            if from_node not in self.nodes or to_node not in self.nodes:
                self.logger.error(f"Node not found: {from_node} or {to_node}")
                return
            
            source_node = self.nodes[from_node]
            target_node = self.nodes[to_node]
            
            # Create connection
            target_input = target_node.addInput(to_input, "float")  # Default type
            target_input.setNodeName(from_node)
            
            # Store connection for tracking
            self.connections.append({
                'from_node': from_node,
                'from_output': from_output,
                'to_node': to_node,
                'to_input': to_input
            })
            
            self.logger.debug(f"Added connection: {from_node}.{from_output} -> {to_node}.{to_input}")
            
        except Exception as e:
            self.logger.error(f"Failed to add connection {from_node}.{from_output} -> {to_node}.{to_input}: {str(e)}")
    
    def add_surface_shader_input(self, surface_node_name: str, input_name: str, input_type: str, 
                                nodegraph_name: str = None, nodename: str = None, value: str = None):
        """
        Add an input to a surface shader.
        
        Args:
            surface_node_name: The surface shader node name
            input_name: The input name
            input_type: The input type
            nodegraph_name: Optional nodegraph name
            nodename: Optional node name
            value: Optional value
        """
        try:
            if surface_node_name not in self.nodes:
                self.logger.error(f"Surface shader node not found: {surface_node_name}")
                return
            
            surface_node = self.nodes[surface_node_name]
            input_elem = surface_node.addInput(input_name, input_type)
            
            if nodename:
                input_elem.setNodeName(nodename)
            elif value is not None:
                input_elem.setValueString(str(value))
            
            self.logger.debug(f"Added surface shader input: {surface_node_name}.{input_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add surface shader input {input_name}: {str(e)}")
    
    def add_output(self, name: str, output_type: str, nodename: str):
        """
        Add an output to the nodegraph.
        
        Args:
            name: The output name
            output_type: The output type
            nodename: The source node name
        """
        try:
            output = self.nodegraph.addOutput(name, output_type)
            output.setNodeName(nodename)
            
            self.logger.debug(f"Added output: {name} of type {output_type} from {nodename}")
            
        except Exception as e:
            self.logger.error(f"Failed to add output {name}: {str(e)}")
    
    def set_material_surface(self, surface_node_name: str):
        """
        Set the material surface shader.
        
        Args:
            surface_node_name: The surface shader node name
        """
        try:
            if surface_node_name not in self.nodes:
                self.logger.error(f"Surface shader node not found: {surface_node_name}")
                return
            
            # In MaterialX 1.38+, materials directly reference shader nodes
            # The material should have a 'surfaceshader' input that connects to the surface shader
            if not self.material.getInput('surfaceshader'):
                self.material.addInput('surfaceshader', 'surfaceshader')
            
            # Connect the material's surfaceshader input to the surface shader node
            surfaceshader_input = self.material.getInput('surfaceshader')
            surfaceshader_input.setConnectedNode(self.nodes[surface_node_name])
            
            self.logger.info(f"Set material surface to {surface_node_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set material surface: {str(e)}")
    
    def _get_param_type(self, value) -> str:
        """Get the MaterialX type for a parameter value."""
        if isinstance(value, (list, tuple)):
            if len(value) == 2:
                return "vector2"
            elif len(value) == 3:
                return "color3"
            elif len(value) == 4:
                return "color4"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        return "float"
    
    def to_string(self) -> str:
        """
        Convert the document to a string.
        
        Returns:
            str: The MaterialX document as a string
        """
        try:
            if not self.document:
                return ""
            
            # Validate document before serialization
            if not self.validate():
                self.logger.warning("Document validation failed, but continuing with serialization")
            
            # Write to string
            return mx.writeToXmlString(self.document)
            
        except Exception as e:
            self.logger.error(f"Failed to serialize document: {str(e)}")
            return ""
    
    def write_to_file(self, filepath: str) -> bool:
        """
        Write the document to a file.
        
        Args:
            filepath: The output file path
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.document:
                self.logger.error("No document to write")
                return False
            
            # Validate document before writing
            if not self.validate():
                self.logger.warning("Document validation failed, but continuing with write")
            
            # Write to file
            mx.writeToXmlFile(self.document, filepath)
            
            self.logger.info(f"Document written to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write document to {filepath}: {str(e)}")
            return False
    
    def validate(self) -> bool:
        """
        Validate the document.
        
        Returns:
            bool: True if document is valid
        """
        try:
            return self.document_manager.validate_document()
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {}  # Performance monitoring removed
    
    def set_write_options(self, **options):
        """Set write options for the document."""
        # This could be extended to support various write options
        self.logger.debug(f"Write options set: {options}")
    
    def optimize_document(self) -> bool:
        """
        Optimize the document by removing unused nodes and connections.
        
        Returns:
            bool: True if optimization was successful
        """
        try:
            # Remove unused nodes
            unused_count = self.remove_unused_nodes()
            self.logger.info(f"Removed {unused_count} unused nodes during optimization")
            
            # Additional optimizations could be added here
            return True
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {str(e)}")
            return False
    
    def remove_unused_nodes(self) -> int:
        """
        Remove unused nodes from the document.
        
        Returns:
            int: Number of nodes removed
        """
        try:
            if not self.document:
                return 0
            
            # Collect all connected nodes
            connected_nodes = set()
            
            # Start from outputs
            for output in self.nodegraph.getOutputs():
                if output.getNodeName():
                    self._collect_connected_nodes_recursive(
                        self.document.getNode(output.getNodeName()), 
                        connected_nodes
                    )
            
            # Start from material shaders
            for shaderref in self.material.getShaderRefs():
                if shaderref.getNodeName():
                    self._collect_connected_nodes_recursive(
                        self.document.getNode(shaderref.getNodeName()), 
                        connected_nodes
                    )
            
            # Find unused nodes
            all_nodes = set(self.nodegraph.getNodes())
            unused_nodes = all_nodes - connected_nodes
            
            # Remove unused nodes
            for node in unused_nodes:
                self.nodegraph.removeChild(node.getName())
                if node.getName() in self.nodes:
                    del self.nodes[node.getName()]
            
            return len(unused_nodes)
            
        except Exception as e:
            self.logger.error(f"Failed to remove unused nodes: {str(e)}")
            return 0
    
    def _collect_connected_nodes_recursive(self, element: mx.Element, connected_nodes: set):
        """Recursively collect all connected nodes."""
        if not element or element in connected_nodes:
            return
        
        connected_nodes.add(element)
        
        for input_elem in element.getInputs():
            if input_elem.getNodeName():
                connected_node = self.document.getNode(input_elem.getNodeName())
                if connected_node:
                    self._collect_connected_nodes_recursive(connected_node, connected_nodes)
    
    def _is_custom_node_type(self, node_type: str) -> bool:
        """Check if a node type is a custom type."""
        from ..node_definitions import is_custom_node_type
        return is_custom_node_type(node_type)
    
    def _add_custom_node(self, node_type: str, name: str, **params) -> str:
        """Add a custom node to the document."""
        try:
            # Get custom node manager
            custom_manager = self.document_manager.custom_node_manager
            if not custom_manager:
                self.logger.error("Custom node manager not available")
                raise RuntimeError("Custom node manager not available")
            
            # Add custom node
            node = custom_manager.add_custom_node_to_document(node_type, name, self.nodegraph)
            if not node:
                raise RuntimeError(f"Failed to add custom node {name} of type {node_type}")
            
            # Set parameters
            for param_name, param_value in params.items():
                if param_value is not None:
                    input_elem = node.addInput(param_name, "float")  # Default type
                    if isinstance(param_value, (list, tuple)):
                        input_elem.setValueString(",".join(str(v) for v in param_value))
                    else:
                        input_elem.setValueString(str(param_value))
            
            self.nodes[name] = node
            self.node_counter += 1
            self.logger.debug(f"Added custom node: {name} of type {node_type}")
            return name
            
        except Exception as e:
            self.logger.error(f"Failed to add custom node {name}: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.document_manager.cleanup()
            self.nodes.clear()
            self.connections.clear()
            self.document = None
            self.nodegraph = None
            self.surface_shader = None
            self.material = None
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")


class NodeBuilder:
    """
    Helper class for creating MaterialX node inputs with proper type handling.
    """
    
    def __init__(self, logger):
        self.logger = logger
    
    def create_mtlx_input(self, node, input_name: str, value=None, node_type: str = None, category: str = None):
        """
        Create a MaterialX input with proper type handling.
        
        Args:
            node: The MaterialX node to add the input to
            input_name: The input name
            value: The input value
            node_type: The node type for type inference
            category: The node category for type inference
        """
        try:
            # Determine input type
            input_type = self._get_input_type(input_name, value, node_type, category)
            
            # Create input
            input_elem = node.addInput(input_name, input_type)
            
            # Set value if provided
            if value is not None:
                if isinstance(value, (list, tuple)):
                    input_elem.setValueString(",".join(str(v) for v in value))
                else:
                    input_elem.setValueString(str(value))
            
            self.logger.debug(f"Created input {input_name} of type {input_type} for node {node.getName()}")
            return input_elem
            
        except Exception as e:
            self.logger.error(f"Failed to create input {input_name}: {str(e)}")
            raise
    
    def _get_input_type(self, input_name: str, value, node_type: str = None, category: str = None) -> str:
        """
        Determine the appropriate MaterialX type for an input.
        
        Args:
            input_name: The input name
            value: The input value
            node_type: The node type
            category: The node category
            
        Returns:
            str: The MaterialX type string
        """
        # Type mapping based on input names
        type_mapping = {
            # Color inputs
            'base_color': 'color3',
            'basecolor': 'color3',
            'color': 'color3',
            'diffuse_color': 'color3',
            'diffusecolor': 'color3',
            'emission_color': 'color3',
            'emissioncolor': 'color3',
            'specular_color': 'color3',
            'specularcolor': 'color3',
            'subsurface_color': 'color3',
            'subsurfacecolor': 'color3',
            'transmission_color': 'color3',
            'transmissioncolor': 'color3',
            
            # Vector inputs
            'normal': 'vector3',
            'tangent': 'vector3',
            'position': 'vector3',
            'vector': 'vector3',
            'scale': 'vector3',
            'offset': 'vector3',
            'rotation': 'vector3',
            
            # Float inputs
            'roughness': 'float',
            'metallic': 'float',
            'specular': 'float',
            'specular_roughness': 'float',
            'ior': 'float',
            'transmission': 'float',
            'transmission_roughness': 'float',
            'subsurface': 'float',
            'subsurface_radius': 'float',
            'subsurface_scale': 'float',
            'subsurface_anisotropy': 'float',
            'anisotropic': 'float',
            'anisotropic_rotation': 'float',
            'anisotropic_tangent': 'float',
            'sheen': 'float',
            'sheen_roughness': 'float',
            'sheen_color': 'color3',
            'sheencolor': 'color3',
            'clearcoat': 'float',
            'clearcoat_roughness': 'float',
            'clearcoat_ior': 'float',
            'clearcoat_normal': 'vector3',
            'clearcoat_normal_scale': 'float',
            'clearcoat_tint': 'color3',
            'clearcoat_tint_scale': 'float',
            'emission_strength': 'float',
            'emission_strength': 'float',
            'alpha': 'float',
            'coat': 'float',
            'coat_roughness': 'float',
            'coat_ior': 'float',
            'coat_color': 'color3',
            'coatcolor': 'color3',
            'coat_normal': 'vector3',
            'coat_normal_scale': 'float',
            'coat_tint': 'color3',
            'coat_tint_scale': 'float',
            
            # String inputs
            'file': 'filename',
            'filename': 'filename',
            'colorspace': 'string',
            'color_space': 'string',
        }
        
        # Check if input name is in our mapping
        if input_name.lower() in type_mapping:
            return type_mapping[input_name.lower()]
        
        # Infer type from value
        if value is not None:
            if isinstance(value, (list, tuple)):
                if len(value) == 2:
                    return 'vector2'
                elif len(value) == 3:
                    # Check if it looks like a color (values between 0-1) or vector
                    if all(0 <= v <= 1 for v in value):
                        return 'color3'
                    else:
                        return 'vector3'
                elif len(value) == 4:
                    return 'color4'
            elif isinstance(value, bool):
                return 'boolean'
            elif isinstance(value, int):
                return 'integer'
            elif isinstance(value, float):
                return 'float'
            elif isinstance(value, str):
                return 'string'
        
        # Default to float for unknown types
        return 'float'
