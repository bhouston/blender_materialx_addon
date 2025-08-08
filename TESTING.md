# MaterialX Addon Testing Guide

This document provides comprehensive information about testing the MaterialX addon for Blender.

## 🧪 Test Suite Overview

The MaterialX addon includes a comprehensive test suite with multiple levels of testing:

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions

4. **End-to-End Tests** - Test complete workflows

### Test Files Structure

```
materialx_addon/tests/
├── __init__.py              # Test package initialization
├── test_config.py           # Test configuration and settings
├── test_utils.py            # Test framework and utilities
├── test_node_utils.py       # Node utility tests
├── test_logging.py          # Logging system tests

├── test_exporters.py        # Exporter component tests
├── test_mappers.py          # Mapper component tests
└── test_core.py            # Core component tests
```

## 🚀 Running Tests

### 1. Complete Test Suite (Recommended)

Run the full test suite with automatic deployment:

```bash
python3 run_tests.py
```

This script:
- Deploys the addon to Blender
- Runs all unit tests
- Runs integration tests
- Provides comprehensive results

### 2. Unit Tests Only

Run just the unit tests:

```bash
python3 unit_tests.py
```

### 3. Integration Tests

Run integration tests (requires addon to be installed):

```bash
python3 integration_tests.py
```

### 4. Quick Tests in Blender Console

For quick testing during development:

```python
# In Blender's Python console
exec(open('/path/to/blender_test_runner.py').read())

# Or run specific functions
run_quick_tests()                    # Basic functionality
run_full_tests()                     # Complete test suite
test_specific_component('exporters') # Test specific component
```

## 📊 Test Coverage

### Exporter Tests (`test_exporters.py`)

- **BaseExporter**: Core exporter functionality
- **MaterialExporter**: Single material export
- **BatchExporter**: Multiple material export
- **TextureExporter**: Texture handling
- **Integration**: Exporter interactions


### Mapper Tests (`test_mappers.py`)

- **BaseMapper**: Core mapping functionality
- **NodeMapperRegistry**: Mapper registration and lookup
- **PrincipledMapper**: Principled BSDF mapping
- **TextureMapper**: Texture node mapping
- **MathMapper**: Math operation mapping
- **UtilityMapper**: Utility node mapping
- **Integration**: Complex mapping scenarios

### Core Tests (`test_core.py`)

- **DocumentManager**: MaterialX document handling
- **AdvancedValidator**: Material validation
- **TypeConverter**: Type conversion utilities
- **LibraryBuilder**: Library creation and management
- **MaterialXValidator**: MaterialX validation
- **Integration**: Core component workflows


### Utility Tests

- **NodeUtils**: Node manipulation utilities
- **Logging**: Logging system functionality

- **Configuration**: Settings and configuration

## ⚙️ Test Configuration

The test suite is configurable through `materialx_addon/tests/test_config.py`:

### Test Settings

```python
TEST_SETTINGS = {
    
    'enable_integration_tests': True,
    'enable_stress_tests': False,
    'timeout_seconds': 300,
    'max_test_duration': 30.0,
    'enable_debug_output': False,
    'save_test_artifacts': True,
    'test_artifacts_dir': 'test_output_mtlx'
}
```



## 🔧 Test Framework

### BlenderTestCase

Base class for all tests that require Blender environment:

```python
from materialx_addon.tests.test_utils import BlenderTestCase

class TestMyComponent(BlenderTestCase):
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Create test materials, nodes, etc.
    
    def test(self):
        """Run the actual test."""
        # Test assertions
        self.assertTrue(condition)
        self.assertEqual(actual, expected)
    
    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        # Clean up test data
```

### TestRunner

Manages test execution and reporting:

```python
from materialx_addon.tests.test_utils import TestRunner

runner = TestRunner()
runner.add_test(TestMyComponent("MyTest"))
results = runner.run_tests()
summary = runner.get_summary()
```

### Test Results

Test results include:

- **Success/Failure status**
- **Execution duration**
- **Error messages**

- **Detailed logs**

## 🐛 Debugging Tests

### Enable Debug Output

```python
# In test_config.py
TEST_SETTINGS['enable_debug_output'] = True
```

### Test Specific Components

```python
# Test just exporters
from materialx_addon.tests.test_exporters import create_exporter_tests
from materialx_addon.tests.test_utils import TestRunner

runner = TestRunner()
runner.add_tests(create_exporter_tests())
results = runner.run_tests()
```

### Environment Validation

```python
from materialx_addon.tests.test_config import validate_test_environment

env_status = validate_test_environment()
print(f"Environment ready: {env_status['environment_ready']}")
```



The test suite tracks:

- **Export time** per material
- **Memory usage** during operations
- **Document creation time**
- **Validation time**
- **Batch processing time**







## 🧹 Test Cleanup

### Automatic Cleanup

Tests automatically clean up:

- **Temporary materials**
- **Test files**
- **Blender objects**
- **Temporary directories**

### Manual Cleanup

If tests are interrupted, manual cleanup may be needed:

```python
# Clean up test materials
for material in bpy.data.materials:
    if material.name.startswith("Test"):
        bpy.data.materials.remove(material)

# Clean up test objects
for obj in bpy.data.objects:
    if obj.name.startswith("Test"):
        bpy.data.objects.remove(obj)
```

## 🔄 Continuous Integration

### CI/CD Integration

The test suite is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run MaterialX Addon Tests
  run: |
    python3 run_tests.py
  env:
    BLENDER_VERSION: "4.0"
```

### Test Artifacts

Tests can save artifacts for analysis:

- **Exported MaterialX files**
- **Test logs**

- **Screenshots**

## 📝 Writing New Tests

### Adding Test Cases

1. **Create test class** inheriting from `BlenderTestCase`
2. **Implement setUp()** for test preparation
3. **Implement test()** with actual test logic
4. **Implement tearDown()** for cleanup
5. **Add to test module** creation function

### Example New Test

```python
class TestNewFeature(BlenderTestCase):
    def setUp(self):
        super().setUp()
        self.material = bpy.data.materials.new(name="TestMaterial")
        self.material.use_nodes = True
    
    def test(self):
        # Test the new feature
        result = self.new_feature.process(self.material)
        self.assertTrue(result['success'])
        self.assertIn('expected_field', result)
    
    def tearDown(self):
        if self.material:
            bpy.data.materials.remove(self.material)
        super().tearDown()

# Add to module creation function
def create_new_feature_tests() -> List[BlenderTestCase]:
    return [TestNewFeature("NewFeature")]
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure addon is deployed to Blender
2. **MaterialX Library**: Verify MaterialX is installed
3. **Blender Version**: Check minimum version requirements
4. **Test Timeouts**: Increase timeout settings if needed

### Debug Commands

```python
# Check environment
from materialx_addon.tests.test_config import validate_test_environment
print(validate_test_environment())

# Check test configuration
from materialx_addon.tests.test_config import get_test_config_summary
print(get_test_config_summary())

# Run quick diagnostic
exec(open('blender_test_runner.py').read())
```

## 📚 Additional Resources

- **README.md**: Main project documentation
- **CONTRIBUTING.md**: Contribution guidelines
- **MAINTENANCE.md**: Maintenance procedures
- **Examples/**: Example materials and workflows

---

For questions or issues with the test suite, please refer to the project documentation or create an issue in the project repository.
