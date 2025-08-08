#!/usr/bin/env python3
"""
MaterialX Addon Exceptions

This module contains custom exception classes for better error handling
and more specific error messages throughout the addon.
"""

from typing import Optional, List, Dict, Any


class MaterialXExportError(Exception):
    """
    Base exception for all MaterialX export related errors.
    
    This is the parent class for all custom exceptions in the MaterialX addon.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class UnsupportedNodeError(MaterialXExportError):
    """
    Raised when encountering a node type that is not supported by the exporter.
    
    This exception is raised when the exporter encounters a Blender node type
    that it doesn't know how to convert to MaterialX format.
    """
    
    def __init__(self, node_type: str, node_name: Optional[str] = None, 
                 suggestion: Optional[str] = None):
        message = f"Unsupported node type: {node_type}"
        if node_name:
            message += f" (Node: {node_name})"
        
        details = {
            'node_type': node_type,
            'node_name': node_name,
            'suggestion': suggestion
        }
        
        super().__init__(message, details)


class ValidationError(MaterialXExportError):
    """
    Raised when MaterialX validation fails.
    
    This exception is raised when the generated MaterialX document fails
    validation against the MaterialX specification.
    """
    
    def __init__(self, errors: List[str], warnings: Optional[List[str]] = None):
        message = f"MaterialX validation failed with {len(errors)} error(s)"
        details = {
            'errors': errors,
            'warnings': warnings or [],
            'error_count': len(errors),
            'warning_count': len(warnings) if warnings else 0
        }
        
        super().__init__(message, details)


class ConfigurationError(MaterialXExportError):
    """
    Raised when there are issues with the export configuration.
    
    This exception is raised when the export options or configuration
    are invalid or incompatible.
    """
    
    def __init__(self, config_key: str, value: Any, reason: str):
        message = f"Invalid configuration: {config_key} = {value} - {reason}"
        details = {
            'config_key': config_key,
            'value': value,
            'reason': reason
        }
        
        super().__init__(message, details)


class FileOperationError(MaterialXExportError):
    """
    Raised when file operations fail.
    
    This exception is raised when there are issues with reading from or
    writing to files during the export process.
    """
    
    def __init__(self, operation: str, file_path: str, original_error: Optional[Exception] = None):
        message = f"File operation failed: {operation} on {file_path}"
        details = {
            'operation': operation,
            'file_path': file_path,
            'original_error': str(original_error) if original_error else None
        }
        
        super().__init__(message, details)


class TextureExportError(MaterialXExportError):
    """
    Raised when texture export operations fail.
    
    This exception is raised when there are issues with exporting,
    copying, or processing texture files.
    """
    
    def __init__(self, texture_name: str, operation: str, original_error: Optional[Exception] = None):
        message = f"Texture export failed: {operation} for {texture_name}"
        details = {
            'texture_name': texture_name,
            'operation': operation,
            'original_error': str(original_error) if original_error else None
        }
        
        super().__init__(message, details)


class NodeMappingError(MaterialXExportError):
    """
    Raised when node mapping operations fail.
    
    This exception is raised when there are issues with mapping
    Blender nodes to MaterialX nodes.
    """
    
    def __init__(self, node_type: str, node_name: str, mapping_step: str, 
                 original_error: Optional[Exception] = None):
        message = f"Node mapping failed: {mapping_step} for {node_type} ({node_name})"
        details = {
            'node_type': node_type,
            'node_name': node_name,
            'mapping_step': mapping_step,
            'original_error': str(original_error) if original_error else None
        }
        
        super().__init__(message, details)


class PerformanceError(MaterialXExportError):
    """
    Raised when performance thresholds are exceeded.
    
    This exception is raised when operations take longer than expected
    and performance monitoring is enabled.
    """
    
    def __init__(self, operation: str, duration: float, threshold: float):
        message = f"Performance threshold exceeded: {operation} took {duration:.2f}s (threshold: {threshold:.2f}s)"
        details = {
            'operation': operation,
            'duration': duration,
            'threshold': threshold,
            'exceeded_by': duration - threshold
        }
        
        super().__init__(message, details)


class MaterialXLibraryError(MaterialXExportError):
    """
    Raised when there are issues with the MaterialX library.
    
    This exception is raised when there are problems with the MaterialX
    Python library or its integration.
    """
    
    def __init__(self, operation: str, library_error: Optional[Exception] = None):
        message = f"MaterialX library error during {operation}"
        details = {
            'operation': operation,
            'library_error': str(library_error) if library_error else None
        }
        
        super().__init__(message, details)


class TypeConversionError(MaterialXExportError):
    """
    Raised when type conversion operations fail.
    
    This exception is raised when there are issues with converting
    between Blender types and MaterialX types.
    """
    
    def __init__(self, source_type: str, target_type: str, value: Any, 
                 reason: Optional[str] = None, original_error: Optional[Exception] = None):
        message = f"Type conversion failed: {source_type} -> {target_type}"
        if reason:
            message += f" - {reason}"
        
        details = {
            'source_type': source_type,
            'target_type': target_type,
            'value': str(value),
            'reason': reason,
            'original_error': str(original_error) if original_error else None
        }
        
        super().__init__(message, details)


# Convenience function for creating error messages
def create_error_message(error_type: str, **kwargs) -> str:
    """
    Create a formatted error message using the error message templates.
    
    Args:
        error_type: The type of error message to create
        **kwargs: Parameters to format into the error message
        
    Returns:
        Formatted error message string
    """
    from .constants import ERROR_MESSAGES
    
    template = ERROR_MESSAGES.get(error_type, "Unknown error: {error_type}")
    return template.format(error_type=error_type, **kwargs)
