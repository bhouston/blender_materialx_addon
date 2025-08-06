# MaterialX Export for Blender

A professional-grade Blender addon to export Blender materials to MaterialX (.mtlx) format with comprehensive node support and validation.

## 🚀 Features

- **MaterialX 1.39 Compliance**: Full compliance with latest MaterialX specification
- **35+ Supported Node Types**: Comprehensive Blender node support including Principled BSDF, textures, math operations, and utilities
- **Blender Addon UI**: Export single or all materials from the Blender UI
- **Command-Line Export**: Export materials from any `.blend` file without opening Blender
- **Texture Export**: Export and copy textures with relative/absolute path support
- **Advanced Validation**: Built-in MaterialX document validation with detailed error reporting
- **Performance Monitoring**: Real-time performance tracking and optimization
- **Configuration Panel**: In-UI configuration for export settings

## 📦 Installation

### Manual Installation

1. Copy the `materialx_addon/` directory to your Blender addons directory:

   - **macOS**: `~/Library/Application Support/Blender/VERSION/scripts/addons/`
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\VERSION\scripts\addons\`
   - **Linux**: `~/.config/blender/VERSION/scripts/addons/`

2. Enable the addon in Blender: `Edit > Preferences > Add-ons`, search for "MaterialX Export"

### Development Installation (macOS)

```bash
python3 dev_upgrade_addon.py
```

**Important**: Run this script after making code changes to deploy updates to Blender.

## 🎮 Usage

### In Blender

- Access the MaterialX panel in `Properties > Material > MaterialX`
- Export the selected material or all materials
- Configure export settings in the Configuration panel
- View real-time export status and performance metrics

### Command-Line

```bash
python cmdline_export.py <blend_file> <material_name> <output_mtlx_file> [options]
```

**Options:**

- `--export-textures` : Export texture files
- `--texture-path PATH` : Directory to export textures to
- `--version VERSION` : MaterialX version (default: 1.39)
- `--relative-paths` : Use relative paths for textures
- `--copy-textures` : Copy texture files

## 🧩 Supported Node Types

### Core Material Nodes

- **Principled BSDF** → `standard_surface` (with full parameter support)
- **Image Texture** → `image` (with texture coordinate support)
- **Texture Coordinate** → `texcoord` (with multiple coordinate types)

### Math and Color Nodes

- **RGB, Value** → `constant` (color3/float)
- **Math, Vector Math** → `math`, `vector_math` (with all operations)
- **Mix** → `mix` (with proper parameter mapping)
- **Invert, Separate/Combine Color** → `invert`, `separate3`, `combine3`

### Texture Nodes

- **Checker, Gradient, Noise, Wave** → `checkerboard`, `ramplr`, `noise2d`, `wave`

### Utility Nodes

- **Normal Map, Bump** → `normalmap`, `bump`
- **Mapping, Layer, Add, Multiply** → `place2d`, `layer`, `add`, `multiply`
- **Color Ramp, HSV/RGB conversion** → `ramplr`, `hsvtorgb`, `rgbtohsv`

## 📊 Export Results

The exporter returns comprehensive results including:

- Export success status and error messages
- List of unsupported nodes with helpful suggestions
- Performance metrics and optimization suggestions
- MaterialX validation results
- File output path and optimization status

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_blender_addon.py
```

This tests:

- Addon installation and UI functionality
- Export of 8 real-world material examples
- MaterialX file validation
- Error handling for unsupported nodes
- Performance testing

See [TESTING.md](TESTING.md) for detailed test results and analysis.

## 🔧 Development

For development setup, testing, and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📋 Requirements

- **Blender**: 4.0 or higher
- **No external dependencies** (uses included MaterialX library)

## 📄 License

MIT License. See [LICENSE](LICENSE).

## 🙏 Acknowledgments

- **MaterialX Team**: For the excellent MaterialX specification and library
- **Blender Foundation**: For the powerful Blender platform
