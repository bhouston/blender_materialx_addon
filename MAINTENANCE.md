# Blender MaterialX Addon - Maintenance Guide

This document explains how to add support for new Blender node types to the MaterialX addon. The addon uses an explicit mapping system to ensure robust translation between Blender and MaterialX node types.

## Overview

The addon uses three main components for node mapping:

1. **`NODE_MAPPING`** - Explicit Blender-to-MaterialX node type and input/output mapping
2. **`NODE_SCHEMAS`** - Type-safe input definitions for complex nodes
3. **`NodeMapper` class** - Mapper functions that handle the actual node creation

## Architecture

### 1. NODE_MAPPING Dictionary

Located in `materialx_addon/blender_materialx_exporter.py` around line 229.

**Purpose:** Provides explicit mapping between Blender node types and their MaterialX equivalents, including input/output name translations.

**Structure:**
```python
NODE_MAPPING = {
    'BLENDER_NODE_TYPE': {
        'mtlx_type': 'materialx_node_type',
        'mtlx_category': 'materialx_category',
        'inputs': {
            'Blender_Input_Name': 'MaterialX_Input_Name',
            # ... more inputs
        },
        'outputs': {
            'Blender_Output_Name': 'MaterialX_Output_Name',
            # ... more outputs
        }
    },
    # ... more node types
}
```

**Example:**
```python
'TEX_NOISE': {
    'mtlx_type': 'fractal3d',
    'mtlx_category': 'color3',
    'inputs': {
        'Vector': 'position',
        'Scale': 'lacunarity',
        'Detail': 'octaves',
        'Roughness': 'diminish',
    },
    'outputs': {
        'Fac': 'out',
        'Color': 'out',
    }
},
```

### 2. NODE_SCHEMAS Dictionary

Located in `materialx_addon/blender_materialx_exporter.py` around line 143.

**Purpose:** Provides type information and category for complex nodes that use schema-driven mapping.

**Structure:**
```python
NODE_SCHEMAS = {
    'NODE_TYPE': [
        {
            'blender': 'Blender_Input_Name',
            'mtlx': 'MaterialX_Input_Name', 
            'type': 'materialx_type',
            'category': 'materialx_category'
        },
        # ... more inputs
    ],
    # ... more node types
}
```

**Example:**
```python
'NOISE_TEXTURE': [
    {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
    {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
    {'blender': 'Detail', 'mtlx': 'detail', 'type': 'float', 'category': 'color3'},
    {'blender': 'Roughness', 'mtlx': 'roughness', 'type': 'float', 'category': 'color3'},
],
```

### 3. NodeMapper Class

Located in `materialx_addon/blender_materialx_exporter.py` around line 728.

**Purpose:** Contains mapper functions that handle the actual node creation and connection logic.

**Structure:**
```python
class NodeMapper:
    @staticmethod
    def get_node_mapper(node_type: str):
        """Get the appropriate mapper for a node type."""
        mappers = {
            'NODE_TYPE': NodeMapper.map_node_type_enhanced,
            # ... more mappers
        }
        return mappers.get(node_type)
    
    @staticmethod
    def map_node_type_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
        """Enhanced node type mapping with type-safe input creation."""
        return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['NODE_TYPE'], 'materialx_type', 'materialx_category', constant_manager, exported_nodes)
```

## How to Add a New Node Type

### Step 1: Identify the Blender Node Type

First, determine the exact Blender node type name. You can find this by:
1. Creating the node in Blender
2. Looking at the node's `bl_idname` property
3. Or checking the error messages when the addon encounters an unsupported node

### Step 2: Find the MaterialX Equivalent

Research what MaterialX node type corresponds to your Blender node:
1. Check the MaterialX documentation
2. Look at existing MaterialX node definitions
3. Use the `investigate_with_addon.py` script to explore available MaterialX nodes

**⚠️ IMPORTANT: Only add nodes that have direct MaterialX equivalents**

- **DO NOT** add nodes to the mapping tables if they don't have a direct MaterialX equivalent
- **DO NOT** create placeholder nodes or fallback mappings for unsupported functionality
- **DO** document unsupported nodes in error messages with helpful suggestions
- **DO** consider using the emulation system (see EMULATE_NODE_PLAN.md) for complex nodes without direct equivalents

If a Blender node doesn't have a direct MaterialX equivalent, it should be handled as an unsupported node with a helpful error message rather than creating a placeholder or incorrect mapping.

### Step 3: Add to NODE_MAPPING

Add an entry to the `NODE_MAPPING` dictionary:

```python
'YOUR_NODE_TYPE': {
    'mtlx_type': 'materialx_node_type',
    'mtlx_category': 'materialx_category',
    'inputs': {
        'Blender_Input_1': 'MaterialX_Input_1',
        'Blender_Input_2': 'MaterialX_Input_2',
        # ... map all inputs
    },
    'outputs': {
        'Blender_Output_1': 'MaterialX_Output_1',
        'Blender_Output_2': 'MaterialX_Output_2',
        # ... map all outputs
    }
},
```

**Important:** Map ALL inputs and outputs, even if they seem obvious. The explicit mapping system requires complete coverage.

### Step 4: Add to NODE_SCHEMAS (if needed)

For complex nodes, add a schema entry:

```python
'YOUR_NODE_TYPE': [
    {'blender': 'Input_1', 'mtlx': 'input_1', 'type': 'materialx_type', 'category': 'materialx_category'},
    {'blender': 'Input_2', 'mtlx': 'input_2', 'type': 'materialx_type', 'category': 'materialx_category'},
    # ... all inputs
],
```

### Step 5: Add Mapper Function

Add a mapper function to the `NodeMapper` class:

```python
@staticmethod
def map_your_node_type_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
    """Enhanced your node type mapping with type-safe input creation."""
    return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['YOUR_NODE_TYPE'], 'materialx_type', 'materialx_category', constant_manager, exported_nodes)
```

### Step 6: Register the Mapper

Add the mapper to the `get_node_mapper` function:

```python
mappers = {
    # ... existing mappers
    'YOUR_NODE_TYPE': NodeMapper.map_your_node_type_enhanced,
}
```

### Step 7: Test

1. Deploy the updated addon: `python3 dev_upgrade_addon.py`
2. Create a test material with your new node type
3. Export and verify the MaterialX output is correct

## Common MaterialX Node Types

### Basic Types
- `color3` - RGB color (3 floats)
- `color4` - RGBA color (4 floats)
- `float` - Single float value
- `vector2` - 2D vector (2 floats)
- `vector3` - 3D vector (3 floats)
- `vector4` - 4D vector (4 floats)
- `integer` - Integer value
- `boolean` - Boolean value
- `string` - String value

### Categories
- `color3` - Color processing nodes
- `float` - Math and utility nodes
- `vector3` - Vector math nodes
- `surfaceshader` - Surface shader nodes
- `material` - Material nodes

## Common Blender Node Types

### Texture Nodes
- `TEX_NOISE` - Noise texture
- `TEX_VORONOI` - Voronoi texture
- `TEX_WAVE` - Wave texture
- `TEX_CHECKER` - Checker texture
- `TEX_GRADIENT` - Gradient texture
- `TEX_IMAGE` - Image texture

### Math Nodes
- `MATH` - Math operations
- `VECTOR_MATH` - Vector math operations
- `MIX` - Mix operations
- `MIX_RGB` - Color mixing

### Utility Nodes
- `CLAMP` - Clamp values
- `MAP_RANGE` - Map value ranges
- `CURVE_RGB` - RGB curves
- `VALTORGB` - Color ramp
- `INVERT` - Invert values

### Input Nodes
- `TEX_COORD` - Texture coordinates
- `RGB` - RGB color
- `VALUE` - Single value

## Troubleshooting

### "No explicit mapping found" Error

This means the node type is not in `NODE_MAPPING`. Add it following Step 3.

### "No mapper found" Error

This means the node type is not registered in `get_node_mapper`. Add it following Step 6.

### "No node definition found" Error

This means MaterialX doesn't have the specified node type. You may need to:
1. Use a different MaterialX node type
2. Create a placeholder node
3. Use a fallback approach

### Connection Failures

Check that:
1. Input/output names in `NODE_MAPPING` match the actual MaterialX node definition
2. The MaterialX node type exists and is spelled correctly
3. The category matches the MaterialX node definition

## Testing Your Changes

### 1. Create Test Material
Create a Blender material using your new node type and connect it to a Principled BSDF.

### 2. Export Test
```bash
python3 cmdline_export.py your_test_file.blend MaterialName test_output.mtlx
```

### 3. Verify Output
Check the generated `.mtlx` file to ensure:
- The node was created with the correct MaterialX type
- Input connections are properly mapped
- Output connections work correctly
- The MaterialX file validates successfully

### 4. Test with Real Materials
Try exporting complex materials that use your new node type to ensure it works in realistic scenarios.

## Best Practices

1. **Be Explicit:** Always map all inputs and outputs explicitly
2. **Use Correct Types:** Ensure MaterialX types and categories match the actual node definitions
3. **Test Thoroughly:** Test with various input connections and parameter values
4. **Document Changes:** Update this guide when adding new patterns or node types
5. **Follow Naming:** Use consistent naming conventions for mapper functions
6. **Handle Errors:** Add appropriate error handling for unsupported operations

## Example: Adding a New Texture Node

Let's say we want to add support for a `TEX_BRICK` (Brick Texture) node:

### Step 1: Add to NODE_MAPPING
```python
'TEX_BRICK': {
    'mtlx_type': 'brick',
    'mtlx_category': 'color3',
    'inputs': {
        'Vector': 'texcoord',
        'Color1': 'in1',
        'Color2': 'in2',
        'Scale': 'scale',
        'Mortar': 'mortar',
    },
    'outputs': {
        'Color': 'out',
    }
},
```

### Step 2: Add to NODE_SCHEMAS
```python
'TEX_BRICK': [
    {'blender': 'Vector', 'mtlx': 'texcoord', 'type': 'vector3', 'category': 'color3'},
    {'blender': 'Color1', 'mtlx': 'in1', 'type': 'color3', 'category': 'color3'},
    {'blender': 'Color2', 'mtlx': 'in2', 'type': 'color3', 'category': 'color3'},
    {'blender': 'Scale', 'mtlx': 'scale', 'type': 'float', 'category': 'color3'},
    {'blender': 'Mortar', 'mtlx': 'mortar', 'type': 'color3', 'category': 'color3'},
],
```

### Step 3: Add Mapper Function
```python
@staticmethod
def map_brick_texture_enhanced(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
    """Enhanced brick texture mapping with type-safe input creation."""
    return map_node_with_schema_enhanced(node, builder, NODE_SCHEMAS['TEX_BRICK'], 'brick', 'color3', constant_manager, exported_nodes)
```

### Step 4: Register Mapper
```python
mappers = {
    # ... existing mappers
    'TEX_BRICK': NodeMapper.map_brick_texture_enhanced,
}
```

This completes the addition of the new node type to the addon.

## Conclusion

The explicit mapping system ensures robust translation between Blender and MaterialX nodes. By following this guide, you can systematically add support for new node types while maintaining the reliability and consistency of the addon.

Remember to test thoroughly and document any new patterns or approaches you discover during development. 