# MaterialX Addon Testing Guide

This document provides comprehensive information about testing the MaterialX Export addon for Blender.

## 🧪 Test Scripts Overview

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

## 🚀 Test Execution

### Prerequisites

1. Install the MaterialX addon in Blender
2. Create test materials: `blender --background --python create_test_materials.py`
3. Ensure Blender is in your PATH or update the paths in the test script

### Running Tests

```bash
python3 test_blender_addon.py
```

**Note**: The test script now preserves all exported MaterialX files in a `test_output_mtlx/` directory for inspection. This allows you to examine the actual output and identify any issues that might not be caught by the validation.

## 📊 Test Results

### Current Test Status (Latest Run)

**✅ Successfully Tested Materials (8/8):**

- **SimplePrincipled**: Basic Principled BSDF material
- **TextureBased**: Material with noise textures and color ramps
- **ComplexProcedural**: Complex procedural material with multiple noise layers
- **MetallicMaterial**: Metallic material with anisotropy
- **MixedShader**: Material mixing different shaders
- **MathHeavy**: Material with extensive math operations
- **EmissionMaterial**: Emission shader material (handled gracefully)
- **GlassMaterial**: Glass material with transparency (handled gracefully)

### Test Coverage

The test suite provides comprehensive coverage:

- ✅ **Addon Installation**: Verifies proper installation and loading
- ✅ **UI Functionality**: Tests all UI elements and operators
- ✅ **Material Export**: Tests export of 8 real-world materials
- ✅ **MaterialX Validation**: Validates exported files for proper structure
- ✅ **Error Handling**: Tests graceful handling of unsupported nodes
- ✅ **Performance**: Ensures export completes within reasonable time
- ✅ **File Structure**: Validates MaterialX document structure and version

## 📁 Test Materials

The test suite uses these real-world materials from `examples/blender/`:

### Successfully Exported Materials

- **SimplePrincipled.blend**: Basic Principled BSDF material
- **TextureBased.blend**: Material with noise textures and color ramps
- **ComplexProcedural.blend**: Complex procedural material with multiple noise layers
- **MetallicMaterial.blend**: Metallic material with anisotropy
- **MixedShader.blend**: Material mixing different shaders
- **MathHeavy.blend**: Material with extensive math operations

### Materials with Unsupported Nodes (Handled Gracefully)

- **EmissionMaterial.blend**: Emission shader material
  - **Status**: Exported successfully with helpful error messages
  - **Unsupported**: Pure Emission shader (needs Principled BSDF conversion)
- **GlassMaterial.blend**: Glass material with transparency
  - **Status**: Exported successfully with helpful error messages
  - **Unsupported**: Fresnel node (needs Principled BSDF conversion)

## 🔍 Error Condition Testing

The test suite specifically tests error handling for unsupported nodes:

### Unsupported Node Types

- **Emission Shader**: Should be identified as unsupported with helpful message
- **Fresnel Node**: Should be identified as unsupported with helpful message

### Error Message Validation

The tests verify that the exporter provides helpful error messages rather than crashing:

**Expected Error Messages:**

- **Emission Shader**: "Replace with Principled BSDF and use 'Emission Color' and 'Emission Strength' inputs"
- **Fresnel Node**: "Remove this node and use Principled BSDF's built-in fresnel effects via 'Specular IOR Level' and 'IOR' inputs"

## 📋 MaterialX File Validation

The test suite validates exported MaterialX files for:

### Structure Validation

- ✅ MaterialX version (1.39)
- ✅ Proper XML structure
- ✅ Required elements (materials, nodegraphs)
- ✅ Standard surface nodes
- ✅ Valid node connections

### Content Validation

- ✅ Node type compatibility
- ✅ Input/output type matching
- ✅ Texture file references (when applicable)
- ✅ Material surface assignments

## ⚡ Performance Testing

### Performance Benchmarks

- **Simple Materials**: < 1 second export time
- **Complex Materials**: < 5 seconds export time
- **Memory Usage**: Monitored for optimization
- **File Size**: Validated for reasonable output

### Performance Monitoring

The test suite tracks:

- Export time per material
- Memory usage during export
- File size of output MaterialX files
- Node count and complexity metrics

## 📊 Test Results Output

Test results are printed to stdout. To save the output to a file, use command line redirection:

```bash
python3 test_blender_addon.py > test_results.txt 2>&1
```

### Sample Test Report

```
================================================================================
COMPREHENSIVE BLENDER MATERIALX ADDON TEST REPORT
================================================================================

SUMMARY:
- Total Tests: 6
- Passed: 6
- Failed: 0
- Success Rate: 100.0%

DETAILED RESULTS:
- addon_installation: ✓ PASSED
- ui_functionality: ✓ PASSED
- error_conditions: ✓ PASSED
- material_export: ✓ PASSED
- material_validation: ✓ PASSED
- performance: ✓ PASSED

TEST MATERIALS USED:
- SimplePrincipled.blend: Basic Principled BSDF material
- TextureBased.blend: Material with noise textures and color ramps
- ComplexProcedural.blend: Complex procedural material with multiple noise layers
- GlassMaterial.blend: Glass material with transparency and fresnel
- MetallicMaterial.blend: Metallic material with anisotropy
- EmissionMaterial.blend: Emission shader material
- MixedShader.blend: Material mixing different shaders
- MathHeavy.blend: Material with extensive math operations

ERROR CONDITION TESTS:
- Emission shader (unsupported node type)
- Fresnel node (unsupported node type)

================================================================================
🎉 ALL TESTS PASSED! MaterialX addon is working correctly with real-world materials.
```

## 📁 Exported Files

After running the test suite, all exported MaterialX files are preserved in the `test_output_mtlx/` directory. This allows you to:

- **Inspect the actual output** to verify export quality
- **Identify issues** that might not be caught by validation
- **Compare different material exports** to understand the exporter behavior
- **Debug specific problems** by examining the generated MaterialX structure

The test script will list all exported files with their sizes, making it easy to identify which materials were successfully exported.

## 🔧 Troubleshooting

### Common Test Issues

**Blender Not Found:**

- Ensure Blender is installed and in your PATH
- Update the Blender path in the test script if needed

**Test Materials Missing:**

- Run `blender --background --python create_test_materials.py` first
- Check that `examples/blender/` directory contains the test files

**Addon Not Installed:**

- Install the addon using `python3 dev_upgrade_addon.py`
- Verify the addon is enabled in Blender preferences

**Permission Errors:**

- Ensure write permissions for test output directories
- Check file system permissions for Blender addon directory

## 📈 Continuous Integration

The test suite is designed for continuous integration:

- **Automated Testing**: Can run in headless mode
- **Exit Codes**: Proper exit codes for CI systems
- **Logging**: Comprehensive logging for debugging
- **Performance Tracking**: Automated performance regression detection

## 🎯 Future Testing Enhancements

Planned testing improvements:

- **More Node Types**: Additional Blender node type coverage
- **Complex Material Graphs**: Testing with very large node networks
- **Texture Validation**: Comprehensive texture export testing
- **Cross-Platform Testing**: Windows, macOS, and Linux validation
- **Blender Version Testing**: Multiple Blender version compatibility
