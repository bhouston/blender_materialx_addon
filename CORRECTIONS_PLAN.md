# MaterialX Exporter Corrections Plan

## Overview

Analysis of the Blender MaterialX exporter has revealed several critical issues that prevent complex materials from loading properly in the MaterialX Graph Viewer. These issues stem from incorrect connection syntax, type mismatches, and improper output handling.

## Issues Identified

### 1. Nodegraph Connection Syntax Error

**Problem**: The exporter incorrectly uses `nodename` attribute for nodegraph connections instead of the proper `nodegraph` and `output` attributes.

**Current (Incorrect)**:
```xml
<input name="base_color" type="color3" nodename="ComplexProcedural.base_color" />
```

**Correct (Per MaterialX Specification)**:
```xml
<input name="base_color" type="color3" nodegraph="ComplexProcedural" output="base_color" />
```

**Location**: `materialx_addon/materialx_library_core.py` line 1760

**Specification Reference**: MaterialX Specification v1.39, Section "Inputs":
> "Input elements can assign an explicit uniform value by providing a `value` attribute, make a connection to the output of another node by providing a `nodename` attribute, or make a connection to the output of a nodegraph by providing a `nodegraph` attribute. An optional `output` attribute may also be provided for `<input>` elements, allowing the input to connect to a specific, named output of the referenced upstream node or nodegraph."

### 2. Type Conversion Issues

The exporter fails to handle type mismatches between connected nodes, leading to invalid connections.

#### 2.1 texcoord → fractal3d position
- **Issue**: `texcoord` outputs `vector2`, `fractal3d` expects `vector3` for position input
- **Specification**: `fractal3d` has `position (vector3)` input
- **Solution**: Insert conversion node to transform `vector2` to `vector3` (add Z=0)

#### 2.2 mix → ramp texcoord  
- **Issue**: `mix` outputs `color3`, `ramp` expects `vector2` for texcoord input
- **Specification**: `ramplr` has `texcoord (vector2)` input
- **Solution**: Insert conversion node to extract first two components from `color3`

#### 2.3 mix → normalmap default
- **Issue**: `mix` outputs `color3`, `normalmap` expects `vector3` for default input
- **Specification**: `normalmap` expects vector3 input
- **Solution**: Insert conversion node to transform `color3` to `vector3`

### 3. Output Chaining Error

**Problem**: The exporter creates invalid output chains that reference other outputs instead of nodes.

**Current (Incorrect)**:
```xml
<output name="base_color" type="color3" nodename="colorramp_Color_Ramp" />
<output name="base_color2" type="color3" nodename="base_color" />
```

**Issue**: `base_color2` connects to the `base_color` output instead of a node, which violates MaterialX specification.

**Specification Reference**: MaterialX Specification v1.39, Section "Output Elements":
> "`nodename` (string, optional): the name of a node at the same scope within the document, whose result value will be output. This attribute is required for `<output>` elements within a node graph, but is not allowed in `<output>` elements within a `<nodedef>`."

## Recommended Fixes

### Fix 1: Correct Nodegraph Connection Syntax

**File**: `materialx_addon/materialx_library_core.py`
**Method**: `add_surface_shader_input`

**Current Code**:
```python
self.node_builder.create_mtlx_input(surface_node, input_name, nodename=f"{nodegraph_name}.{input_name}", node_type='standard_surface', category='surfaceshader')
```

**Proposed Fix**:
```python
input_elem = surface_node.addInput(input_name, input_type)
if input_elem:
    input_elem.setAttribute('nodegraph', nodegraph_name)
    input_elem.setAttribute('output', input_name)
```

### Fix 2: Add Automatic Type Conversion

**File**: `materialx_addon/materialx_library_core.py`
**Method**: `connect_nodes`

Add type validation and automatic conversion node insertion:

```python
def _connect_with_conversion(self, from_node: mx.Node, from_output: str, 
                            to_node: mx.Node, to_input: str, from_type: str, to_type: str) -> bool:
    """Connect nodes with automatic type conversion."""
    conversion_node = self._create_conversion_node(from_type, to_type, from_node.getParent())
    if conversion_node:
        # Connect source to conversion node
        self._direct_connect_nodes(from_node, from_output, conversion_node, 'in')
        # Connect conversion node to target
        self._direct_connect_nodes(conversion_node, 'out', to_node, to_input)
        return True
    return False

def _create_conversion_node(self, from_type: str, to_type: str, parent: mx.Element) -> Optional[mx.Node]:
    """Create appropriate conversion node based on type transformation needed."""
    conversion_name = f"convert_{from_type}_to_{to_type}_{id(self)}"
    conversion_node = parent.addChildOfCategory('convert', conversion_name)
    conversion_node.setType(to_type)
    return conversion_node
```

### Fix 3: Fix Output Chaining

**File**: `materialx_addon/materialx_library_core.py`
**Method**: `add_output`

Ensure outputs always connect to actual nodes, not other outputs:

```python
def add_output(self, name: str, output_type: str, nodename: str):
    """Add an output node to the nodegraph."""
    if self.nodegraph:
        # Validate that nodename refers to an actual node, not an output
        if not self.nodegraph.getChild(nodename):
            self.logger.warning(f"Output {name} references non-existent node: {nodename}")
            return None
        
        valid_name = self.nodegraph.createValidChildName(name)
        output = self.nodegraph.addOutput(valid_name, output_type)
        if output:
            output.setNodeName(nodename)
        return output
```

### Fix 4: Enhanced Type Validation

**File**: `materialx_addon/materialx_library_core.py`
**Method**: `connect_nodes`

Improve type checking before making connections:

```python
def connect_nodes(self, from_node: mx.Node, from_output: str, 
                 to_node: mx.Node, to_input: str) -> bool:
    """Connect two nodes with type validation and automatic conversion."""
    # Get output type from source node
    from_type = self._get_node_output_type(from_node, from_output)
    
    # Get input type from target node
    to_type = self._get_node_input_type(to_node, to_input)
    
    # Check type compatibility
    if self.type_converter.validate_type_compatibility(from_type, to_type):
        return self._direct_connect_nodes(from_node, from_output, to_node, to_input)
    else:
        # Types are incompatible, need conversion
        return self._connect_with_conversion(from_node, from_output, to_node, to_input, from_type, to_type)
```

## Implementation Priority

1. **High Priority**: Fix nodegraph connection syntax (Fix 1)
   - This is the primary cause of BSDF disconnection in MaterialX Graph Viewer
   - Affects all complex materials with nodegraphs

2. **Medium Priority**: Add type conversion (Fix 2)
   - Required for proper node connections within nodegraphs
   - Prevents type mismatch errors

3. **Medium Priority**: Fix output chaining (Fix 3)
   - Ensures valid MaterialX document structure
   - Prevents output reference errors

4. **Low Priority**: Enhanced type validation (Fix 4)
   - Improves robustness and error handling
   - Better debugging information

## Testing Strategy

### Test Cases to Verify Fixes

1. **Simple Principled BSDF**: Should work as before (no nodegraph)
2. **ComplexProcedural.mtlx**: Should load properly in MaterialX Graph Viewer
3. **TextureBased.mtlx**: Should have proper type conversions
4. **All test materials**: Should validate without errors

### Validation Steps

1. Export test materials using the fixed exporter
2. Load exported .mtlx files in MaterialX Graph Viewer
3. Verify BSDF connections are properly established
4. Check that all node connections are valid
5. Validate MaterialX documents using MaterialX validation tools

## Expected Results

After implementing these fixes:

- Complex materials should load properly in MaterialX Graph Viewer
- BSDF nodes should be correctly connected to their input nodegraphs
- Type conversion nodes should be automatically inserted where needed
- All exported .mtlx files should pass MaterialX validation
- The exporter should handle type mismatches gracefully

## References

- MaterialX Specification v1.39: `Specification/MaterialX.Specification.md`
- MaterialX Standard Nodes: `Specification/MaterialX.StandardNodes.md`
- Current test outputs: `test_output_mtlx/`
- Reference materials: `StandardSurface/` 