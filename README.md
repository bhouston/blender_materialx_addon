# MaterialX Export for Blender

A Blender addon and command-line tool to export Blender materials to MaterialX (.mtlx) format, with robust node and texture support.

## Features

- **Blender Addon UI**: Export single or all materials from the Blender UI.
- **Command-Line Export**: Export any material from any `.blend` file without opening Blender’s UI.
- **Texture Export**: Optionally export and copy textures, with support for relative or absolute paths.
- **Comprehensive Node Support**: See below for supported Blender node types.
- **MaterialX 1.38 Compliance**.

## Installation

### Manual

1. Copy the `materialx_addon/` directory to your Blender addons directory (e.g., `~/Library/Application Support/Blender/4.0/scripts/addons/` on macOS).
2. Enable the addon in Blender: `Edit > Preferences > Add-ons`, search for "MaterialX Export".

### Development (macOS)

- Use `dev_upgrade_addon.py` to install the addon to the latest Blender version for development.

```bash
python3 dev_upgrade_addon.py
```

## Usage

### In Blender

- Access the MaterialX panel in `Properties > Material > MaterialX`.
- Export the selected material or all materials.
- Options for exporting/copying textures and using relative paths are available in the export dialogs.

### Command-Line

Export a material from any `.blend` file:

```bash
python cmdline_export.py <blend_file> <material_name> <output_mtlx_file> [options]
```

**Options:**
- `--export-textures` : Export texture files.
- `--texture-path PATH` : Directory to export textures to.
- `--version VERSION` : MaterialX version (default: 1.38).
- `--relative-paths` : Use relative paths for textures.
- `--copy-textures` : Copy texture files.
- `--active-uvmap NAME` : Active UV map name.
- `--blender-path PATH` : Path to Blender executable.

See `cmdline_export.py --help` for full details.

## Supported Blender Node Types

- Principled BSDF → `standard_surface`
- Image Texture → `image`
- Texture Coordinate → `texcoord`
- RGB → `constant`
- Value → `constant`
- Math → `math`
- Vector Math → `vector_math`
- Mix → `mix`
- Invert → `invert`
- Separate Color → `separate3`
- Combine Color → `combine3`
- Checker Texture → `checkerboard`
- Gradient Texture → `ramplr`/`ramptb`
- Noise Texture → `noise2d`/`noise3d`
- Normal Map → `normalmap`
- Bump → `bump`
- Mapping → `place2d`
- Layer → `layer`
- Add → `add`
- Multiply → `multiply`
- Roughness Anisotropy → `roughness_anisotropy`
- Artistic IOR → `artistic_ior`

## Export Results and Unsupported Nodes

The exporter now returns a result object (not just True/False) with the following fields:

- `success`: True if export succeeded and all nodes were supported, False otherwise.
- `unsupported_nodes`: List of unsupported nodes encountered (each with `name` and `type`).
- `output_path`: The path to the exported .mtlx file.

If unsupported nodes are found, `success` will be False and the list will help you identify and fix all issues in one go.

## Example Output

```xml
<materialx version="1.38">
  <nodegraph name="TestMaterial">
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
- **No external dependencies** (uses Python standard library)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).

---