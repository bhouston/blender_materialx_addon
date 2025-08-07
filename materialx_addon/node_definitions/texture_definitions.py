#!/usr/bin/env python3
"""
Texture Node Definitions

This module contains texture-related node definitions for the MaterialX addon.
"""

import MaterialX as mx
from typing import Dict, Optional


class TextureDefinitionManager:
    """Manages texture-related node definitions."""
    
    def __init__(self, document: mx.Document, logger):
        """Initialize the texture definition manager."""
        self.document = document
        self.logger = logger
        self.texture_defs = {}
    
    def add_brick_texture_definition(self):
        """Add brick texture node definition and implementation."""
        self.logger.info("=== TEXTURE DEFINITIONS: Adding brick texture definition ===")
        
        # Check if already exists
        existing_nodedef, existing_impl = self._check_existing_definition("brick_texture", "color3")
        if existing_nodedef and existing_impl:
            self.texture_defs["brick_texture"] = {
                "nodedef": existing_nodedef,
                "implementation": existing_impl
            }
            return
        elif existing_nodedef and not existing_impl:
            self.logger.warning("Brick texture node definition exists but implementation is missing - skipping to avoid conflicts")
            return
        
        # Node Definition
        nodedef = self.document.addNodeDef("ND_brick_texture_color3", "color3", "brick_texture")
        nodedef.setNodeGroup("texture")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Brick texture pattern")
        
        # Inputs
        texcoord_input = nodedef.addInput("texcoord", "vector2")
        texcoord_input.setAttribute("description", "Texture coordinates")
        
        color1_input = nodedef.addInput("color1", "color3")
        color1_input.setAttribute("description", "First brick color")
        color1_input.setValueString("0.8,0.2,0.2")
        
        color2_input = nodedef.addInput("color2", "color3")
        color2_input.setAttribute("description", "Second brick color")
        color2_input.setValueString("0.2,0.2,0.8")
        
        mortar_input = nodedef.addInput("mortar", "color3")
        mortar_input.setAttribute("description", "Mortar color")
        mortar_input.setValueString("0.5,0.5,0.5")
        
        # Output
        output = nodedef.addOutput("out", "color3")
        output.setAttribute("description", "Brick texture output")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_brick_texture")
        impl.setAttribute("description", "Brick texture implementation")
        
        # Create the implementation
        self._create_brick_texture_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_brick_texture")
        
        # Store for later use
        self.texture_defs["brick_texture"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Brick Texture node definition")
    
    def add_voronoi_texture_definition(self):
        """Add Voronoi Texture node definition and implementation."""
        self.logger.info("=== TEXTURE DEFINITIONS: Adding voronoi texture definition ===")
        
        # Check if already exists
        existing_nodedef, existing_impl = self._check_existing_definition("voronoi", "color3")
        if existing_nodedef and existing_impl:
            self.texture_defs["voronoi"] = {
                "nodedef": existing_nodedef,
                "implementation": existing_impl
            }
            return
        elif existing_nodedef and not existing_impl:
            self.logger.warning("Voronoi texture node definition exists but implementation is missing - skipping to avoid conflicts")
            return
        
        # Node Definition
        nodedef = self.document.addNodeDef("ND_voronoi_color3", "color3", "voronoi")
        nodedef.setNodeGroup("texture")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Voronoi texture pattern")
        
        # Inputs
        input_elem = nodedef.addInput("position", "vector2")
        input_elem.setAttribute("description", "Texture coordinates")
        
        # Output
        output = nodedef.addOutput("out", "color3")
        output.setAttribute("description", "Voronoi texture output")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_voronoi_color3")
        impl.setAttribute("description", "Voronoi texture implementation")
        
        # Create the implementation
        self._create_voronoi_texture_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_voronoi_color3")
        
        # Store for later use
        self.texture_defs["voronoi"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Voronoi Texture node definition")
    
    def _check_existing_definition(self, base_name: str, node_type: str) -> tuple[Optional[mx.NodeDef], Optional[mx.NodeGraph]]:
        """Check if a node definition already exists."""
        nodedef_name = f"ND_{base_name}_{node_type}"
        impl_name = f"IM_{base_name}"
        
        existing_nodedef = self.document.getNodeDef(nodedef_name)
        existing_impl = self.document.getNodeGraph(impl_name)
        
        return existing_nodedef, existing_impl
    
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
        scale_node.addInput("in2", "vector2").setValueString("5.0,5.0")
        
        # Extract X and Y components
        x_extract.addInput("in", "vector2").setNodeName("scale_texcoord")
        y_extract.addInput("in", "vector2").setNodeName("scale_texcoord")
        
        # X modulo
        x_mod_node.addInput("in1", "float").setNodeName("x_extract")
        x_mod_node.addInput("in2", "float").setValueString("1.0")
        
        # Y modulo
        y_mod_node.addInput("in1", "float").setNodeName("y_extract")
        y_mod_node.addInput("in2", "float").setValueString("1.0")
        
        # Brick offset
        offset_node.addInput("in1", "float").setNodeName("y_modulo")
        offset_node.addInput("in2", "float").setValueString("0.5")
        
        # Mortar mask X
        mortar_x_node.addInput("in1", "float").setNodeName("x_modulo")
        mortar_x_node.addInput("in2", "float").setValueString("0.02")
        mortar_x_node.addInput("value1", "float").setValueString("1.0")
        mortar_x_node.addInput("value2", "float").setValueString("0.0")
        
        # Mortar mask Y
        mortar_y_node.addInput("in1", "float").setNodeName("y_modulo")
        mortar_y_node.addInput("in2", "float").setValueString("0.02")
        mortar_y_node.addInput("value1", "float").setValueString("1.0")
        mortar_y_node.addInput("value2", "float").setValueString("0.0")
        
        # Combine mortar masks
        mortar_combine.addInput("in1", "float").setNodeName("mortar_mask_x")
        mortar_combine.addInput("in2", "float").setNodeName("mortar_mask_y")
        
        # Select brick color
        color_select.addInput("in1", "float").setNodeName("x_modulo")
        color_select.addInput("in2", "float").setValueString("0.5")
        color_select.addInput("value1", "color3").setNodeName("color1")
        color_select.addInput("value2", "color3").setNodeName("color2")
        
        # Final color mix
        final_mix.addInput("in1", "color3").setNodeName("brick_color_select")
        final_mix.addInput("in2", "color3").setNodeName("mortar")
        final_mix.addInput("mix", "float").setNodeName("mortar_mask")
        
        # Set output
        nodegraph.addOutput("out", "color3").setNodeName("final_color")
        
        self.logger.debug("Created Brick Texture implementation nodegraph")
    
    def _create_voronoi_texture_implementation(self, nodegraph: mx.NodeGraph):
        """Create the nodegraph implementation for voronoi texture."""
        # For now, create a simple implementation using noise as a placeholder
        # In a real implementation, this would use proper voronoi cell calculation
        
        # Input node
        input_node = nodegraph.addNode("position", "voronoi_input")
        input_node.setType("vector2")
        
        # Connect input
        input_input = input_node.addInput("in", "vector2")
        input_input.setNodeName("position")
        
        # Use noise as a simple voronoi approximation
        noise_node = nodegraph.addNode("fractal3d", "voronoi_noise")
        noise_node.setType("color3")
        
        # Connect position to noise
        noise_input = noise_node.addInput("position", "vector2")
        noise_input.setNodeName("voronoi_input.out")
        
        # Output
        output = nodegraph.addOutput("out", "color3")
        output.setNodeName("voronoi_noise.out")
    
    def get_texture_definition(self, texture_type: str) -> Optional[mx.NodeDef]:
        """Get a texture node definition by type."""
        if texture_type in self.texture_defs:
            return self.texture_defs[texture_type]["nodedef"]
        return None
    
    def has_texture_definition(self, texture_type: str) -> bool:
        """Check if a texture definition exists."""
        return texture_type in self.texture_defs
    
    def get_all_texture_types(self) -> list[str]:
        """Get all available texture types."""
        return list(self.texture_defs.keys())
