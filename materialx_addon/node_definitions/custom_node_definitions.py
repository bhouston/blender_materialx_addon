#!/usr/bin/env python3
"""
Custom Node Definitions for Blender MaterialX Exporter

This module provides custom node definitions and nodegraphs for Blender nodes
that don't have direct equivalents in the MaterialX standard library.

The system uses MaterialX's functional nodegraph system to define custom nodes
as compositions of standard MaterialX nodes.
"""

import MaterialX as mx
from typing import Dict, List, Optional, Any, Tuple

from .type_conversions import TYPE_CONVERSION_CONFIGS
from .texture_definitions import TextureDefinitionManager


class CustomNodeDefinitionManager:
    """Manages custom node definitions and their nodegraph implementations."""
    
    # Class-level counter to track total initializations
    _total_initializations = 0
    _total_node_defs_created = 0
    
    def __init__(self, document: mx.Document, logger):
        """Initialize the custom node definition manager."""
        self.document = document
        self.logger = logger
        self.custom_node_defs = {}
        
        # Increment initialization counter
        CustomNodeDefinitionManager._total_initializations += 1
        self.logger.info(f"=== CUSTOM NODE MANAGER: Initialization #{CustomNodeDefinitionManager._total_initializations} ===")
        self.logger.info(f"=== CUSTOM NODE MANAGER: Document has {len(document.getNodeDefs())} existing node definitions ===")
        self.logger.info(f"=== CUSTOM NODE MANAGER: Document has {len(document.getNodeGraphs())} existing node graphs ===")
        
        # Initialize sub-managers
        self.texture_manager = TextureDefinitionManager(document, logger)
        
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Manager created ===")
        
        # Initialize custom definitions
        self._initialize_custom_definitions()
    
    def _initialize_custom_definitions(self):
        """Initialize all custom node definitions."""
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Starting initialization ===")
        
        # First, populate any existing definitions
        self._populate_existing_definitions()
        
        # Add texture definitions
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Adding texture definitions ===")
        self._add_texture_definitions()
        
        # Add curve RGB definition
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Adding curve RGB definition ===")
        self._add_curve_rgb_definition()
        
        # Add type conversion definitions using configuration
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Adding type conversion definitions ===")
        self._add_type_conversion_definitions()
        
        self.logger.info(f"=== CUSTOM NODE DEFINITIONS: Initialization completed. Total definitions: {len(self.custom_node_defs)} ===")
    
    def _populate_existing_definitions(self):
        """Populate custom_node_defs with existing definitions from the document."""
        # Find existing custom node definitions
        for nodedef in self.document.getNodeDefs():
            name = nodedef.getName()
            if name.startswith("ND_"):
                if "brick_texture" in name:
                    self.custom_node_defs["brick_texture"] = {
                        "nodedef": nodedef,
                        "implementation": self.document.getNodeGraph("IM_brick_texture")
                    }
                elif "curvelookup" in name:
                    self.custom_node_defs["curvelookup"] = {
                        "nodedef": nodedef,
                        "implementation": self.document.getNodeGraph("IM_curvelookup")
                    }
                # Handle type conversions using configuration
                for conv_name in TYPE_CONVERSION_CONFIGS.keys():
                    if conv_name in name:
                        impl_name = f"IM_{conv_name}_{TYPE_CONVERSION_CONFIGS[conv_name]['output_type']}"
                        self.custom_node_defs[conv_name] = {
                            "nodedef": nodedef,
                            "implementation": self.document.getNodeGraph(impl_name)
                        }
                        break
        
        self.logger.info(f"Populated {len(self.custom_node_defs)} existing custom node definitions")
    
    def _add_texture_definitions(self):
        """Add texture-related node definitions."""
        self.texture_manager.add_brick_texture_definition()
        self.texture_manager.add_voronoi_texture_definition()
        
        # Merge texture definitions into main dictionary
        for texture_type, texture_data in self.texture_manager.texture_defs.items():
            self.custom_node_defs[texture_type] = texture_data
    
    def _add_curve_rgb_definition(self):
        """Add custom Curve RGB node definition."""
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Starting curve RGB definition creation ===")
        
        # Check if the node definition already exists
        existing_nodedef, existing_impl = self._check_existing_definition("curvelookup", "color3")
        if existing_nodedef and existing_impl:
            self.logger.info("=== CUSTOM NODE DEFINITIONS: Using existing curve RGB definition ===")
            self.custom_node_defs["curvelookup"] = {
                "nodedef": existing_nodedef,
                "implementation": existing_impl
            }
            return
        elif existing_nodedef and not existing_impl:
            # Node definition exists but implementation is missing - skip creation to avoid conflicts
            self.logger.warning("=== CUSTOM NODE DEFINITIONS: Curve RGB node definition exists but implementation is missing - skipping to avoid conflicts ===")
            return
        
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Creating new curve RGB definition ===")
        
        # Node Definition
        CustomNodeDefinitionManager._total_node_defs_created += 1
        self.logger.info(f"=== CUSTOM NODE MANAGER: Creating node definition #{CustomNodeDefinitionManager._total_node_defs_created} ===")
        self.logger.info(f"=== CUSTOM NODE MANAGER: Adding 'ND_curvelookup_color3' to document ===")
        
        nodedef = self.document.addNodeDef("ND_curvelookup_color3", "color3", "curvelookup")
        nodedef.setNodeGroup("adjustment")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "RGB curve adjustment")
        
        # Inputs
        try:
            input_elem = nodedef.addInput("in", "color3")
            input_elem.setAttribute("description", "Input color")
        except Exception as e:
            self.logger.error(f"Failed to add input for curve RGB definition: {e}")
            return
        
        # Output
        try:
            output = nodedef.addOutput("out", "color3")
            output.setAttribute("description", "Curve-adjusted color")
        except Exception as e:
            # If output already exists, try a different name
            self.logger.warning(f"Output 'out' already exists for curve RGB definition, trying 'result': {e}")
            try:
                output = nodedef.addOutput("result", "color3")
                output.setAttribute("description", "Curve-adjusted color")
            except Exception as e2:
                self.logger.error(f"Failed to add output for curve RGB definition: {e2}")
                return
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_curvelookup")
        impl.setAttribute("description", "RGB curve implementation")
        
        # Create the implementation
        self._create_curve_rgb_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_curvelookup")
        
        # Store for later use
        self.custom_node_defs["curvelookup"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("=== CUSTOM NODE DEFINITIONS: Successfully created curve RGB definition ===")
    
    def _create_curve_rgb_implementation(self, nodegraph: mx.NodeGraph):
        """Create the nodegraph implementation for RGB curve adjustment."""
        # For now, create a simple pass-through implementation
        # In a real implementation, this would use proper curve interpolation
        
        # Input node
        input_node = nodegraph.addNode("color3", "curve_input")
        input_node.setType("color3")
        
        # Connect input
        input_input = input_node.addInput("in", "color3")
        input_input.setNodeName("in")
        
        # Output (pass-through for now)
        output = nodegraph.addOutput("out", "color3")
        output.setNodeName("curve_input.out")
    
    def _add_type_conversion_definitions(self):
        """Add all type conversion node definitions."""
        for conv_name, conv_config in TYPE_CONVERSION_CONFIGS.items():
            self._add_type_conversion_definition(conv_name, conv_config)
    
    def _add_type_conversion_definition(self, conv_name: str, conv_config: Dict):
        """Add a single type conversion node definition using configuration."""
        
        # Check if already exists
        existing_nodedef, existing_impl = self._check_existing_definition(conv_name, conv_config["output_type"])
        if existing_nodedef and existing_impl:
            self.custom_node_defs[conv_name] = {
                "nodedef": existing_nodedef,
                "implementation": existing_impl
            }
            return
        elif existing_nodedef and not existing_impl:
            # Node definition exists but implementation is missing - skip creation to avoid conflicts
            self.logger.warning(f"{conv_name} node definition exists but implementation is missing - skipping to avoid conflicts")
            return
        
        # Node Definition
        CustomNodeDefinitionManager._total_node_defs_created += 1
        node_def_name = f"ND_{conv_name}_{conv_config['output_type']}"
        self.logger.info(f"=== CUSTOM NODE MANAGER: Creating node definition #{CustomNodeDefinitionManager._total_node_defs_created} ===")
        self.logger.info(f"=== CUSTOM NODE MANAGER: Adding '{node_def_name}' to document ===")
        
        nodedef = self.document.addNodeDef(node_def_name, conv_config["output_type"], conv_name)
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", conv_config["description"])
        
        # Input
        input_elem = nodedef.addInput("in", conv_config["input_type"])
        input_elem.setAttribute("description", conv_config["input_description"])
        
        # Output
        try:
            output = nodedef.addOutput("out", conv_config["output_type"])
            output.setAttribute("description", conv_config["output_description"])
        except Exception as e:
            # If output already exists, try a different name
            self.logger.warning(f"Output 'out' already exists for {conv_name} definition, trying 'result': {e}")
            try:
                output = nodedef.addOutput("result", conv_config["output_type"])
                output.setAttribute("description", conv_config["output_description"])
            except Exception as e2:
                self.logger.error(f"Failed to add output for {conv_name} definition: {e2}")
                return
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph(f"IM_{conv_name}_{conv_config['output_type']}")
        impl.setAttribute("description", f"{conv_name} implementation")
        
        # Create the implementation
        self._create_type_conversion_implementation(impl, conv_config)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", f"IM_{conv_name}_{conv_config['output_type']}")
        
        # Store for later use
        self.custom_node_defs[conv_name] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info(f"Added {conv_name} conversion node definition")
    
    def _create_type_conversion_implementation(self, nodegraph: mx.NodeGraph, conv_config: Dict):
        """Create the implementation for a type conversion using separate and combine nodes."""
        
        # Input node
        input_node = nodegraph.addNode(conv_config["implementation"]["separate_node"]["type"], conv_config["implementation"]["separate_node"]["name"])
        input_node.setType(conv_config["input_type"])
        
        # Connect input
        input_input = input_node.addInput("in", conv_config["input_type"])
        input_input.setNodeName("in")
        
        # Combine outputs
        combine_node = nodegraph.addNode(conv_config["implementation"]["combine_node"]["type"], conv_config["implementation"]["combine_node"]["name"])
        combine_node.setType(conv_config["output_type"])
        
        # Connect inputs
        for i, output_name in enumerate(conv_config["implementation"]["combine_inputs"]):
            if output_name == "0": # For vector2/vector3 with Z=0
                combine_node.addInput(f"in{i + 1}", "float").setValueString("0.0")
            elif output_name == "1": # For vector4/color4 with W=1
                combine_node.addInput(f"in{i + 1}", "float").setValueString("1.0")
            else: # Connect to separate node output
                combine_node.addInput(f"in{i + 1}", "float").setNodeName(f"{conv_config['implementation']['separate_node']['name']}.{output_name}")
        
        # Output
        output = nodegraph.addOutput("out", conv_config["output_type"])
        output.setNodeName(conv_config["implementation"]["combine_node"]["name"])
    
    def _check_existing_definition(self, base_name: str, node_type: str) -> tuple[Optional[mx.NodeDef], Optional[mx.NodeGraph]]:
        """Check if a node definition already exists."""
        nodedef_name = f"ND_{base_name}_{node_type}"
        impl_name = f"IM_{base_name}"
        
        existing_nodedef = self.document.getNodeDef(nodedef_name)
        existing_impl = self.document.getNodeGraph(impl_name)
        
        return existing_nodedef, existing_impl
    
    def get_custom_node_definition(self, node_type: str) -> Optional[mx.NodeDef]:
        """Get a custom node definition by type."""
        if node_type in self.custom_node_defs:
            return self.custom_node_defs[node_type]["nodedef"]
        return None
    
    def has_custom_definition(self, node_type: str) -> bool:
        """Check if a custom definition exists."""
        return node_type in self.custom_node_defs
    
    def get_all_custom_types(self) -> List[str]:
        """Get all available custom node types."""
        return list(self.custom_node_defs.keys())
    
    def add_custom_node_to_document(self, node_type: str, node_name: str, parent: mx.Element) -> Optional[mx.Node]:
        """Add a custom node to the document."""
        if node_type not in self.custom_node_defs:
            self.logger.warning(f"Custom node type '{node_type}' not found")
            return None
        
        try:
            # Create the node
            node = parent.addNode(node_type, node_name)
            
            # Set the node definition
            nodedef = self.custom_node_defs[node_type]["nodedef"]
            node.setNodeDefString(nodedef.getName())
            
            self.logger.info(f"Added custom node '{node_name}' of type '{node_type}'")
            return node
            
        except Exception as e:
            self.logger.error(f"Failed to add custom node '{node_name}' of type '{node_type}': {e}")
            return None


def get_custom_node_type(blender_node_type: str) -> Optional[str]:
    """Get the MaterialX custom node type for a Blender node type."""
    # Mapping from Blender node types to custom MaterialX node types
    custom_node_mapping = {
        'BRICK_TEXTURE': 'brick_texture',
        'CURVE_RGB': 'curvelookup',
        'VORONOI_TEXTURE': 'voronoi'
    }
    
    return custom_node_mapping.get(blender_node_type)


def is_custom_node_type(blender_node_type: str) -> bool:
    """Check if a Blender node type has a custom MaterialX equivalent."""
    return get_custom_node_type(blender_node_type) is not None
