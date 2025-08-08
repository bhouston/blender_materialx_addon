#!/usr/bin/env python3
"""
Test Configuration for MaterialX Addon

This module contains configuration settings for the test suite.
"""

import os
from typing import Dict, Any, List

# Test execution settings
TEST_SETTINGS = {

    'enable_integration_tests': True,
    'enable_stress_tests': False,
    'timeout_seconds': 300,
    'max_test_duration': 30.0,
    'enable_debug_output': False,
    'save_test_artifacts': True,
    'test_artifacts_dir': 'test_output_mtlx'
}

# Test categories and their settings
TEST_CATEGORIES = {
    'unit_tests': {
        'enabled': True,
        'modules': [
            'test_utils',
            'test_node_utils', 
            'test_logging',
        
            'test_exporters',
            'test_mappers',
            'test_core'
        ],
        'timeout': 60
    },
    'integration_tests': {
        'enabled': True,
        'modules': [
            'test_integration'
        ],
        'timeout': 120
    },

}

# Test data and fixtures
TEST_DATA = {
    'sample_materials': [
        'simple_rgb_material',
        'principled_bsdf_material',
        'texture_material',
        'complex_node_material'
    ],
    'sample_textures': [
        'test_diffuse.jpg',
        'test_normal.jpg',
        'test_roughness.jpg'
    ]
}



# Test environment settings
TEST_ENVIRONMENT = {
    'blender_version_min': (3, 0, 0),
    'materialx_version_min': '1.38',
    'required_addons': [],
    'test_scene_name': 'MaterialX_Test_Scene',
    'cleanup_after_tests': True
}

# Test reporting settings
REPORTING_SETTINGS = {
    'generate_html_report': True,
    'generate_junit_xml': True,
    'save_screenshots': True,
    'log_level': 'INFO',
    'detailed_output': True
}

def get_test_setting(key: str, default: Any = None) -> Any:
    """Get a test setting value."""
    return TEST_SETTINGS.get(key, default)

def is_test_category_enabled(category: str) -> bool:
    """Check if a test category is enabled."""
    return TEST_CATEGORIES.get(category, {}).get('enabled', False)

def get_test_modules(category: str) -> List[str]:
    """Get test modules for a category."""
    return TEST_CATEGORIES.get(category, {}).get('modules', [])



def should_save_artifacts() -> bool:
    """Check if test artifacts should be saved."""
    return get_test_setting('save_test_artifacts', True)

def get_artifacts_dir() -> str:
    """Get the test artifacts directory."""
    return get_test_setting('test_artifacts_dir', 'test_output_mtlx')

def create_test_artifacts_dir() -> str:
    """Create and return the test artifacts directory."""
    artifacts_dir = get_artifacts_dir()
    os.makedirs(artifacts_dir, exist_ok=True)
    return artifacts_dir

def get_test_timeout(category: str) -> int:
    """Get timeout for a test category."""
    return TEST_CATEGORIES.get(category, {}).get('timeout', 60)

def is_debug_enabled() -> bool:
    """Check if debug output is enabled."""
    return get_test_setting('enable_debug_output', False)

def should_cleanup_after_tests() -> bool:
    """Check if cleanup should be performed after tests."""
    return TEST_ENVIRONMENT.get('cleanup_after_tests', True)

def get_required_blender_version() -> tuple:
    """Get minimum required Blender version."""
    return TEST_ENVIRONMENT.get('blender_version_min', (3, 0, 0))

def get_required_materialx_version() -> str:
    """Get minimum required MaterialX version."""
    return TEST_ENVIRONMENT.get('materialx_version_min', '1.38')

def validate_test_environment() -> Dict[str, Any]:
    """Validate the test environment and return results."""
    results = {
        'blender_version_ok': False,
        'materialx_version_ok': False,
        'addons_ok': True,
        'environment_ready': False
    }
    
    try:
        import bpy
        blender_version = bpy.app.version
        required_version = get_required_blender_version()
        
        results['blender_version_ok'] = blender_version >= required_version
        results['blender_version'] = f"{blender_version[0]}.{blender_version[1]}.{blender_version[2]}"
        
    except ImportError:
        results['blender_version_ok'] = False
        results['blender_version'] = 'Not available'
    
    try:
        import MaterialX as mx
        # Note: MaterialX version checking might need adjustment based on actual API
        results['materialx_version_ok'] = True
        results['materialx_version'] = 'Available'
        
    except ImportError:
        results['materialx_version_ok'] = False
        results['materialx_version'] = 'Not available'
    
    # Check required addons
    required_addons = TEST_ENVIRONMENT.get('required_addons', [])
    for addon in required_addons:
        try:
            __import__(addon)
        except ImportError:
            results['addons_ok'] = False
            break
    
    # Overall environment readiness
    results['environment_ready'] = (
        results['blender_version_ok'] and 
        results['materialx_version_ok'] and 
        results['addons_ok']
    )
    
    return results

def get_test_config_summary() -> Dict[str, Any]:
    """Get a summary of the test configuration."""
    return {
        'settings': TEST_SETTINGS,
        'categories': {k: v.get('enabled', False) for k, v in TEST_CATEGORIES.items()},

        'environment': TEST_ENVIRONMENT,
        'reporting': REPORTING_SETTINGS
    }
