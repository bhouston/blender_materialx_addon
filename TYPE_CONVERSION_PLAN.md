# MaterialX Exporter Type Conversion Plan

## Current Issues Analysis

### 1. **Problem Statement**
The MaterialX exporter currently has inconsistent and unsustainable type conversion handling:
- Special case conversions added to specific node mappers (`map_math_enhanced`, `map_noise_texture_enhanced`)
- Enhanced type conversion system in `MaterialXNodeBuilder` that creates placeholder nodes
- Manual type conversion attempts that fail with MaterialX Graph Viewer compatibility issues
- No unified approach to handle type mismatches across all node connections

### 2. **Current Special Case Conversions (To Be Removed)**

#### A. `map_math_enhanced` in `blender_materialx_exporter.py` (Lines ~1470-1490)
```python
# Handle type conversion for specific cases
if source_node_type == 'TEX_NOISE' and mtlx_operation in ['modulo', 'ifgreater']:
    # Create a luminance node to convert color3 to float
    luminance_node_name = f"luminance_{value_or_node}"
    # ... manual conversion logic
```
**Issues:**
- Only handles TEX_NOISE to math node conversions
- Creates luminance nodes that may not have proper MaterialX definitions
- Hardcoded for specific node types and operations

#### B. `map_noise_texture_enhanced` in `blender_materialx_exporter.py` (Lines ~1580-1620)
```python
# Handle vector2 to vector3 conversion for position input
if mtlx_param == 'texcoord' and type_str == 'VECTOR':
    # Create a combine3 node to convert vector2 to vector3
    combine_node_name = f"combine_{value_or_node}_to_vector3"
    # ... manual conversion logic
```
**Issues:**
- Only handles vector2 to vector3 conversion for noise textures
- Uses direct MaterialX library calls that bypass the connection system
- Not reusable for other node types

#### C. Enhanced Type Conversion System in `MaterialXNodeBuilder` (Lines ~1400-1500)
```python
def _connect_with_conversion(self, from_node, from_output, to_node, to_input, from_type, to_type):
    # Creates conversion nodes like 'convert_color3_to_float_XXXX'
    conversion_node = self._create_conversion_node(from_type, to_type, from_node.getParent())
```
**Issues:**
- Creates placeholder nodes with generic names
- Conversion nodes often lack proper MaterialX node definitions
- Results in MaterialX Graph Viewer errors

## Proposed Solution: Automatic Type Conversion System

### 1. **Core Design Principles**

#### A. **Centralized Type Conversion**
- Single point of type conversion logic in the connection system
- No special case handling in individual node mappers
- Consistent behavior across all node types

#### B. **MaterialX-Compliant Conversions**
- Use only valid MaterialX nodes for conversions
- Ensure all conversion nodes have proper node definitions
- Maintain compatibility with MaterialX Graph Viewer

#### C. **Transparent Operation**
- Type conversion happens automatically during connection
- Node mappers don't need to know about type conversion
- Clean separation of concerns

### 2. **Implementation Strategy**

#### Phase 1: Type Conversion Registry
Create a centralized registry of valid MaterialX type conversions:

```python
MATERIALX_TYPE_CONVERSIONS = {
    # Vector conversions
    ('vector2', 'vector3'): {
        'node_type': 'combine3',
        'node_def': 'ND_combine3_vector3',
        'input_mapping': {'in1': 'source', 'in2': '0', 'in3': '0'},
        'output': 'out'
    },
    ('vector3', 'vector2'): {
        'node_type': 'separate3',
        'node_def': 'ND_separate3_vector2',
        'input_mapping': {'in': 'source'},
        'output': 'out'
    },
    
    # Color conversions
    ('color3', 'float'): {
        'node_type': 'luminance',
        'node_def': 'ND_luminance_color3',
        'input_mapping': {'in': 'source'},
        'output': 'out'
    },
    ('float', 'color3'): {
        'node_type': 'combine3',
        'node_def': 'ND_combine3_color3',
        'input_mapping': {'in1': 'source', 'in2': 'source', 'in3': 'source'},
        'output': 'out'
    },
    
    # Additional conversions...
}
```

#### Phase 2: Enhanced Connection System
Modify the `connect_nodes` method in `MaterialXNodeBuilder`:

```python
def connect_nodes(self, from_node, from_output, to_node, to_input):
    """Connect nodes with automatic type conversion."""
    from_type = self._get_node_output_type(from_node, from_output)
    to_type = self._get_node_input_type(to_node, to_input)
    
    if from_type == to_type:
        # Direct connection
        return self._direct_connect_nodes(from_node, from_output, to_node, to_input)
    
    # Check if conversion is supported
    conversion_key = (from_type, to_type)
    if conversion_key in MATERIALX_TYPE_CONVERSIONS:
        return self._connect_with_automatic_conversion(
            from_node, from_output, to_node, to_input, conversion_key
        )
    
    # Unsupported conversion
    raise MaterialXError(f"Unsupported type conversion: {from_type} -> {to_type}")
```

#### Phase 3: Automatic Conversion Implementation
```python
def _connect_with_automatic_conversion(self, from_node, from_output, to_node, to_input, conversion_key):
    """Create and connect conversion node automatically."""
    conversion_spec = MATERIALX_TYPE_CONVERSIONS[conversion_key]
    
    # Create conversion node
    conversion_name = f"convert_{from_node.getName()}_{to_node.getName()}_{conversion_key[0]}_to_{conversion_key[1]}"
    conversion_node = self._create_node_with_definition(
        conversion_spec['node_type'],
        conversion_name,
        conversion_spec['node_def']
    )
    
    # Connect source to conversion node
    source_input = conversion_spec['input_mapping']['in']
    self._direct_connect_nodes(from_node, from_output, conversion_node, source_input)
    
    # Connect conversion node to target
    self._direct_connect_nodes(conversion_node, conversion_spec['output'], to_node, to_input)
    
    return True
```

### 3. **MaterialX Node Definition Management**

#### A. **Node Definition Validation**
- Ensure all conversion nodes have valid MaterialX node definitions
- Validate node definitions against MaterialX library
- Provide fallback options for missing definitions

#### B. **Common Conversion Nodes**
Focus on MaterialX nodes that are widely supported:
- `combine3` (vector3, color3)
- `separate3` (vector3, color3)
- `luminance` (color3 -> float)
- `normalize` (vector3)
- `length` (vector3 -> float)

### 4. **Migration Plan**

#### Step 1: Remove Special Case Conversions
1. Remove type conversion logic from `map_math_enhanced`
2. Remove type conversion logic from `map_noise_texture_enhanced`
3. Simplify these methods to use standard connection calls

#### Step 2: Implement Centralized System
1. Create `MATERIALX_TYPE_CONVERSIONS` registry
2. Implement `_connect_with_automatic_conversion` method
3. Update `connect_nodes` to use automatic conversion

#### Step 3: Test and Validate
1. Test with existing materials (MTLX_Checkerboard, etc.)
2. Verify MaterialX Graph Viewer compatibility
3. Ensure all existing functionality still works

### 5. **Benefits of This Approach**

#### A. **Scalability**
- New node types automatically get type conversion support
- No need to modify individual node mappers
- Consistent behavior across all connections

#### B. **Maintainability**
- Single point of truth for type conversion logic
- Easy to add new conversion types
- Clear separation of concerns

#### C. **Reliability**
- Uses only valid MaterialX nodes
- Proper node definitions ensure compatibility
- Consistent error handling

### 6. **Potential Challenges**

#### A. **MaterialX Node Definition Availability**
- Some conversion nodes may not be available in all MaterialX versions
- Need fallback strategies for missing definitions

#### B. **Performance**
- Additional nodes created for conversions
- Need to optimize for common conversion paths

#### C. **Complex Conversions**
- Some conversions may require multiple nodes
- Need to handle multi-step conversions

### 7. **Implementation Priority**

#### High Priority
1. Remove existing special case conversions
2. Implement basic type conversion registry
3. Update connection system

#### Medium Priority
1. Add comprehensive conversion coverage
2. Optimize conversion node creation
3. Add conversion caching

#### Low Priority
1. Complex multi-step conversions
2. Performance optimizations
3. Advanced conversion strategies

## Conclusion

The current approach of special case conversions is unsustainable and creates maintenance burden. A centralized automatic type conversion system will provide:

1. **Consistency** - All connections handled the same way
2. **Scalability** - Easy to add new node types and conversions
3. **Reliability** - Uses only valid MaterialX nodes
4. **Maintainability** - Single point of truth for conversion logic

This plan provides a robust foundation for handling type conversions in a way that scales with the exporter's growth and maintains compatibility with MaterialX standards. 