# MaterialX Exporter Fix Proposal

## Executive Summary

The test suite has identified several critical issues with the MaterialX exporter that prevent successful validation of exported `.mtlx` files. This document outlines the specific problems and proposes comprehensive fixes to ensure MaterialX 1.39 compliance.

## Issues Identified

### 1. Missing Node Definitions
- **`curve` node type**: Not found in MaterialX libraries (but `curvelookup`, `curveuniformlinear`, `curveuniformcubic` exist)
- **`dotproduct`, `distance` operations**: Actually exist in MaterialX but not being found by exporter
- **Placeholder node failures**: Created but not properly connected

### 2. Type Conversion Issues
- **Vector3 to Vector2 conversion failures**: Conversion nodes can't create proper input ports
- **Incorrect port mappings**: Wrong input/output names for conversion nodes
- **Type incompatibility warnings**: Vector3 → Vector2 connections failing

### 3. Node Schema Problems
- **Non-existent MaterialX nodes**: Schemas reference unavailable node types
- **Incorrect input/output mappings**: Wrong parameter names and types
- **Missing fallback strategies**: No proper handling for unsupported operations

### 5. Color Ramp Issues
- **Wrong node type**: Using `ramp` instead of proper MaterialX ramp nodes
- **Incorrect input mapping**: Vector3 input to `texcoord` expecting Vector2
- **Missing proper ramp implementation**: Should use `ramplr`, `ramptb`, or `ramp4`

## Root Cause Analysis

### 1. MaterialX Specification Compliance
The exporter is trying to use node types that don't exist in MaterialX 1.39:
- `curve` node doesn't exist in standard MaterialX libraries (but `curvelookup`, `curveuniformlinear`, `curveuniformcubic` do exist)
- Vector math operations like `dotproduct` and `distance` actually exist in MaterialX but are not being found by the exporter
- Color ramp should use `ramplr`, `ramptb`, or `ramp4` nodes, not a generic `ramp`

### 2. Type System Issues
The conversion system has fundamental flaws:
- Vector3 to Vector2 conversion using `separate3` with wrong port names
- Conversion nodes created but input ports not properly defined
- Missing proper MaterialX node definitions for conversion operations

### 3. Schema Definition Problems
Node schemas reference incorrect MaterialX node types and parameters:
- `CURVE_RGB` schema maps to non-existent `curve` node (should use custom definition)
- `VALTORGB` schema uses wrong node type and input mapping
- Vector math operations missing proper MaterialX equivalents

### 4. Node Definition Lookup Issues
The exporter is not finding existing MaterialX nodes:
- `dotproduct` and `distance` nodes exist in MaterialX but are not being found
- Node definition search logic may be too restrictive
- Missing proper fallback to custom node definitions

## Proposed Fixes

### 1. Fix Node Type Mappings

#### 1.1 Replace Non-existent Nodes with MaterialX Equivalents

**Current Problem:**
```python
# Current mapping - WRONG
'CURVE_RGB': 'curve'  # This node doesn't exist in MaterialX
'VALTORGB': 'ramp'    # Wrong ramp type
```

**Proposed Fix:**
```python
# Correct MaterialX mappings
'CURVE_RGB': 'curvelookup'  # Use MaterialX curve lookup node
'VALTORGB': 'ramplr'        # Use proper MaterialX ramp node
```

#### 1.2 Fix Vector Math Operation Mappings

**Current Problem:**
```python
# Operations exist but not being found
'dotproduct': 'dotproduct'  # Actually exists in MaterialX
'distance': 'distance'      # Actually exists in MaterialX
```

**Proposed Fix:**
```python
# Use existing MaterialX math operations
'dotproduct': 'dotproduct'  # Use native MaterialX dotproduct node
'distance': 'distance'      # Use native MaterialX distance node
```

### 2. Fix Type Conversion System Using Custom Node Definitions

#### 2.1 Create Custom Type Conversion Nodes

Instead of trying to force single nodes to do complex conversions, we'll create custom node definitions for complex type conversions that use multiple MaterialX nodes in a nodegraph.

**Current Problem:**
```python
# Wrong conversion approach - trying to force single nodes
elif from_type == 'vector3' and to_type == 'vector2':
    conversion_node = parent.addChildOfCategory('separate3', conversion_name)
    conversion_node.setType('vector2')  # Wrong type
```

**Proposed Fix:**
```python
# Use custom conversion node definitions
def _create_conversion_node(self, from_type: str, to_type: str, parent: mx.Element) -> Optional[mx.Node]:
    """Create appropriate conversion node using custom definitions for complex conversions."""
    
    # Simple conversions that can use single nodes
    simple_conversions = {
        ('color3', 'float'): 'separate3',  # Extract red channel
        ('vector3', 'color3'): 'combine3',  # Direct conversion
        ('color3', 'vector3'): 'combine3',  # Direct conversion
    }
    
    # Complex conversions that need custom nodegraphs
    complex_conversions = {
        ('vector3', 'vector2'): 'convert_vector3_to_vector2',
        ('vector2', 'vector3'): 'convert_vector2_to_vector3',
        ('color3', 'vector2'): 'convert_color3_to_vector2',
        ('vector4', 'vector3'): 'convert_vector4_to_vector3',
        ('vector3', 'vector4'): 'convert_vector3_to_vector4',
        ('color4', 'color3'): 'convert_color4_to_color3',
        ('color3', 'color4'): 'convert_color3_to_color4',
    }
    
    conversion_key = (from_type, to_type)
    
    if conversion_key in simple_conversions:
        # Use standard MaterialX nodes for simple conversions
        node_type = simple_conversions[conversion_key]
        conversion_node = parent.addChildOfCategory(node_type, conversion_name)
        conversion_node.setType(to_type)
        return conversion_node
        
    elif conversion_key in complex_conversions:
        # Use custom node definitions for complex conversions
        custom_node_type = complex_conversions[conversion_key]
        return self.custom_node_manager.add_custom_node_to_document(
            custom_node_type, conversion_name, parent
        )
    
    return None
```

#### 2.2 Create Custom Type Conversion Node Definitions

**Proposed Implementation:**
```python
def _add_type_conversion_definitions(self):
    """Add custom node definitions for complex type conversions."""
    
    # Vector3 to Vector2 conversion
    self._add_vector3_to_vector2_definition()
    
    # Vector2 to Vector3 conversion  
    self._add_vector2_to_vector3_definition()
    
    # Color3 to Vector2 conversion
    self._add_color3_to_vector2_definition()
    
    # Vector4 to Vector3 conversion
    self._add_vector4_to_vector3_definition()
    
    # Color4 to Color3 conversion
    self._add_color4_to_color3_definition()

def _add_vector3_to_vector2_definition(self):
    """Add custom Vector3 to Vector2 conversion node definition."""
    
    # Node Definition
    nodedef = self.document.addNodeDef("ND_convert_vector3_to_vector2", "vector2", "convert_vector3_to_vector2")
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
    impl = self.document.addNodeGraph("IM_convert_vector3_to_vector2")
    impl.setAttribute("description", "Vector3 to Vector2 conversion implementation")
    
    # Create the implementation
    self._create_vector3_to_vector2_implementation(impl)
    
    # Link implementation to node definition
    nodedef.setImplementation("IM_convert_vector3_to_vector2")

def _create_vector3_to_vector2_implementation(self, nodegraph: mx.NodeGraph):
    """Create the nodegraph implementation for vector3 to vector2 conversion."""
    
    # Separate the vector3 into components
    separate_node = nodegraph.addNode("separate3", "separate_vector3")
    separate_node.setType("float")
    
    # Combine X and Y components into vector2
    combine_node = nodegraph.addNode("combine2", "combine_vector2")
    combine_node.setType("vector2")
    
    # Set up connections
    separate_node.addInput("in", "vector3").setNodeName("in")
    
    # Connect X and Y components to vector2
    combine_node.addInput("in1", "float").setNodeName("separate_vector3")
    combine_node.addInput("in2", "float").setNodeName("separate_vector3")
    
    # Set output
    nodegraph.addOutput("out", "vector2").setNodeName("combine_vector2")

def _add_vector2_to_vector3_definition(self):
    """Add custom Vector2 to Vector3 conversion node definition."""
    
    # Node Definition
    nodedef = self.document.addNodeDef("ND_convert_vector2_to_vector3", "vector3", "convert_vector2_to_vector3")
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
    impl = self.document.addNodeGraph("IM_convert_vector2_to_vector3")
    impl.setAttribute("description", "Vector2 to Vector3 conversion implementation")
    
    # Create the implementation
    self._create_vector2_to_vector3_implementation(impl)
    
    # Link implementation to node definition
    nodedef.setImplementation("IM_convert_vector2_to_vector3")

def _create_vector2_to_vector3_implementation(self, nodegraph: mx.NodeGraph):
    """Create the nodegraph implementation for vector2 to vector3 conversion."""
    
    # Separate the vector2 into components
    separate_node = nodegraph.addNode("separate2", "separate_vector2")
    separate_node.setType("float")
    
    # Create constant for Z=0
    z_constant = nodegraph.addNode("constant", "z_constant")
    z_constant.setType("float")
    z_constant.addInput("value", "float").setValue(0.0)
    
    # Combine X, Y, and Z=0 into vector3
    combine_node = nodegraph.addNode("combine3", "combine_vector3")
    combine_node.setType("vector3")
    
    # Set up connections
    separate_node.addInput("in", "vector2").setNodeName("in")
    
    # Connect X, Y, and Z components to vector3
    combine_node.addInput("in1", "float").setNodeName("separate_vector2")
    combine_node.addInput("in2", "float").setNodeName("separate_vector2")
    combine_node.addInput("in3", "float").setNodeName("z_constant")
    
    # Set output
    nodegraph.addOutput("out", "vector3").setNodeName("combine_vector3")
```

#### 2.3 Update Port Mappings for Custom Conversions

**Proposed Fix:**
```python
def _get_conversion_node_ports(self, from_type: str, to_type: str) -> Tuple[str, str]:
    """Get the correct input and output port names for conversion nodes."""
    
    # Simple conversions
    if from_type == 'color3' and to_type == 'float':
        return 'in', 'outr'  # separate3: input 'in', output 'outr' (red component)
    elif from_type == 'color3' and to_type == 'vector3':
        return 'in1', 'out'  # combine3: inputs 'in1', 'in2', 'in3', output 'out'
    elif from_type == 'vector3' and to_type == 'color3':
        return 'in1', 'out'  # combine3: inputs 'in1', 'in2', 'in3', output 'out'
    
    # Complex conversions using custom nodes
    elif from_type == 'vector3' and to_type == 'vector2':
        return 'in', 'out'  # Custom node: input 'in', output 'out'
    elif from_type == 'vector2' and to_type == 'vector3':
        return 'in', 'out'  # Custom node: input 'in', output 'out'
    elif from_type == 'color3' and to_type == 'vector2':
        return 'in', 'out'  # Custom node: input 'in', output 'out'
    elif from_type == 'vector4' and to_type == 'vector3':
        return 'in', 'out'  # Custom node: input 'in', output 'out'
    elif from_type == 'color4' and to_type == 'color3':
        return 'in', 'out'  # Custom node: input 'in', output 'out'
    
    # Default fallback
    return 'in', 'out'
```

### 3. Fix Node Definition Lookup

#### 3.1 Improve Node Definition Search

**Current Problem:**
```python
# Node definition search is too restrictive
Searching for node definition 'dotproduct' (category: vector3) among 780 node definitions
No exact match by type, trying search by name...
No match by name, trying partial matching on type...
WARNING: No node definition found for 'dotproduct' (category: vector3)
```

**Proposed Fix:**
```python
def find_node_definition(self, node_type: str, category: str = None) -> Optional[mx.NodeDef]:
    """Enhanced node definition search with better fallbacks."""
    
    # First try exact match
    nodedef = self.document.getNodeDef(f"ND_{node_type}_{category}")
    if nodedef:
        return nodedef
    
    # Try without category
    nodedef = self.document.getNodeDef(f"ND_{node_type}")
    if nodedef:
        return nodedef
    
    # Try search by name pattern
    for node_def in self.document.getNodeDefs():
        if node_def.getNodeString() == node_type:
            return node_def
    
    # Try custom node definitions
    if self.custom_node_manager.has_custom_definition(node_type):
        return self.custom_node_manager.get_custom_node_definition(node_type)
    
    return None
```

### 4. Fix Node Schemas

#### 4.1 Update CURVE_RGB Schema

**Current Problem:**
```python
'CURVE_RGB': [
    {'blender': 'Color', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
]
```

**Proposed Fix:**
```python
'CURVE_RGB': [
    {'blender': 'Color', 'mtlx': 'in', 'type': 'color3', 'category': 'color3'},
    {'blender': 'Fac', 'mtlx': 'texcoord', 'type': 'vector2', 'category': 'color3'},
]
```

#### 3.2 Update VALTORGB Schema

**Current Problem:**
```python
'VALTORGB': [
    {'blender': 'Fac', 'mtlx': 'in', 'type': 'float', 'category': 'color3'},
]
```

**Proposed Fix:**
```python
'VALTORGB': [
    {'blender': 'Fac', 'mtlx': 'texcoord', 'type': 'vector2', 'category': 'color4'},
    # Add ramp-specific inputs
    {'blender': 'Color Ramp', 'mtlx': 'valuel', 'type': 'color4', 'category': 'color4'},
    {'blender': 'Color Ramp', 'mtlx': 'valuer', 'type': 'color4', 'category': 'color4'},
]
```

### 5. Implement Proper Color Ramp Support

#### 4.1 Use Correct MaterialX Ramp Nodes

**Current Problem:**
```python
def map_color_ramp(node, builder, ...):
    node_name = builder.add_node("ramp", f"colorramp_{node.name}", "color4")
    # Wrong node type and implementation
```

**Proposed Fix:**
```python
def map_color_ramp(node, builder, ...):
    # Use proper MaterialX ramp node
    node_name = builder.add_node("ramplr", f"colorramp_{node.name}", "color4")
    
    # Extract ramp data from Blender node
    if hasattr(node, 'color_ramp'):
        ramp = node.color_ramp
        
        # Get first and last elements for ramplr
        if len(ramp.elements) >= 2:
            first_element = ramp.elements[0]
            last_element = ramp.elements[-1]
            
            # Set left and right values
            builder.library_builder.node_builder.create_mtlx_input(
                builder.nodes[node_name], 'valuel', 
                value=[first_element.color[0], first_element.color[1], first_element.color[2], first_element.alpha],
                node_type='ramplr', category='color4'
            )
            
            builder.library_builder.node_builder.create_mtlx_input(
                builder.nodes[node_name], 'valuer', 
                value=[last_element.color[0], last_element.color[1], last_element.color[2], last_element.alpha],
                node_type='ramplr', category='color4'
            )
```

#### 4.2 Fix Input Connection

**Current Problem:**
```python
# Wrong connection - trying to connect vector3 to texcoord
builder.add_connection(value_or_node, 'out', node_name, 'texcoord')
```

**Proposed Fix:**
```python
# Correct connection - use proper input name
builder.add_connection(value_or_node, 'out', node_name, 'texcoord')
# But ensure value_or_node outputs vector2, not vector3
```

### 6. Add Missing Vector Math Operations

#### 5.1 Implement Dot Product

**Proposed Implementation:**
```python
def map_dotproduct_vector3(node, builder, ...):
    # Use separate3 + multiply + add to compute dot product
    # A.B = A.x*B.x + A.y*B.y + A.z*B.z
    
    # Create separate3 nodes for A and B
    separate_a = builder.add_node("separate3", f"separate_a_{node.name}", "vector3")
    separate_b = builder.add_node("separate3", f"separate_b_{node.name}", "vector3")
    
    # Create multiply nodes for each component
    mult_x = builder.add_node("multiply", f"mult_x_{node.name}", "float")
    mult_y = builder.add_node("multiply", f"mult_y_{node.name}", "float")
    mult_z = builder.add_node("multiply", f"mult_z_{node.name}", "float")
    
    # Create add nodes to sum components
    add_xy = builder.add_node("add", f"add_xy_{node.name}", "float")
    add_xyz = builder.add_node("add", f"add_xyz_{node.name}", "float")
    
    # Connect the network
    # ... connection logic
    
    return add_xyz
```

#### 5.2 Implement Distance

**Proposed Implementation:**
```python
def map_distance_vector3(node, builder, ...):
    # Use subtract + length to compute distance
    # distance(A,B) = length(A-B)
    
    # Create subtract node
    subtract_node = builder.add_node("subtract", f"subtract_{node.name}", "vector3")
    
    # Create length node
    length_node = builder.add_node("length", f"length_{node.name}", "float")
    
    # Connect the network
    # ... connection logic
    
    return length_node
```

### 7. Fix Conversion Node Input Port Creation

#### 6.1 Proper Node Definition Setting

**Current Problem:**
```python
# Conversion nodes created but input ports not properly defined
conversion_node = parent.addChildOfCategory('separate3', conversion_name)
conversion_node.setType('vector2')
# Missing proper node definition
```

**Proposed Fix:**
```python
# Set proper node definition for conversion nodes
conversion_node = parent.addChildOfCategory('separate3', conversion_name)
conversion_node.setType('vector2')

# Set the correct node definition
if from_type == 'vector3' and to_type == 'vector2':
    conversion_node.setNodeDefString('ND_separate3_vector2')
elif from_type == 'color3' and to_type == 'vector2':
    conversion_node.setNodeDefString('ND_separate3_vector2')
```

### 8. Add Custom Node Definitions for Missing Operations

#### 7.1 Create Custom Curve Node Definition

Since MaterialX doesn't have a generic `curve` node but does have `curvelookup`, `curveuniformlinear`, and `curveuniformcubic`, we can create a custom node definition that maps Blender's RGB Curves to the appropriate MaterialX curve node.

**Proposed Implementation:**
```python
def _add_curve_rgb_definition(self):
    """Add custom RGB Curves node definition and implementation."""
    
    # Node Definition
    curve_nodedef = self.document.addNodeDef("ND_curve_rgb", "color3", "curve_rgb")
    curve_nodedef.setNodeGroup("adjustment")
    curve_nodedef.setAttribute("version", "1.0")
    curve_nodedef.setAttribute("description", "RGB Curves node for Blender compatibility")
    
    # Inputs
    inputs = [
        ("in", "color3", "0,0,0", "Input color"),
        ("knots", "floatarray", "0,1", "Knot positions"),
        ("knotvalues", "floatarray", "0,1", "Knot values"),
    ]
    
    for name, type_str, default_value, description in inputs:
        input_elem = curve_nodedef.addInput(name, type_str)
        input_elem.setValueString(default_value)
        input_elem.setAttribute("description", description)
    
    # Output
    output = curve_nodedef.addOutput("out", "color3")
    output.setAttribute("description", "Curved color output")
    
    # Implementation NodeGraph using curvelookup
    curve_impl = self.document.addNodeGraph("IM_curve_rgb")
    curve_impl.setAttribute("description", "RGB Curves implementation using curvelookup")
    
    # Create the curve implementation
    self._create_curve_rgb_implementation(curve_impl)
    
    # Link implementation to node definition
    curve_nodedef.setImplementation("IM_curve_rgb")
    
    self.logger.info("Added Curve RGB custom node definition")

def _create_curve_rgb_implementation(self, nodegraph: mx.NodeGraph):
    """Create the nodegraph implementation for RGB curves."""
    
    # Use curvelookup for each channel
    red_curve = nodegraph.addNode("curvelookup", "red_curve")
    red_curve.setType("float")
    
    green_curve = nodegraph.addNode("curvelookup", "green_curve")
    green_curve.setType("float")
    
    blue_curve = nodegraph.addNode("curvelookup", "blue_curve")
    blue_curve.setType("float")
    
    # Separate input color
    separate_color = nodegraph.addNode("separate3", "separate_color")
    separate_color.setType("float")
    
    # Combine curved colors
    combine_color = nodegraph.addNode("combine3", "combine_color")
    combine_color.setType("color3")
    
    # Set up connections
    separate_color.addInput("in", "color3").setNodeName("in")
    
    # Connect each channel to its curve
    red_curve.addInput("in", "float").setNodeName("separate_color")
    red_curve.addInput("knots", "floatarray").setNodeName("knots")
    red_curve.addInput("knotvalues", "floatarray").setNodeName("knotvalues")
    
    green_curve.addInput("in", "float").setNodeName("separate_color")
    green_curve.addInput("knots", "floatarray").setNodeName("knots")
    green_curve.addInput("knotvalues", "floatarray").setNodeName("knotvalues")
    
    blue_curve.addInput("in", "float").setNodeName("separate_color")
    blue_curve.addInput("knots", "floatarray").setNodeName("knots")
    blue_curve.addInput("knotvalues", "floatarray").setNodeName("knotvalues")
    
    # Combine the curved channels
    combine_color.addInput("in1", "float").setNodeName("red_curve")
    combine_color.addInput("in2", "float").setNodeName("green_curve")
    combine_color.addInput("in3", "float").setNodeName("blue_curve")
    
    # Set output
    nodegraph.addOutput("out", "color3").setNodeName("combine_color")
```

#### 7.2 Integrate with Custom Node Definition Manager

The exporter already has a `CustomNodeDefinitionManager` class. We need to integrate both curve definitions and type conversion definitions:

```python
# In CustomNodeDefinitionManager._initialize_custom_definitions()
def _initialize_custom_definitions(self):
    """Initialize all custom node definitions."""
    self._add_brick_texture_definition()
    self._add_curve_rgb_definition()
    self._add_type_conversion_definitions()  # Add type conversion definitions
    # Add more custom definitions here as needed

# Update the registry to include type conversion nodes
BLENDER_CUSTOM_NODE_TYPES = {
    "TEX_BRICK": "brick_texture",
    "CURVE_RGB": "curve_rgb",
    # Type conversion nodes are handled automatically by the conversion system
}
```

#### 7.3 Integrate Type Conversion System with Custom Node Manager

**Proposed Implementation:**
```python
class MaterialXTypeConversionManager:
    """Manages type conversions using custom node definitions."""
    
    def __init__(self, custom_node_manager: CustomNodeDefinitionManager):
        self.custom_node_manager = custom_node_manager
        self.simple_conversions = {
            ('color3', 'float'): 'separate3',
            ('vector3', 'color3'): 'combine3',
            ('color3', 'vector3'): 'combine3',
        }
        self.complex_conversions = {
            ('vector3', 'vector2'): 'convert_vector3_to_vector2',
            ('vector2', 'vector3'): 'convert_vector2_to_vector3',
            ('color3', 'vector2'): 'convert_color3_to_vector2',
            ('vector4', 'vector3'): 'convert_vector4_to_vector3',
            ('vector3', 'vector4'): 'convert_vector3_to_vector4',
            ('color4', 'color3'): 'convert_color4_to_color3',
            ('color3', 'color4'): 'convert_color3_to_color4',
        }
    
    def create_conversion_node(self, from_type: str, to_type: str, parent: mx.Element, name: str) -> Optional[mx.Node]:
        """Create a conversion node using custom definitions when needed."""
        
        conversion_key = (from_type, to_type)
        
        if conversion_key in self.simple_conversions:
            # Use standard MaterialX nodes for simple conversions
            node_type = self.simple_conversions[conversion_key]
            conversion_node = parent.addChildOfCategory(node_type, name)
            conversion_node.setType(to_type)
            return conversion_node
            
        elif conversion_key in self.complex_conversions:
            # Use custom node definitions for complex conversions
            custom_node_type = self.complex_conversions[conversion_key]
            return self.custom_node_manager.add_custom_node_to_document(
                custom_node_type, name, parent
            )
        
        return None
    
    def get_conversion_ports(self, from_type: str, to_type: str) -> Tuple[str, str]:
        """Get input and output port names for conversion nodes."""
        
        conversion_key = (from_type, to_type)
        
        if conversion_key in self.simple_conversions:
            # Standard node port mappings
            if from_type == 'color3' and to_type == 'float':
                return 'in', 'outr'  # separate3
            elif 'vector3' in from_type or 'color3' in from_type:
                return 'in1', 'out'  # combine3
        
        # Custom nodes use standard 'in'/'out' ports
        return 'in', 'out'
```

### 9. Add Fallback Strategies

#### 8.1 Graceful Degradation for Unsupported Operations

**Proposed Implementation:**
```python
def _export_unknown_node(self, node: bpy.types.Node) -> str:
    """Handle unsupported nodes with graceful fallbacks."""
    
    # Try to find a reasonable fallback
    fallback_mapping = {
        'CURVE_RGB': 'curve_rgb',  # Use custom curve definition
        'DOT_PRODUCT': 'dotproduct',  # Use native MaterialX dotproduct
        'DISTANCE': 'distance',  # Use native MaterialX distance
    }
    
    node_type = node.bl_idname
    if node_type in fallback_mapping:
        fallback_type = fallback_mapping[node_type]
        self.logger.warning(f"Using fallback {fallback_type} for unsupported {node_type}")
        return self._create_fallback_node(node, fallback_type)
    
    # If no fallback, create a placeholder with warning
    return self._create_placeholder_node(node)
```

## Implementation Plan

### Phase 1: Fix Critical Node Mappings (Priority 1)
1. Create custom `curve_rgb` node definition using MaterialX `curvelookup`
2. Fix `VALTORGB` to use `ramplr` instead of `ramp`
3. Fix `dotproduct` and `distance` mappings to use native MaterialX nodes
4. Update node schemas with correct MaterialX types
5. Improve node definition lookup to find existing MaterialX nodes

### Phase 2: Implement Custom Type Conversion System (Priority 2)
1. Create custom type conversion node definitions (vector3→vector2, vector2→vector3, etc.)
2. Implement MaterialXTypeConversionManager class
3. Integrate type conversion system with existing CustomNodeDefinitionManager
4. Replace existing conversion logic with custom node-based approach
5. Test complex type conversions with real Blender materials

### Phase 3: Add Other Custom Node Definitions (Priority 3)
1. Implement custom curve RGB node definition and nodegraph
2. Add proper node definition lookups in the exporter
3. Test all custom node definitions with real Blender materials
4. Add more custom definitions as needed

### Phase 4: Improve Error Handling (Priority 4)
1. Add graceful fallbacks for unsupported operations
2. Improve error messages with actionable suggestions
3. Add validation for node definitions before use

### Phase 5: Testing and Validation (Priority 5)
1. Update test suite to verify fixes
2. Test with real-world MaterialX files
3. Validate against MaterialX 1.39 specification

## Expected Outcomes

After implementing these fixes:

1. **All test materials should export successfully** without validation errors
2. **MaterialX files should pass validation** using MaterialX library validation
3. **Type conversions should work correctly** for all supported operations
4. **Graceful fallbacks** should handle unsupported operations
5. **Better error messages** should guide users to solutions

## Risk Assessment

### Low Risk
- Fixing node type mappings (well-defined MaterialX specification)
- Updating schemas (clear documentation available)

### Medium Risk
- Type conversion system changes (complex interaction with MaterialX library)
- Vector math operation implementations (need to verify correctness)

### High Risk
- Breaking existing working exports (need comprehensive testing)
- Performance impact of conversion nodes (need optimization)

## Testing Strategy

1. **Unit Tests**: Test each fixed component individually
2. **Integration Tests**: Test complete material export workflows
3. **Regression Tests**: Ensure existing working exports still work
4. **Validation Tests**: Verify exported files pass MaterialX validation
5. **Performance Tests**: Ensure fixes don't significantly impact performance

## Custom Node Definitions Approach

The MaterialX exporter already has a robust custom node definition system in `custom_node_definitions.py`. This approach allows us to:

1. **Create custom node definitions** for Blender nodes that don't have direct MaterialX equivalents
2. **Implement nodegraphs** that use standard MaterialX nodes to achieve the desired functionality
3. **Maintain MaterialX compliance** while supporting Blender-specific features
4. **Extend functionality** without breaking existing MaterialX renderers

### Benefits of Custom Node Definitions:

- **MaterialX Compliant**: Custom definitions follow MaterialX specification
- **Renderer Compatible**: Any MaterialX renderer can understand and process these nodes
- **Extensible**: Easy to add new custom nodes as needed
- **Maintainable**: Clear separation between standard and custom functionality

### Example: Curve RGB Node

Instead of trying to use a non-existent `curve` node, we create a custom `curve_rgb` node definition that:
- Defines the interface (inputs/outputs) for RGB curves
- Implements the functionality using MaterialX `curvelookup` nodes
- Provides a clean mapping from Blender's RGB Curves to MaterialX

### Example: Type Conversion Nodes

Instead of trying to force single MaterialX nodes to do complex conversions, we create custom conversion node definitions that:
- Use multiple MaterialX nodes in a nodegraph to achieve the desired conversion
- Provide clean, well-defined interfaces for each conversion type
- Handle complex conversions like vector3→vector2, color4→color3, etc.
- Maintain MaterialX compliance while supporting complex type transformations

This approach ensures that exported MaterialX files are valid and compatible with all MaterialX renderers while supporting Blender's rich node ecosystem and complex type conversions.

## Conclusion

The proposed fixes address the root causes of the MaterialX validation failures while maintaining backward compatibility where possible. The implementation plan prioritizes critical fixes first, followed by improvements and optimizations.

The key insights are:
1. **Use existing MaterialX nodes** where possible (`dotproduct`, `distance`, `ramplr`, etc.)
2. **Create custom node definitions** for Blender-specific nodes that don't have MaterialX equivalents
3. **Fix node definition lookup** to properly find existing MaterialX nodes
4. **Follow MaterialX specification exactly** to ensure compatibility with all renderers

This approach will ensure compatibility with all MaterialX-compliant renderers and tools while providing full support for Blender's material system.
