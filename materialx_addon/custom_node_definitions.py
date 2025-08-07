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
        self._add_curve_rgb_definition()
        self._add_type_conversion_definitions()
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
        
        # Output
        output = brick_nodedef.addOutput("out", "color3")
        output.setAttribute("description", "Brick texture output")
        
        # Implementation NodeGraph
        brick_impl = self.document.addNodeGraph("IM_brick_texture")
        brick_impl.setAttribute("description", "Brick texture implementation")
        
        # Create the brick texture implementation
        self._create_brick_texture_implementation(brick_impl)
        
        # Link implementation to node definition
        brick_nodedef.setAttribute("implname", "IM_brick_texture")
        
        # Store for later use
        self.custom_node_defs["brick_texture"] = {
            "nodedef": brick_nodedef,
            "implementation": brick_impl
        }
        
        self.logger.info("Added Brick Texture custom node definition")
    
    def _add_curve_rgb_definition(self):
        """Add custom RGB Curves node definition and implementation."""
        
        # Check if the node definition already exists
        existing_nodedef = self.document.getNodeDef("ND_curvelookup")
        if existing_nodedef:
            self.logger.info("Curve lookup node definition already exists, skipping creation")
            self.custom_node_defs["curvelookup"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_curvelookup")
            }
            return
        
        # Node Definition
        curve_nodedef = self.document.addNodeDef("ND_curvelookup", "color3", "curvelookup")
        curve_nodedef.setNodeGroup("adjustment")
        curve_nodedef.setAttribute("version", "1.0")
        curve_nodedef.setAttribute("description", "RGB Curves lookup node for Blender compatibility")
        
        # Inputs
        inputs = [
            ("in", "color3", "0,0,0", "Input color"),
            ("texcoord", "vector2", "0,0", "Texture coordinates for curve lookup"),
        ]
        
        for name, type_str, default_value, description in inputs:
            input_elem = curve_nodedef.addInput(name, type_str)
            input_elem.setValueString(default_value)
            input_elem.setAttribute("description", description)
        
        # Output
        output = curve_nodedef.addOutput("out", "color3")
        output.setAttribute("description", "Curve-adjusted color output")
        
        # Implementation NodeGraph
        curve_impl = self.document.addNodeGraph("IM_curvelookup")
        curve_impl.setAttribute("description", "RGB Curves implementation")
        
        # Create the curve implementation
        self._create_curve_rgb_implementation(curve_impl)
        
        # Link implementation to node definition
        curve_nodedef.setAttribute("implname", "IM_curvelookup")
        
        # Store for later use
        self.custom_node_defs["curvelookup"] = {
            "nodedef": curve_nodedef,
            "implementation": curve_impl
        }
        
        self.logger.info("Added Curve Lookup custom node definition")
    
    def _create_curve_rgb_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for RGB Curves using standard MaterialX nodes."""
        
        # For now, implement a simple pass-through using a mix node
        # This can be enhanced later with actual curve interpolation
        mix_node = nodegraph.addNode("mix", "curve_mix")
        mix_node.setType("color3")
        
        # Connect input to mix node - use setNodeName for string connections
        fg_input = mix_node.addInput("fg", "color3")
        fg_input.setNodeName("in")
        
        bg_input = mix_node.addInput("bg", "color3")
        bg_input.setNodeName("in")  # Same as input for now
        
        mix_input = mix_node.addInput("mix", "float")
        mix_input.setValueString("1.0")  # Full mix for pass-through
        
        # Set output - use setNodeName for string connections
        output = nodegraph.addOutput("out", "color3")
        output.setNodeName("curve_mix")
        
        self.logger.debug("Created Curve RGB implementation using mix node (pass-through)")
    
    def _add_type_conversion_definitions(self):
        """Add all type conversion node definitions."""
        self._add_vector3_to_vector2_definition()
        self._add_vector2_to_vector3_definition()
        self._add_color3_to_vector2_definition()
        self._add_vector4_to_vector3_definition()
        self._add_vector3_to_vector4_definition()
        self._add_color4_to_color3_definition()
        self._add_color3_to_color4_definition()
    
    def _add_vector3_to_vector2_definition(self):
        """Add custom Vector3 to Vector2 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_vector3_to_vector2_vector2")
        if existing_nodedef:
            self.custom_node_defs["convert_vector3_to_vector2"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_vector3_to_vector2_vector2")
            }
            return
        
        # Node Definition - FIXED: use proper naming convention
        nodedef = self.document.addNodeDef("ND_convert_vector3_to_vector2_vector2", "vector2", "convert_vector3_to_vector2")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert vector3 to vector2 by extracting X,Y components")
        
        # Input
        input_elem = nodedef.addInput("in", "vector3")
        input_elem.setAttribute("description", "Input vector3")
        
        # Output
        output = nodedef.addOutput("out", "vector2")
        output.setAttribute("description", "Output vector2 (X,Y components)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_vector3_to_vector2_vector2")
        impl.setAttribute("description", "Vector3 to Vector2 conversion implementation")
        
        # Create the implementation
        self._create_vector3_to_vector2_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_vector3_to_vector2_vector2")
        
        # Store for later use
        self.custom_node_defs["convert_vector3_to_vector2"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Vector3 to Vector2 conversion node definition")
    
    def _create_vector3_to_vector2_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Vector3 to Vector2 conversion using separate3 and combine2."""
        
        # Input node
        input_node = nodegraph.addNode("separate3", "separate_input")
        input_node.setType("vector3")
        
        # Connect input
        input_input = input_node.addInput("in", "vector3")
        input_input.setNodeName("in")
        
        # Combine X and Y components
        combine_node = nodegraph.addNode("combine2", "combine_xy")
        combine_node.setType("vector2")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        # Output
        output = nodegraph.addOutput("out", "vector2")
        output.setNodeName("combine_xy.out")
    
    def _add_vector2_to_vector3_definition(self):
        """Add custom Vector2 to Vector3 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_vector2_to_vector3_vector3")
        if existing_nodedef:
            self.custom_node_defs["convert_vector2_to_vector3"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_vector2_to_vector3_vector3")
            }
            return
        
        # Node Definition - FIXED: use proper naming convention
        nodedef = self.document.addNodeDef("ND_convert_vector2_to_vector3_vector3", "vector3", "convert_vector2_to_vector3")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert vector2 to vector3 by adding Z=0")
        
        # Input
        input_elem = nodedef.addInput("in", "vector2")
        input_elem.setAttribute("description", "Input vector2")
        
        # Output
        output = nodedef.addOutput("out", "vector3")
        output.setAttribute("description", "Output vector3 (X,Y,0)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_vector2_to_vector3_vector3")
        impl.setAttribute("description", "Vector2 to Vector3 conversion implementation")
        
        # Create the implementation
        self._create_vector2_to_vector3_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_vector2_to_vector3_vector3")
        
        # Store for later use
        self.custom_node_defs["convert_vector2_to_vector3"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Vector2 to Vector3 conversion node definition")
    
    def _create_vector2_to_vector3_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Vector2 to Vector3 conversion using separate2 and combine3."""
        
        # Input node
        input_node = nodegraph.addNode("separate2", "separate_input")
        input_node.setType("vector2")
        
        # Connect input
        input_input = input_node.addInput("in", "vector2")
        input_input.setNodeName("in")
        
        # Constant for Z=0
        z_constant = nodegraph.addNode("constant", "z_zero")
        z_constant.setType("float")
        z_input = z_constant.addInput("value", "float")
        z_input.setValueString("0.0")
        
        # Combine X, Y, and Z=0
        combine_node = nodegraph.addNode("combine3", "combine_xyz")
        combine_node.setType("vector3")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        in3_input = combine_node.addInput("in3", "float")
        in3_input.setNodeName("z_zero.out")
        
        # Output
        output = nodegraph.addOutput("out", "vector3")
        output.setNodeName("combine_xyz.out")
    
    def _add_color3_to_vector2_definition(self):
        """Add custom Color3 to Vector2 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_color3_to_vector2_vector2")
        if existing_nodedef:
            self.custom_node_defs["convert_color3_to_vector2"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_color3_to_vector2_vector2")
            }
            return
        
        # Node Definition - FIXED: use proper naming convention
        nodedef = self.document.addNodeDef("ND_convert_color3_to_vector2_vector2", "vector2", "convert_color3_to_vector2")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert color3 to vector2 by extracting R,G components")
        
        # Input
        input_elem = nodedef.addInput("in", "color3")
        input_elem.setAttribute("description", "Input color3")
        
        # Output
        output = nodedef.addOutput("out", "vector2")
        output.setAttribute("description", "Output vector2 (R,G components)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_color3_to_vector2_vector2")
        impl.setAttribute("description", "Color3 to Vector2 conversion implementation")
        
        # Create the implementation
        self._create_color3_to_vector2_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_color3_to_vector2_vector2")
        
        # Store for later use
        self.custom_node_defs["convert_color3_to_vector2"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Color3 to Vector2 conversion node definition")
    
    def _create_color3_to_vector2_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Color3 to Vector2 conversion using separate3 and combine2."""
        
        # Input node
        input_node = nodegraph.addNode("separate3", "separate_input")
        input_node.setType("color3")
        
        # Connect input
        input_input = input_node.addInput("in", "color3")
        input_input.setNodeName("in")
        
        # Combine R and G components
        combine_node = nodegraph.addNode("combine2", "combine_rg")
        combine_node.setType("vector2")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        # Output
        output = nodegraph.addOutput("out", "vector2")
        output.setNodeName("combine_rg.out")
    
    def _add_vector4_to_vector3_definition(self):
        """Add custom Vector4 to Vector3 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_vector4_to_vector3_vector3")
        if existing_nodedef:
            self.custom_node_defs["convert_vector4_to_vector3"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_vector4_to_vector3_vector3")
            }
            return
        
        # Node Definition - FIXED: use proper naming convention
        nodedef = self.document.addNodeDef("ND_convert_vector4_to_vector3_vector3", "vector3", "convert_vector4_to_vector3")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert vector4 to vector3 by extracting X,Y,Z components")
        
        # Input
        input_elem = nodedef.addInput("in", "vector4")
        input_elem.setAttribute("description", "Input vector4")
        
        # Output
        output = nodedef.addOutput("out", "vector3")
        output.setAttribute("description", "Output vector3 (X,Y,Z components)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_vector4_to_vector3_vector3")
        impl.setAttribute("description", "Vector4 to Vector3 conversion implementation")
        
        # Create the implementation
        self._create_vector4_to_vector3_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_vector4_to_vector3_vector3")
        
        # Store for later use
        self.custom_node_defs["convert_vector4_to_vector3"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Vector4 to Vector3 conversion node definition")
    
    def _create_vector4_to_vector3_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Vector4 to Vector3 conversion using separate4 and combine3."""
        
        # Input node
        input_node = nodegraph.addNode("separate4", "separate_input")
        input_node.setType("vector4")
        
        # Connect input
        input_input = input_node.addInput("in", "vector4")
        input_input.setNodeName("in")
        
        # Combine X, Y, and Z components
        combine_node = nodegraph.addNode("combine3", "combine_xyz")
        combine_node.setType("vector3")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        in3_input = combine_node.addInput("in3", "float")
        in3_input.setNodeName("separate_input.outz")
        
        # Output
        output = nodegraph.addOutput("out", "vector3")
        output.setNodeName("combine_xyz.out")
    
    def _add_color4_to_color3_definition(self):
        """Add custom Color4 to Color3 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_color4_to_color3_color3")
        if existing_nodedef:
            self.custom_node_defs["convert_color4_to_color3"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_color4_to_color3_color3")
            }
            return
        
        # Node Definition - FIXED: use proper naming convention
        nodedef = self.document.addNodeDef("ND_convert_color4_to_color3_color3", "color3", "convert_color4_to_color3")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert color4 to color3 by extracting R,G,B components")
        
        # Input
        input_elem = nodedef.addInput("in", "color4")
        input_elem.setAttribute("description", "Input color4")
        
        # Output
        output = nodedef.addOutput("out", "color3")
        output.setAttribute("description", "Output color3 (R,G,B components)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_color4_to_color3_color3")
        impl.setAttribute("description", "Color4 to Color3 conversion implementation")
        
        # Create the implementation
        self._create_color4_to_color3_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_color4_to_color3_color3")
        
        # Store for later use
        self.custom_node_defs["convert_color4_to_color3"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Color4 to Color3 conversion node definition")
    
    def _create_color4_to_color3_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Color4 to Color3 conversion using separate4 and combine3."""
        
        # Input node
        input_node = nodegraph.addNode("separate4", "separate_input")
        input_node.setType("float")
        
        # Combine R, G, and B components
        combine_node = nodegraph.addNode("combine3", "combine_rgb")
        combine_node.setType("color3")
        
        # Set up connections
        input_node.addInput("in", "color4").setNodeName("in")
        
        # Connect R, G, B components to combine3
        combine_node.addInput("in1", "float").setNodeName("separate_input")
        combine_node.addInput("in2", "float").setNodeName("separate_input")
        combine_node.addInput("in3", "float").setNodeName("separate_input")
        
        # Set output
        nodegraph.addOutput("out", "color3").setNodeName("combine_rgb")
    
    def _add_vector3_to_vector4_definition(self):
        """Add custom Vector3 to Vector4 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_vector3_to_vector4_vector4")
        if existing_nodedef:
            self.custom_node_defs["convert_vector3_to_vector4"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_vector3_to_vector4_vector4")
            }
            return
        
        # Node Definition
        nodedef = self.document.addNodeDef("ND_convert_vector3_to_vector4_vector4", "vector4", "convert_vector3_to_vector4")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert vector3 to vector4 by adding W=1.0")
        
        # Input
        input_elem = nodedef.addInput("in", "vector3")
        input_elem.setAttribute("description", "Input vector3")
        
        # Output
        output = nodedef.addOutput("out", "vector4")
        output.setAttribute("description", "Output vector4 (X,Y,Z,W=1.0)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_vector3_to_vector4_vector4")
        impl.setAttribute("description", "Vector3 to Vector4 conversion implementation")
        
        # Create the implementation
        self._create_vector3_to_vector4_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_vector3_to_vector4_vector4")
        
        # Store for later use
        self.custom_node_defs["convert_vector3_to_vector4"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Vector3 to Vector4 conversion node definition")
    
    def _create_vector3_to_vector4_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Vector3 to Vector4 conversion using separate3 and combine4."""
        
        # Input node
        input_node = nodegraph.addNode("separate3", "separate_input")
        input_node.setType("vector3")
        
        # Connect input
        input_input = input_node.addInput("in", "vector3")
        input_input.setNodeName("in")
        
        # Constant for W=1.0
        w_constant = nodegraph.addNode("constant", "w_one")
        w_constant.setType("float")
        w_input = w_constant.addInput("value", "float")
        w_input.setValueString("1.0")
        
        # Combine X, Y, Z, and W=1.0
        combine_node = nodegraph.addNode("combine4", "combine_xyzw")
        combine_node.setType("vector4")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        in3_input = combine_node.addInput("in3", "float")
        in3_input.setNodeName("separate_input.outz")
        
        in4_input = combine_node.addInput("in4", "float")
        in4_input.setNodeName("w_one.out")
        
        # Output
        output = nodegraph.addOutput("out", "vector4")
        output.setNodeName("combine_xyzw.out")
    
    def _add_color3_to_color4_definition(self):
        """Add custom Color3 to Color4 conversion node definition."""
        
        # Check if already exists
        existing_nodedef = self.document.getNodeDef("ND_convert_color3_to_color4_color4")
        if existing_nodedef:
            self.custom_node_defs["convert_color3_to_color4"] = {
                "nodedef": existing_nodedef,
                "implementation": self.document.getNodeGraph("IM_convert_color3_to_color4_color4")
            }
            return
        
        # Node Definition
        nodedef = self.document.addNodeDef("ND_convert_color3_to_color4_color4", "color4", "convert_color3_to_color4")
        nodedef.setNodeGroup("conversion")
        nodedef.setAttribute("version", "1.0")
        nodedef.setAttribute("description", "Convert color3 to color4 by adding A=1.0")
        
        # Input
        input_elem = nodedef.addInput("in", "color3")
        input_elem.setAttribute("description", "Input color3")
        
        # Output
        output = nodedef.addOutput("out", "color4")
        output.setAttribute("description", "Output color4 (R,G,B,A=1.0)")
        
        # Implementation NodeGraph
        impl = self.document.addNodeGraph("IM_convert_color3_to_color4_color4")
        impl.setAttribute("description", "Color3 to Color4 conversion implementation")
        
        # Create the implementation
        self._create_color3_to_color4_implementation(impl)
        
        # Link implementation to node definition
        nodedef.setAttribute("implname", "IM_convert_color3_to_color4_color4")
        
        # Store for later use
        self.custom_node_defs["convert_color3_to_color4"] = {
            "nodedef": nodedef,
            "implementation": impl
        }
        
        self.logger.info("Added Color3 to Color4 conversion node definition")
    
    def _create_color3_to_color4_implementation(self, nodegraph: mx.NodeGraph):
        """Create the implementation for Color3 to Color4 conversion using separate3 and combine4."""
        
        # Input node
        input_node = nodegraph.addNode("separate3", "separate_input")
        input_node.setType("color3")
        
        # Connect input
        input_input = input_node.addInput("in", "color3")
        input_input.setNodeName("in")
        
        # Constant for A=1.0
        a_constant = nodegraph.addNode("constant", "a_one")
        a_constant.setType("float")
        a_input = a_constant.addInput("value", "float")
        a_input.setValueString("1.0")
        
        # Combine R, G, B, and A=1.0
        combine_node = nodegraph.addNode("combine4", "combine_rgba")
        combine_node.setType("color4")
        
        # Connect inputs
        in1_input = combine_node.addInput("in1", "float")
        in1_input.setNodeName("separate_input.outx")
        
        in2_input = combine_node.addInput("in2", "float")
        in2_input.setNodeName("separate_input.outy")
        
        in3_input = combine_node.addInput("in3", "float")
        in3_input.setNodeName("separate_input.outz")
        
        in4_input = combine_node.addInput("in4", "float")
        in4_input.setNodeName("a_one.out")
        
        # Output
        output = nodegraph.addOutput("out", "color4")
        output.setNodeName("combine_rgba.out")

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
    "CURVE_RGB": "curvelookup",
    # Add more mappings as needed
}


def get_custom_node_type(blender_node_type: str) -> Optional[str]:
    """Get the custom MaterialX node type for a Blender node type."""
    return BLENDER_CUSTOM_NODE_TYPES.get(blender_node_type)


def is_custom_node_type(blender_node_type: str) -> bool:
    """Check if a Blender node type requires a custom definition."""
    return blender_node_type in BLENDER_CUSTOM_NODE_TYPES
