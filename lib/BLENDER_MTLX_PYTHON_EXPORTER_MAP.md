# Blender MaterialX Python Exporter - Implementation Plan

## Overview

This document outlines the plan to create a Python-based MaterialX exporter that replicates the existing C++ functionality found in Blender's USD exporter. The goal is to create a standalone Python script that can export Blender materials to MaterialX (.mtlx) files with the same fidelity as the C++ implementation.

## Current C++ Implementation Analysis

### Core Components

1. **Main Export Function**: `create_usd_materialx_material()` in `usd_writer_material.cc`
2. **MaterialX Generation**: `export_to_materialx()` in `material.cc`
3. **Node Graph Processing**: `NodeGraph` class in `node_graph.cc`
4. **Node Item System**: `NodeItem` class in `node_item.cc`
5. **Node Parsers**: Various node-specific parsers in `node_parser.cc`

### Key Features

- **Principled BSDF Focus**: Primary support for Principled BSDF nodes
- **Node Traversal**: Recursive traversal of shader node networks
- **MaterialX Document Generation**: Creates MaterialX XML documents
- **Texture Export**: Handles image texture export and path resolution
- **UV Coordinate Handling**: Manages texture coordinate mapping

## Python Implementation Plan

### 1. Core Architecture

#### 1.1 Main Exporter Class
```python
class MaterialXExporter:
    def __init__(self, material, output_path, active_uvmap_name="UVMap"):
        self.material = material
        self.output_path = output_path
        self.active_uvmap_name = active_uvmap_name
        self.node_counter = 0
        self.exported_nodes = {}
        self.texture_paths = {}
```

#### 1.2 Node Graph Traversal
```python
class NodeGraphTraverser:
    def traverse_node(self, node, parent_node=None):
        # Recursively traverse connected nodes
        # Build dependency graph
        # Handle circular references
```

### 2. Node Type Mappings

#### 2.1 Supported Blender Nodes → MaterialX Nodes

| Blender Node | MaterialX Node | Notes |
|--------------|----------------|-------|
| Principled BSDF | `standard_surface` | Primary surface shader |
| Image Texture | `image` | Texture sampling |
| UV Map | `texcoord` | Texture coordinates |
| RGB | `constant` | Color values |
| Value | `constant` | Float values |
| Normal Map | `normalmap` | Normal mapping |
| Vector Math | Various math nodes | Vector operations |
| Math | Various math nodes | Scalar operations |
| Mix | `mix` | Color/vector mixing |
| Invert | `invert` | Value inversion |
| Separate Color | `separate3` | Color component separation |
| Combine Color | `combine3` | Color component combination |
| Bump | `bump` | Height-to-normal conversion |
| Checker Texture | `checkerboard` | Checker pattern |
| Gradient Texture | `ramplr`/`ramptb` | Gradient patterns |
| Noise Texture | `noise2d`/`noise3d` | Noise patterns |
| Mapping | `place2d` | UV transformations |

#### 2.2 Principled BSDF Parameter Mapping

| Blender Parameter | MaterialX Parameter | Type |
|-------------------|---------------------|------|
| Base Color | `base_color` | Color3 |
| Metallic | `metallic` | Float |
| Roughness | `roughness` | Float |
| Specular | `specular` | Float |
| IOR | `ior` | Float |
| Transmission | `transmission` | Float |
| Alpha | `opacity` | Float |
| Normal | `normal` | Vector3 |
| Emission Color | `emission_color` | Color3 |
| Emission Strength | `emission` | Float |
| Subsurface | `subsurface` | Float |
| Subsurface Radius | `subsurface_radius` | Vector3 |
| Subsurface Scale | `subsurface_scale` | Float |
| Subsurface Anisotropy | `subsurface_anisotropy` | Float |
| Sheen | `sheen` | Float |
| Sheen Tint | `sheen_tint` | Color3 |
| Sheen Roughness | `sheen_roughness` | Float |
| Clearcoat | `clearcoat` | Float |
| Clearcoat Roughness | `clearcoat_roughness` | Float |
| Clearcoat IOR | `clearcoat_ior` | Float |
| Clearcoat Normal | `clearcoat_normal` | Vector3 |
| Tangent | `tangent` | Vector3 |
| Anisotropic | `anisotropic` | Float |
| Anisotropic Rotation | `anisotropic_rotation` | Float |

### 3. Implementation Strategy

#### 3.1 Phase 1: Core Infrastructure
1. **MaterialX Document Builder**
   - XML document creation
   - Node definition generation
   - Connection management
   - Namespace handling

2. **Node Traversal System**
   - Find Principled BSDF node
   - Recursive input traversal
   - Dependency resolution
   - Circular reference detection

3. **Basic Node Support**
   - Principled BSDF
   - Image Texture
   - UV Map
   - RGB/Value constants

#### 3.2 Phase 2: Advanced Node Support
1. **Math Operations**
   - Vector Math node
   - Math node
   - Mix node
   - Invert node

2. **Texture Nodes**
   - Normal Map
   - Bump
   - Procedural textures (Checker, Gradient, Noise)

3. **UV Transformations**
   - Mapping node
   - UV coordinate handling

#### 3.3 Phase 3: Advanced Features
1. **Texture Export**
   - Image path resolution
   - Texture copying
   - UDIM support

2. **MaterialX Standards Compliance**
   - Proper node definitions
   - Standard surface shader
   - MaterialX version compatibility

### 4. File Structure

```
blender_materialx_exporter/
├── __init__.py
├── exporter.py              # Main exporter class
├── node_mappers.py          # Node type mappings
├── materialx_builder.py     # MaterialX document builder
├── texture_handler.py       # Texture export utilities
├── utils.py                 # Utility functions
└── examples/
    ├── basic_export.py      # Basic usage example
    └── advanced_export.py   # Advanced usage example
```

### 5. API Design

#### 5.1 Main Export Function
```python
def export_material_to_materialx(material, output_path, options=None):
    """
    Export a Blender material to MaterialX format.
    
    Args:
        material: Blender material object
        output_path: Path to output .mtlx file
        options: Export options dictionary
    
    Returns:
        bool: Success status
    """
```

#### 5.2 Export Options
```python
export_options = {
    'active_uvmap': 'UVMap',           # Active UV map name
    'export_textures': True,           # Export texture files
    'texture_path': './textures',      # Texture export directory
    'materialx_version': '1.38',       # MaterialX version
    'surface_shader': 'standard_surface',  # Surface shader type
    'copy_textures': True,             # Copy texture files
    'relative_paths': True,            # Use relative texture paths
}
```

### 6. MaterialX Output Structure

#### 6.1 Document Structure
```xml
<?xml version="1.0"?>
<materialx version="1.38">
  <nodegraph name="NG_material_name">
    <!-- Node definitions -->
    <standard_surface name="surface_shader" type="surfaceshader">
      <!-- Surface shader parameters -->
    </standard_surface>
    
    <!-- Supporting nodes -->
    <image name="texture_node" type="color3">
      <!-- Texture parameters -->
    </image>
    
    <!-- Connections -->
    <connect from="texture_node" to="surface_shader.base_color"/>
  </nodegraph>
  
  <surfacematerial name="material_name" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="surface_shader"/>
  </surfacematerial>
</materialx>
```

### 7. Testing Strategy

#### 7.1 Unit Tests
- Individual node type mappings
- Parameter conversion accuracy
- Connection handling
- Error cases

#### 7.2 Integration Tests
- Complete material export
- Comparison with C++ output
- Round-trip validation
- Performance benchmarks

#### 7.3 Test Materials
- Simple Principled BSDF
- Complex node networks
- Texture-heavy materials
- Procedural materials

### 8. Limitations and Considerations

#### 8.1 Known Limitations
- **Node Support**: Limited to supported node types
- **Performance**: Python implementation may be slower than C++
- **Memory**: Large materials may consume significant memory
- **Compatibility**: MaterialX version compatibility

#### 8.2 Future Enhancements
- **Extended Node Support**: More Blender node types
- **Custom Node Definitions**: User-defined node mappings
- **Optimization**: Performance improvements
- **Validation**: MaterialX schema validation

### 9. Implementation Timeline

1. **Week 1**: Core infrastructure and basic node support
2. **Week 2**: Advanced node types and math operations
3. **Week 3**: Texture handling and UV transformations
4. **Week 4**: Testing, documentation, and refinement

### 10. Success Criteria

- [ ] Exports Principled BSDF materials correctly
- [ ] Handles basic texture nodes
- [ ] Generates valid MaterialX XML
- [ ] Matches C++ output fidelity
- [ ] Provides clear error messages
- [ ] Includes comprehensive documentation
- [ ] Passes all test cases

## Conclusion

This Python-based MaterialX exporter will provide a standalone solution for exporting Blender materials to MaterialX format, replicating the functionality of the existing C++ implementation while offering greater flexibility and ease of use for Python-based workflows. 