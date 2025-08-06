# MaterialX Node Emulation Planning Document

## Overview

This document outlines strategies for supporting Blender nodes that don't have direct MaterialX equivalents by creating node networks that emulate the missing functionality.

## Problem Statement

Many Blender nodes (like Brick Texture, Musgrave Texture, etc.) don't have direct MaterialX equivalents. Currently, these are handled as unsupported nodes with error messages. However, we could provide better support by creating MaterialX node networks that emulate the Blender functionality.

## Proposed Solutions

### Solution 1: Direct Node Network Emulation

**Approach:** Create complex MaterialX node networks that replicate Blender node behavior using existing MaterialX nodes.

**Implementation:**
- Define emulation templates for each unsupported Blender node
- During export, replace unsupported nodes with their emulation networks
- Use existing MaterialX nodes (math, noise, mix, etc.) to build the functionality

**Example - Brick Texture Emulation:**
```
Brick Texture → [Checkerboard + Math nodes for mortar + Transform for brick pattern]
```

**Pros:**
- ✅ Provides actual functionality instead of error messages
- ✅ Uses only standard MaterialX nodes
- ✅ Results in portable MaterialX files
- ✅ No post-processing required

**Cons:**
- ❌ Complex to implement and maintain
- ❌ May not perfectly replicate Blender behavior
- ❌ Large node networks for complex nodes
- ❌ Performance impact from complex networks

### Solution 2: Custom Node Definitions with Post-Processing

**Approach:** Export unsupported nodes as custom MaterialX node definitions, then post-process to expand them into standard node networks.

**Implementation:**
- Create custom MaterialX node definitions for unsupported Blender nodes
- Export using these custom definitions
- Post-process the MaterialX file to replace custom nodes with standard node networks
- Use MaterialX's node definition system for the expansion

**Example:**
```xml
<!-- Custom node definition -->
<nodedef name="ND_brick_color3" node="brick" type="color3">
  <input name="texcoord" type="vector2" value="0,0" />
  <input name="color1" type="color3" value="1,0,0" />
  <input name="color2" type="color3" value="0,0,1" />
  <input name="mortar" type="color3" value="0.5,0.5,0.5" />
  <!-- ... other inputs -->
</nodedef>

<!-- Post-processing expands to: -->
<nodegraph name="brick_emulation">
  <!-- Complex node network using standard MaterialX nodes -->
</nodegraph>
```

**Pros:**
- ✅ Clean separation between export and emulation logic
- ✅ Can use MaterialX's built-in node definition system
- ✅ Easier to maintain and update emulation logic
- ✅ Can cache expanded networks for performance

**Cons:**
- ❌ Requires post-processing step
- ❌ More complex MaterialX files during intermediate stages
- ❌ Need to implement MaterialX node definition expansion

### Solution 3: Hybrid Approach with Emulation Registry

**Approach:** Combine direct emulation with a registry system that can be extended and updated.

**Implementation:**
- Create an emulation registry that maps Blender node types to emulation functions
- Each emulation function returns a MaterialX node network
- Support both immediate expansion and custom node definition approaches
- Allow for different emulation strategies based on complexity

**Example Registry:**
```python
EMULATION_REGISTRY = {
    'TEX_BRICK': {
        'strategy': 'direct_network',
        'emulation_func': create_brick_emulation_network,
        'complexity': 'high'
    },
    'TEX_MUSGRAVE': {
        'strategy': 'custom_definition',
        'emulation_func': create_musgrave_definition,
        'complexity': 'medium'
    }
}
```

**Pros:**
- ✅ Flexible approach that can handle different node types optimally
- ✅ Easy to extend and maintain
- ✅ Can choose best strategy per node type
- ✅ Supports both simple and complex emulations

**Cons:**
- ❌ More complex implementation
- ❌ Requires careful design of registry system
- ❌ Need to maintain multiple emulation strategies

### Solution 4: MaterialX Library Extension

**Approach:** Create a custom MaterialX library with node definitions that emulate Blender functionality.

**Implementation:**
- Create a custom MaterialX library file with node definitions
- Define nodes that map to Blender functionality
- Load this library alongside standard MaterialX libraries
- Export using these custom definitions

**Example Library:**
```xml
<!-- custom_blender_nodes.mtlx -->
<library name="blender_emulation">
  <nodedef name="ND_brick_color3" node="brick" type="color3">
    <!-- Node definition that emulates Blender brick texture -->
  </nodedef>
</library>
```

**Pros:**
- ✅ Uses MaterialX's native extension system
- ✅ Clean and portable approach
- ✅ Can be shared across different tools
- ✅ Leverages MaterialX's node definition system

**Cons:**
- ❌ Requires implementing the actual node functionality
- ❌ May not be supported by all MaterialX renderers
- ❌ Need to maintain custom MaterialX library
- ❌ More complex than standard node networks

## Recommended Approach

**Primary Recommendation: Solution 1 (Direct Node Network Emulation)**

**Rationale:**
1. **Immediate Value**: Provides actual functionality instead of error messages
2. **Portability**: Results in standard MaterialX files that work everywhere
3. **Simplicity**: No post-processing or custom libraries required
4. **Maintainability**: Easier to debug and understand

**Implementation Strategy:**

### Phase 1: Simple Emulations
Start with simple nodes that can be easily emulated:
- **Brick Texture**: Use checkerboard + math nodes for mortar lines
- **Musgrave Texture**: Use fractal3d with different parameters
- **Wave Texture**: Use sin/cos math nodes with transforms

### Phase 2: Complex Emulations
Move to more complex nodes:
- **Voronoi Texture**: Use noise + math for distance calculations
- **Color Ramp**: Use ramplr with custom curve definitions
- **Geometry Nodes**: Use position + math for derived values

### Phase 3: Advanced Features
Add advanced emulation features:
- **Performance Optimization**: Cache common emulation networks
- **Quality Settings**: Different emulation quality levels
- **Fallback Strategies**: Graceful degradation for complex nodes

## Implementation Plan

### Step 1: Create Emulation Framework
```python
class NodeEmulator:
    def __init__(self, builder: MaterialXBuilder):
        self.builder = builder
        self.emulation_cache = {}
    
    def emulate_node(self, blender_node, exported_nodes):
        """Emulate a Blender node using MaterialX node networks."""
        node_type = blender_node.type
        if node_type in EMULATION_REGISTRY:
            return EMULATION_REGISTRY[node_type](blender_node, self.builder, exported_nodes)
        return None
```

### Step 2: Define Emulation Functions
```python
def emulate_brick_texture(blender_node, builder, exported_nodes):
    """Emulate Blender brick texture using MaterialX nodes."""
    # Create checkerboard for basic brick pattern
    checker = builder.add_node("checkerboard", f"brick_checker_{blender_node.name}", "color3")
    
    # Create math nodes for mortar lines
    mortar_math = builder.add_node("math", f"brick_mortar_{blender_node.name}", "float")
    
    # Connect and return final node
    return final_node_name
```

### Step 3: Integrate with Export Pipeline
```python
def _export_node(self, node: bpy.types.Node) -> str:
    # Try normal mapping first
    mapper = NodeMapper.get_node_mapper(node.type)
    if mapper:
        return mapper(node, self.builder, ...)
    
    # Try emulation if no direct mapping
    emulator = NodeEmulator(self.builder)
    emulated_node = emulator.emulate_node(node, self.exported_nodes)
    if emulated_node:
        return emulated_node
    
    # Fall back to unsupported node handling
    return self._export_unknown_node(node)
```

## Testing Strategy

### Unit Tests
- Test each emulation function independently
- Verify output matches expected MaterialX structure
- Test with various input parameters

### Integration Tests
- Test complete material export with emulated nodes
- Verify MaterialX files are valid and render correctly
- Test performance impact of emulation networks

### Visual Tests
- Compare rendered results between Blender and MaterialX
- Test with different renderers (Arnold, RenderMan, etc.)
- Validate that emulations are visually acceptable

## Future Considerations

### Performance Optimization
- Cache common emulation networks
- Optimize node networks for rendering performance
- Consider different emulation quality levels

### Quality Improvements
- Iteratively improve emulation accuracy
- Add more sophisticated emulation algorithms
- Support for advanced Blender node features

### Extensibility
- Plugin system for custom emulations
- User-defined emulation rules
- Community-contributed emulation functions

## Conclusion

The direct node network emulation approach provides the best balance of functionality, portability, and maintainability. By implementing this system, we can significantly expand the range of Blender nodes supported by the MaterialX exporter while maintaining compatibility with standard MaterialX renderers.

The key is to start simple and iterate, focusing on the most commonly used nodes first and gradually expanding to more complex functionality. 