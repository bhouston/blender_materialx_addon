# Blender MaterialX Python Exporter

A Python-based MaterialX exporter for Blender that replicates the functionality of Blender's C++ MaterialX exporter. This standalone script allows you to export Blender materials to MaterialX (.mtlx) format with high fidelity.

## Features

- **Principled BSDF Support**: Full support for Blender's Principled BSDF shader
- **Node Network Traversal**: Recursively processes complex shader node networks
- **Texture Handling**: Exports and copies texture files with proper path resolution
- **Multiple Node Types**: Support for various Blender shader nodes
- **MaterialX Standards Compliance**: Generates valid MaterialX XML documents
- **Standalone Operation**: Works independently of Blender's USD exporter

## Supported Node Types

| Blender Node | MaterialX Node | Status |
|--------------|----------------|--------|
| Principled BSDF | `standard_surface` | ✅ Full Support |
| Image Texture | `image` | ✅ Full Support |
| UV Map | `texcoord` | ✅ Full Support |
| RGB | `constant` | ✅ Full Support |
| Value | `constant` | ✅ Full Support |
| Normal Map | `normalmap` | ✅ Full Support |
| Vector Math | Various math nodes | ✅ Full Support |
| Math | Various math nodes | ✅ Full Support |
| Mix | `mix` | ✅ Full Support |
| Invert | `invert` | ✅ Full Support |
| Separate Color | `separate3` | ✅ Full Support |
| Combine Color | `combine3` | ✅ Full Support |
| Bump | `bump` | ✅ Full Support |
| Checker Texture | `checkerboard` | ✅ Full Support |
| Gradient Texture | `ramplr`/`ramptb` | ✅ Full Support |
| Noise Texture | `noise2d`/`noise3d` | ✅ Full Support |
| Mapping | `place2d` | ✅ Full Support |

## Installation

1. Download the `blender_materialx_exporter.py` file
2. Place it in your Blender scripts directory or in the same directory as your Blender project
3. Import it in your Blender Python scripts

## Usage

### Basic Usage

```python
import blender_materialx_exporter as mtlx_exporter

# Export a single material
material = bpy.data.materials["MyMaterial"]
success = mtlx_exporter.export_material_to_materialx(material, "output.mtlx")

if success:
    print("Export successful!")
else:
    print("Export failed!")
```

### Advanced Usage with Options

```python
# Export options
options = {
    'active_uvmap': 'UVMap',           # Active UV map name
    'export_textures': True,           # Export texture files
    'texture_path': './textures',      # Texture export directory
    'materialx_version': '1.38',       # MaterialX version
    'copy_textures': True,             # Copy texture files
    'relative_paths': True,            # Use relative texture paths
}

# Export with options
success = mtlx_exporter.export_material_to_materialx(
    material, 
    "output.mtlx", 
    options
)
```

### Export All Materials

```python
# Export all materials in the scene
results = mtlx_exporter.export_all_materials_to_materialx(
    "exported_materials/", 
    options
)

# Check results
for material_name, success in results.items():
    if success:
        print(f"✓ Exported {material_name}")
    else:
        print(f"✗ Failed to export {material_name}")
```

## API Reference

### `export_material_to_materialx(material, output_path, options=None)`

Exports a Blender material to MaterialX format.

**Parameters:**
- `material` (bpy.types.Material): The Blender material to export
- `output_path` (str): Path to the output .mtlx file
- `options` (dict, optional): Export options dictionary

**Returns:**
- `bool`: Success status

### `export_all_materials_to_materialx(output_directory, options=None)`

Exports all materials in the current scene to MaterialX format.

**Parameters:**
- `output_directory` (str): Directory to save .mtlx files
- `options` (dict, optional): Export options dictionary

**Returns:**
- `dict`: Dictionary mapping material names to success status

### Export Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `active_uvmap` | str | 'UVMap' | Active UV map name |
| `export_textures` | bool | True | Export texture files |
| `texture_path` | str | './textures' | Texture export directory |
| `materialx_version` | str | '1.38' | MaterialX version |
| `copy_textures` | bool | True | Copy texture files |
| `relative_paths` | bool | True | Use relative texture paths |

## Examples

### Example 1: Simple Material Export

```python
import bpy
import blender_materialx_exporter as mtlx_exporter

# Get a material from the scene
material = bpy.data.materials["MyMaterial"]

# Export to MaterialX
success = mtlx_exporter.export_material_to_materialx(material, "my_material.mtlx")

if success:
    print("Material exported successfully!")
```

### Example 2: Complex Material with Textures

```python
import bpy
import blender_materialx_exporter as mtlx_exporter

# Export options for texture handling
options = {
    'export_textures': True,
    'texture_path': './textures',
    'copy_textures': True,
    'relative_paths': True,
}

# Export material with textures
material = bpy.data.materials["TexturedMaterial"]
success = mtlx_exporter.export_material_to_materialx(
    material, 
    "textured_material.mtlx", 
    options
)
```

### Example 3: Batch Export

```python
import blender_materialx_exporter as mtlx_exporter

# Export all materials in the scene
results = mtlx_exporter.export_all_materials_to_materialx("materials/")

# Print results
for material_name, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {material_name}")
```

## Generated MaterialX Structure

The exporter generates MaterialX documents with the following structure:

```xml
<?xml version="1.0"?>
<materialx version="1.38">
  <nodegraph name="NG_MaterialName">
    <!-- Node definitions -->
    <standard_surface name="surface_shader" type="surfaceshader">
      <input name="base_color" type="color3" value="0.8, 0.6, 0.2"/>
      <input name="roughness" type="float" value="0.5"/>
      <input name="metallic" type="float" value="0.0"/>
    </standard_surface>
    
    <!-- Supporting nodes -->
    <image name="texture_node" type="color3">
      <input name="file" type="filename" value="texture.png"/>
    </image>
    
    <!-- Connections -->
    <connect from="texture_node" to="surface_shader.base_color"/>
  </nodegraph>
  
  <surfacematerial name="MaterialName" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="surface_shader"/>
  </surfacematerial>
</materialx>
```

## Limitations

- **Node Support**: Limited to supported node types (see table above)
- **Performance**: Python implementation may be slower than C++ for complex materials
- **Memory**: Large materials may consume significant memory during export
- **Compatibility**: MaterialX version compatibility depends on target application

## Comparison with C++ Implementation

This Python implementation replicates the core functionality of Blender's C++ MaterialX exporter:

| Feature | C++ Implementation | Python Implementation |
|---------|-------------------|----------------------|
| Principled BSDF Support | ✅ | ✅ |
| Node Network Traversal | ✅ | ✅ |
| Texture Export | ✅ | ✅ |
| MaterialX XML Generation | ✅ | ✅ |
| Standalone Operation | ❌ | ✅ |
| Python API | ❌ | ✅ |

## Troubleshooting

### Common Issues

1. **"No Principled BSDF node found"**
   - Ensure your material uses nodes
   - Make sure there's a Principled BSDF node in the material

2. **"Texture file not found"**
   - Check that texture files exist at the specified paths
   - Ensure texture paths are relative to the Blender file

3. **"Export failed"**
   - Check the console for detailed error messages
   - Verify that the output directory is writable

### Debug Mode

To enable debug output, modify the exporter to include more verbose logging:

```python
# Add debug prints in the export functions
print(f"Processing node: {node.name} ({node.type})")
```

## Contributing

To extend the exporter with support for additional node types:

1. Add the node type to the `mappers` dictionary in `NodeMapper.get_node_mapper()`
2. Implement the corresponding mapping function
3. Test with materials using the new node type

## License

This project is released under the same license as Blender (GPL-2.0-or-later).

## Acknowledgments

- Based on Blender's C++ MaterialX exporter implementation
- Uses MaterialX standard for material definition
- Compatible with various MaterialX-compliant renderers and applications
