# Bad MaterialX Examples

This directory contains intentionally bad MaterialX files used to test the validator's error detection capabilities.

## Test Files

### `bad_standard_surface_node.mtlx`
**Error Type**: Invalid pattern usage
**Issue**: Uses `<node type="standard_surface">` instead of `<standard_surface>`
**Expected**: Validator should reject this as invalid pattern

### `bad_no_surface_shader.mtlx`
**Error Type**: Missing surface shader
**Issue**: Material has no surface shader defined
**Expected**: Validator should report "No standard_surface elements found"

### `bad_material_no_shader_connection.mtlx`
**Error Type**: Missing material-shader connection
**Issue**: Material exists but has no surfaceshader input connection
**Expected**: Validator should report "has no surfaceshader input connection"

### `bad_material_wrong_shader_type.mtlx`
**Error Type**: Incorrect shader type
**Issue**: Material connects to a constant node instead of a surface shader
**Expected**: Validator should report "connected to non-standard_surface element"

### `bad_material_nonexistent_shader.mtlx`
**Error Type**: Non-existent reference
**Issue**: Material references a shader that doesn't exist
**Expected**: Validator should report "references non-existent surface shader"

### `bad_disconnected_nodes.mtlx`
**Error Type**: Disconnected nodes
**Issue**: Nodes have no values or connections
**Expected**: Validator should report "has no values or connections"

### `bad_texture_no_texcoord.mtlx`
**Error Type**: Missing texture coordinates
**Issue**: Texture node has no texcoord input
**Expected**: Validator should report "has texcoord input but no connection"

### `bad_missing_default_values.mtlx`
**Error Type**: Missing default values
**Issue**: Standard surface missing essential inputs like 'base' and 'specular_roughness'
**Expected**: Validator should report "missing default value for"

### `bad_invalid_xml.mtlx`
**Error Type**: Invalid XML structure
**Issue**: Unclosed XML tag
**Expected**: Validator should fail to load the file

## Running Tests

To test the validator against these bad examples:

```bash
python3 bad_examples_validation_tests.py
```

This will validate all files in this directory and report which errors were correctly detected and which were missed.

## Purpose

These bad examples help ensure that the MaterialX validator:
1. **Catches real-world errors** that users might make
2. **Provides helpful error messages** that guide users to fix issues
3. **Maintains quality standards** for exported MaterialX files
4. **Prevents invalid files** from being used in production

## Expected Results

A good validator should:
- ✅ **Correctly identify** all the errors in these files
- ✅ **Provide clear error messages** explaining what's wrong
- ✅ **Not produce false positives** on valid files
- ✅ **Help users understand** how to fix the issues
