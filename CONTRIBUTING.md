# Contributing to MaterialX Export for Blender

Thank you for your interest in contributing to the MaterialX Export addon! This guide covers development setup, testing, and contribution guidelines.

## 🔧 Development Setup

### Prerequisites

- **Blender 4.0+**: Latest version recommended
- **Python 3.8+**: For running development scripts
- **Git**: For version control

### Making Code Changes

When developing or debugging the addon:

1. **Make your code changes** to the addon files in `materialx_addon/`
2. **Deploy the changes** using the development script:
   ```bash
   python3 dev_upgrade_addon.py
   ```
3. **Restart Blender** or reload the addon to see changes take effect

**Why This is Required**: Blender caches addon modules for performance. The `dev_upgrade_addon.py` script ensures your changes are properly installed and cached by Blender.

### Development Installation (macOS)

```bash
python3 dev_upgrade_addon.py
```

This script automatically finds the latest Blender installation and installs the addon.

## 🧪 Testing

### Running Tests

After deploying changes, test them using the provided test script:

```bash
python3 run_tests.py
```

This comprehensive test script:
- ✅ Tests addon installation and loading in Blender
- ✅ Uses real-world materials with complex node graphs
- ✅ Tests UI functionality (export buttons, configuration)
- ✅ Validates exported MaterialX files
- ✅ Tests error conditions and edge cases
- ✅ Provides detailed test reports and validation

### Test Material Creation

Create test materials for comprehensive testing:

```bash
blender --background --python create_test_materials.py
```

This creates realistic test materials in `examples/blender/` for comprehensive testing.

### Test Materials

The test suite uses these real-world materials from `examples/blender/`:

- **SimplePrincipled.blend**: Basic Principled BSDF material
- **TextureBased.blend**: Material with noise textures and color ramps
- **ComplexProcedural.blend**: Complex procedural material with multiple noise layers
- **GlassMaterial.blend**: Glass material with transparency and fresnel
- **MetallicMaterial.blend**: Metallic material with anisotropy
- **EmissionMaterial.blend**: Emission shader material
- **MixedShader.blend**: Material mixing different shaders
- **MathHeavy.blend**: Material with extensive math operations

### Error Condition Testing

The test suite specifically tests error handling for unsupported nodes:

- **Emission Shader**: Should be identified as unsupported
- **Fresnel Node**: Should be identified as unsupported

These tests verify that the exporter provides helpful error messages rather than crashing.

## 🧩 Adding New Node Support

The addon is built with extensibility in mind. To add support for a new Blender node type:

### 1. Add Node Mapper

In `materialx_addon/blender_materialx_exporter.py`, add a new mapping function:

```python
@staticmethod
def map_new_node_type(node, builder: MaterialXBuilder, input_nodes: Dict, input_nodes_by_index: Dict = None, blender_node=None, constant_manager=None, exported_nodes=None) -> str:
    """Map new Blender node type to MaterialX."""
    # Implementation here
    pass
```

### 2. Register the Mapper

Add the mapping to the `get_node_mapper` function:

```python
mappers = {
    # ... existing mappers ...
    'NEW_NODE_TYPE': NodeMapper.map_new_node_type,
}
```

### 3. Add Node Schema (if needed)

For complex nodes, add a schema in `NODE_SCHEMAS`:

```python
'NEW_NODE_TYPE': [
    {'blender': 'InputName', 'mtlx': 'output_name', 'type': 'color3', 'category': 'color3'},
    # ... more mappings
],
```

### 4. Test Your Changes

Create a test material with your new node type and run the test suite.

## 🔍 Advanced Features



### Document Optimization

Automatic optimization features:
- Removal of unused nodes
- Structure optimization
- Connection validation and optimization
- Memory usage optimization

### Advanced Validation

Comprehensive validation system:
- Document structure validation
- Node definition validation
- Connection validation with circular dependency detection

- Custom validation rule support

### Type Safety

Type-safe operations:
- Automatic Blender to MaterialX type conversion
- Type compatibility validation for connections
- Input definition lookup for proper type information
- Built-in type checking and validation

## 📊 Error Handling

The addon provides specific error types with user-friendly messages:

### Error Classification

- **Library Loading**: MaterialX library installation issues
- **Node Creation**: Unsupported node types or creation failures
- **Connection Error**: Type mismatches or connection failures
- **Validation Error**: MaterialX document validation issues
- **File Write**: File system or permission issues
- **Type Conversion**: Data type conversion failures
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

## 📋 Code Style Guidelines

- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings to all public functions
- Include type hints where appropriate
- Write comprehensive error messages
- Add tests for new functionality

## 🤝 Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-node-support`
3. **Make your changes** following the guidelines above
4. **Test your changes** using the test suite
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description of changes

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

- **MaterialX Team**: For the excellent MaterialX specification and library
- **Blender Foundation**: For the powerful Blender platform
- **mtlxutils Contributors**: For the comprehensive MaterialX utilities 