# MaterialX Blender Addon Test Scripts

This folder contains test scripts for debugging and testing the MaterialX exporter functionality.

## Test Scripts

### 1. `test_materialx_library.py`
**Purpose**: Basic MaterialX library functionality test
**What it tests**:
- MaterialX library import and version
- Document creation
- Library loading
- Node definition discovery
- Node creation
- XML output generation

**Usage**:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/test_materialx_library.py
```

### 2. `simple_export_test.py`
**Purpose**: Simple material export test
**What it tests**:
- Creates a basic Principled BSDF material
- Tests the MaterialX exporter
- Checks output file content
- Validates XML structure

**Usage**:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/simple_export_test.py
```

### 3. `check_node_definitions.py`
**Purpose**: Comprehensive node definition discovery
**What it tests**:
- Loads multiple MaterialX libraries
- Categorizes node definitions
- Finds specific node types (standard_surface, surfacematerial)
- Tests node creation with found definitions

**Usage**:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/check_node_definitions.py
```

### 4. `debug_library_loading.py`
**Purpose**: Step-by-step library loading debug
**What it tests**:
- Detailed library loading process
- Step-by-step verification
- Node definition availability after loading
- XML output verification

**Usage**:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/debug_library_loading.py
```

## Running Tests

All tests should be run from the project root directory using Blender's Python interpreter:

```bash
# From the project root directory
/Applications/Blender.app/Contents/MacOS/Blender --background --python test/[script_name].py
```

## Expected Results

### Successful Test Output Should Show:
- ✅ MaterialX library imported successfully
- ✅ Document created with correct version (1.39)
- ✅ Libraries loaded successfully
- ✅ Node definitions found
- ✅ Nodes created successfully
- ✅ XML output generated

### Common Issues to Look For:
- ⚠ No standard_surface node definition found
- ⚠ No surfacematerial node definition found
- ⚠ Empty XML output
- ✗ Failed to import MaterialX
- ✗ Failed to load libraries

## Debugging Tips

1. **Start with `test_materialx_library.py`** - This is the most basic test
2. **Use `check_node_definitions.py`** - To see what node definitions are available
3. **Use `debug_library_loading.py`** - For step-by-step debugging
4. **Use `simple_export_test.py`** - To test the actual exporter

## Notes

- These scripts are designed to run in Blender's Python environment
- They import the MaterialX library that comes with Blender
- They test the actual MaterialX exporter code from the addon
- All scripts include comprehensive error handling and logging 