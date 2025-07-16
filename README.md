# MaterialX Integration for Blender

A comprehensive Blender add-on that provides seamless import/export of MaterialX files with real-time compatibility validation and workflow optimization for MaterialX-based pipelines.

## Features

### 🔄 **Import/Export**
- **MaterialX Import**: Convert MaterialX (.mtlx) files to Blender materials with full node graph reconstruction
- **MaterialX Export**: Export Blender materials to industry-standard MaterialX format
- **Bidirectional Compatibility**: Maintains material fidelity across the Blender ↔ MaterialX workflow

### 🔍 **Real-time Validation**
- **Scene Validation**: Analyze entire scenes for MaterialX compatibility
- **Material Validation**: Per-material compatibility checking with detailed feedback
- **Node Compatibility**: Identify incompatible shader nodes before export
- **Object Highlighting**: Visual identification of objects using incompatible materials

### ⚙️ **Workflow Features**
- **Node Filtering**: Option to hide non-MaterialX compatible nodes in shader editor
- **Incompatible Node Highlighting**: Red outline highlighting for non-compatible shader nodes
- **Detailed Logging**: Comprehensive error reporting during import/export operations
- **Graceful Degradation**: Export compatible portions while logging incompatible elements

## Installation

### Method 1: Manual Installation
1. Download the latest release from the [Releases](../../releases) page
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` and select the downloaded ZIP file
4. Enable the "MaterialX Integration" add-on

### Method 2: Development Installation
```bash
git clone https://github.com/your-username/blender-materialx-addon.git
cd blender-materialx-addon
# Copy to your Blender add-ons directory
cp -r materialx_addon/ ~/blender/scripts/addons/
```

## Usage

### Accessing the Add-on
The MaterialX panel is located in `Properties > Material > MaterialX`

### Basic Operations

#### Export MaterialX
1. Select objects with materials you want to export (or export all materials)
2. Click **Export MaterialX** in the MaterialX panel
3. Choose destination file (.mtlx)
4. Review the console for any compatibility warnings

#### Import MaterialX
1. Click **Import MaterialX** in the MaterialX panel
2. Select a .mtlx file
3. New materials will be created and added to your scene

#### Validate Scene
1. Click **Validate Scene** to check all materials for MaterialX compatibility
2. View detailed compatibility report in the console
3. Review the MaterialX panel for per-material compatibility status

### Add-on Preferences

Access via `Edit > Preferences > Add-ons > MaterialX Integration`

- **Filter Non-MaterialX Nodes**: Hide incompatible nodes in shader editor add menu
- **Highlight Incompatible Nodes**: Show red outlines around non-compatible nodes
- **Highlight Objects with Incompatible Materials**: Visual feedback in viewport

## Node Compatibility

### ✅ Fully Supported Nodes
- **Principled BSDF** → `standard_surface`
- **Emission** → `uniform_edf`
- **Image Texture** → `image`
- **Noise Texture** → `noise3d`
- **Texture Coordinate** → `texcoord`
- **Mapping** → `place2d`
- **Math** → `math`
- **RGB/Value** → `constant`

### ⚠️ Partially Supported Nodes
- **ColorRamp** → `ramp4` (limited to 4 control points)
- **Mix RGB** → `mix` (some blend modes not supported)
- **Vector Math** → `vector_math` (limited operations)
- **Voronoi Texture** → `worleynoise3d` (parameter limitations)
- **Musgrave Texture** → `fractal3d` (some types not supported)

### ❌ Unsupported Nodes
- **Wave Texture** (no MaterialX equivalent)
- **Magic Texture** (procedural, no equivalent)
- **Displacement** (different MaterialX context)
- **Legacy BSDF nodes** (use Principled BSDF instead)
- **Volume nodes** (different MaterialX volume system)

## Technical Architecture

### Core Modules

- **`materialx_mapping.py`**: Bidirectional node compatibility mapping system
- **`materialx_validator.py`**: Real-time validation engine with scene analysis
- **`materialx_exporter.py`**: MaterialX XML generation and export logic
- **`materialx_importer.py`**: MaterialX XML parsing and material reconstruction
- **`__init__.py`**: Blender add-on registration and UI components

### Design Principles

- **Domain-driven design**: Separated concerns across focused modules
- **Conservative compatibility**: Unknown nodes default to incompatible for pipeline safety
- **Extensible mapping system**: Easy addition of new node types as MaterialX evolves
- **Comprehensive error reporting**: Detailed feedback for production pipeline debugging

## Example Output

### Validation Report
```
=== MaterialX Scene Validation ===
✓ Material 'SimpleMetal' is compatible
✗ Material 'ProceduralWood' has issues:
    Node 'Wave Texture' (TEX_WAVE) has no MaterialX equivalent
    Node 'Displacement' (DISPLACEMENT) has no MaterialX equivalent
✓ Object 'Cube' uses compatible materials
✗ Object 'Sphere' has incompatible materials
=== Validation Complete ===
```

### Export Log
```
Exporting MaterialX to: /path/to/scene.mtlx
Found 3 materials to export
Successfully exported 2 materials to /path/to/scene.mtlx

Incompatible nodes encountered during export:
  Material 'ProceduralWood': Wave Texture (TEX_WAVE)
  Material 'ProceduralWood': Displacement (DISPLACEMENT)
```

## Requirements

- **Blender**: 4.0 or higher
- **Python**: 3.10+ (included with Blender)
- **Dependencies**: xml.etree.ElementTree, mathutils (built-in)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/your-username/blender-materialx-addon.git
cd blender-materialx-addon
# Install development dependencies
pip install -r requirements-dev.txt
```

### Adding Node Support
1. Update `BLENDER_TO_MATERIALX_MAPPING` in `materialx_mapping.py`
2. Add parameter mappings and compatibility notes
3. Update export/import logic if needed
4. Add tests and update documentation

## Roadmap

- [ ] **Advanced ColorRamp conversion** with unlimited control points
- [ ] **Custom MaterialX node support** for pipeline-specific extensions
- [ ] **Batch processing tools** for large scene conversion
- [ ] **MaterialX node library browser** with drag-and-drop support
- [ ] **Integration with MaterialX viewer** for real-time preview
- [ ] **USD/MaterialX workflow** integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MaterialX Working Group** for the open standard
- **Blender Foundation** for the extensible add-on architecture
- **Academy Software Foundation** for MaterialX development and specification

## Support

- **Issues**: Report bugs via [GitHub Issues](../../issues)
- **Discussions**: Join conversations in [GitHub Discussions](../../discussions)
- **Documentation**: Full docs available in the [Wiki](../../wiki)

---

*Built with ❤️ for the Blender and MaterialX communities*