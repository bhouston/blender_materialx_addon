# MaterialX Export for Blender

A simplified Blender add-on that exports Blender materials to MaterialX (.mtlx) format using a robust and tested exporter library.

## Features

### 🔄 **MaterialX Export**
- **Single Material Export**: Export individual materials to MaterialX format
- **Batch Export**: Export all materials in the scene at once
- **Texture Support**: Export and copy texture files along with MaterialX files
- **Relative Paths**: Option to use relative paths for texture references
- **Principled BSDF Support**: Full support for Blender's Principled BSDF shader

### 🎯 **Simple & Reliable**
- **Tested Exporter**: Uses a thoroughly tested MaterialX exporter library
- **Clean UI**: Simple interface in the Material Properties panel
- **Error Reporting**: Clear feedback on export success or failure
- **No Complex Validation**: Focus on reliable export rather than complex validation

## Installation

### Method 1: Manual Installation
1. Download the latest release from the [Releases](../../releases) page
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` and select the downloaded ZIP file
4. Enable the "MaterialX Export" add-on

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

#### Export Single Material
1. Select a material in the Material Properties panel
2. Click **Export MaterialX** in the MaterialX panel
3. Choose destination file (.mtlx)
4. The material will be exported with all its node connections

#### Export All Materials
1. Click **Export All Materials** in the MaterialX panel
2. Choose a destination directory
3. All materials in the scene will be exported as separate .mtlx files

### Export Options

The exporter supports several options:
- **Export Textures**: Include texture files in the export
- **Copy Textures**: Copy texture files to the export directory
- **Relative Paths**: Use relative paths for texture references

## Supported Node Types

The exporter supports a wide range of Blender nodes:

### ✅ Core Shader Nodes
- **Principled BSDF** → `standard_surface`
- **Image Texture** → `image`
- **Texture Coordinate** → `texcoord`
- **RGB** → `constant`
- **Value** → `constant`

### ✅ Math & Utility Nodes
- **Math** → `math` (add, subtract, multiply, divide, etc.)
- **Vector Math** → `vector_math` (add, subtract, multiply, etc.)
- **Mix** → `mix`
- **Invert** → `invert`
- **Separate Color** → `separate3`
- **Combine Color** → `combine3`

### ✅ Texture Nodes
- **Checker Texture** → `checkerboard`
- **Gradient Texture** → `ramplr`/`ramptb`
- **Noise Texture** → `noise2d`/`noise3d`
- **Normal Map** → `normalmap`
- **Bump** → `bump`
- **Mapping** → `place2d`

## Technical Architecture

### Core Components

- **`blender_materialx_exporter.py`**: The main exporter library with comprehensive node mapping
- **`__init__.py`**: Blender add-on registration and UI components

### Design Principles

- **Simplicity**: Focus on reliable export functionality
- **Comprehensive Node Support**: Wide range of Blender nodes supported
- **Clean MaterialX Output**: Generates standard-compliant MaterialX files
- **Error Handling**: Graceful handling of unsupported nodes

## Example Output

### MaterialX File Structure
```xml
<?xml version="1.0" ?>
<materialx version="1.38">
  <nodegraph name="NG_TestMaterial">
    <standard_surface name="surface_Principled_BSDF" type="surfaceshader">
      <input name="base_color" type="color3" nodename="rgb_RGB" />
      <input name="roughness" type="float" nodename="value_Value" />
    </standard_surface>
    <constant name="rgb_RGB" type="color3" value="0.8, 0.2, 0.2" />
    <constant name="value_Value" type="float" value="0.5" />
  </nodegraph>
  <surfacematerial name="TestMaterial" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="surface_Principled_BSDF" />
  </surfacematerial>
</materialx>
```

## Requirements

- **Blender**: 4.0 or higher
- **Python**: 3.10+ (included with Blender)
- **Dependencies**: xml.etree.ElementTree, pathlib (built-in)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/your-username/blender-materialx-addon.git
cd blender-materialx-addon
```

### Testing
```bash
# Run the test script in Blender
blender --python test_simplified_addon.py
```

## Roadmap

- [ ] **Import Functionality**: Add MaterialX import capabilities
- [ ] **Advanced Node Support**: Support for more complex node setups
- [ ] **MaterialX Library Integration**: Integration with MaterialX node libraries
- [ ] **USD Workflow**: Integration with USD/MaterialX workflows

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MaterialX Working Group** for the open standard
- **Blender Foundation** for the extensible add-on architecture
- **Academy Software Foundation** for MaterialX development and specification

## Support

- **Issues**: Report bugs via [GitHub Issues](../../issues)
- **Discussions**: Join conversations in [GitHub Discussions](../../discussions)

---

*Built with ❤️ for the Blender and MaterialX communities*