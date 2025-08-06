# MaterialX Export for Blender

A professional-grade Blender addon and command-line tool to export Blender materials to MaterialX (.mtlx) format, with robust node and texture support, advanced validation, and performance optimization.

## 🚀 Features

- **Professional MaterialX Library Integration**: Uses MaterialX Python library APIs for guaranteed specification compliance
- **Blender Addon UI**: Export single or all materials from the Blender UI with enhanced error reporting
- **Command-Line Export**: Export any material from any `.blend` file without opening Blender's UI
- **Texture Export**: Optionally export and copy textures, with support for relative or absolute paths
- **Comprehensive Node Support**: 40+ supported Blender node types with type-safe conversion
- **Advanced Validation**: Built-in MaterialX document validation with detailed error reporting
- **Performance Monitoring**: Real-time performance tracking and optimization suggestions
- **Memory Management**: Automatic resource cleanup and memory optimization
- **Configuration System**: Customizable export settings with sensible defaults
- **MaterialX 1.38 Compliance**: Full compliance with latest MaterialX specification

## 🎯 Key Improvements (v1.1.4+)

### Phase 1: Core Infrastructure Migration ✅
- **MaterialX Library Integration**: Replaced manual XML generation with MaterialX library APIs
- **Professional Output**: Guaranteed MaterialX specification compliance
- **Library Loading System**: Robust MaterialX library management with version compatibility
- **Document Builder**: Professional MaterialX document creation and management

### Phase 2: Node Mapping System Enhancement ✅
- **Type-Safe Operations**: Automatic type conversion and validation between Blender and MaterialX
- **Enhanced Node Creation**: Node definition-based creation with proper validation
- **Connection Management**: Type-compatible connection validation and optimization
- **Schema-Driven Mapping**: Enhanced node mapping with comprehensive type information

### Phase 3: Advanced Features Integration ✅
- **Performance Monitoring**: Real-time operation tracking with optimization suggestions
- **Advanced Validation**: Comprehensive document validation with custom rules
- **Document Optimization**: Automatic removal of unused nodes and structure optimization
- **Error Recovery**: Robust error handling with clear, user-friendly messages
- **Memory Management**: Automatic cleanup and resource optimization

### Phase 4: UI Integration and Error Handling ✅
- **Enhanced Error Reporting**: Specific error classification with user-friendly messages
- **Configuration Panel**: In-UI configuration for export settings
- **Status Display**: Real-time export status and performance metrics
- **Professional UX**: Improved user experience with detailed feedback

## 📦 Installation

### Manual Installation

1. Copy the `materialx_addon/` directory to your Blender addons directory:
   - **macOS**: `~/Library/Application Support/Blender/4.0/scripts/addons/`
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\4.0\scripts\addons\`
   - **Linux**: `~/.config/blender/4.0/scripts/addons/`

2. Enable the addon in Blender: `Edit > Preferences > Add-ons`, search for "MaterialX Export"

### Development Installation (macOS)

Use the development script to install the addon to the latest Blender version:

```bash
python3 dev_upgrade_addon.py
```

**Important**: When making code changes to the addon, you must run this script to deploy the changes to Blender. Blender caches addon modules, so direct file edits don't immediately take effect.

## 🎮 Usage

### In Blender

![Blender Screenshot of the MaterialX Export Property Panel](./BlenderScreenshot.png)

- Access the MaterialX panel in `Properties > Material > MaterialX`
- Export the selected material or all materials with enhanced error reporting
- Configure export settings in the Configuration panel
- View real-time export status and performance metrics
- Options for exporting/copying textures and using relative paths

### Configuration Options

The addon provides comprehensive configuration options:

- **Optimize Document**: Remove unused nodes and optimize structure
- **Advanced Validation**: Enable comprehensive MaterialX validation
- **Performance Monitoring**: Track export performance and resource usage
- **Strict Mode**: Fail export on any error (not just unsupported nodes)
- **Continue on Unsupported Nodes**: Continue export with unsupported nodes

### Command-Line

Export a material from any `.blend` file:

```bash
python cmdline_export.py <blend_file> <material_name> <output_mtlx_file> [options]
```

**Options:**
- `--export-textures` : Export texture files
- `--texture-path PATH` : Directory to export textures to
- `--version VERSION` : MaterialX version (default: 1.38)
- `--relative-paths` : Use relative paths for textures
- `--copy-textures` : Copy texture files
- `--active-uvmap NAME` : Active UV map name

## 🔧 Development

### Making Code Changes

When developing or debugging the addon:

1. **Make your code changes** to the addon files in `materialx_addon/`
2. **Deploy the changes** using the development script:
   ```bash
   python3 dev_upgrade_addon.py
   ```
3. **Restart Blender** or reload the addon to see changes take effect

**Why This is Required**: Blender caches addon modules for performance. The `dev_upgrade_addon.py` script ensures your changes are properly installed and cached by Blender.

### Testing Changes

After deploying changes, test them using the provided test scripts:

```bash
# Test basic MaterialX library functionality
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/test_materialx_library.py

# Test simple material export
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/simple_export_test.py

# Test node definition lookup
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/test_node_definition.py
```
- `--blender-path PATH` : Path to Blender executable
- `--optimize-document` : Enable document optimization
- `--advanced-validation` : Enable comprehensive validation
- `--performance-monitoring` : Enable performance tracking

See `cmdline_export.py --help` for full details.

## 🧩 Supported Blender Node Types

### Core Material Nodes
- **Principled BSDF** → `standard_surface` (with full parameter support)
- **Image Texture** → `image` (with texture coordinate support)
- **Texture Coordinate** → `texcoord` (with multiple coordinate types)

### Math and Color Nodes
- **RGB** → `constant` (color3)
- **Value** → `constant` (float)
- **Math** → `math` (with all operations)
- **Vector Math** → `vector_math` (with all operations)
- **Mix** → `mix` (with proper parameter mapping)
- **Invert** → `invert`
- **Separate Color** → `separate3`
- **Combine Color** → `combine3`

### Texture Nodes
- **Checker Texture** → `checkerboard`
- **Gradient Texture** → `ramplr`/`ramptb`
- **Noise Texture** → `noise2d`/`noise3d`
- **Wave Texture** → `wave` (with multiple wave types)

### Utility Nodes
- **Normal Map** → `normalmap`
- **Bump** → `bump`
- **Mapping** → `place2d`
- **Layer** → `layer`
- **Add** → `add`
- **Multiply** → `multiply`

### Advanced Nodes
- **Roughness Anisotropy** → `roughness_anisotropy`
- **Artistic IOR** → `artistic_ior`
- **Color Ramp** → `ramplr`
- **HSV to RGB** → `hsvtorgb`
- **RGB to HSV** → `rgbtohsv`
- **Luminance** → `luminance`
- **Contrast** → `contrast`
- **Saturate** → `saturate`
- **Gamma** → `gamma`

### Vector and Color Utilities
- **Split Color** → `separate3`
- **Merge Color** → `combine3`
- **Split Vector** → `separate3`
- **Merge Vector** → `combine3`

## 📊 Export Results and Error Handling

The exporter now returns a comprehensive result object with detailed information:

```python
result = {
    "success": True,                    # Export success status
    "unsupported_nodes": [],           # List of unsupported nodes
    "output_path": "path/to/file.mtlx", # Output file path
    "error": None,                     # Error message if failed
    "performance_stats": {             # Performance metrics
        "total_time": 1.23,
        "memory_usage": 1024000,
        "cache_sizes": {...},
        "suggestions": [...]
    },
    "validation_results": {            # Validation results
        "valid": True,
        "warnings": [...],
        "errors": [...],
        "suggestions": [...]
    },
    "optimization_applied": True       # Whether optimization was applied
}
```

### Error Classification

The addon provides specific error types with user-friendly messages and actionable suggestions:

- **Library Loading**: MaterialX library installation issues
- **Node Creation**: Unsupported node types or creation failures
- **Connection Error**: Type mismatches or connection failures
- **Validation Error**: MaterialX document validation issues
- **File Write**: File system or permission issues
- **Type Conversion**: Data type conversion failures
- **Performance Warning**: Performance optimization suggestions
- **Memory Error**: Resource management issues

### Helpful Error Messages

The addon provides specific guidance for common issues:

**❌ Unsupported Node Types:**
- **Emission Shader**: "Replace with Principled BSDF and use 'Emission Color' and 'Emission Strength' inputs"
- **Fresnel Node**: "Remove this node and use Principled BSDF's built-in fresnel effects via 'Specular IOR Level' and 'IOR' inputs"
- **Other BSDF Shaders**: "Replace individual BSDF shaders with a single Principled BSDF node"

**❌ No Principled BSDF Found:**
- **Emission Materials**: "Replace the Emission shader with a Principled BSDF node"
- **Multiple BSDF Shaders**: "Replace individual BSDF shaders with a single Principled BSDF node"
- **General**: "Add a Principled BSDF node to your material and connect it to the Material Output"

## 🔧 Advanced Features

### Performance Monitoring
- Real-time operation timing
- Memory usage tracking
- Performance optimization suggestions
- Resource cleanup monitoring

### Document Optimization
- Automatic removal of unused nodes
- Structure optimization
- Connection validation and optimization
- Memory usage optimization

### Advanced Validation
- Comprehensive document structure validation
- Node definition validation
- Connection validation with circular dependency detection
- Performance validation (node count, nesting depth)
- Custom validation rule support

### Type Safety
- Automatic Blender to MaterialX type conversion
- Type compatibility validation for connections
- Input definition lookup for proper type information
- Built-in type checking and validation

## 📋 Example Output

```xml
<materialx version="1.38">
  <nodegraph name="TestMaterial">
    <standard_surface name="surface_Principled_BSDF" type="surfaceshader">
      <input name="base_color" type="color3" nodename="rgb_RGB" />
      <input name="roughness" type="float" nodename="value_Value" />
      <input name="metallic" type="float" value="0.0" />
    </standard_surface>
    <constant name="rgb_RGB" type="color3" value="0.8, 0.2, 0.2" />
    <constant name="value_Value" type="float" value="0.5" />
  </nodegraph>
  <surfacematerial name="TestMaterial" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="surface_Principled_BSDF" />
  </surfacematerial>
</materialx>
```

## 🧪 Testing

The addon includes comprehensive testing with real-world material examples:

### Enhanced Testing with Real-World Materials

```bash
# Run enhanced comprehensive test with real-world materials
python3 test_blender_addon_enhanced.py
```

This enhanced test script uses 8 realistic Blender material examples with varying complexity:

**✅ Successfully Tested Materials (6/8):**
- **SimplePrincipled**: Basic Principled BSDF material
- **TextureBased**: Material with noise textures and color ramps  
- **ComplexProcedural**: Complex procedural material with multiple noise layers
- **MetallicMaterial**: Metallic material with anisotropy
- **MixedShader**: Material mixing different shaders
- **MathHeavy**: Material with extensive math operations

**❌ Materials Needing Support (2/8):**
- **EmissionMaterial**: Pure emission shader (needs Emission node support)
- **GlassMaterial**: Glass with transparency (needs Fresnel node support)

### Basic Testing

```bash
# Run basic Blender addon test
python3 test_blender_addon.py
```

The test scripts:
- ✅ Tests addon installation and loading in Blender
- ✅ Uses real-world materials with complex node graphs
- ✅ Tests UI functionality (export buttons, configuration)
- ✅ Validates exported MaterialX files
- ✅ Tests error conditions and edge cases
- ✅ Performs performance testing with complex materials
- ✅ Provides detailed test reports and validation

### Test Material Creation

```bash
# Create test materials using Blender MCP
blender --background --python create_test_materials.py
```

This creates realistic test materials in `examples/blender/` for comprehensive testing.

See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed analysis of test results and recommendations.

## 📋 Requirements

- **Blender**: 4.0 or higher
- **Python**: 3.10+ (included with Blender)
- **MaterialX**: Python library (included with mtlxutils)
- **No external dependencies** (uses included MaterialX library)

## 🔄 Migration from Previous Versions

The addon maintains backward compatibility while providing enhanced features:

- **Existing workflows**: Continue to work unchanged
- **Enhanced error reporting**: Better feedback for troubleshooting
- **Performance improvements**: Faster export with optimization
- **New configuration options**: Customizable export settings

## 🤝 Contributing

Contributions are welcome! The addon is built with extensibility in mind:

- **Node Support**: Easy to add new Blender node types
- **Validation Rules**: Custom validation rule support
- **Performance Monitoring**: Extensible performance tracking
- **Error Handling**: Custom error classification support

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License. See [LICENSE](LICENSE).

## 🙏 Acknowledgments

- **MaterialX Team**: For the excellent MaterialX specification and library
- **Blender Foundation**: For the powerful Blender platform
- **mtlxutils Contributors**: For the comprehensive MaterialX utilities

---

**Version**: 1.1.4+  
**Last Updated**: December 2024  
**MaterialX Version**: 1.38  
**Status**: Production Ready ✅