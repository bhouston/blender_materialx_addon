#!/usr/bin/env python3
"""
MaterialX Library Builder

This module provides functionality for building and managing MaterialX libraries.
"""

from typing import Dict, List, Optional, Any
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import MaterialXLibraryError


class LibraryBuilder:
    """
    Builder for MaterialX libraries and standard definitions.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the library builder.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger("LibraryBuilder")
        self._libraries: Dict[str, mx.Document] = {}
    
    def load_standard_libraries(self, version: str = "1.39") -> bool:
        """
        Load standard MaterialX libraries.
        
        Args:
            version: MaterialX version to load
            
        Returns:
            True if libraries loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading MaterialX standard libraries (version {version})")
            
            # Create libraries document
            libraries = mx.createDocument()
            
            # Get search path and library folders
            search_path = mx.getDefaultDataSearchPath()
            lib_folders = mx.getDefaultDataLibraryFolders()
            
            # Load libraries
            library_files = mx.loadLibraries(lib_folders, search_path, libraries)
            
            self._libraries['standard'] = libraries
            self.logger.info(f"Loaded {len(library_files)} library files")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load standard libraries: {e}")
            return False
    
    def get_library(self, name: str) -> Optional[mx.Document]:
        """
        Get a library by name.
        
        Args:
            name: Name of the library
            
        Returns:
            MaterialX document if found, None otherwise
        """
        return self._libraries.get(name)
    
    def add_library(self, name: str, library: mx.Document):
        """
        Add a library.
        
        Args:
            name: Name for the library
            library: MaterialX document containing the library
        """
        self._libraries[name] = library
        self.logger.debug(f"Added library: {name}")
    
    def get_node_definitions(self, library_name: str = "standard") -> List[mx.NodeDef]:
        """
        Get node definitions from a library.
        
        Args:
            library_name: Name of the library
            
        Returns:
            List of node definitions
        """
        library = self.get_library(library_name)
        if not library:
            return []
        
        return library.getNodeDefs()
    
    def find_node_definition(self, node_type: str, library_name: str = "standard") -> Optional[mx.NodeDef]:
        """
        Find a node definition by type.
        
        Args:
            node_type: Type of node to find
            library_name: Name of the library to search
            
        Returns:
            Node definition if found, None otherwise
        """
        library = self.get_library(library_name)
        if not library:
            return None
        
        node_defs = library.getNodeDefs()
        for node_def in node_defs:
            if node_def.getNodeString() == node_type:
                return node_def
        
        return None
    
    def list_libraries(self) -> List[str]:
        """
        Get a list of all library names.
        
        Returns:
            List of library names
        """
        return list(self._libraries.keys())
    
    def clear_libraries(self):
        """Clear all libraries."""
        self._libraries.clear()
        self.logger.debug("Cleared all libraries")
