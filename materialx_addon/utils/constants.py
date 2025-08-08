#!/usr/bin/env python3
"""
MaterialX Addon Constants

This module contains all constants and default configuration values used throughout the addon.
"""

# MaterialX version
MATERIALX_VERSION = '1.39'

# Default export options
DEFAULT_EXPORT_OPTIONS = {
    'export_textures': True,
    'copy_textures': True,
    'relative_paths': True,
    'strict_mode': True,
    'optimize_document': True,
    'advanced_validation': True,
    'performance_monitoring': True,
    'materialx_version': MATERIALX_VERSION,
}

# Supported MaterialX versions
SUPPORTED_MATERIALX_VERSIONS = [
    ('1.39', '1.39', 'MaterialX 1.39'),
    ('1.38', '1.38', 'MaterialX 1.38'),
    ('1.37', '1.37', 'MaterialX 1.37')
]

# Default MaterialX version
DEFAULT_MATERIALX_VERSION = '1.39'

# File extensions
MATERIALX_EXTENSION = '.mtlx'
BLEND_EXTENSION = '.blend'

# Default texture directory name
DEFAULT_TEXTURE_DIR = 'textures'

# Node type categories
NODE_CATEGORIES = {
    'SURFACE': 'surface',
    'TEXTURE': 'texture', 
    'MATH': 'math',
    'UTILITY': 'utility',
    'VECTOR': 'vector',
    'COLOR': 'color',
    'INPUT': 'input',
    'OUTPUT': 'output'
}

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Performance thresholds (in seconds)
PERFORMANCE_THRESHOLDS = {
    'EXPORT_WARNING': 5.0,  # Warn if export takes longer than 5 seconds
    'VALIDATION_WARNING': 2.0,  # Warn if validation takes longer than 2 seconds
    'OPTIMIZATION_WARNING': 3.0,  # Warn if optimization takes longer than 3 seconds
}

# Error messages
ERROR_MESSAGES = {
    'NO_MATERIAL_SELECTED': 'No material selected for export',
    'NO_PRINCIPLED_BSDF': 'No Principled BSDF node found in material',
    'UNSUPPORTED_NODE': 'Unsupported node type: {node_type}',
    'VALIDATION_FAILED': 'MaterialX validation failed: {errors}',
    'FILE_WRITE_ERROR': 'Failed to write MaterialX file: {error}',
    'TEXTURE_EXPORT_ERROR': 'Failed to export texture: {error}',
    'INVALID_CONFIG': 'Invalid configuration: {error}',
}

# Success messages
SUCCESS_MESSAGES = {
    'EXPORT_COMPLETE': 'MaterialX export completed successfully',
    'VALIDATION_PASSED': 'MaterialX validation passed',
    'OPTIMIZATION_COMPLETE': 'Document optimization completed',
    'TEXTURES_EXPORTED': 'Textures exported successfully',
}

# UI labels and descriptions
UI_LABELS = {
    'EXPORT_MATERIAL': 'Export MaterialX',
    'EXPORT_ALL': 'Export All Materials',
    'CONFIGURATION': 'Configuration',
    'EXPORT_TEXTURES': 'Export Textures',
    'COPY_TEXTURES': 'Copy Textures',
    'RELATIVE_PATHS': 'Relative Paths',
    'STRICT_MODE': 'Strict Mode',
    'OPTIMIZE_DOCUMENT': 'Optimize Document',
    'ADVANCED_VALIDATION': 'Advanced Validation',
    'PERFORMANCE_MONITORING': 'Performance Monitoring',
}

# Addon information
ADDON_INFO = {
    'name': 'MaterialX Export',
    'author': 'Ben Houston (neuralsoft@gmail.com)',
    'website': 'https://github.com/bhouston/blender-materialx',
    'support': 'COMMUNITY',
    'version': (1, 1, 4),
    'blender': (4, 0, 0),
    'location': 'Properties > Material',
    'description': 'Export Blender materials to MaterialX format',
    'category': 'Material',
}
