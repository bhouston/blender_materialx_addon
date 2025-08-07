# Nodegraph-Based MaterialX Export Implementation Plan

## Overview

Currently, the MaterialX exporter always places the `standard_surface` at the document level, outside of any nodegraph. However, MaterialX supports two different architectural patterns:

1. **Direct Materials** - `standard_surface` at document level (current implementation)
2. **Nodegraph-Based Materials** - `standard_surface` inside the nodegraph (target implementation)

This plan outlines the changes needed to support nodegraph-based materials for complex node networks.

## Current Issues

### 1. Standard Surface Placement
- **Problem**: `standard_surface` is always outside nodegraph
- **Impact**: Materials with complex node networks don't match MaterialX reference patterns
- **Example**: `MTLX_Checkerboard.mtlx` has `standard_surface` outside, but reference has it inside

### 2. Math Node Connections
- **Problem**: Math nodes (`modulo`, `ifgreater`) are created but missing input connections
- **Impact**: Node networks are incomplete and non-functional
- **Example**: `modulo` node should have `in1="fractal3d_Noise_Texture" in2="2.0"`

## Context and Background

### Current Exporter Architecture
The current MaterialX exporter uses a single pattern for all materials:
- All nodes are placed inside a nodegraph
- The `standard_surface` is always placed at the document level (outside nodegraph)
- Connections are made from nodegraph outputs to the `standard_surface` inputs

### MaterialX Reference Patterns
MaterialX supports two distinct architectural patterns:

1. **Direct Materials** (Simple): `standard_surface` at document level with direct parameter values
2. **Nodegraph-Based Materials** (Complex): `standard_surface` inside nodegraph with connected inputs

### Official MaterialX Examples
The MaterialX project provides reference examples in `examples/standard_surface/`:
- `checkerboard_test.mtlx` - Complex nodegraph with `standard_surface` inside
- `brick_test.mtlx` - Procedural brick pattern with math operations
- `concrete_test.mtlx` - Noise-based concrete material
- `dirt_test.mtlx` - Procedural dirt material
- `single_color_test.mtlx` - Simple direct material pattern

## Reference MaterialX Patterns

### Pattern 1: Direct Materials (Simple)
```xml
<standard_surface name="surface_Principled_BSDF" type="surfaceshader">
  <input name="base_color" type="color3" value="1,0,0"/>
</standard_surface>
<surfacematerial name="material">
  <input name="surfaceshader" nodename="surface_Principled_BSDF"/>
</surfacematerial>
```

### Pattern 2: Nodegraph-Based Materials (Complex)
```xml
<nodegraph name="NG_checkerboard">
  <input name="texcoord" type="vector2"/>
  <cellnoise3d name="checker_noise" position="[texcoord.x, texcoord.y, 0.0]"/>
  <modulo name="checker_mod" in1="checker_noise.out" in2="2.0"/>
  <ifgreater name="checker_if" in1="checker_mod.out" in2="1.0" in3="1.0" in4="0.0"/>
  <mix name="checker_mix" fg="color_white" bg="color_black" amount="checker_if.out"/>
  <standard_surface name="checker_surface" base_color="checker_mix.out"/>
</nodegraph>
<surfacematerial name="checkerboard_mat">
  <input name="surfaceshader" nodename="checker_surface"/>
</surfacematerial>
```

## Implementation Plan

### Phase 1: Material Complexity Detection

#### 1.1 Add Material Complexity Analyzer
**File**: `materialx_addon/blender_materialx_exporter.py`

```python
class MaterialComplexityAnalyzer:
    """Analyzes material complexity to determine export pattern."""
    
    @staticmethod
    def should_use_nodegraph(material: bpy.types.Material) -> bool:
        """
        Determine if material should use nodegraph-based export.
        
        Criteria:
        - Has more than 3 nodes (excluding Principled BSDF and Material Output)
        - Has math operations (MATH, VECTOR_MATH nodes)
        - Has texture nodes with connections
        - Has procedural texture chains
        """
        pass
    
    @staticmethod
    def get_node_count(material: bpy.types.Material) -> int:
        """Count non-trivial nodes in material."""
        pass
    
    @staticmethod
    def has_complex_operations(material: bpy.types.Material) -> bool:
        """Check for math operations, procedural textures, etc."""
        pass
```

#### 1.2 Integration Points
- **MaterialXExporter.export()**: Call complexity analyzer before export
- **Export decision**: Choose between direct and nodegraph-based export

### Phase 2: Nodegraph-Based Export Architecture

#### 2.1 Create NodegraphBuilder Class
**File**: `materialx_addon/materialx_library_core.py`

```python
class NodegraphBuilder:
    """Handles creation of nodegraph-based MaterialX documents."""
    
    def __init__(self, material_name: str, logger, version: str = "1.39"):
        self.material_name = material_name
        self.logger = logger
        self.version = version
        self.document = None
        self.nodegraph = None
        self.surface_shader = None
        self.nodes = {}
        
    def create_nodegraph_document(self) -> bool:
        """Create MaterialX document with nodegraph structure."""
        pass
    
    def add_node_to_nodegraph(self, node_type: str, name: str, **params) -> str:
        """Add node inside the nodegraph."""
        pass
    
    def add_surface_shader_to_nodegraph(self, node_type: str, name: str, **params) -> str:
        """Add surface shader inside the nodegraph."""
        pass
    
    def add_connection_in_nodegraph(self, from_node: str, from_output: str, 
                                   to_node: str, to_input: str) -> bool:
        """Add connection between nodes in nodegraph."""
        pass
    
    def add_nodegraph_output(self, name: str, output_type: str, nodename: str) -> bool:
        """Add output to nodegraph."""
        pass
```

#### 2.2 Modify MaterialXBuilder
**File**: `materialx_addon/materialx_library_core.py`

```python
class MaterialXBuilder:
    """Enhanced builder supporting both direct and nodegraph patterns."""
    
    def __init__(self, material_name: str, logger, version: str = "1.39", 
                 use_nodegraph: bool = False):
        self.use_nodegraph = use_nodegraph
        if use_nodegraph:
            self.nodegraph_builder = NodegraphBuilder(material_name, logger, version)
        else:
            # Existing direct material logic
            pass
    
    def add_node(self, node_type: str, name: str, **params) -> str:
        """Add node using appropriate builder."""
        if self.use_nodegraph:
            return self.nodegraph_builder.add_node_to_nodegraph(node_type, name, **params)
        else:
            # Existing logic
            pass
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """Add surface shader using appropriate builder."""
        if self.use_nodegraph:
            return self.nodegraph_builder.add_surface_shader_to_nodegraph(node_type, name, **params)
        else:
            # Existing logic
            pass
```

### Phase 3: Math Node Connection Fixes

#### 3.1 Enhanced Connection Detection
**File**: `materialx_addon/blender_materialx_exporter.py`

```python
def get_math_node_connections(node: bpy.types.Node, exported_nodes: Dict) -> Dict[str, str]:
    """
    Get all connections for math nodes.
    
    Returns:
        Dict mapping MaterialX input names to source node names
    """
    connections = {}
    
    # Handle input indices for math nodes
    for i, input_socket in enumerate(node.inputs):
        if input_socket.is_linked and input_socket.links:
            from_node = input_socket.links[0].from_node
            if from_node in exported_nodes:
                mtlx_input_name = f"in{i+1}"  # in1, in2, etc.
                connections[mtlx_input_name] = exported_nodes[from_node]
    
    return connections
```

#### 3.2 Update Math Node Mapping
**File**: `materialx_addon/blender_materialx_exporter.py`

```python
@staticmethod
def map_math_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, 
                     input_nodes_by_index: Dict = None, blender_node=None, 
                     constant_manager=None, exported_nodes=None) -> str:
    """Enhanced math mapping with proper connection handling."""
    
    # Get operation and create node
    operation = node.operation.lower()
    mtlx_operation = get_mtlx_operation(operation)
    node_name = builder.add_node(mtlx_operation, f"{mtlx_operation}_{node.name}", "float")
    
    # Get all connections
    connections = get_math_node_connections(node, exported_nodes)
    
    # Add connections
    for mtlx_input, source_node in connections.items():
        builder.add_connection(source_node, "out", node_name, mtlx_input)
    
    # Add default values for unconnected inputs
    add_math_default_values(node_name, mtlx_operation, connections, builder)
    
    return node_name
```

### Phase 4: Export Strategy Implementation

#### 4.1 Modify MaterialXExporter
**File**: `materialx_addon/blender_materialx_exporter.py`

```python
class MaterialXExporter:
    def __init__(self, material: bpy.types.Material, output_path: str, logger, options: Dict = None):
        self.material = material
        self.output_path = output_path
        self.logger = logger
        self.options = options or {}
        
        # Determine export strategy
        self.use_nodegraph = MaterialComplexityAnalyzer.should_use_nodegraph(material)
        self.logger.info(f"Material complexity analysis: {'nodegraph' if self.use_nodegraph else 'direct'}")
    
    def export(self) -> dict:
        """Export material using appropriate strategy."""
        if self.use_nodegraph:
            return self._export_nodegraph_material()
        else:
            return self._export_direct_material()
    
    def _export_nodegraph_material(self) -> dict:
        """Export material using nodegraph-based pattern."""
        # Implementation for nodegraph-based export
        pass
    
    def _export_direct_material(self) -> dict:
        """Export material using direct pattern (existing logic)."""
        # Existing export logic
        pass
```

### Phase 5: Testing and Validation

#### 5.1 Test Cases

**Test Files Location**: `examples/blender/` (existing test materials)

##### Simple Materials (should use direct pattern):
1. **SimplePrincipled.blend** - Single Principled BSDF with basic parameters
   - **Expected Pattern**: Direct
   - **Validation**: `standard_surface` at document level with direct values
   - **Reference**: `examples/standard_surface/single_color_test.mtlx`

2. **MTLX_Gold.blend** - Gold material with basic parameters
   - **Expected Pattern**: Direct
   - **Validation**: `standard_surface` at document level
   - **Reference**: `examples/standard_surface/standard_surface_gold.mtlx`

3. **MTLX_Glass.blend** - Glass material with IOR and transmission
   - **Expected Pattern**: Direct
   - **Validation**: `standard_surface` at document level
   - **Reference**: `examples/standard_surface/standard_surface_glass.mtlx`

##### Complex Materials (should use nodegraph pattern):
1. **MTLX_Checkerboard.blend** - Checkerboard with math operations
   - **Expected Pattern**: Nodegraph
   - **Validation**: `standard_surface` inside nodegraph
   - **Reference**: `examples/standard_surface/checkerboard_test.mtlx`
   - **Key Features**: Math nodes (modulo, ifgreater), texture coordinates, mix operations

2. **ComplexProcedural.blend** - Complex procedural wood material
   - **Expected Pattern**: Nodegraph
   - **Validation**: `standard_surface` inside nodegraph
   - **Reference**: `examples/standard_surface/compatible_export.mtlx`
   - **Key Features**: Multiple noise textures, color ramps, math operations

3. **MathHeavy.blend** - Material with extensive math operations
   - **Expected Pattern**: Nodegraph
   - **Validation**: `standard_surface` inside nodegraph
   - **Key Features**: Multiple math nodes, vector operations, complex chains

4. **TextureBased.blend** - Material with texture chains
   - **Expected Pattern**: Nodegraph
   - **Validation**: `standard_surface` inside nodegraph
   - **Key Features**: Texture coordinates, noise textures, color ramps

5. **MathNodes.blend** - Material with various math operations
   - **Expected Pattern**: Nodegraph
   - **Validation**: `standard_surface` inside nodegraph
   - **Key Features**: Different math operations, connections between math nodes

##### Edge Cases:
1. **MixedShader.blend** - Material mixing different shaders
   - **Expected Pattern**: Direct (simple mixing)
   - **Validation**: `standard_surface` at document level
   - **Note**: Mix shader operations are handled differently

2. **EmissionMaterial.blend** - Emission shader material
   - **Expected Pattern**: Direct
   - **Validation**: `standard_surface` at document level
   - **Note**: Emission is a parameter, not a complex node network

#### 5.2 Validation Criteria

##### Pattern Selection Validation:
- **Simple Materials**: Should use direct pattern (current behavior)
- **Complex Materials**: Should use nodegraph pattern (new behavior)
- **Automatic Detection**: Complexity analyzer correctly identifies material type

##### Nodegraph Structure Validation:
- **Simple Materials**: `standard_surface` at document level
- **Complex Materials**: `standard_surface` inside nodegraph
- **Nodegraph Naming**: Consistent naming convention (e.g., `NG_materialname`)

##### Math Connections Validation:
- **Math Node Creation**: All math nodes created with correct MaterialX types
- **Input Connections**: All math node inputs properly connected
- **Default Values**: Unconnected inputs have appropriate default values
- **Operation Mapping**: Blender math operations correctly mapped to MaterialX

##### MaterialX Compliance:
- **Schema Validation**: All exported files pass MaterialX schema validation
- **Version Compatibility**: Files work with MaterialX 1.39
- **Colorspace**: Proper colorspace attributes set

##### Reference Compatibility:
- **Structure Match**: Exported files match official MaterialX reference patterns
- **Node Types**: Correct MaterialX node types used
- **Connection Patterns**: Connections follow MaterialX conventions

##### Specific Test Validations:

###### MTLX_Checkerboard.blend → checkerboard_test.mtlx:
- [ ] `standard_surface` inside nodegraph
- [ ] `modulo` node has `in1="fractal3d_Noise_Texture" in2="2.0"`
- [ ] `ifgreater` node has `in1="modulo_Math" in2="1.0" in3="1.0" in4="0.0"`
- [ ] `mix` node connected to `ifgreater` output
- [ ] `standard_surface` connected to `mix` output

###### ComplexProcedural.blend → compatible_export.mtlx:
- [ ] `standard_surface` inside nodegraph
- [ ] All noise textures properly connected
- [ ] Math operations correctly mapped
- [ ] Color ramps properly exported

###### SimplePrincipled.blend → single_color_test.mtlx:
- [ ] `standard_surface` at document level
- [ ] Direct parameter values (no nodegraph)
- [ ] Simple material structure maintained

## Implementation Steps

### Step 1: Material Complexity Detection (Week 1)
1. Implement `MaterialComplexityAnalyzer` class
2. Add complexity detection to `MaterialXExporter`
3. Test with test cases:
   - **Simple Materials**: `SimplePrincipled.blend`, `MTLX_Gold.blend`, `MTLX_Glass.blend`
   - **Complex Materials**: `MTLX_Checkerboard.blend`, `ComplexProcedural.blend`, `MathHeavy.blend`
   - **Edge Cases**: `MixedShader.blend`, `EmissionMaterial.blend`

### Step 2: NodegraphBuilder Implementation (Week 2)
1. Create `NodegraphBuilder` class
2. Implement nodegraph-based document creation
3. Add surface shader placement inside nodegraph
4. Test with complex materials:
   - **Primary Test**: `MTLX_Checkerboard.blend` → `checkerboard_test.mtlx`
   - **Secondary Test**: `ComplexProcedural.blend` → `compatible_export.mtlx`

### Step 3: Math Connection Fixes (Week 3)
1. Implement enhanced connection detection
2. Update math node mapping
3. Test with math-heavy materials:
   - **Primary Test**: `MTLX_Checkerboard.blend` (modulo, ifgreater connections)
   - **Secondary Test**: `MathHeavy.blend` (complex math chains)
   - **Validation Test**: `MathNodes.blend` (various math operations)

### Step 4: Integration and Testing (Week 4)
1. Integrate all components
2. Comprehensive testing with all material types:
   - **Simple Materials**: Verify direct pattern maintained
   - **Complex Materials**: Verify nodegraph pattern implemented
   - **Edge Cases**: Verify proper handling
3. Validation against MaterialX reference files:
   - Compare exports with `examples/standard_surface/` references
   - Validate MaterialX schema compliance
   - Test with MaterialX validation tools

### Step 5: Documentation and Cleanup (Week 5)
1. Update documentation with new patterns
2. Add examples showing both direct and nodegraph patterns
3. Performance optimization and cleanup
4. Final validation with all test cases

## Expected Outcomes

### After Implementation:
1. **Automatic Pattern Selection**: Exporter automatically chooses appropriate pattern
2. **Nodegraph-Based Materials**: Complex materials use nodegraph structure
3. **Proper Math Connections**: All math node inputs correctly connected
4. **MaterialX Compliance**: Files match official MaterialX patterns
5. **Backward Compatibility**: Simple materials continue to work as before

### Example Output (Checkerboard):
```xml
<?xml version="1.0"?>
<materialx version="1.39" colorspace="lin_rec709">
  <nodegraph name="NG_checkerboard">
    <input name="texcoord" type="vector2"/>
    <fractal3d name="checker_noise" position="[texcoord.x, texcoord.y, 0.0]" scale="10"/>
    <modulo name="checker_mod" in1="checker_noise.out" in2="2.0"/>
    <ifgreater name="checker_if" in1="checker_mod.out" in2="1.0" in3="1.0" in4="0.0"/>
    <mix name="checker_mix" fg="1,1,1" bg="0,0,0" amount="checker_if.out"/>
    <standard_surface name="checker_surface" base_color="checker_mix.out"/>
  </nodegraph>
  <surfacematerial name="checkerboard_mat">
    <input name="surfaceshader" nodename="checker_surface"/>
  </surfacematerial>
</materialx>
```

## Risk Assessment

### Low Risk:
- Material complexity detection (well-defined criteria)
- Math connection fixes (isolated changes)

### Medium Risk:
- NodegraphBuilder implementation (new architecture)
- Integration with existing codebase

### Mitigation Strategies:
1. **Incremental Implementation**: Implement and test each phase separately
2. **Backward Compatibility**: Ensure simple materials continue to work
3. **Comprehensive Testing**: Test with wide variety of material types
4. **Fallback Mechanism**: Fall back to direct pattern if nodegraph fails

## Success Metrics

### Quantitative Metrics:
1. **Pattern Selection Accuracy**: 100% correct pattern selection for test materials
2. **Math Connection Completeness**: All math node inputs properly connected
3. **MaterialX Validation**: All exported files pass MaterialX validation
4. **Reference Compatibility**: Exported files match official MaterialX patterns
5. **Performance**: No significant performance degradation (< 10% increase in export time)
6. **Backward Compatibility**: All existing materials continue to export correctly

### Specific Test Case Success Criteria:

#### Simple Materials (Direct Pattern):
- [ ] `SimplePrincipled.blend` → `standard_surface` at document level
- [ ] `MTLX_Gold.blend` → `standard_surface` at document level
- [ ] `MTLX_Glass.blend` → `standard_surface` at document level

#### Complex Materials (Nodegraph Pattern):
- [ ] `MTLX_Checkerboard.blend` → `standard_surface` inside nodegraph
- [ ] `ComplexProcedural.blend` → `standard_surface` inside nodegraph
- [ ] `MathHeavy.blend` → `standard_surface` inside nodegraph
- [ ] `TextureBased.blend` → `standard_surface` inside nodegraph
- [ ] `MathNodes.blend` → `standard_surface` inside nodegraph

#### Math Connection Validation:
- [ ] `MTLX_Checkerboard.blend`: `modulo` node has proper `in1` and `in2` connections
- [ ] `MTLX_Checkerboard.blend`: `ifgreater` node has proper `in1`, `in2`, `in3`, `in4` connections
- [ ] `MathHeavy.blend`: All math operations properly connected
- [ ] `MathNodes.blend`: All math node types correctly mapped

#### Reference File Comparison:
- [ ] `MTLX_Checkerboard.mtlx` structure matches `checkerboard_test.mtlx`
- [ ] `ComplexProcedural.mtlx` structure matches `compatible_export.mtlx`
- [ ] `SimplePrincipled.mtlx` structure matches `single_color_test.mtlx`

### Quality Gates:
- **Phase 1**: All simple materials export correctly with direct pattern
- **Phase 2**: All complex materials export with nodegraph pattern
- **Phase 3**: All math connections properly established
- **Phase 4**: All test cases pass validation
- **Phase 5**: Documentation complete and performance acceptable 