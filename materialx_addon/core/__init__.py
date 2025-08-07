#!/usr/bin/env python3
"""
MaterialX Core Package

This package contains the core MaterialX library functionality.
"""

from .document_manager import MaterialXDocumentManager
from .library_builder import MaterialXLibraryBuilder
from .type_converter import MaterialXTypeConverter
from .advanced_validator import MaterialXAdvancedValidator

# Import validation functions for backward compatibility
from ..validation.validator import MaterialXValidator, validate_materialx_document, validate_materialx_file

__all__ = [
    'MaterialXDocumentManager',
    'MaterialXLibraryBuilder', 
    'MaterialXTypeConverter',
    'MaterialXAdvancedValidator',
    'MaterialXValidator',
    'validate_materialx_document',
    'validate_materialx_file'
]
