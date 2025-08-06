# MaterialX Addon Test Results

## Test Scripts Overview

### Main Test Script: `test_blender_addon.py`
This is the **only** test script you need to run. It consolidates all testing functionality:

- **Addon Installation Test**: Verifies the MaterialX addon is properly installed and enabled
- **UI Functionality Test**: Checks that operators and panels are registered correctly
- **Error Condition Test**: Tests handling of unsupported nodes (Emission, Fresnel)
- **Material Export Test**: Tests exporting real-world materials from `examples/blender/` files
- **Material Validation Test**: Validates exported MaterialX files for proper structure
- **Performance Test**: Tests export performance with complex materials

### Test Material Creation: `create_test_materials.py`
This script creates the test materials used by the main test script. Run this first to generate the test blend files:

```bash
blender --background --python create_test_materials.py
```

## Test Execution

### Prerequisites
1. Install the MaterialX addon in Blender
2. Create test materials: `blender --background --python create_test_materials.py`
3. Ensure Blender is in your PATH or update the paths in the test script

### Running Tests
```bash
python test_blender_addon.py
```

## Test Materials

The test suite uses these real-world materials from `examples/blender/`:

- **SimplePrincipled.blend**: Basic Principled BSDF material
- **TextureBased.blend**: Material with noise textures and color ramps
- **ComplexProcedural.blend**: Complex procedural material with multiple noise layers
- **GlassMaterial.blend**: Glass material with transparency and fresnel
- **MetallicMaterial.blend**: Metallic material with anisotropy
- **EmissionMaterial.blend**: Emission shader material
- **MixedShader.blend**: Material mixing different shaders
- **MathHeavy.blend**: Material with extensive math operations

## Error Condition Testing

The test suite specifically tests error handling for unsupported nodes:

- **Emission Shader**: Should be identified as unsupported
- **Fresnel Node**: Should be identified as unsupported

These tests verify that the exporter provides helpful error messages rather than crashing.

## Test Results

Test results are saved to:
- `blender_addon_test.log`: Detailed test execution log
- `blender_addon_test_report.txt`: Summary test report


## Notes

- All tests run Blender in background mode using subprocess
- Tests use real-world materials for more accurate validation
- Error condition tests verify proper handling of unsupported nodes
- Performance tests ensure export doesn't take too long (>60 seconds)
- MaterialX file validation checks XML structure and required elements 