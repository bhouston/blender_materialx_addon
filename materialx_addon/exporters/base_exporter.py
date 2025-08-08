#!/usr/bin/env python3
"""
Base Exporter

This module provides the base class for all exporters in the MaterialX addon.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import MaterialXExportError
from ..utils.performance import monitor_performance
from ..core.document_manager import DocumentManager


class BaseExporter(ABC):
    """
    Abstract base class for all exporters.
    
    This class defines the interface that all exporters must implement
    for exporting Blender materials to MaterialX.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the base exporter.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger(f"Exporter.{self.__class__.__name__}")
        self.document_manager = DocumentManager(self.logger)
        self.export_options: Dict[str, Any] = {}
        self.exported_nodes: Dict[str, str] = {}
        self.exported_materials: Dict[str, str] = {}
        self.exported_textures: Dict[str, str] = {}
    
    @abstractmethod
    def can_export(self, blender_object: bpy.types.Object) -> bool:
        """
        Check if this exporter can handle the given Blender object.
        
        Args:
            blender_object: The Blender object to check
            
        Returns:
            True if this exporter can handle the object, False otherwise
        """
        pass
    
    @abstractmethod
    def export(self, blender_object: bpy.types.Object, export_path: str,
               options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Export a Blender object to MaterialX.
        
        Args:
            blender_object: The Blender object to export
            export_path: Path where to save the MaterialX file
            options: Optional export options
            
        Returns:
            True if export successful, False otherwise
            
        Raises:
            MaterialXExportError: If export fails
        """
        pass
    
    def set_export_options(self, options: Dict[str, Any]):
        """
        Set export options.
        
        Args:
            options: Dictionary of export options
        """
        self.export_options.update(options)
        self.logger.debug(f"Set export options: {options}")
    
    def get_export_options(self) -> Dict[str, Any]:
        """
        Get current export options.
        
        Returns:
            Dictionary of current export options
        """
        return self.export_options.copy()
    
    def validate_export_options(self, options: Dict[str, Any]) -> List[str]:
        """
        Validate export options.
        
        Args:
            options: Export options to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required options
        required_options = self.get_required_options()
        for option in required_options:
            if option not in options:
                errors.append(f"Required option '{option}' not found")
        
        # Check option types
        option_types = self.get_option_types()
        for option, value in options.items():
            if option in option_types:
                expected_type = option_types[option]
                if not isinstance(value, expected_type):
                    errors.append(f"Option '{option}' must be of type {expected_type.__name__}, got {type(value).__name__}")
        
        return errors
    
    def get_required_options(self) -> List[str]:
        """
        Get list of required export options.
        
        Returns:
            List of required option names
        """
        return []
    
    def get_option_types(self) -> Dict[str, type]:
        """
        Get expected types for export options.
        
        Returns:
            Dictionary mapping option names to expected types
        """
        return {}
    
    def get_default_options(self) -> Dict[str, Any]:
        """
        Get default export options.
        
        Returns:
            Dictionary of default export options
        """
        return {}
    
    def pre_export(self, blender_object: bpy.types.Object) -> bool:
        """
        Perform pre-export operations.
        
        Args:
            blender_object: The Blender object to export
            
        Returns:
            True if pre-export successful, False otherwise
        """
        try:
            self.logger.info(f"Starting export of {blender_object.name}")
            
            # Clear previous export data
            self.exported_nodes.clear()
            self.exported_materials.clear()
            self.exported_textures.clear()
            
            # Validate object
            if not self._validate_object(blender_object):
                return False
            
            # Set default options if not provided
            if not self.export_options:
                self.export_options = self.get_default_options()
            
            # Validate options
            validation_errors = self.validate_export_options(self.export_options)
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Export option validation error: {error}")
                return False
            
            self.logger.debug("Pre-export completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-export failed: {e}")
            return False
    
    def post_export(self, export_path: str) -> bool:
        """
        Perform post-export operations.
        
        Args:
            export_path: Path where the MaterialX file was saved
            
        Returns:
            True if post-export successful, False otherwise
        """
        try:
            self.logger.info(f"Export completed: {export_path}")
            self.logger.info(f"Exported {len(self.exported_materials)} materials")
            self.logger.info(f"Exported {len(self.exported_nodes)} nodes")
            self.logger.info(f"Exported {len(self.exported_textures)} textures")
            
            # Log export statistics
            self._log_export_statistics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-export failed: {e}")
            return False
    
    def _validate_object(self, blender_object: bpy.types.Object) -> bool:
        """
        Validate a Blender object for export.
        
        Args:
            blender_object: The Blender object to validate
            
        Returns:
            True if object is valid, False otherwise
        """
        if not blender_object:
            self.logger.error("Blender object is None")
            return False
        
        if not blender_object.active_material:
            self.logger.warning(f"Object '{blender_object.name}' has no active material")
            return False
        
        return True
    
    def _log_export_statistics(self):
        """Log export statistics."""
        stats = {
            'materials': len(self.exported_materials),
            'nodes': len(self.exported_nodes),
            'textures': len(self.exported_textures),
            'document_count': len(self.document_manager.list_documents())
        }
        
        self.logger.info("Export Statistics:")
        for key, value in stats.items():
            self.logger.info(f"  {key}: {value}")
    
    def get_export_info(self) -> Dict[str, Any]:
        """
        Get information about the last export.
        
        Returns:
            Dictionary containing export information
        """
        return {
            'exported_materials': self.exported_materials.copy(),
            'exported_nodes': self.exported_nodes.copy(),
            'exported_textures': self.exported_textures.copy(),
            'export_options': self.export_options.copy(),
            'document_info': {
                name: self.document_manager.get_document_info(name)
                for name in self.document_manager.list_documents()
            }
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.document_manager.clear_documents()
        self.exported_nodes.clear()
        self.exported_materials.clear()
        self.exported_textures.clear()
        self.export_options.clear()
        self.logger.debug("Cleanup completed")
