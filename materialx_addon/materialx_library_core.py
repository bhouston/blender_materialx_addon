#!/usr/bin/env python3
"""
MaterialX Library Core - Phase 1, 2 & 3 Implementation

This module implements the core infrastructure migration from manual XML generation
to MaterialX library APIs as outlined in the integration plan.

Phase 1: Core Infrastructure Migration
- Replace XML generation with MaterialX library
- Implement library loading system
- Create MaterialX document builder

Phase 2: Node Mapping System Enhancement
- Leverage node definitions for type-safe mapping
- Implement automatic type conversion and validation
- Enhanced node creation with validation

Phase 3: Advanced Features Integration
- File writing improvements with advanced options
- Enhanced validation and error handling
- Performance optimization and memory management
- Error recovery and robustness features
"""
print("DEBUG: MaterialX library core module loaded")

import MaterialX as mx
import os
import sys
import time
import gc
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import logging

# Import mtlxutils
try:
    from . import mtlxutils
    from .mtlxutils import mxbase as mxb
    from .mtlxutils import mxfile as mxf
    from .mtlxutils import mxnodegraph as mxg
    from .mtlxutils import mxtraversal as mxt

except ImportError:
    # Fallback for direct import
    import mtlxutils
    import mtlxutils.mxbase as mxb
    import mtlxutils.mxfile as mxf
    import mtlxutils.mxnodegraph as mxg
    import mtlxutils.mxtraversal as mxt



class MaterialXConfig:
    """Configuration system for MaterialX export settings."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        # Core settings
        'materialx_version': '1.39',
        'optimize_document': True,
        'advanced_validation': True,
        'performance_monitoring': True,
        
        # File writing options
        'skip_library_elements': True,
        'write_xinclude': False,
        'remove_layout': True,
        'format_output': True,
        
        # Error handling
        'strict_mode': True,
        'max_errors': 10,
        
        # Performance settings
        'enable_caching': True,
        'cache_size_limit': 1000,
        'memory_warning_threshold_mb': 100,
        
        # Validation settings
        'validate_connections': True,
        'check_circular_dependencies': True,
        'warn_unused_nodes': True,
        'max_node_count_warning': 100,
        'max_nesting_depth_warning': 10
    }
    
    def __init__(self, custom_config: Dict = None):
        """Initialize configuration with defaults and custom overrides."""
        self.config = self.DEFAULT_CONFIG.copy()
        if custom_config:
            self.config.update(custom_config)
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value
    
    def update(self, new_config: Dict):
        """Update configuration with new values."""
        self.config.update(new_config)
    
    def get_export_options(self) -> Dict:
        """Get export-specific options."""
        return {
            'optimize_document': self.get('optimize_document'),
            'advanced_validation': self.get('advanced_validation'),
            'performance_monitoring': self.get('performance_monitoring')
        }
    
    def get_write_options(self) -> Dict:
        """Get file writing options."""
        return {
            'skip_library_elements': self.get('skip_library_elements'),
            'write_xinclude': self.get('write_xinclude'),
            'remove_layout': self.get('remove_layout'),
            'format_output': self.get('format_output')
        }


class MaterialXValidationError(Exception):
    """Custom exception for MaterialX validation errors."""
    pass


class MaterialXError(Exception):
    """Base class for MaterialX-specific errors with classification."""
    
    def __init__(self, message: str, error_type: str = "general", details: Dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
    
    def get_user_friendly_message(self) -> str:
        """Get a user-friendly error message."""
        error_messages = {
            "library_loading": "Failed to load MaterialX libraries. Please check your MaterialX installation.",
            "node_creation": "Failed to create MaterialX node. The node type may not be supported.",
            "connection_error": "Failed to connect nodes. There may be a type mismatch.",
            "validation_error": "MaterialX document validation failed. Check the material setup.",
            "file_write": "Failed to write MaterialX file. Check file permissions and disk space.",
            "type_conversion": "Failed to convert data types. Check input values.",
            "unsupported_node": "This Blender node type is not supported in MaterialX export.",
            "performance_warning": "Export completed but performance issues were detected.",
            "memory_error": "Insufficient memory for export operation."
        }
        return error_messages.get(self.error_type, str(self))


class MaterialXPerformanceMonitor:
    """
    Monitors performance metrics for MaterialX operations.
    
    This class provides:
    - Operation timing
    - Memory usage tracking
    - Performance optimization suggestions
    - Resource cleanup monitoring
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.operation_times = {}
        self.memory_snapshots = {}
        self.start_time = None
        self.enabled = True
    
    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        if not self.enabled:
            return
        
        self.operation_times[operation_name] = {
            'start': time.time(),
            'memory_before': self._get_memory_usage()
        }
    
    def end_operation(self, operation_name: str):
        """End timing an operation and log results."""
        if not self.enabled or operation_name not in self.operation_times:
            return
        
        end_time = time.time()
        memory_after = self._get_memory_usage()
        
        timing = self.operation_times[operation_name]
        duration = end_time - timing['start']
        memory_delta = memory_after - timing['memory_before']
        
        self.logger.debug(f"Operation '{operation_name}': {duration:.4f}s, Memory: {memory_delta:+d} bytes")
        
        # Performance warnings
        if duration > 1.0:
            self.logger.warning(f"Slow operation detected: '{operation_name}' took {duration:.4f}s")
        if memory_delta > 10 * 1024 * 1024:  # 10MB
            self.logger.warning(f"High memory usage detected: '{operation_name}' used {memory_delta / (1024*1024):.2f}MB")
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def suggest_optimizations(self) -> List[str]:
        """Analyze performance data and suggest optimizations."""
        suggestions = []
        
        if not self.operation_times:
            return suggestions
        
        # Find slowest operations
        slow_operations = [(name, data.get('duration', 0)) 
                          for name, data in self.operation_times.items()]
        slow_operations.sort(key=lambda x: x[1], reverse=True)
        
        if slow_operations and slow_operations[0][1] > 0.5:
            suggestions.append(f"Consider optimizing '{slow_operations[0][0]}' (took {slow_operations[0][1]:.4f}s)")
        
        return suggestions
    
    def cleanup(self):
        """Clean up performance monitoring data."""
        self.operation_times.clear()
        self.memory_snapshots.clear()
        gc.collect()





class MaterialXAdvancedValidator:
    """
    Advanced validation features for MaterialX documents.
    
    This class provides:
    - Comprehensive document validation
    - Node definition validation
    - Connection validation
    - Performance validation
    - Custom validation rules
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.validation_rules = {}
        self.custom_validators = {}
    
    def validate_document_comprehensive(self, document: mx.Document) -> Dict[str, Any]:
        """
        Perform comprehensive validation of a MaterialX document.
        
        Args:
            document: The MaterialX document to validate
            
        Returns:
            Dict containing validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'performance_issues': [],
            'suggestions': []
        }
        
        try:
            # Basic document validation
            if not self._validate_basic_structure(document, results):
                results['valid'] = False
            
            # Node validation
            self._validate_nodes(document, results)
            
            # Connection validation
            self._validate_connections(document, results)
            
            # Performance validation
            self._validate_performance(document, results)
            
            # Custom validation rules
            self._apply_custom_validators(document, results)
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation failed with exception: {str(e)}")
            self.logger.error(f"Document validation failed: {str(e)}")
        
        return results
    
    def _validate_basic_structure(self, document: mx.Document, results: Dict[str, Any]) -> bool:
        """Validate basic document structure."""
        try:
            # Check for required elements
            materials = document.getMaterialNodes()
            if not materials:
                results['warnings'].append("No material nodes found in document")
            
            # Check for surface shaders - get all nodes and filter by type
            all_nodes = document.getNodes()
            surface_shaders = [node for node in all_nodes if node.getType() == 'surfaceshader']
            if not surface_shaders:
                results['warnings'].append("No surface shader nodes found in document")
            
            # Check for nodegraphs
            nodegraphs = document.getNodeGraphs()
            if not nodegraphs:
                results['warnings'].append("No nodegraphs found in document")
            
            return True
            
        except Exception as e:
            results['errors'].append(f"Basic structure validation failed: {str(e)}")
            return False
    
    def _validate_nodes(self, document: mx.Document, results: Dict[str, Any]):
        """Validate all nodes in the document."""
        try:
            nodes = document.getNodes()
            for node in nodes:
                # Check node definition
                nodedef = node.getNodeDef()
                if not nodedef:
                    results['warnings'].append(f"Node '{node.getName()}' has no node definition")
                    continue
                
                # Check input connections - use MaterialX 1.39 compatible API
                for input_elem in node.getInputs():
                    try:
                        # Check if input has a connection
                        if hasattr(input_elem, 'getConnectedNode'):
                            connected_node = input_elem.getConnectedNode()
                            if connected_node:
                                # Validate the connected node exists
                                if not document.getChild(connected_node.getName()):
                                    results['warnings'].append(f"Input '{input_elem.getName()}' on node '{node.getName()}' connects to non-existent node")
                    except Exception as e:
                        # Skip validation for this input if API is not available
                        pass
                
                # Check output connections - use MaterialX 1.39 compatible API
                for output_elem in node.getOutputs():
                    try:
                        # Check if output has connections
                        if hasattr(output_elem, 'getConnections'):
                            connections = output_elem.getConnections()
                            if connections:
                                for connection in connections:
                                    if hasattr(connection, 'getDownstreamElement'):
                                        downstream = connection.getDownstreamElement()
                                        if downstream and not document.getChild(downstream.getName()):
                                            results['warnings'].append(f"Output '{output_elem.getName()}' on node '{node.getName()}' connects to non-existent node")
                    except Exception as e:
                        # Skip validation for this output if API is not available
                        pass
                        
        except Exception as e:
            results['errors'].append(f"Node validation failed: {str(e)}")
    
    def _validate_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate all connections in the document."""
        try:
            # Use MaterialX 1.39 compatible connection analysis
            nodes = document.getNodes()
            for node in nodes:
                # Check input connections
                for input_elem in node.getInputs():
                    try:
                        if hasattr(input_elem, 'getConnectedNode'):
                            connected_node = input_elem.getConnectedNode()
                            if connected_node:
                                # Basic connection validation
                                if not document.getChild(connected_node.getName()):
                                    results['warnings'].append(f"Input '{input_elem.getName()}' on node '{node.getName()}' connects to non-existent node")
                    except Exception as e:
                        # Skip validation if API is not available
                        pass
                        
        except Exception as e:
            results['errors'].append(f"Connection validation failed: {str(e)}")
    
    def _validate_performance(self, document: mx.Document, results: Dict[str, Any]):
        """Validate document for performance issues."""
        try:
            # Check for excessive node count
            nodes = document.getNodes()
            if len(nodes) > 100:
                results['performance_issues'].append(f"Large number of nodes ({len(nodes)}) may impact performance")
            
            # Check for deep nesting
            nodegraphs = document.getNodeGraphs()
            for nodegraph in nodegraphs:
                depth = self._calculate_nesting_depth(nodegraph)
                if depth > 5:
                    results['performance_issues'].append(f"Deep nesting detected in nodegraph '{nodegraph.getName()}' (depth: {depth})")
            
            # Check for unused nodes
            unused_nodes = self._find_unused_nodes(document)
            if unused_nodes:
                results['suggestions'].append(f"Found {len(unused_nodes)} unused nodes that could be removed")
                
        except Exception as e:
            results['errors'].append(f"Performance validation failed: {str(e)}")
    
    def _has_circular_connection(self, document: mx.Document, start_elem: mx.Element, target_elem: mx.Element) -> bool:
        """Check for circular connections."""
        visited = set()
        return self._dfs_for_circular(start_elem, target_elem, visited, document)
    
    def _dfs_for_circular(self, current: mx.Element, target: mx.Element, visited: set, document: mx.Document) -> bool:
        """Depth-first search for circular connections."""
        if current == target:
            return True
        
        if current.getNamePath() in visited:
            return False
        
        visited.add(current.getNamePath())
        
        # Check downstream connections
        if current.isA(mx.Node):
            for output in current.getOutputs():
                if output.isConnected():
                    for edge in output.getConnections():
                        downstream = edge.getDownstreamElement()
                        if downstream and self._dfs_for_circular(downstream, target, visited, document):
                            return True
        
        return False
    
    def _calculate_nesting_depth(self, element: mx.Element, current_depth: int = 0) -> int:
        """Calculate the nesting depth of an element."""
        max_depth = current_depth
        
        for child in element.getChildren():
            if child.isA(mx.NodeGraph):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _find_unused_nodes(self, document: mx.Document) -> List[mx.Node]:
        """Find nodes that are not connected to any material output."""
        try:
            # Get all nodes
            all_nodes = list(document.getNodes())
            
            # Find nodes connected to materials
            connected_nodes = []
            materials = document.getMaterialNodes()
            
            for material in materials:
                self._collect_connected_nodes(material, connected_nodes, document)
            
            # Return unused nodes (nodes not in connected_nodes)
            unused_nodes = []
            for node in all_nodes:
                if node not in connected_nodes:
                    unused_nodes.append(node)
            
            return unused_nodes
            
        except Exception as e:
            self.logger.error(f"Error finding unused nodes: {str(e)}")
            return []
    
    def _collect_connected_nodes(self, element: mx.Element, connected_nodes: list, document: mx.Document):
        """Collect all nodes connected to a given element."""
        if element.isA(mx.Node):
            if element not in connected_nodes:
                connected_nodes.append(element)
            
            # Check inputs
            for input_elem in element.getInputs():
                try:
                    if hasattr(input_elem, 'getConnectedNode'):
                        connected_node = input_elem.getConnectedNode()
                        if connected_node and connected_node not in connected_nodes:
                            self._collect_connected_nodes(connected_node, connected_nodes, document)
                except Exception as e:
                    # Skip if API is not available
                    pass
    
    def _apply_custom_validators(self, document: mx.Document, results: Dict[str, Any]):
        """Apply custom validation rules."""
        for validator_name, validator_func in self.custom_validators.items():
            try:
                validator_result = validator_func(document)
                if not validator_result['valid']:
                    results['errors'].extend(validator_result.get('errors', []))
                    results['warnings'].extend(validator_result.get('warnings', []))
            except Exception as e:
                results['errors'].append(f"Custom validator '{validator_name}' failed: {str(e)}")
    
    def add_custom_validator(self, name: str, validator_func):
        """Add a custom validation rule."""
        self.custom_validators[name] = validator_func
    
    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """Get a summary of validation results."""
        summary = f"Validation {'PASSED' if results['valid'] else 'FAILED'}\n"
        summary += f"Errors: {len(results['errors'])}\n"
        summary += f"Warnings: {len(results['warnings'])}\n"
        summary += f"Performance Issues: {len(results['performance_issues'])}\n"
        summary += f"Suggestions: {len(results['suggestions'])}"
        return summary


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
            
            # Validate document after creation
            validation_results = self.advanced_validator.validate_document_comprehensive(self.document)
            if not validation_results['valid']:
                self.logger.warning("Document validation issues detected:")
                for error in validation_results['errors']:
                    self.logger.warning(f"  - {error}")
            
            self.logger.info("MaterialX document created successfully")
            
            self.performance_monitor.end_operation("create_document")
            return self.document
            
        except Exception as e:
            self.logger.error(f"Failed to create MaterialX document: {str(e)}")
            self.performance_monitor.end_operation("create_document")
            raise
    
    def get_node_definition(self, node_type: str, category: str = None) -> Optional[mx.NodeDef]:
        """
        Get a node definition from the loaded libraries with caching.
        
        Args:
            node_type: The node type to find
            category: Optional category filter
            
        Returns:
            mx.NodeDef: The node definition or None if not found
        """
        if not self.document:
            self.logger.error("No document available for node definition lookup")
            return None
        
        # Create cache key
        cache_key = f"{node_type}_{category or 'any'}"
        
        # Check cache first
        if cache_key in self._node_def_cache:
            return self._node_def_cache[cache_key]
        
        try:
            self.performance_monitor.start_operation("get_node_definition")
            
            # Get all node definitions and search through them
            all_node_defs = self.document.getNodeDefs()
            print(f"DEBUG: Searching for node definition '{node_type}' (category: {category}) among {len(all_node_defs)} node definitions")
            self.logger.info(f"Searching for node definition '{node_type}' (category: {category}) among {len(all_node_defs)} node definitions")
            
            # Look for exact match first by node type
            for nodedef in all_node_defs:
                if nodedef.getType() == node_type:
                    if category is None or nodedef.getCategory() == category:
                        result = nodedef
                        self.logger.info(f"Found exact match by type: {nodedef.getName()}")
                        break
            else:
                # If no exact match by type, try searching by node name
                print(f"DEBUG: No exact match by type, trying search by name...")
                self.logger.info(f"No exact match by type, trying search by name...")
                
                # Debug: Show some node names that contain our search term
                matching_names = []
                for nodedef in all_node_defs:
                    nodedef_name = nodedef.getName()
                    if node_type.lower() in nodedef_name.lower():
                        matching_names.append(nodedef_name)
                
                if matching_names:
                    print(f"DEBUG: Found {len(matching_names)} node names containing '{node_type}': {matching_names[:5]}")
                
                for nodedef in all_node_defs:
                    nodedef_name = nodedef.getName()
                    # Look for the node type in the name (e.g., "standard_surface" in "ND_standard_surface_surfaceshader")
                    if node_type.lower() in nodedef_name.lower():
                        nodedef_category = nodedef.getCategory()
                        nodedef_type = nodedef.getType()
                        print(f"DEBUG: Checking {nodedef_name} - category: {nodedef_category}, type: {nodedef_type}, expected: {category}")
                        if category is None or nodedef_type == category:
                            result = nodedef
                            print(f"DEBUG: Found match by name: {nodedef_name} (type: {nodedef.getType()})")
                            self.logger.info(f"Found match by name: {nodedef_name} (type: {nodedef.getType()})")
                            break
                else:
                    # If no match by name, try partial matching on type
                    self.logger.info(f"No match by name, trying partial matching on type...")
                    for nodedef in all_node_defs:
                        nodedef_type = nodedef.getType()
                        if node_type in nodedef_type or nodedef_type in node_type:
                            if category is None or nodedef.getCategory() == category:
                                result = nodedef
                                self.logger.info(f"Found partial match by type: {nodedef.getName()} (type: {nodedef_type})")
                                break
                    else:
                        result = None
                        self.logger.warning(f"No node definition found for '{node_type}' (category: {category})")
            
            # Cache the result
            if result is not None:
                self._node_def_cache[cache_key] = result
            
            self.performance_monitor.end_operation("get_node_definition")
            return result
            
        except Exception as e:
            self.logger.error(f"Error looking up node definition {node_type}: {str(e)}")
            self.performance_monitor.end_operation("get_node_definition")
            return None
    
    def get_input_definition(self, node_type: str, input_name: str, category: str = None) -> Optional[mx.Input]:
        """
        Get an input definition from a node definition.
        
        Args:
            node_type: The node type
            input_name: The input name
            category: Optional category filter
            
        Returns:
            mx.Input: The input definition or None if not found
        """
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            return nodedef.getInput(input_name)
        return None
    
    def get_output_definition(self, node_type: str, output_name: str, category: str = None) -> Optional[mx.Output]:
        """
        Get an output definition from a node definition.
        
        Args:
            node_type: The node type
            output_name: The output name
            category: Optional category filter
            
        Returns:
            mx.Output: The output definition or None if not found
        """
        nodedef = self.get_node_definition(node_type, category)
        if nodedef:
            return nodedef.getOutput(output_name)
        return None
    
    def validate_document(self) -> bool:
        """
        Validate the MaterialX document with comprehensive validation.
        
        Returns:
            bool: True if document is valid
        """
        if not self.document:
            return False
        
        try:
            self.performance_monitor.start_operation("validate_document")
            
            # Use advanced validator for comprehensive validation
            validation_results = self.advanced_validator.validate_document_comprehensive(self.document)
            
            # Log validation summary
            summary = self.advanced_validator.get_validation_summary(validation_results)
            self.logger.info(f"Document validation: {summary}")
            
            # Log detailed results
            if validation_results['errors']:
                self.logger.error("Validation errors:")
                for error in validation_results['errors']:
                    self.logger.error(f"  - {error}")
            
            if validation_results['warnings']:
                self.logger.warning("Validation warnings:")
                for warning in validation_results['warnings']:
                    self.logger.warning(f"  - {warning}")
            
            if validation_results['performance_issues']:
                self.logger.warning("Performance issues:")
                for issue in validation_results['performance_issues']:
                    self.logger.warning(f"  - {issue}")
            
            if validation_results['suggestions']:
                self.logger.info("Suggestions:")
                for suggestion in validation_results['suggestions']:
                    self.logger.info(f"  - {suggestion}")
            
            self.performance_monitor.end_operation("validate_document")
            return validation_results['valid']
            
        except Exception as e:
            self.logger.error(f"Document validation failed: {str(e)}")
            self.performance_monitor.end_operation("validate_document")
            return False
    
    def _clear_caches(self):
        """Clear all caches to free memory."""
        self._node_def_cache.clear()
        self._input_def_cache.clear()
        self._output_def_cache.clear()
        gc.collect()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'cache_sizes': {
                'node_defs': len(self._node_def_cache),
                'input_defs': len(self._input_def_cache),
                'output_defs': len(self._output_def_cache)
            },
            'suggestions': self.performance_monitor.suggest_optimizations()
        }
    
    def cleanup(self):
        """Clean up resources and free memory."""
        self._clear_caches()
        self.performance_monitor.cleanup()
        self.logger.info("MaterialXDocumentManager cleanup completed")


class MaterialXTypeConverter:
    """
    Handles type conversion and validation for MaterialX inputs and outputs.
    
    This class provides:
    - Automatic type conversion between Blender and MaterialX types
    - Type validation and compatibility checking
    - Value formatting for different MaterialX types
    """
    
    def __init__(self, logger):
        self.logger = logger
        
        # Type compatibility mapping
        self.type_compatibility = {
            'color3': ['color3', 'vector3', 'vector2'],  # color3 can convert to vector2 (extract first two components)
            'vector3': ['vector3', 'color3'],
            'vector2': ['vector2', 'vector3'],  # vector2 can convert to vector3 (add Z=0)
            'vector4': ['vector4', 'color4'],
            'color4': ['color4', 'vector4'],
            'float': ['float'],
            'filename': ['filename'],
            'string': ['string'],
            'integer': ['integer'],
            'boolean': ['boolean']
        }
        
        # Blender to MaterialX type mapping
        self.blender_to_mtlx_types = {
            'RGBA': 'color4',
            'RGB': 'color3',
            'VECTOR': 'vector3',
            'VECTOR_2D': 'vector2',
            'VALUE': 'float',
            'INT': 'integer',
            'BOOLEAN': 'boolean',
            'STRING': 'string'
        }
    
    def convert_blender_type(self, blender_type: str) -> str:
        """
        Convert a Blender socket type to MaterialX type.
        
        Args:
            blender_type: The Blender socket type
            
        Returns:
            str: The corresponding MaterialX type
        """
        return self.blender_to_mtlx_types.get(blender_type, 'color3')
    
    def validate_type_compatibility(self, from_type: str, to_type: str) -> bool:
        """
        Validate if a type conversion is compatible.
        
        Args:
            from_type: The source type
            to_type: The target type
            
        Returns:
            bool: True if conversion is compatible
        """
        # Direct match
        if from_type == to_type:
            return True
        
        # Check compatibility mapping
        if from_type in self.type_compatibility:
            compatible_types = self.type_compatibility[from_type]
            if to_type in compatible_types:
                return True
        
        # Special cases for specific conversions mentioned in corrections plan
        if from_type == 'vector2' and to_type == 'vector3':
            return True  # texcoord -> fractal3d position
        if from_type == 'color3' and to_type == 'vector2':
            return True  # mix -> ramp texcoord
        if from_type == 'color3' and to_type == 'vector3':
            return True  # mix -> normalmap default
        
        # Legacy special cases
        if from_type == 'color3' and to_type == 'vector3':
            return True
        if from_type == 'vector3' and to_type == 'color3':
            return True
        if from_type == 'color4' and to_type == 'vector4':
            return True
        if from_type == 'vector4' and to_type == 'color4':
            return True
        
        self.logger.warning(f"Type incompatibility: {from_type} -> {to_type}")
        return False
    
    def convert_value(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the target MaterialX type.
        
        Args:
            value: The value to convert
            target_type: The target MaterialX type
            
        Returns:
            Any: The converted value
        """
        try:
            # Handle Blender's bpy_prop_array types
            if hasattr(value, '__len__') and not isinstance(value, (str, bytes)):
                # Convert Blender arrays to list of floats
                try:
                    if hasattr(value, 'default_value'):
                        # Handle Blender socket default values
                        value = value.default_value
                    
                    # Convert to list of floats
                    float_list = []
                    for i in range(len(value)):
                        try:
                            float_list.append(float(value[i]))
                        except (TypeError, ValueError, IndexError):
                            float_list.append(0.0)
                    
                    # Now handle based on target type
                    if target_type == 'float':
                        return float_list[0] if float_list else 0.0
                    elif target_type == 'integer':
                        return int(float_list[0]) if float_list else 0
                    elif target_type == 'boolean':
                        return bool(float_list[0]) if float_list else False
                    elif target_type == 'string':
                        return str(value)
                    elif target_type == 'color3':
                        if len(float_list) >= 3:
                            return [float_list[0], float_list[1], float_list[2]]
                        elif len(float_list) >= 1:
                            return [float_list[0], float_list[0], float_list[0]]
                        else:
                            return [0.0, 0.0, 0.0]
                    elif target_type == 'vector3':
                        if len(float_list) >= 3:
                            return [float_list[0], float_list[1], float_list[2]]
                        elif len(float_list) >= 1:
                            return [float_list[0], float_list[0], float_list[0]]
                        else:
                            return [0.0, 0.0, 0.0]
                    elif target_type == 'vector2':
                        if len(float_list) >= 2:
                            return [float_list[0], float_list[1]]
                        elif len(float_list) >= 1:
                            return [float_list[0], float_list[0]]
                        else:
                            return [0.0, 0.0]
                    elif target_type == 'color4':
                        if len(float_list) >= 4:
                            return [float_list[0], float_list[1], float_list[2], float_list[3]]
                        elif len(float_list) >= 3:
                            return [float_list[0], float_list[1], float_list[2], 1.0]
                        elif len(float_list) >= 1:
                            return [float_list[0], float_list[0], float_list[0], 1.0]
                        else:
                            return [0.0, 0.0, 0.0, 1.0]
                    
                    return float_list
                    
                except Exception as e:
                    self.logger.error(f"Error converting Blender array {value} to type {target_type}: {str(e)}")
                    # Fallback to default values
                    if target_type == 'float':
                        return 0.0
                    elif target_type == 'integer':
                        return 0
                    elif target_type == 'boolean':
                        return False
                    elif target_type == 'string':
                        return str(value)
                    elif target_type == 'color3':
                        return [0.0, 0.0, 0.0]
                    elif target_type == 'vector3':
                        return [0.0, 0.0, 0.0]
                    elif target_type == 'vector2':
                        return [0.0, 0.0]
                    elif target_type == 'color4':
                        return [0.0, 0.0, 0.0, 1.0]
                    return value
            
            # Handle regular types (non-array)
            if target_type == 'float':
                return float(value)
            elif target_type == 'integer':
                return int(value)
            elif target_type == 'boolean':
                return bool(value)
            elif target_type == 'string':
                return str(value)
            elif target_type == 'color3':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val, val]
            elif target_type == 'vector3':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val, val]
            elif target_type == 'vector2':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 2:
                        return [float(value[0]), float(value[1])]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0])]
                else:
                    val = float(value)
                    return [val, val]
            elif target_type == 'color4':
                if isinstance(value, (list, tuple)):
                    if len(value) >= 4:
                        return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
                    elif len(value) >= 3:
                        return [float(value[0]), float(value[1]), float(value[2]), 1.0]
                    elif len(value) == 1:
                        return [float(value[0]), float(value[0]), float(value[0]), 1.0]
                else:
                    val = float(value)
                    return [val, val, val, 1.0]
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error converting value {value} to type {target_type}: {str(e)}")
            # Return safe defaults
            if target_type == 'float':
                return 0.0
            elif target_type == 'integer':
                return 0
            elif target_type == 'boolean':
                return False
            elif target_type == 'string':
                return str(value)
            elif target_type == 'color3':
                return [0.0, 0.0, 0.0]
            elif target_type == 'vector3':
                return [0.0, 0.0, 0.0]
            elif target_type == 'vector2':
                return [0.0, 0.0]
            elif target_type == 'color4':
                return [0.0, 0.0, 0.0, 1.0]
            return value
    
    def format_value_string(self, value: Any, value_type: str) -> str:
        """
        Format a value as a MaterialX value string.
        
        Args:
            value: The value to format
            value_type: The MaterialX type
            
        Returns:
            str: The formatted value string
        """
        try:
            if isinstance(value, (int, float)):
                return f"{value:.4g}"
            elif isinstance(value, (list, tuple)):
                # Handle vector/color types
                if value_type in ['color3', 'vector3'] and len(value) >= 3:
                    return f"{value[0]:.4g},{value[1]:.4g},{value[2]:.4g}"
                elif value_type in ['color4', 'vector4'] and len(value) >= 4:
                    return f"{value[0]:.4g},{value[1]:.4g},{value[2]:.4g},{value[3]:.4g}"
                elif value_type in ['vector2'] and len(value) >= 2:
                    return f"{value[0]:.4g},{value[1]:.4g}"
                else:
                    return ",".join(f"{v:.4g}" for v in value)
            else:
                return str(value)
                
        except Exception as e:
            self.logger.error(f"Error formatting value {value} for type {value_type}: {str(e)}")
            return str(value)


class MaterialXNodeBuilder:
    """
    Handles node creation using MaterialX library.
    
    This class provides:
    - Type-safe node creation with proper node definitions
    - Input/output handling with automatic type conversion
    - Connection management using mtlxutils
    - Value formatting and validation
    - Nodegraph creation and management
    """
    
    def __init__(self, document_manager: MaterialXDocumentManager, logger):
        self.doc_manager = document_manager
        self.logger = logger
        self.node_counter = 0
        self.created_nodes = {}
        self.type_converter = MaterialXTypeConverter(logger)
        
    def add_node(self, node_type: str, name: str, category: str = None, 
                 parent: mx.Element = None) -> Optional[mx.Node]:
        """
        Add a node to the document using MaterialX library.
        
        Args:
            node_type: The node type (e.g., 'standard_surface', 'mix')
            name: The node name
            category: Optional category (e.g., 'surfaceshader', 'color3')
            parent: Parent element (defaults to document root)
            
        Returns:
            mx.Node: The created node or None if failed
        """
        try:
            if not parent:
                parent = self.doc_manager.document
            
            # Generate unique name if needed
            if not name:
                name = f"{node_type}_{self.node_counter}"
                self.node_counter += 1
            
            # Create valid child name
            valid_name = parent.createValidChildName(name)
            
            # Get node definition
            if category:
                nodedef = self.doc_manager.get_node_definition(node_type, category)
            else:
                nodedef = self.doc_manager.get_node_definition(node_type)
            
            if not nodedef:
                self.logger.warning(f"No node definition found for {node_type} (category: {category})")
                return None
            
            # Create node instance
            node = parent.addNodeInstance(nodedef, valid_name)
            
            if node:
                self.created_nodes[valid_name] = node
                self.logger.debug(f"Created node: {valid_name} (type: {node_type})")
            
            return node
            
        except Exception as e:
            self.logger.error(f"Failed to create node {name} of type {node_type}: {str(e)}")
            return None
    
    def add_nodegraph(self, name: str, parent: mx.Element = None) -> Optional[mx.NodeGraph]:
        """
        Add a nodegraph to the document.
        
        Args:
            name: The nodegraph name
            parent: Parent element (defaults to document root)
            
        Returns:
            mx.NodeGraph: The created nodegraph or None if failed
        """
        try:
            if not parent:
                parent = self.doc_manager.document
            
            valid_name = parent.createValidChildName(name)
            nodegraph = parent.addChildOfCategory('nodegraph', valid_name)
            
            if nodegraph:
                self.created_nodes[valid_name] = nodegraph
                self.logger.debug(f"Created nodegraph: {valid_name}")
            
            return nodegraph
            
        except Exception as e:
            self.logger.error(f"Failed to create nodegraph {name}: {str(e)}")
            return None
    
    def create_mtlx_input(self, node: mx.Node, input_name: str, value: Any = None, 
                         nodename: str = None, node_type: str = None, category: str = None) -> Optional[mx.Input]:
        """
        Create a MaterialX input with type-safe handling.
        
        Args:
            node: The target node
            input_name: The input name
            value: The input value (for constant inputs)
            nodename: The connected node name (for connections)
            node_type: The node type for definition lookup
            category: The node category for definition lookup
            
        Returns:
            mx.Input: The created input or None if failed
        """
        try:
            # Get input definition for type information
            input_def = None
            if node_type:
                input_def = self.doc_manager.get_input_definition(node_type, input_name, category)
            
            # Determine input type
            if input_def:
                input_type = input_def.getType()
            else:
                # Fallback type determination
                input_type = self._get_input_type_from_name(input_name)
            
            # Create input
            input_elem = node.addInput(input_name, input_type)
            
            if input_elem:
                if value is not None:
                    # Convert and set constant value
                    converted_value = self.type_converter.convert_value(value, input_type)
                    formatted_value = self.type_converter.format_value_string(converted_value, input_type)
                    input_elem.setValueString(formatted_value)
                    self.logger.debug(f"Set input {input_name} = {formatted_value} (type: {input_type})")
                elif nodename:
                    # Set connection
                    input_elem.setNodeName(nodename)
                    self.logger.debug(f"Connected input {input_name} to {nodename}")
                
                # Add colorspace attribute for opacity inputs
                if input_name == 'opacity':
                    input_elem.setAttribute('colorspace', 'lin_rec709')
            
            return input_elem
            
        except Exception as e:
            self.logger.error(f"Failed to create input {input_name} for node {node.getName()}: {str(e)}")
            return None
    
    def add_input(self, node: mx.Node, input_name: str, input_type: str, 
                  value: Any = None, nodename: str = None) -> Optional[mx.Input]:
        """
        Add an input to a node (legacy method for backward compatibility).
        
        Args:
            node: The target node
            input_name: The input name
            input_type: The input type
            value: The input value (for constant inputs)
            nodename: The connected node name (for connections)
            
        Returns:
            mx.Input: The created input or None if failed
        """
        return self.create_mtlx_input(node, input_name, value, nodename)
    
    def add_output(self, nodegraph: mx.NodeGraph, name: str, output_type: str, 
                   nodename: str) -> Optional[mx.Output]:
        """
        Add an output to a nodegraph with validation.
        
        Args:
            nodegraph: The target nodegraph
            name: The output name
            output_type: The output type
            nodename: The connected node name
            
        Returns:
            mx.Output: The created output or None if failed
        """
        try:
            # Validate that nodename refers to an actual node, not an output
            if not nodegraph.getChild(nodename):
                self.logger.warning(f"Output {name} references non-existent node: {nodename}")
                return None
            
            # Check if nodename is actually an output (which would be invalid)
            existing_output = nodegraph.getOutput(nodename)
            if existing_output:
                self.logger.warning(f"Output {name} references another output '{nodename}' instead of a node")
                return None
            
            valid_name = nodegraph.createValidChildName(name)
            output = nodegraph.addOutput(valid_name, output_type)
            
            if output:
                output.setNodeName(nodename)
                self.logger.debug(f"Added output {valid_name} connected to node {nodename}")
            
            return output
            
        except Exception as e:
            self.logger.error(f"Failed to add output {name} to nodegraph {nodegraph.getName()}: {str(e)}")
            return None
    
    def connect_nodes(self, from_node: mx.Node, from_output: str, 
                     to_node: mx.Node, to_input: str) -> bool:
        """
        Connect two nodes with type validation and automatic conversion.
        
        Args:
            from_node: The source node
            from_output: The source output name
            to_node: The target node
            to_input: The target input name
            
        Returns:
            bool: True if connection successful
            
        Raises:
            MaterialXError: If connection fails for any reason
        """
        try:
            # Validate that nodes exist
            if not from_node:
                raise MaterialXError(f"Source node is None for connection to {to_node.getName()}.{to_input}", "invalid_source_node")
            
            if not to_node:
                raise MaterialXError(f"Target node is None for connection from {from_node.getName()}.{from_output}", "invalid_target_node")
            
            # Validate output and input names
            if not from_output:
                raise MaterialXError(f"Source output name is empty for node {from_node.getName()}", "invalid_output_name")
            
            if not to_input:
                raise MaterialXError(f"Target input name is empty for node {to_node.getName()}", "invalid_input_name")
            
            # Get output and input types for validation
            from_type = self._get_node_output_type(from_node, from_output)
            to_type = self._get_node_input_type(to_node, to_input)
            
            self.logger.debug(f"Attempting connection: {from_node.getName()}.{from_output} ({from_type}) -> {to_node.getName()}.{to_input} ({to_type})")
            
            # Check type compatibility
            if self.type_converter.validate_type_compatibility(from_type, to_type):
                self.logger.debug(f"Types compatible, direct connection: {from_type} -> {to_type}")
                return self._direct_connect_nodes(from_node, from_output, to_node, to_input)
            else:
                # Types are incompatible, need conversion
                self.logger.debug(f"Type mismatch detected: {from_type} -> {to_type}, attempting conversion")
                return self._connect_with_conversion(from_node, from_output, to_node, to_input, from_type, to_type)
            
        except MaterialXError:
            # Re-raise MaterialXError exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error connecting {from_node.getName() if from_node else 'None'}.{from_output} -> {to_node.getName() if to_node else 'None'}.{to_input}: {str(e)}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "connection_exception", {"original_error": str(e)})
    
    def _get_node_output_type(self, node: mx.Node, output_name: str) -> str:
        """Get the output type of a node."""
        try:
            output_def = node.getActiveOutput(output_name)
            if output_def:
                return output_def.getType()
            
            # Fallback: try to get from node definition
            node_def = node.getNodeDef()
            if node_def:
                output_def = node_def.getOutput(output_name)
                if output_def:
                    return output_def.getType()
            
            # Default fallback
            return 'color3'
        except Exception:
            return 'color3'
    
    def _get_node_input_type(self, node: mx.Node, input_name: str) -> str:
        """Get the input type of a node."""
        try:
            input_def = node.getActiveInput(input_name)
            if input_def:
                return input_def.getType()
            
            # Fallback: try to get from node definition
            node_def = node.getNodeDef()
            if node_def:
                input_def = node_def.getInput(input_name)
                if input_def:
                    return input_def.getType()
            
            # Default fallback based on input name
            return self._get_input_type_from_name(input_name)
        except Exception:
            return self._get_input_type_from_name(input_name)
    
    def _direct_connect_nodes(self, from_node: mx.Node, from_output: str, 
                             to_node: mx.Node, to_input: str) -> bool:
        """Directly connect two nodes without type conversion."""
        try:
            # Validate that the source node has the specified output
            if from_output and from_output != 'out':
                # Check if the output exists on the source node
                output_def = from_node.getActiveOutput(from_output)
                if not output_def:
                    # Try to get from node definition
                    node_def = from_node.getNodeDef()
                    if node_def:
                        output_def = node_def.getOutput(from_output)
                
                if not output_def:
                    raise MaterialXError(f"Output '{from_output}' not found on node '{from_node.getName()}'", "missing_output")
            
            # Create input if it doesn't exist
            input_port = to_node.addInputFromNodeDef(to_input)
            if not input_port:
                raise MaterialXError(f"Failed to create input port '{to_input}' on node '{to_node.getName()}'", "input_creation_failed")
            
            # Remove any existing value
            input_port.removeAttribute('value')
            
            # Set the connection
            input_port.setAttribute('nodename', from_node.getName())
            if from_output and from_output != 'out':
                input_port.setOutputString(from_output)
            
            self.logger.debug(f"✓ Direct connection successful: {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input}")
            return True
            
        except MaterialXError:
            # Re-raise MaterialXError exceptions
            raise
        except Exception as e:
            error_msg = f"Direct connection failed: {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input} - {str(e)}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "direct_connection_exception", {"original_error": str(e)})
    
    def _connect_with_conversion(self, from_node: mx.Node, from_output: str, 
                                to_node: mx.Node, to_input: str, from_type: str, to_type: str) -> bool:
        """Connect nodes with automatic type conversion."""
        try:
            # Create conversion node
            conversion_node = self._create_conversion_node(from_type, to_type, from_node.getParent())
            if not conversion_node:
                raise MaterialXError(f"Failed to create conversion node for {from_type} -> {to_type}", "conversion_node_creation_failed")
            
            # Determine the correct input and output names for the conversion node
            conversion_input, conversion_output = self._get_conversion_node_ports(from_type, to_type)
            
            self.logger.debug(f"Using conversion node '{conversion_node.getName()}' with ports: {conversion_input} -> {conversion_output}")
            
            # Connect source to conversion node
            try:
                self._direct_connect_nodes(from_node, from_output, conversion_node, conversion_input)
            except MaterialXError as e:
                raise MaterialXError(f"Failed to connect source to conversion node: {str(e)}", "source_to_conversion_failed", {"original_error": str(e)})
            
            # Connect conversion node to target
            try:
                self._direct_connect_nodes(conversion_node, conversion_output, to_node, to_input)
            except MaterialXError as e:
                raise MaterialXError(f"Failed to connect conversion node to target: {str(e)}", "conversion_to_target_failed", {"original_error": str(e)})
            
            self.logger.debug(f"✓ Conversion connection successful: {from_node.getName()}.{from_output} -> [{conversion_node.getName()}] -> {to_node.getName()}.{to_input}")
            return True
            
        except MaterialXError:
            # Re-raise MaterialXError exceptions
            raise
        except Exception as e:
            error_msg = f"Conversion connection failed: {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input} - {str(e)}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "conversion_connection_exception", {"original_error": str(e)})
    
    def _get_conversion_node_ports(self, from_type: str, to_type: str) -> Tuple[str, str]:
        """Get the correct input and output port names for conversion nodes."""
        if from_type == 'color3' and to_type == 'float':
            # separate3 node: input 'in', output 'outr' (red component)
            return 'in', 'outr'
        elif from_type == 'color3' and to_type == 'vector2':
            # separate3 node: input 'in', outputs 'outr', 'outg', 'outb'
            # For now, use 'in' and 'outr' as a simple approach
            return 'in', 'outr'
        elif from_type == 'vector2' and to_type == 'vector3':
            # combine3 node: inputs 'in1', 'in2', 'in3', output 'out'
            # For now, use 'in1' and 'out' as a simple approach
            return 'in1', 'out'
        elif from_type == 'color3' and to_type == 'vector3':
            # combine3 node: inputs 'in1', 'in2', 'in3', output 'out'
            return 'in1', 'out'
        else:
            # Default fallback
            return 'in', 'out'
    
    def _create_conversion_node(self, from_type: str, to_type: str, parent: mx.Element) -> Optional[mx.Node]:
        """Create appropriate conversion node based on type transformation needed."""
        try:
            # Generate unique name for conversion node
            conversion_name = f"convert_{from_type}_to_{to_type}_{id(self)}"
            conversion_name = parent.createValidChildName(conversion_name)
            
            # Create conversion node based on type transformation using proper MaterialX nodes
            if from_type == 'vector2' and to_type == 'vector3':
                # vector2 -> vector3: use combine3 node to add Z=0
                conversion_node = parent.addChildOfCategory('combine3', conversion_name)
                conversion_node.setType('vector3')
                # The combine3 node will take the vector2 input and add a Z component
                self.logger.debug(f"Created vector2->vector3 conversion using combine3: {conversion_name}")
                
            elif from_type == 'color3' and to_type == 'vector2':
                # color3 -> vector2: use separate3 node to extract first two components
                conversion_node = parent.addChildOfCategory('separate3', conversion_name)
                conversion_node.setType('vector2')
                # The separate3 node will extract R and G components
                self.logger.debug(f"Created color3->vector2 conversion using separate3: {conversion_name}")
                
            elif from_type == 'color3' and to_type == 'vector3':
                # color3 -> vector3: direct conversion, use the color3 as vector3
                conversion_node = parent.addChildOfCategory('combine3', conversion_name)
                conversion_node.setType('vector3')
                # The combine3 node will combine the RGB components as XYZ
                self.logger.debug(f"Created color3->vector3 conversion using combine3: {conversion_name}")
                
            elif from_type == 'color3' and to_type == 'float':
                # color3 -> float: use separate3 node to extract red component
                conversion_node = parent.addChildOfCategory('separate3', conversion_name)
                conversion_node.setType('float')
                # Set the proper node definition for separate3
                conversion_node.setNodeDefString('ND_separate3_float')
                # The separate3 node extracts components from color3
                self.logger.debug(f"Created color3->float conversion using separate3: {conversion_name}")
                
            elif from_type == 'vector3' and to_type == 'color3':
                # vector3 -> color3: direct conversion, use the vector3 as color3
                conversion_node = parent.addChildOfCategory('combine3', conversion_name)
                conversion_node.setType('color3')
                # The combine3 node will combine the XYZ components as RGB
                self.logger.debug(f"Created vector3->color3 conversion using combine3: {conversion_name}")
                
            else:
                # For other conversions, try to use a generic approach
                # Use separate3 for extracting components or combine3 for combining
                if 'vector' in from_type and 'color' in to_type:
                    conversion_node = parent.addChildOfCategory('combine3', conversion_name)
                    conversion_node.setType(to_type)
                elif 'color' in from_type and 'vector' in to_type:
                    conversion_node = parent.addChildOfCategory('separate3', conversion_name)
                    conversion_node.setType(to_type)
                else:
                    # Fallback: try to create a simple pass-through
                    conversion_node = parent.addChildOfCategory('constant', conversion_name)
                    conversion_node.setType(to_type)
                
                self.logger.debug(f"Created generic conversion node {from_type}->{to_type}: {conversion_name}")
            
            return conversion_node
            
        except Exception as e:
            self.logger.error(f"Failed to create conversion node: {e}")
            return None
    
    def _get_input_type_from_name(self, input_name: str) -> str:
        """
        Get the expected type for an input based on its name.
        
        Args:
            input_name: The input name
            
        Returns:
            str: The expected input type
        """
        # Common input type mappings
        type_mapping = {
            'texcoord': 'vector2',
            'in': 'color3',
            'in1': 'color3',
            'in2': 'color3',
            'a': 'color3',
            'b': 'color3',
            'factor': 'float',
            'scale': 'float',
            'strength': 'float',
            'amount': 'float',
            'pivot': 'vector2',
            'translate': 'vector2',
            'rotate': 'float',
            'file': 'filename',
            'default': 'color3',
            'surfaceshader': 'surfaceshader',
            'normal': 'vector3',
            'tangent': 'vector3',
            
            # Standard surface specific mappings
            'base': 'float',
            'base_color': 'color3',
            'metalness': 'float',
            'specular': 'float',
            'specular_color': 'color3',
            'specular_roughness': 'float',
            'specular_ior': 'float',
            'transmission': 'float',
            'transmission_color': 'color3',
            'transmission_depth': 'float',
            'transmission_scatter': 'color3',
            'transmission_scatter_anisotropy': 'float',
            'transmission_dispersion': 'float',
            'transmission_extra_roughness': 'float',
            'opacity': 'float',
            'emission': 'float',
            'emission_color': 'color3',
            'subsurface': 'float',
            'subsurface_color': 'color3',
            'subsurface_radius': 'color3',
            'subsurface_scale': 'float',
            'subsurface_anisotropy': 'float',
            'sheen': 'float',
            'sheen_color': 'color3',
            'sheen_tint': 'float',
            'sheen_roughness': 'float',
            'coat': 'float',
            'coat_color': 'color3',
            'coat_roughness': 'float',
            'coat_ior': 'float',
            'coat_normal': 'vector3',
            'anisotropic': 'float',
            'anisotropic_rotation': 'float',
            'anisotropic_direction': 'vector3',
        }
        
        return type_mapping.get(input_name.lower(), 'color3')


class MaterialXConnectionManager:
    """
    Manages node connections and input/output handling.
    
    This class provides:
    - Connection validation
    - Type checking
    - Input/output mapping
    - Connection optimization
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.connections = []
        self.type_mapping = {
            'color3': ['color3', 'vector3'],
            'vector3': ['vector3', 'color3'],
            'vector2': ['vector2'],
            'float': ['float'],
            'filename': ['filename'],
            'string': ['string']
        }
    
    def validate_connection(self, from_type: str, to_type: str) -> bool:
        """
        Validate if a connection between types is valid.
        
        Args:
            from_type: The source type
            to_type: The target type
            
        Returns:
            bool: True if connection is valid
        """
        # Direct type match
        if from_type == to_type:
            return True
        
        # Check type compatibility
        if from_type in self.type_mapping:
            compatible_types = self.type_mapping[from_type]
            if to_type in compatible_types:
                return True
        
        # Special cases
        if from_type == 'color3' and to_type == 'vector3':
            return True
        if from_type == 'vector3' and to_type == 'color3':
            return True
        
        self.logger.warning(f"Type mismatch: {from_type} -> {to_type}")
        return False
    
    def get_input_type(self, input_name: str, node_type: str) -> str:
        """
        Get the expected type for an input based on its name and node type.
        
        Args:
            input_name: The input name
            node_type: The node type
            
        Returns:
            str: The expected input type
        """
        # Common input type mappings
        type_mapping = {
            'texcoord': 'vector2',
            'in': 'color3',
            'in1': 'color3',
            'in2': 'color3',
            'a': 'color3',
            'b': 'color3',
            'factor': 'float',
            'scale': 'float',
            'strength': 'float',
            'amount': 'float',
            'pivot': 'vector2',
            'translate': 'vector2',
            'rotate': 'float',
            'file': 'filename',
            'default': 'color3',
            'normal': 'vector3',
            'tangent': 'vector3',
            
            # Standard surface specific mappings
            'base': 'float',
            'base_color': 'color3',
            'metalness': 'float',
            'specular': 'float',
            'specular_color': 'color3',
            'specular_roughness': 'float',
            'specular_ior': 'float',
            'transmission': 'float',
            'transmission_color': 'color3',
            'transmission_depth': 'float',
            'transmission_scatter': 'color3',
            'transmission_scatter_anisotropy': 'float',
            'transmission_dispersion': 'float',
            'transmission_extra_roughness': 'float',
            'opacity': 'float',
            'emission': 'float',
            'emission_color': 'color3',
            'subsurface': 'float',
            'subsurface_color': 'color3',
            'subsurface_radius': 'color3',
            'subsurface_scale': 'float',
            'subsurface_anisotropy': 'float',
            'sheen': 'float',
            'sheen_color': 'color3',
            'sheen_tint': 'float',
            'sheen_roughness': 'float',
            'coat': 'float',
            'coat_color': 'color3',
            'coat_roughness': 'float',
            'coat_ior': 'float',
            'coat_normal': 'vector3',
            'anisotropic': 'float',
            'anisotropic_rotation': 'float',
            'anisotropic_direction': 'vector3',
        }
        
        return type_mapping.get(input_name.lower(), 'color3')
    
    def record_connection(self, from_node: str, from_output: str, 
                         to_node: str, to_input: str):
        """
        Record a connection for later analysis.
        
        Args:
            from_node: Source node name
            from_output: Source output name
            to_node: Target node name
            to_input: Target input name
        """
        connection = {
            'from_node': from_node,
            'from_output': from_output,
            'to_node': to_node,
            'to_input': to_input
        }
        self.connections.append(connection)
    
    def get_connection_count(self, node_name: str) -> int:
        """
        Get the number of connections for a node.
        
        Args:
            node_name: The node name
            
        Returns:
            int: The number of connections
        """
        count = 0
        for conn in self.connections:
            if conn['from_node'] == node_name or conn['to_node'] == node_name:
                count += 1
        return count


class MaterialXLibraryBuilder:
    """
    Builds MaterialX documents using the MaterialX library.
    
    This is the main builder class that replaces the manual XML generation
    with proper MaterialX library APIs and Phase 3 enhancements.
    """
    
    def __init__(self, material_name: str, logger, version: str = "1.39"):
        self.material_name = material_name
        self.version = version
        self.logger = logger
        
        # Initialize core components
        self.doc_manager = MaterialXDocumentManager(logger, version)
        self.node_builder = MaterialXNodeBuilder(self.doc_manager, logger)
        self.connection_manager = MaterialXConnectionManager(logger)
        
        # Create document
        self.document = self.doc_manager.create_document()
        
        # Track created elements
        self.material_node = None
        self.nodegraph = None
        self.surface_shader = None
        
        # Legacy compatibility
        self.nodes = {}  # For backward compatibility
        self.connections = []
        self.node_counter = 0
        
        # Phase 3 enhancements
        self.performance_monitor = self.doc_manager.performance_monitor
        self.advanced_validator = self.doc_manager.advanced_validator
        
        # Advanced file writing options
        self.write_options = {
            'skip_library_elements': True,
            'write_xinclude': False,
            'remove_layout': True,
            'format_output': True
        }
        
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """
        Add a node to the nodegraph (legacy compatibility method).
        
        Args:
            node_type: The node type
            name: The node name
            node_type_category: The node category
            **params: Node parameters
            
        Returns:
            str: The created node name
        """
        # Ensure nodegraph exists
        if not self.nodegraph:
            self.nodegraph = self.node_builder.add_nodegraph(self.material_name, self.document)
        
        # Create node
        node = self.node_builder.add_node(node_type, name, node_type_category, self.nodegraph)
        
        if node:
            node_name = node.getName()
            self.nodes[node_name] = node
            
            # Add parameters as inputs using type-safe method
            for param_name, param_value in params.items():
                if param_value is not None:
                    self.node_builder.create_mtlx_input(
                        node, param_name, param_value, 
                        node_type=node_type, category=node_type_category
                    )
            
            return node_name
        else:
            # Fallback: create a placeholder node
            placeholder_name = f"placeholder_{node_type}_{self.node_counter}"
            self.node_counter += 1
            self.logger.warning(f"Created placeholder node: {placeholder_name}")
            return placeholder_name
    
    def add_surface_shader_node(self, node_type: str, name: str, **params) -> str:
        """
        Add a surface shader node outside the nodegraph.
        
        Args:
            node_type: The node type
            name: The node name
            **params: Node parameters
            
        Returns:
            str: The created node name
        """
        # Create surface shader node at document level
        node = self.node_builder.add_node(node_type, name, 'surfaceshader', self.document)
        
        if node:
            node_name = node.getName()
            self.nodes[node_name] = node
            self.surface_shader = node
            
            # Add parameters as inputs using type-safe method
            for param_name, param_value in params.items():
                if param_value is not None:
                    self.node_builder.create_mtlx_input(
                        node, param_name, param_value, 
                        node_type=node_type, category='surfaceshader'
                    )
            
            return node_name
        else:
            return f"surface_{node_type}_{self.node_counter}"
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """
        Add a connection between nodes with robust error handling.
        
        Args:
            from_node: Source node name
            from_output: Source output name
            to_node: Target node name
            to_input: Target input name
            
        Raises:
            MaterialXError: If connection fails for any reason
        """
        # Validate input parameters
        if not from_node or not from_output or not to_node or not to_input:
            error_msg = f"Invalid connection parameters: from_node='{from_node}', from_output='{from_output}', to_node='{to_node}', to_input='{to_input}'"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "connection_validation")
        
        # Check if nodes exist
        from_node_elem = self.nodes.get(from_node)
        to_node_elem = self.nodes.get(to_node)
        
        if not from_node_elem:
            error_msg = f"Source node '{from_node}' not found. Available nodes: {list(self.nodes.keys())}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "missing_source_node")
        
        if not to_node_elem:
            error_msg = f"Target node '{to_node}' not found. Available nodes: {list(self.nodes.keys())}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "missing_target_node")
        
        # Attempt the connection
        try:
            success = self.node_builder.connect_nodes(from_node_elem, from_output, to_node_elem, to_input)
            
            if success:
                # Record successful connection
                self.connection_manager.record_connection(from_node, from_output, to_node, to_input)
                self.connections.append((from_node, from_output, to_node, to_input))
                self.logger.debug(f"✓ Connection successful: {from_node}.{from_output} -> {to_node}.{to_input}")
            else:
                # Connection failed but didn't raise an exception
                error_msg = f"Connection failed silently: {from_node}.{from_output} -> {to_node}.{to_input}"
                self.logger.error(error_msg)
                raise MaterialXError(error_msg, "connection_failed")
                
        except Exception as e:
            # Connection failed with an exception
            error_msg = f"Connection failed with exception: {from_node}.{from_output} -> {to_node}.{to_input} - {str(e)}"
            self.logger.error(error_msg)
            raise MaterialXError(error_msg, "connection_exception", {"original_error": str(e)})
    
    def add_surface_shader_input(self, surface_node_name: str, input_name: str, input_type: str, 
                                nodegraph_name: str = None, nodename: str = None, value: str = None):
        """
        Add an input to a surface shader node.
        
        Args:
            surface_node_name: The surface shader node name
            input_name: The input name
            input_type: The input type
            nodegraph_name: The connected nodegraph name
            nodename: The connected node name
            value: The input value
        """
        surface_node = self.nodes.get(surface_node_name)
        if not surface_node:
            self.logger.warning(f"Surface shader node '{surface_node_name}' not found")
            return
        
        if nodegraph_name:
            # Connect to nodegraph output
            if self.nodegraph:
                output = self.node_builder.add_output(self.nodegraph, input_name, input_type, nodename or input_name)
                # Connect surface shader input to nodegraph output using proper nodegraph syntax
                input_elem = surface_node.addInput(input_name, input_type)
                if input_elem:
                    input_elem.setAttribute('nodegraph', nodegraph_name)
                    input_elem.setAttribute('output', input_name)
                    self.logger.debug(f"Connected surface shader input {input_name} to nodegraph {nodegraph_name} output {input_name}")
        elif nodename:
            # Connect to specific node
            self.node_builder.create_mtlx_input(surface_node, input_name, nodename=nodename)
        elif value is not None:
            # Set constant value
            self.node_builder.create_mtlx_input(surface_node, input_name, value)
    
    def add_output(self, name: str, output_type: str, nodename: str):
        """
        Add an output node to the nodegraph.
        
        Args:
            name: The output name
            output_type: The output type
            nodename: The connected node name
        """
        if self.nodegraph:
            self.node_builder.add_output(self.nodegraph, name, output_type, nodename)
    
    def set_material_surface(self, surface_node_name: str):
        """
        Set the surface shader for the material.
        
        Args:
            surface_node_name: The surface shader node name
        """
        if not self.material_node:
            # Create material node
            self.material_node = self.node_builder.add_node('surfacematerial', self.material_name, 'material', self.document)
        
        if self.material_node and self.surface_shader:
            # Connect material to surface shader
            self.node_builder.create_mtlx_input(self.material_node, 'surfaceshader', nodename=surface_node_name)
    
    def _get_param_type(self, value) -> str:
        """
        Determine the MaterialX type for a value.
        
        Args:
            value: The value to type-check
            
        Returns:
            str: The MaterialX type
        """
        if isinstance(value, (int, float)):
            return "float"
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                return "vector2"
            elif len(value) == 3:
                return "color3"
            elif len(value) == 4:
                return "color4"
        return "string"
    
    def to_string(self) -> str:
        """
        Convert the document to a formatted XML string with advanced options.
        
        Returns:
            str: The formatted XML string
        """
        try:
            self.performance_monitor.start_operation("to_string")
            
            # Apply advanced write options
            if self.write_options['remove_layout']:
                mxf.MtlxFile.removeLayout(self.document)
            
            # Use custom predicate for library elements
            predicate = mxf.MtlxFile.skipLibraryElement if self.write_options['skip_library_elements'] else None
            
            # Use mtlxutils for writing with advanced options
            content = mxf.MtlxFile.writeDocumentToString(self.document, predicate)
            
            # Format output if requested
            if self.write_options['format_output']:
                try:
                    import xml.dom.minidom
                    dom = xml.dom.minidom.parseString(content)
                    content = dom.toprettyxml(indent="  ")
                except Exception as format_error:
                    self.logger.warning(f"Failed to format XML output: {str(format_error)}")
            
            self.performance_monitor.end_operation("to_string")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to convert document to string: {str(e)}")
            self.performance_monitor.end_operation("to_string")
            return ""
    
    def write_to_file(self, filepath: str) -> bool:
        """
        Write the document to a file with advanced options and validation.
        
        Args:
            filepath: The output file path
            
        Returns:
            bool: True if successful
        """
        try:
            self.performance_monitor.start_operation("write_to_file")
            
            # Validate document before writing
            validation_results = self.advanced_validator.validate_document_comprehensive(self.document)
            if not validation_results['valid']:
                self.logger.warning("Writing document with validation issues:")
                for error in validation_results['errors']:
                    self.logger.warning(f"  - {error}")
            
            # Apply advanced write options
            if self.write_options['remove_layout']:
                mxf.MtlxFile.removeLayout(self.document)
            
            # Use custom predicate for library elements
            predicate = mxf.MtlxFile.skipLibraryElement if self.write_options['skip_library_elements'] else None
            
            # Use mtlxutils for writing with advanced options
            mxf.MtlxFile.writeDocumentToFile(self.document, filepath, predicate)
            
            # Verify file was written successfully
            if not os.path.exists(filepath):
                raise RuntimeError(f"File was not created: {filepath}")
            
            file_size = os.path.getsize(filepath)
            self.logger.info(f"Successfully wrote MaterialX document to: {filepath} ({file_size} bytes)")
            
            self.performance_monitor.end_operation("write_to_file")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write document to file: {str(e)}")
            self.performance_monitor.end_operation("write_to_file")
            return False
    
    def validate(self) -> bool:
        """
        Validate the MaterialX document with comprehensive validation.
        
        Returns:
            bool: True if document is valid
        """
        return self.doc_manager.validate_document()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dict containing performance metrics
        """
        return self.doc_manager.get_performance_stats()
    
    def set_write_options(self, **options):
        """
        Set advanced file writing options.
        
        Args:
            **options: Writing options to set
        """
        self.write_options.update(options)
        self.logger.info(f"Updated write options: {self.write_options}")
    
    def optimize_document(self) -> bool:
        """
        Optimize the MaterialX document for better performance.
        
        Returns:
            bool: True if optimization was successful
        """
        try:
            self.performance_monitor.start_operation("optimize_document")
            
            self.logger.info("Optimizing MaterialX document...")
            
            # Remove unused nodes
            unused_nodes = self.advanced_validator._find_unused_nodes(self.document)
            if unused_nodes:
                self.logger.info(f"Removing {len(unused_nodes)} unused nodes")
                for node in unused_nodes:
                    try:
                        node.getParent().removeChild(node.getName())
                    except Exception as e:
                        self.logger.warning(f"Failed to remove unused node {node.getName()}: {str(e)}")
            
            # Clear caches to free memory
            self.doc_manager._clear_caches()
            
            # Validate after optimization
            validation_results = self.advanced_validator.validate_document_comprehensive(self.document)
            if not validation_results['valid']:
                self.logger.warning("Document has validation issues after optimization")
            
            self.logger.info("Document optimization completed")
            
            self.performance_monitor.end_operation("optimize_document")
            return True
            
        except Exception as e:
            self.logger.error(f"Document optimization failed: {str(e)}")
            self.performance_monitor.end_operation("optimize_document")
            return False
    

    
    def cleanup(self):
        """
        Clean up resources and free memory.
        """
        self.doc_manager.cleanup()
        self.logger.info("MaterialXLibraryBuilder cleanup completed") 