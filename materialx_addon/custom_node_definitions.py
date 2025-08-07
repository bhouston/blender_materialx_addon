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


class CustomNodeDefinitionManager:
    """Manages custom node definitions and their nodegraph implementations."""
    
    def __init__(self, document: mx.Document, logger):
        self.document = document
        self.logger = logger
        self.custom_node_defs = {}
        self._initialize_custom_definitions()
    
    def _initialize_custom_definitions(self):
        """Initialize all custom node definitions."""
        self._add_brick_texture_definition()
        # Add more custom definitions here as needed
    
    def _add_brick_texture_definition(self):
        """Add Brick Texture node definition and implementation."""
        
        # Check if the node definition already exists
        existing_nodedef = self.document.getNodeDef("ND_brick_texture")
        if existing_nodedef:
            self.logger.info("Brick texture node definition already exists, skipping creation")
            self.custom_node_defs["brick_texture"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_brick_texture")
            }
            return
        
        # Node Definition
        brick_nodedef = self.document.addNodeDef("ND_brick_texture", "color3", "brick_texture")
        brick_nodedef.setNodeGroup("texture2d")
        brick_nodedef.setAttribute("version", "1.0")
        brick_nodedef.setAttribute("description", "Brick texture node for Blender compatibility")
        
        # Inputs
        inputs = [
            ("texcoord", "vector2", "0,0", "Texture coordinates"),
            ("color1", "color3", "0.8,0.8,0.8", "First brick color"),
            ("color2", "color3", "0.2,0.2,0.2", "Second brick color"),
            ("mortar", "color3", "0.2,0.2,0.2", "Mortar color"),
            ("scale", "float", "5.0", "Scale of the brick pattern"),
            ("mortar_size", "float", "0.02", "Size of mortar lines"),
            ("bias", "float", "0.0", "Bias for brick offset"),
            ("brick_width", "float", "0.5", "Width of bricks (0-1)"),
            ("row_height", "float", "0.25", "Height of brick rows (0-1)")
        ]
        
        for name, type_str, default_value, description in inputs:
            input_elem = brick_nodedef.addInput(name, type_str)
            input_elem.setValueString(default_value)
            input_elem.setAttribute("description", description)
        
        # Output - check if it already exists to avoid conflicts
        existing_output = brick_nodedef.getOutput("out")
        if existing_output is None:
            output = brick_nodedef.addOutput("out", "color3")
            output.setAttribute("description", "Brick texture output")
        else:
            self.logger.info("Brick texture output already exists, skipping creation")
        
        # Implementation NodeGraph
        brick_impl = self.document.addNodeGraph("IM_brick_texture")
        brick_impl.setAttribute("description", "Brick texture implementation")
        
        # Create the brick texture implementation
        self._create_brick_texture_implementation(brick_impl)
        
        # Link implementation to node definition
        brick_nodedef.setImplementation("IM_brick_texture")
        
        # Store for later use
        self.custom_node_defs["brick_texture"] = {
            "nodedef": brick_nodedef,
            "implementation": brick_impl
        }
        
        self.logger.info("Added Brick Texture custom node definition")
    
    def _create_brick_texture_implementation(self, nodegraph: mx.NodeGraph):
        """Create the nodegraph implementation for brick texture."""
        
        # Create nodes for brick texture calculation
        
        # 1. Scale the texture coordinates
        scale_node = nodegraph.addNode("multiply", "scale_texcoord")
        scale_node.setType("vector2")
        
        # 2. Extract X and Y components from scaled coordinates
        x_extract = nodegraph.addNode("separate2", "x_extract")
        x_extract.setType("float")
        
        y_extract = nodegraph.addNode("separate2", "y_extract")
        y_extract.setType("float")
        
        # 3. Create brick pattern using modulo operations
        # X coordinate modulo for brick width
        x_mod_node = nodegraph.addNode("modulo", "x_modulo")
        x_mod_node.setType("float")
        
        # Y coordinate modulo for row height
        y_mod_node = nodegraph.addNode("modulo", "y_modulo")
        y_mod_node.setType("float")
        
        # 4. Add offset for brick staggering
        offset_node = nodegraph.addNode("add", "brick_offset")
        offset_node.setType("float")
        
        # 5. Create mortar masks
        mortar_x_node = nodegraph.addNode("ifgreater", "mortar_mask_x")
        mortar_x_node.setType("float")
        
        mortar_y_node = nodegraph.addNode("ifgreater", "mortar_mask_y")
        mortar_y_node.setType("float")
        
        # 6. Combine mortar masks
        mortar_combine = nodegraph.addNode("multiply", "mortar_mask")
        mortar_combine.setType("float")
        
        # 7. Select brick color based on position
        color_select = nodegraph.addNode("ifgreater", "brick_color_select")
        color_select.setType("color3")
        
        # 8. Mix brick and mortar colors
        final_mix = nodegraph.addNode("mix", "final_color")
        final_mix.setType("color3")
        
        # Set up connections
        # Scale texture coordinates
        scale_node.addInput("in1", "vector2").setNodeName("texcoord")
        scale_node.addInput("in2", "vector2").setValue(mx.Vector2(5.0, 5.0))
        
        # Extract X and Y components
        x_extract.addInput("in", "vector2").setNodeName("scale_texcoord")
        y_extract.addInput("in", "vector2").setNodeName("scale_texcoord")
        
        # X modulo
        x_mod_node.addInput("in1", "float").setNodeName("x_extract")
        x_mod_node.addInput("in2", "float").setValue(1.0)
        
        # Y modulo
        y_mod_node.addInput("in1", "float").setNodeName("y_extract")
        y_mod_node.addInput("in2", "float").setValue(1.0)
        
        # Brick offset
        offset_node.addInput("in1", "float").setNodeName("y_modulo")
        offset_node.addInput("in2", "float").setValue(0.5)
        
        # Mortar mask X
        mortar_x_node.addInput("in1", "float").setNodeName("x_modulo")
        mortar_x_node.addInput("in2", "float").setValue(0.02)
        mortar_x_node.addInput("value1", "float").setValue(1.0)
        mortar_x_node.addInput("value2", "float").setValue(0.0)
        
        # Mortar mask Y
        mortar_y_node.addInput("in1", "float").setNodeName("y_modulo")
        mortar_y_node.addInput("in2", "float").setValue(0.02)
        mortar_y_node.addInput("value1", "float").setValue(1.0)
        mortar_y_node.addInput("value2", "float").setValue(0.0)
        
        # Combine mortar masks
        mortar_combine.addInput("in1", "float").setNodeName("mortar_mask_x")
        mortar_combine.addInput("in2", "float").setNodeName("mortar_mask_y")
        
        # Select brick color
        color_select.addInput("in1", "float").setNodeName("x_modulo")
        color_select.addInput("in2", "float").setValue(0.5)
        color_select.addInput("value1", "color3").setNodeName("color1")
        color_select.addInput("value2", "color3").setNodeName("color2")
        
        # Final color mix
        final_mix.addInput("in1", "color3").setNodeName("brick_color_select")
        final_mix.addInput("in2", "color3").setNodeName("mortar")
        final_mix.addInput("mix", "float").setNodeName("mortar_mask")
        
        # Set output
        nodegraph.addOutput("out", "color3").setNodeName("final_color")
        
        self.logger.debug("Created Brick Texture implementation nodegraph")
    
    def get_custom_node_definition(self, node_type: str) -> Optional[mx.NodeDef]:
        """Get a custom node definition by type."""
        if node_type in self.custom_node_defs:
            return self.custom_node_defs[node_type]["nodedef"]
        return None
    
    def has_custom_definition(self, node_type: str) -> bool:
        """Check if a custom definition exists for the given node type."""
        return node_type in self.custom_node_defs
    
    def get_all_custom_types(self) -> List[str]:
        """Get all available custom node types."""
        return list(self.custom_node_defs.keys())
    
    def add_custom_node_to_document(self, node_type: str, node_name: str, parent: mx.Element) -> Optional[mx.Node]:
        """Add a custom node to the document."""
        if not self.has_custom_definition(node_type):
            self.logger.error(f"No custom definition found for node type: {node_type}")
            return None
        
        try:
            # Create the node
            custom_node = parent.addChildOfCategory(node_type, node_name)
            if not custom_node:
                self.logger.error(f"Failed to create custom node: {node_name}")
                return None
            
            # Set the node definition
            nodedef = self.get_custom_node_definition(node_type)
            if nodedef:
                custom_node.setNodeDefString(nodedef.getName())
            
            self.logger.debug(f"Created custom node: {node_name} of type {node_type}")
            return custom_node
            
        except Exception as e:
            self.logger.error(f"Failed to add custom node {node_name}: {str(e)}")
            return None


# Registry of Blender node types that need custom definitions
BLENDER_CUSTOM_NODE_TYPES = {
    "TEX_BRICK": "brick_texture",
    # Add more mappings as needed
}


def get_custom_node_type(blender_node_type: str) -> Optional[str]:
    """Get the custom MaterialX node type for a Blender node type."""
    return BLENDER_CUSTOM_NODE_TYPES.get(blender_node_type)


def is_custom_node_type(blender_node_type: str) -> bool:
    """Check if a Blender node type requires a custom definition."""
    return blender_node_type in BLENDER_CUSTOM_NODE_TYPES
