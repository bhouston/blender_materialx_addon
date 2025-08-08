#!/usr/bin/env python3
"""
MaterialX Addon Logging Utilities

This module provides structured logging utilities for the MaterialX addon.
"""

import logging
import sys
from typing import Optional, Dict, Any
from .constants import LOG_LEVELS


class MaterialXLogger:
    """
    Structured logger for MaterialX addon operations.
    
    This class provides a consistent logging interface with proper formatting
    and log level management for the MaterialX addon.
    """
    
    def __init__(self, name: str = "MaterialX", level: str = "INFO"):
        """
        Initialize the MaterialX logger.
        
        Args:
            name: The logger name
            level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Only add handler if none exists (prevents duplicate handlers)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        formatted_message = self._format_message(message, **kwargs)
        self.logger.debug(formatted_message)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        formatted_message = self._format_message(message, **kwargs)
        self.logger.info(formatted_message)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        formatted_message = self._format_message(message, **kwargs)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        formatted_message = self._format_message(message, **kwargs)
        self.logger.error(formatted_message)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        formatted_message = self._format_message(message, **kwargs)
        self.logger.critical(formatted_message)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """
        Format a message with optional keyword arguments.
        
        Args:
            message: The base message
            **kwargs: Additional context to include in the message
            
        Returns:
            Formatted message string
        """
        if kwargs:
            context = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {context}"
        return message
    
    def log_export_start(self, material_name: str, output_path: str):
        """Log the start of an export operation."""
        self.info("Starting MaterialX export", 
                 material=material_name, 
                 output=output_path)
    
    def log_export_complete(self, material_name: str, output_path: str, 
                           duration: float, success: bool):
        """Log the completion of an export operation."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Export {status}", 
                 material=material_name, 
                 output=output_path, 
                 duration=f"{duration:.3f}s")
    
    def log_node_export(self, node_type: str, node_name: str, success: bool):
        """Log the export of a node."""
        status = "✓" if success else "✗"
        self.debug(f"{status} Node export", 
                  node_type=node_type, 
                  node_name=node_name)
    
    def log_unsupported_node(self, node_type: str, node_name: str, 
                           suggestion: Optional[str] = None):
        """Log an unsupported node."""
        message = f"Unsupported node: {node_type} ({node_name})"
        if suggestion:
            message += f" - Suggestion: {suggestion}"
        self.warning(message)
    
    def log_validation_result(self, valid: bool, errors: list, warnings: list):
        """Log validation results."""
        if valid:
            self.info("MaterialX validation passed", 
                     errors=len(errors), 
                     warnings=len(warnings))
        else:
            self.error("MaterialX validation failed", 
                      errors=len(errors), 
                      warnings=len(warnings))
            for error in errors:
                self.error(f"Validation error: {error}")
    

    
    def log_texture_export(self, texture_name: str, source_path: str, 
                          target_path: str, success: bool):
        """Log texture export operations."""
        status = "✓" if success else "✗"
        self.debug(f"{status} Texture export", 
                  texture=texture_name, 
                  source=source_path, 
                  target=target_path)





class ValidationLogger:
    """
    Specialized logger for validation operations.
    
    This class provides logging specifically for MaterialX validation
    and error reporting.
    """
    
    def __init__(self, base_logger: MaterialXLogger):
        """
        Initialize the validation logger.
        
        Args:
            base_logger: The base MaterialX logger to use
        """
        self.logger = base_logger
    
    def log_validation_start(self, document_name: str):
        """Log the start of validation."""
        self.logger.debug(f"Starting validation: {document_name}")
    
    def log_validation_end(self, document_name: str, valid: bool, 
                          error_count: int, warning_count: int):
        """Log the end of validation."""
        status = "PASSED" if valid else "FAILED"
        self.logger.info(
            f"Validation {status}: {document_name} "
            f"({error_count} errors, {warning_count} warnings)"
        )
    
    def log_validation_error(self, error: str, context: Optional[Dict[str, Any]] = None):
        """Log a validation error."""
        if context:
            self.logger.error(f"Validation error: {error}", **context)
        else:
            self.logger.error(f"Validation error: {error}")
    
    def log_validation_warning(self, warning: str, context: Optional[Dict[str, Any]] = None):
        """Log a validation warning."""
        if context:
            self.logger.warning(f"Validation warning: {warning}", **context)
        else:
            self.logger.warning(f"Validation warning: {warning}")


# Global logger instance for convenience
_global_logger: Optional[MaterialXLogger] = None


def get_logger(name: str = "MaterialX", level: str = "INFO") -> MaterialXLogger:
    """
    Get a logger instance, creating it if it doesn't exist.
    
    Args:
        name: The logger name
        level: The logging level
        
    Returns:
        MaterialXLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = MaterialXLogger(name, level)
    return _global_logger


def set_log_level(level: str):
    """
    Set the log level for the global logger.
    
    Args:
        level: The logging level to set
    """
    logger = get_logger()
    logger.logger.setLevel(getattr(logging, level.upper()))


def log_startup_message():
    """Log the addon startup message."""
    from .constants import ADDON_INFO, SUCCESS_MESSAGES
    
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"🎨 {ADDON_INFO['name']} v{ADDON_INFO['version']} loaded successfully!")
    logger.info("=" * 60)
    logger.info("📁 Location: Properties > Material > MaterialX")
    logger.info("🔧 Features:")
    logger.info("   • Export individual materials to MaterialX format")
    logger.info("   • Export all materials at once")
    logger.info("   • Support for texture export and copying")
    logger.info(f"   • MaterialX {ADDON_INFO['version']} specification compliance")
    logger.info("   • Enhanced logging and error handling")
    logger.info("=" * 60)
    logger.info("💡 Usage: Select a material and click 'Export MaterialX'")
    logger.info(f"🌐 More info: {ADDON_INFO['website']}")
    logger.info("=" * 60)
