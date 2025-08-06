#!/usr/bin/env python3
"""
MaterialX Library Core - Phase 1 & 2 Implementation

This module implements the core infrastructure migration from manual XML generation
to MaterialX library APIs as outlined in the integration plan.

Phase 1: Core Infrastructure Migration
- Replace XML generation with MaterialX library
- Implement library loading system
- Create MaterialX document builder

Phase 2: Node Mapping System Enhancement
- Leverage node definitions for type-safe mapping
- Implement automatic type conversion and validation
- Enhanced node creation with validation
"""

import MaterialX as mx
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import logging

# Import mtlxutils
try:
    from . import mtlxutils
    from .mtlxutils import mxbase as mxb
    from .mtlxutils import mxfile as mxf
    from .mtlxutils import mxnodegraph as mxg
    from .mtlxutils import mxtraversal as mxt
except ImportError:
    # Fallback for direct import
    import mtlxutils
    import mtlxutils.mxbase as mxb
    import mtlxutils.mxfile as mxf
    import mtlxutils.mxnodegraph as mxg
    import mtlxutils.mxtraversal as mxt


class MaterialXDocumentManager:
    """
    Manages MaterialX document creation and library loading.
    
    This class handles:
    - MaterialX document creation
    - Library loading and validation
    - Version compatibility
    - Search path management
    """
    
    def __init__(self, logger, version: str = "1.38"):
        self.logger = logger
        self.version = version
        self.document = None
        self.libraries = None
        self.library_files = []
        self.search_path = None
        
    def load_libraries(self, custom_search_path: Optional[str] = None) -> bool:
        """
        Load MaterialX libraries with proper version handling.
        
        Args:
            custom_search_path: Optional custom search path for libraries
            
        Returns:
            bool: True if libraries loaded successfully
        """
        try:
            self.logger.info(f"Loading MaterialX libraries (version: {self.version})")
            
            # Create search path
            self.search_path = mx.FileSearchPath()
            if custom_search_path:
                self.search_path.append(mx.FilePath(custom_search_path))
            
            # Check MaterialX version and use appropriate loading method
            if mxb.haveVersion(1, 38, 7):
                self.logger.info("Using MaterialX 1.38.7+ library loading method")
                search_path = mx.getDefaultDataSearchPath()
                search_path.append(self.search_path)
                lib_folders = mx.getDefaultDataLibraryFolders()
                self.library_files = mx.loadLibraries(lib_folders, search_path, self.libraries)
            else:
                self.logger.info("Using legacy MaterialX library loading method")
                library_path = mx.FilePath('libraries')
                search_path = mx.FileSearchPath()
                search_path.append(self.search_path)
                self.library_files = mx.loadLibraries([library_path], search_path, self.libraries)
            
            self.logger.info(f"Loaded {len(self.library_files)} library files")
            self.logger.info(f"Library files: {[f.asString() for f in self.library_files]}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MaterialX libraries: {str(e)}")
            return False
    
    def create_document(self) -> mx.Document:
        """
        Create a new MaterialX document with loaded libraries.
        
        Returns:
            mx.Document: The created document
        """
        try:
            self.logger.info("Creating MaterialX document")
            
            # Create libraries document if not already created
            if self.libraries is None:
                self.libraries = mx.createDocument()
                if not self.load_libraries():
                    raise RuntimeError("Failed to load MaterialX libraries")
            
            # Create working document
            self.document = mx.createDocument()
            self.document.importLibrary(self.libraries)
            
            self.logger.info("MaterialX document created successfully")
            return self.document
            
        except Exception as e:
            self.logger.error(f"Failed to create MaterialX document: {str(e)}")
            raise
    
    def get_node_definition(self, node_type: str, category: str = None) -> Optional[mx.NodeDef]:
        """
        Get a node definition from the loaded libraries.
        
        Args:
            node_type: The node type to find
            category: Optional category filter
            
        Returns:
            mx.NodeDef: The node definition or None if not found
        """
        if not self.document:
            self.logger.error("No document available for node definition lookup")
            return None
        
        try:
            if category:
                # Search by category and type
                nodedefs = self.document.getMatchingNodeDefs(category)
                for nodedef in nodedefs:
                    if nodedef.getType() == node_type:
                        return nodedef
            else:
                # Search by name
                return self.document.getNodeDef(node_type)
                
        except Exception as e:
            self.logger.error(f"Error looking up node definition {node_type}: {str(e)}")
            return None
    
    def get_input_definition(self, node_type: str, input_name: str, category: str = None) -> Optional[mx.Input]:
        """
        Get an input definition from a node definition.
        
        Args:
            node_type: The node type
            input_name: The input name
            category: Optional category filter
            
        Returns:
            mx.Input: The input definition or None if not found
        """
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            return nodedef.getInput(input_name)
        return None
    
    def get_output_definition(self, node_type: str, output_name: str, category: str = None) -> Optional[mx.Output]:
        """
        Get an output definition from a node definition.
        
        Args:
            node_type: The node type
            output_name: The output name
            category: Optional category filter
            
        Returns:
            mx.Output: The output definition or None if not found
        """
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            return nodedef.getOutput(output_name)
        return None
    
    def validate_document(self) -> bool:
        """
        Validate the MaterialX document.
        
        Returns:
            bool: True if document is valid
        """
        if not self.document:
            return False
        
        try:
            # Basic validation - check for required elements
            materials = self.document.getMaterialNodes()
            if not materials:
                self.logger.warning("No material nodes found in document")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Document validation failed: {str(e)}")
            return False


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
            'color3': ['color3', 'vector3'],
            'vector3': ['vector3', 'color3'],
            'vector2': ['vector2'],
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
        
        # Special cases
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
        try:
            if target_type == 'float':
                return float(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'boolean':
                return bool(value)
            elif target_type == 'string':
                return str(value)
            elif target_type == 'color3':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val, val]
            elif target_type == 'vector3':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val, val]
            elif target_type == 'vector2':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 2:
                        return [float(value[0]), float(value[1])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val]
            elif target_type == 'color4':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 4:
                        return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
                    elif len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2]), 1.0]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0]), 1.0]
                else:
                    val = float(value)
                    return [val, val, val, 1.0]
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error converting value {value} to type {target_type}: {str(e)}")
            return value
    
    def format_value_string(self, value: Any, value_type: str) -> str:
        """
        Format a value as a MaterialX value string.
        
        Args:
            value: The value to format
            value_type: The MaterialX type
            
        Returns:
            str: The formatted value string
        """
        try:
            if isinstance(value, (int, float)):
                return f"{value:.4g}"
            elif isinstance(value, (list, tuple)):
                # Handle vector/color types
                if value_type in ['color3', 'vector3'] and len(value) >= 3:
                    return f"{value[0]:.4g},{value[1]:.4g},{value[2]:.4g}"
                elif value_type in ['color4', 'vector4'] and len(value) >= 4:
                    return f"{value[0]:.4g},{value[1]:.4g},{value[2]:.4g},{value[3]:.4g}"
                elif value_type in ['vector2'] and len(value) >= 2:
                    return f"{value[0]:.4g},{value[1]:.4g}"
                else:
                    return ",".join(f"{v:.4g}" for v in value)
            else:
                return str(value)
                
        except Exception as e:
            self.logger.error(f"Error formatting value {value} for type {value_type}: {str(e)}")
            return str(value)


class MaterialXNodeBuilder:
    """
    Handles node creation using MaterialX library.
    
    This class provides:
    - Type-safe node creation with proper node definitions
    - Input/output handling with automatic type conversion
    - Connection management using mtlxutils
    - Value formatting and validation
    - Nodegraph creation and management
    """
    
    def __init__(self, document_manager: MaterialXDocumentManager, logger):
        self.doc_manager = document_manager
        self.logger = logger
        self.node_counter = 0
        self.created_nodes = {}
        self.type_converter = MaterialXTypeConverter(logger)
        
    def add_node(self, node_type: str, name: str, category: str = None, 
                 parent: mx.Element = None) -> Optional[mx.Node]:
        """
        Add a node to the document using MaterialX library.
        
        Args:
            node_type: The node type (e.g., 'standard_surface', 'mix')
            name: The node name
            category: Optional category (e.g., 'surfaceshader', 'color3')
            parent: Parent element (defaults to document root)
            
        Returns:
            mx.Node: The created node or None if failed
        """
        try:
            if not parent:
                parent = self.doc_manager.document
            
            # Generate unique name if needed
            if not name:
                name = f"{node_type}_{self.node_counter}"
                self.node_counter += 1
            
            # Create valid child name
            valid_name = parent.createValidChildName(name)
            
            # Get node definition
            if category:
                nodedef = self.doc_manager.get_node_definition(node_type, category)
            else:
                nodedef = self.doc_manager.get_node_definition(node_type)
            
            if not nodedef:
                self.logger.warning(f"No node definition found for {node_type} (category: {category})")
                return None
            
            # Create node instance
            node = parent.addNodeInstance(nodedef, valid_name)
            
            if node:
                self.created_nodes[valid_name] = node
                self.logger.debug(f"Created node: {valid_name} (type: {node_type})")
            
            return node
            
        except Exception as e:
            self.logger.error(f"Failed to create node {name} of type {node_type}: {str(e)}")
            return None
    
    def add_nodegraph(self, name: str, parent: mx.Element = None) -> Optional[mx.NodeGraph]:
        """
        Add a nodegraph to the document.
        
        Args:
            name: The nodegraph name
            parent: Parent element (defaults to document root)
            
        Returns:
            mx.NodeGraph: The created nodegraph or None if failed
        """
        try:
            if not parent:
                parent = self.doc_manager.document
            
            valid_name = parent.createValidChildName(name)
            nodegraph = parent.addChildOfCategory('nodegraph', valid_name)
            
            if nodegraph:
                self.created_nodes[valid_name] = nodegraph
                self.logger.debug(f"Created nodegraph: {valid_name}")
            
            return nodegraph
            
        except Exception as e:
            self.logger.error(f"Failed to create nodegraph {name}: {str(e)}")
            return None
    
    def create_mtlx_input(self, node: mx.Node, input_name: str, value: Any = None, 
                         nodename: str = None, node_type: str = None, category: str = None) -> Optional[mx.Input]:
        """
        Create a MaterialX input with type-safe handling.
        
        Args:
            node: The target node
            input_name: The input name
            value: The input value (for constant inputs)
            nodename: The connected node name (for connections)
            node_type: The node type for definition lookup
            category: The node category for definition lookup
            
        Returns:
            mx.Input: The created input or None if failed
        """
        try:
            # Get input definition for type information
            input_def = None
            if node_type:
                input_def = self.doc_manager.get_input_definition(node_type, input_name, category)
            
            # Determine input type
            if input_def:
                input_type = input_def.getType()
            else:
                # Fallback type determination
                input_type = self._get_input_type_from_name(input_name)
            
            # Create input
            input_elem = node.addInput(input_name, input_type)
            
            if input_elem:
                if value is not None:
                    # Convert and set constant value
                    converted_value = self.type_converter.convert_value(value, input_type)
                    formatted_value = self.type_converter.format_value_string(converted_value, input_type)
                    input_elem.setValueString(formatted_value)
                    self.logger.debug(f"Set input {input_name} = {formatted_value} (type: {input_type})")
                elif nodename:
                    # Set connection
                    input_elem.setNodeName(nodename)
                    self.logger.debug(f"Connected input {input_name} to {nodename}")
            
            return input_elem
            
        except Exception as e:
            self.logger.error(f"Failed to create input {input_name} for node {node.getName()}: {str(e)}")
            return None
    
    def add_input(self, node: mx.Node, input_name: str, input_type: str, 
                  value: Any = None, nodename: str = None) -> Optional[mx.Input]:
        """
        Add an input to a node (legacy method for backward compatibility).
        
        Args:
            node: The target node
            input_name: The input name
            input_type: The input type
            value: The input value (for constant inputs)
            nodename: The connected node name (for connections)
            
        Returns:
            mx.Input: The created input or None if failed
        """
        return self.create_mtlx_input(node, input_name, value, nodename)
    
    def add_output(self, nodegraph: mx.NodeGraph, name: str, output_type: str, 
                   nodename: str) -> Optional[mx.Output]:
        """
        Add an output to a nodegraph.
        
        Args:
            nodegraph: The target nodegraph
            name: The output name
            output_type: The output type
            nodename: The connected node name
            
        Returns:
            mx.Output: The created output or None if failed
        """
        try:
            valid_name = nodegraph.createValidChildName(name)
            output = nodegraph.addOutput(valid_name, output_type)
            
            if output:
                output.setNodeName(nodename)
                self.logger.debug(f"Added output {valid_name} connected to {nodename}")
            
            return output
            
        except Exception as e:
            self.logger.error(f"Failed to add output {name} to nodegraph {nodegraph.getName()}: {str(e)}")
            return None
    
    def connect_nodes(self, from_node: mx.Node, from_output: str, 
                     to_node: mx.Node, to_input: str) -> bool:
        """
        Connect two nodes with type validation.
        
        Args:
            from_node: The source node
            from_output: The source output name
            to_node: The target node
            to_input: The target input name
            
        Returns:
            bool: True if connection successful
        """
        try:
            # Get output and input definitions for type checking
            from_output_def = from_node.getActiveOutput(from_output)
            to_input_def = to_node.getActiveInput(to_input)
            
            if from_output_def and to_input_def:
                from_type = from_output_def.getType()
                to_type = to_input_def.getType()
                
                # Validate type compatibility
                if not self.type_converter.validate_type_compatibility(from_type, to_type):
                    self.logger.warning(f"Type mismatch in connection: {from_type} -> {to_type}")
                    return False
            
            # Use mtlxutils for connection
            success = mxg.MtlxNodeGraph.connectNodeToNode(to_node, to_input, from_node, from_output)
            
            if success:
                self.logger.debug(f"Connected {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input}")
            else:
                self.logger.warning(f"Failed to connect {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error connecting nodes: {str(e)}")
            return False
    
    def _get_input_type_from_name(self, input_name: str) -> str:
        """
        Get the expected type for an input based on its name.
        
        Args:
            input_name: The input name
            
        Returns:
            str: The expected input type
        """
        # Common input type mappings
        type_mapping = {
            'texcoord': 'vector2',
            'in': 'color3',
            'in1': 'color3',
            'in2': 'color3',
            'a': 'color3',
            'b': 'color3',
            'factor': 'float',
            'scale': 'float',
            'strength': 'float',
            'amount': 'float',
            'pivot': 'vector2',
            'translate': 'vector2',
            'rotate': 'float',
            'file': 'filename',
            'default': 'color3',
        }
        
        return type_mapping.get(input_name.lower(), 'color3')


class MaterialXConnectionManager:
    """
    Manages node connections and input/output handling.
    
    This class provides:
    - Connection validation
    - Type checking
    - Input/output mapping
    - Connection optimization
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.connections = []
        self.type_mapping = {
            'color3': ['color3', 'vector3'],
            'vector3': ['vector3', 'color3'],
            'vector2': ['vector2'],
            'float': ['float'],
            'filename': ['filename'],
            'string': ['string']
        }
    
    def validate_connection(self, from_type: str, to_type: str) -> bool:
        """
        Validate if a connection between types is valid.
        
        Args:
            from_type: The source type
            to_type: The target type
            
        Returns:
            bool: True if connection is valid
        """
        # Direct type match
        if from_type == to_type:
            return True
        
        # Check type compatibility
        if from_type in self.type_mapping:
            compatible_types = self.type_mapping[from_type]
            if to_type in compatible_types:
                return True
        
        # Special cases
        if from_type == 'color3' and to_type == 'vector3':
            return True
        if from_type == 'vector3' and to_type == 'color3':
            return True
        
        self.logger.warning(f"Type mismatch: {from_type} -> {to_type}")
        return False
    
    def get_input_type(self, input_name: str, node_type: str) -> str:
        """
        Get the expected type for an input based on its name and node type.
        
        Args:
            input_name: The input name
            node_type: The node type
            
        Returns:
            str: The expected input type
        """
        # Common input type mappings
        type_mapping = {
            'texcoord': 'vector2',
            'in': 'color3',
            'in1': 'color3',
            'in2': 'color3',
            'a': 'color3',
            'b': 'color3',
            'factor': 'float',
            'scale': 'float',
            'strength': 'float',
            'amount': 'float',
            'pivot': 'vector2',
            'translate': 'vector2',
            'rotate': 'float',
            'file': 'filename',
            'default': 'color3',
        }
        
        return type_mapping.get(input_name.lower(), 'color3')
    
    def record_connection(self, from_node: str, from_output: str, 
                         to_node: str, to_input: str):
        """
        Record a connection for later analysis.
        
        Args:
            from_node: Source node name
            from_output: Source output name
            to_node: Target node name
            to_input: Target input name
        """
        connection = {
            'from_node': from_node,
            'from_output': from_output,
            'to_node': to_node,
            'to_input': to_input
        }
        self.connections.append(connection)
    
    def get_connection_count(self, node_name: str) -> int:
        """
        Get the number of connections for a node.
        
        Args:
            node_name: The node name
            
        Returns:
            int: The number of connections
        """
        count = 0
        for conn in self.connections:
            if conn['from_node'] == node_name or conn['to_node'] == node_name:
                count += 1
        return count


class MaterialXLibraryBuilder:
    """
    Builds MaterialX documents using the MaterialX library.
    
    This is the main builder class that replaces the manual XML generation
    with proper MaterialX library APIs.
    """
    
    def __init__(self, material_name: str, logger, version: str = "1.38"):
        self.material_name = material_name
        self.version = version
        self.logger = logger
        
        # Initialize core components
        self.doc_manager = MaterialXDocumentManager(logger, version)
        self.node_builder = MaterialXNodeBuilder(self.doc_manager, logger)
        self.connection_manager = MaterialXConnectionManager(logger)
        
        # Create document
        self.document = self.doc_manager.create_document()
        
        # Track created elements
        self.material_node = None
        self.nodegraph = None
        self.surface_shader = None
        
        # Legacy compatibility
        self.nodes = {}  # For backward compatibility
        self.connections = []
        self.node_counter = 0
        
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """
        Add a node to the nodegraph (legacy compatibility method).
        
        Args:
            node_type: The node type
            name: The node name
            node_type_category: The node category
            **params: Node parameters
            
        Returns:
            str: The created node name
        """
        # Ensure nodegraph exists
        if not self.nodegraph:
            self.nodegraph = self.node_builder.add_nodegraph(self.material_name, self.document)
        
        # Create node
        node = self.node_builder.add_node(node_type, name, node_type_category, self.nodegraph)
        
        if node:
            node_name = node.getName()
            self.nodes[node_name] = node
            
            # Add parameters as inputs using type-safe method
            for param_name, param_value in params.items():
                if param_value is not None:
                    self.node_builder.create_mtlx_input(
                        node, param_name, param_value, 
                        node_type=node_type, category=node_type_category
                    )
            
            return node_name
        else:
            # Fallback: create a placeholder node
            placeholder_name = f"placeholder_{node_type}_{self.node_counter}"
            self.node_counter += 1
            self.logger.warning(f"Created placeholder node: {placeholder_name}")
            return placeholder_name
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """
        Add a surface shader node outside the nodegraph.
        
        Args:
            node_type: The node type
            name: The node name
            **params: Node parameters
            
        Returns:
            str: The created node name
        """
        # Create surface shader node at document level
        node = self.node_builder.add_node(node_type, name, 'surfaceshader', self.document)
        
        if node:
            node_name = node.getName()
            self.nodes[node_name] = node
            self.surface_shader = node
            
            # Add parameters as inputs using type-safe method
            for param_name, param_value in params.items():
                if param_value is not None:
                    self.node_builder.create_mtlx_input(
                        node, param_name, param_value, 
                        node_type=node_type, category='surfaceshader'
                    )
            
            return node_name
        else:
            return f"surface_{node_type}_{self.node_counter}"
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """
        Add a connection between nodes.
        
        Args:
            from_node: Source node name
            from_output: Source output name
            to_node: Target node name
            to_input: Target input name
        """
        from_node_elem = self.nodes.get(from_node)
        to_node_elem = self.nodes.get(to_node)
        
        if from_node_elem and to_node_elem:
            success = self.node_builder.connect_nodes(from_node_elem, from_output, to_node_elem, to_input)
            if success:
                self.connection_manager.record_connection(from_node, from_output, to_node, to_input)
                self.connections.append((from_node, from_output, to_node, to_input))
        else:
            self.logger.warning(f"Connection failed: {from_node}.{from_output} -> {to_node}.{to_input}")
    
    def add_surface_shader_input(self, surface_node_name: str, input_name: str, input_type: str, 
                                nodegraph_name: str = None, nodename: str = None, value: str = None):
        """
        Add an input to a surface shader node.
        
        Args:
            surface_node_name: The surface shader node name
            input_name: The input name
            input_type: The input type
            nodegraph_name: The connected nodegraph name
            nodename: The connected node name
            value: The input value
        """
        surface_node = self.nodes.get(surface_node_name)
        if not surface_node:
            self.logger.warning(f"Surface shader node '{surface_node_name}' not found")
            return
        
        if nodegraph_name:
            # Connect to nodegraph output
            if self.nodegraph:
                output = self.node_builder.add_output(self.nodegraph, input_name, input_type, nodename or input_name)
        elif nodename:
            # Connect to specific node
            self.node_builder.create_mtlx_input(surface_node, input_name, nodename=nodename)
        elif value is not None:
            # Set constant value
            self.node_builder.create_mtlx_input(surface_node, input_name, value)
    
    def add_output(self, name: str, output_type: str, nodename: str):
        """
        Add an output node to the nodegraph.
        
        Args:
            name: The output name
            output_type: The output type
            nodename: The connected node name
        """
        if self.nodegraph:
            self.node_builder.add_output(self.nodegraph, name, output_type, nodename)
    
    def set_material_surface(self, surface_node_name: str):
        """
        Set the surface shader for the material.
        
        Args:
            surface_node_name: The surface shader node name
        """
        if not self.material_node:
            # Create material node
            self.material_node = self.node_builder.add_node('surfacematerial', self.material_name, 'material', self.document)
        
        if self.material_node and self.surface_shader:
            # Connect material to surface shader
            self.node_builder.create_mtlx_input(self.material_node, 'surfaceshader', nodename=surface_node_name)
    
    def _get_param_type(self, value) -> str:
        """
        Determine the MaterialX type for a value.
        
        Args:
            value: The value to type-check
            
        Returns:
            str: The MaterialX type
        """
        if isinstance(value, (int, float)):
            return "float"
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                return "vector2"
            elif len(value) == 3:
                return "color3"
            elif len(value) == 4:
                return "color4"
        return "string"
    
    def to_string(self) -> str:
        """
        Convert the document to a formatted XML string.
        
        Returns:
            str: The formatted XML string
        """
        try:
            # Use mtlxutils for writing
            content = mxf.MtlxFile.writeDocumentToString(self.document)
            return content
        except Exception as e:
            self.logger.error(f"Failed to convert document to string: {str(e)}")
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
            # Use mtlxutils for writing
            mxf.MtlxFile.writeDocumentToFile(self.document, filepath)
            self.logger.info(f"Successfully wrote MaterialX document to: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write document to file: {str(e)}")
            return False
    
    def validate(self) -> bool:
        """
        Validate the MaterialX document.
        
        Returns:
            bool: True if document is valid
        """
        return self.doc_manager.validate_document() 