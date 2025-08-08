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
        self.advanced_validator = MaterialXAdvancedValidator(logger)
        
        # Cache for performance optimization
        self._node_def_cache = {}
        self._input_def_cache = {}
        self._output_def_cache = {}
        
        # Custom node definitions manager
        self.custom_node_manager = None
        
        self.logger.info(f"=== DOCUMENT MANAGER: Created new instance (version: {version}) ===")
        
    def load_libraries(self, custom_search_path: Optional[str] = None) -> bool:
        """
        Load MaterialX libraries with proper version handling.
        
        Args:
            custom_search_path: Optional custom search path for libraries
            
        Returns:
            bool: True if libraries loaded successfully
        """
        try:
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MaterialX libraries: {str(e)}")
            return False
    
    def create_document(self) -> mx.Document:
        """
        Create a new MaterialX document with loaded libraries and validation.
        
        Returns:
            mx.Document: The created document
        """
        try:
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
            
            return self.document
            
        except Exception as e:
            self.logger.error(f"Failed to create MaterialX document: {str(e)}")
            raise
    
    def create_clean_document(self) -> mx.Document:
        """
        Create a new MaterialX document without library includes for export.
        
        Returns:
            mx.Document: The created document
        """
        try:
            self.logger.info("Creating clean MaterialX document for export")
            
            # Create working document
            self.document = mx.createDocument()
            
            # Set colorspace attribute (required for MaterialX compliance)
            self.document.setColorSpace("lin_rec709")
            
            # Create a completely clean document with no library imports
            # Libraries will only be used for validation, not in the export
            
            self.logger.info(f"Clean document created without any library includes")
            
            # Initialize custom node definitions manager (lazy initialization)
            self._initialize_custom_node_manager()
            
            return self.document
            
        except Exception as e:
            self.logger.error(f"Failed to create clean MaterialX document: {str(e)}")
            raise
    
    def _remove_library_includes(self):
        """
        Remove all xi:include elements from the document to make it portable.
        """
        try:
            # Get all elements in the document
            elements = self.document.getChildren()
            
            # Find and remove xi:include elements
            includes_to_remove = []
            for element in elements:
                # Check if it's an xi:include element by looking at the element type
                if hasattr(element, 'getCategory') and element.getCategory() == "xi:include":
                    includes_to_remove.append(element)
                # Also check by name pattern
                elif hasattr(element, 'getName') and element.getName().startswith('xi:include'):
                    includes_to_remove.append(element)
            
            # Remove the includes
            for include in includes_to_remove:
                try:
                    self.document.removeChild(include.getName())
                except:
                    # Try alternative removal method
                    try:
                        self.document.removeChild(include)
                    except:
                        self.logger.warning(f"Could not remove include: {include.getName() if hasattr(include, 'getName') else str(include)}")
            
            self.logger.info(f"Removed {len(includes_to_remove)} library includes from document")
            
        except Exception as e:
            self.logger.warning(f"Failed to remove library includes: {str(e)}")
            
        # Alternative approach: Create a new document without includes
        try:
            # Create a new clean document
            clean_doc = mx.createDocument()
            clean_doc.setColorSpace("lin_rec709")
            
            # Copy only the elements we want (materials, nodegraphs, etc.)
            for element in self.document.getChildren():
                if element.getCategory() not in ["xi:include"]:
                    # Clone the element to the new document
                    clean_doc.importLibrary(self.document)
                    break  # importLibrary copies all non-include elements
            
            # Replace the document
            self.document = clean_doc
            self.logger.info("Created clean document without library includes")
            
        except Exception as e:
            self.logger.warning(f"Failed to create clean document: {str(e)}")
    
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
        Validate the current document using libraries for validation only.
        
        Returns:
            bool: True if document is valid
        """
        if not self.document:
            self.logger.warning("No document to validate")
            return False
        
        try:
            # Use the MaterialXValidator with libraries for validation only
            from ..validation.validator import MaterialXValidator
            
            validator = MaterialXValidator(self.logger)
            
            # Load libraries for validation only (not attached to document)
            if not validator.load_standard_libraries():
                self.logger.warning("Could not load standard libraries for validation")
                # Continue with basic validation only
                valid, message = self.document.validate()
                if not valid:
                    self.logger.error(f"Document validation failed: {message}")
                    return False
                self.logger.info("Document validation passed (basic only)")
                return True
            
            # Validate the document with libraries for reference
            results = validator.validate_document(self.document, include_stdlib=True)
            
            if results['valid']:
                self.logger.info("Document validation passed")
                return True
            else:
                self.logger.error(f"Document validation failed: {results['errors']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during document validation: {str(e)}")
            return False
    
    def _clear_caches(self):
        """Clear all caches."""
        self._node_def_cache.clear()
        self._input_def_cache.clear()
        self._output_def_cache.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {}  # Performance monitoring removed
    
    def _initialize_custom_node_manager(self):
        """Initialize the custom node manager if not already done."""
        if self.custom_node_manager is None and self.document:
            self.logger.info(f"=== DOCUMENT MANAGER: Initializing custom node manager ===")
            self.logger.info(f"=== DOCUMENT MANAGER: Document has {len(self.document.getNodeDefs())} node definitions before custom manager init ===")
            self.custom_node_manager = CustomNodeDefinitionManager(self.document, self.logger)
            self.logger.info(f"=== DOCUMENT MANAGER: Document has {len(self.document.getNodeDefs())} node definitions after custom manager init ===")
        else:
            self.logger.info(f"=== DOCUMENT MANAGER: Custom node manager already initialized or no document ===")
    
    def _is_custom_node_type(self, node_type: str) -> bool:
        """Check if a node type is a custom type."""
        from ..node_definitions import is_custom_node_type
        return is_custom_node_type(node_type)
    
    def cleanup(self):
        """Clean up resources."""
        self._clear_caches()
        self.document = None
        self.libraries = None
