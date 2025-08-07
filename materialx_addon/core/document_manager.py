#!/usr/bin/env python3
"""
MaterialX Document Manager

This module provides document management functionality for MaterialX.
"""

import MaterialX as mx
import logging
from typing import Dict, List, Optional, Any
from .advanced_validator import MaterialXAdvancedValidator
from ..node_definitions import CustomNodeDefinitionManager


class MaterialXDocumentManager:
    """
    Manages MaterialX document creation and library loading.
    
    This class handles:
    - MaterialX document creation
    - Library loading and validation
    - Version compatibility
    - Search path management
    - Advanced validation and error recovery
    - Performance monitoring
    """
    
    def __init__(self, logger, version: str = "1.39"):
        self.logger = logger
        self.version = version
        self.document = None
        self.libraries = None
        self.library_files = []
        self.search_path = None
        
        # Phase 3 enhancements
        self.performance_monitor = MaterialXPerformanceMonitor(logger)
        self.advanced_validator = MaterialXAdvancedValidator(logger)
        
        # Cache for performance optimization
        self._node_def_cache = {}
        self._input_def_cache = {}
        self._output_def_cache = {}
        
        # Custom node definitions manager
        self.custom_node_manager = None
        
    def load_libraries(self, custom_search_path: Optional[str] = None) -> bool:
        """
        Load MaterialX libraries with proper version handling.
        
        Args:
            custom_search_path: Optional custom search path for libraries
            
        Returns:
            bool: True if libraries loaded successfully
        """
        try:
            self.performance_monitor.start_operation("load_libraries")
            
            self.logger.info(f"Loading MaterialX libraries (version: {self.version})")
            
            # Create libraries document if not already created
            if self.libraries is None:
                self.libraries = mx.createDocument()
            
            # Use the working method from our debug test
            self.logger.info("Using MaterialX 1.39+ library loading method")
            search_path = mx.getDefaultDataSearchPath()
            lib_folders = mx.getDefaultDataLibraryFolders()
            self.library_files = mx.loadLibraries(lib_folders, search_path, self.libraries)
            
            self.logger.info(f"Loaded {len(self.library_files)} library files")
            
            # Clear caches after library loading
            self._clear_caches()
            
            self.performance_monitor.end_operation("load_libraries")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MaterialX libraries: {str(e)}")
            self.performance_monitor.end_operation("load_libraries")
            return False
    
    def create_document(self) -> mx.Document:
        """
        Create a new MaterialX document with loaded libraries and validation.
        
        Returns:
            mx.Document: The created document
        """
        try:
            self.performance_monitor.start_operation("create_document")
            
            self.logger.info("Creating MaterialX document")
            
            # Create libraries document if not already created
            if self.libraries is None:
                self.libraries = mx.createDocument()
                if not self.load_libraries():
                    raise RuntimeError("Failed to load MaterialX libraries")
            
            # Create working document
            self.document = mx.createDocument()
            
            # Set colorspace attribute (required for MaterialX compliance)
            self.document.setColorSpace("lin_rec709")
            
            self.logger.info(f"Working document has {len(self.document.getNodeDefs())} node definitions before import")
            self.document.importLibrary(self.libraries)
            self.logger.info(f"Working document has {len(self.document.getNodeDefs())} node definitions after import")
            
            # Initialize custom node definitions manager (lazy initialization)
            self._initialize_custom_node_manager()
            
            self.performance_monitor.end_operation("create_document")
            return self.document
            
        except Exception as e:
            self.logger.error(f"Failed to create MaterialX document: {str(e)}")
            self.performance_monitor.end_operation("create_document")
            raise
    
    def get_node_definition(self, node_type: str, category: str = None) -> Optional[mx.NodeDef]:
        """
        Get a node definition by type and optional category.
        
        Args:
            node_type: The node type to look for
            category: Optional category filter
            
        Returns:
            Optional[mx.NodeDef]: The node definition if found
        """
        cache_key = f"{node_type}_{category}" if category else node_type
        
        if cache_key in self._node_def_cache:
            return self._node_def_cache[cache_key]
        
        if not self.document:
            self.logger.warning("No document available for node definition lookup")
            return None
        
        try:
            # First check if it's a custom node type
            if self._is_custom_node_type(node_type):
                if self.custom_node_manager:
                    nodedef = self.custom_node_manager.get_custom_node_definition(node_type)
                    if nodedef:
                        self._node_def_cache[cache_key] = nodedef
                        return nodedef
            
            # Look for standard node definitions
            node_defs = self.document.getNodeDefs()
            
            for nodedef in node_defs:
                if nodedef.getNodeString() == node_type:
                    if category is None or nodedef.getNodeGroup() == category:
                        self._node_def_cache[cache_key] = nodedef
                        return nodedef
            
            # If not found, try without category filter
            if category is not None:
                for nodedef in node_defs:
                    if nodedef.getNodeString() == node_type:
                        self._node_def_cache[cache_key] = nodedef
                        return nodedef
            
            self.logger.debug(f"Node definition not found for type: {node_type}, category: {category}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error looking up node definition for {node_type}: {str(e)}")
            return None
    
    def get_input_definition(self, node_type: str, input_name: str, category: str = None) -> Optional[mx.Input]:
        """
        Get an input definition for a node type.
        
        Args:
            node_type: The node type
            input_name: The input name
            category: Optional category filter
            
        Returns:
            Optional[mx.Input]: The input definition if found
        """
        cache_key = f"{node_type}_{input_name}_{category}" if category else f"{node_type}_{input_name}"
        
        if cache_key in self._input_def_cache:
            return self._input_def_cache[cache_key]
        
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            input_def = nodedef.getInput(input_name)
            if input_def:
                self._input_def_cache[cache_key] = input_def
                return input_def
        
        return None
    
    def get_output_definition(self, node_type: str, output_name: str, category: str = None) -> Optional[mx.Output]:
        """
        Get an output definition for a node type.
        
        Args:
            node_type: The node type
            output_name: The output name
            category: Optional category filter
            
        Returns:
            Optional[mx.Output]: The output definition if found
        """
        cache_key = f"{node_type}_{output_name}_{category}" if category else f"{node_type}_{output_name}"
        
        if cache_key in self._output_def_cache:
            return self._output_def_cache[cache_key]
        
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            output_def = nodedef.getOutput(output_name)
            if output_def:
                self._output_def_cache[cache_key] = output_def
                return output_def
        
        return None
    
    def validate_document(self) -> bool:
        """
        Validate the current document.
        
        Returns:
            bool: True if document is valid
        """
        if not self.document:
            self.logger.warning("No document to validate")
            return False
        
        try:
            self.performance_monitor.start_operation("validate_document")
            
            # Basic validation
            valid, message = self.document.validate()
            if not valid:
                self.logger.error(f"Document validation failed: {message}")
                return False
            
            # Advanced validation
            validation_results = self.advanced_validator.validate_document_comprehensive(self.document)
            if not validation_results.get('valid', False):
                self.logger.error("Advanced validation failed")
                self.logger.error(self.advanced_validator.get_validation_summary(validation_results))
                return False
            
            self.logger.info("Document validation passed")
            self.performance_monitor.end_operation("validate_document")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during document validation: {str(e)}")
            self.performance_monitor.end_operation("validate_document")
            return False
    
    def _clear_caches(self):
        """Clear all caches."""
        self._node_def_cache.clear()
        self._input_def_cache.clear()
        self._output_def_cache.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.performance_monitor.get_stats()
    
    def _initialize_custom_node_manager(self):
        """Initialize the custom node manager if not already done."""
        if self.custom_node_manager is None and self.document:
            self.custom_node_manager = CustomNodeDefinitionManager(self.document, self.logger)
    
    def _is_custom_node_type(self, node_type: str) -> bool:
        """Check if a node type is a custom type."""
        from ..node_definitions import is_custom_node_type
        return is_custom_node_type(node_type)
    
    def cleanup(self):
        """Clean up resources."""
        self.performance_monitor.cleanup()
        self._clear_caches()
        self.document = None
        self.libraries = None
