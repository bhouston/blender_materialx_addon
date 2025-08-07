#!/usr/bin/env python3
"""
MaterialX Advanced Validator

This module provides advanced validation functionality for MaterialX documents.
"""

import MaterialX as mx
import logging
from typing import Dict, List, Optional, Any


class MaterialXAdvancedValidator:
    """
    Advanced MaterialX document validator.
    
    This class provides comprehensive validation including:
    - Document structure validation
    - Node and connection validation
    - Performance analysis
    - Custom validation rules
    """
    
    def __init__(self, logger):
        self.logger = logger
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
            'errors': [],
            'warnings': [],
            'info': [],
            'statistics': {},
            'details': {}
        }
        
        try:
            # Basic structure validation
            if not self._validate_basic_structure(document, results):
                results['valid'] = False
            
            # Node validation
            self._validate_nodes(document, results)
            
            # Connection validation
            self._validate_connections(document, results)
            
            # Performance validation
            self._validate_performance(document, results)
            
            # Custom validators
            self._apply_custom_validators(document, results)
            
            # Update overall validity
            if results['errors']:
                results['valid'] = False
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive validation: {str(e)}")
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
        
        return results
    
    def _validate_basic_structure(self, document: mx.Document, results: Dict[str, Any]) -> bool:
        """Validate basic document structure."""
        try:
            # Check if document is valid
            valid, message = document.validate()
            if not valid:
                results['errors'].append(f"Document validation failed: {message}")
                return False
            
            # Check for required elements
            materials = document.getMaterials()
            if not materials:
                results['warnings'].append("No materials found in document")
            
            nodegraphs = document.getNodeGraphs()
            if not nodegraphs:
                results['info'].append("No nodegraphs found in document")
            
            # Record statistics
            results['statistics']['materials'] = len(materials)
            results['statistics']['nodegraphs'] = len(nodegraphs)
            results['statistics']['nodes'] = len(document.getNodes())
            results['statistics']['nodedefs'] = len(document.getNodeDefs())
            
            return True
            
        except Exception as e:
            results['errors'].append(f"Basic structure validation error: {str(e)}")
            return False
    
    def _validate_nodes(self, document: mx.Document, results: Dict[str, Any]):
        """Validate nodes in the document."""
        try:
            nodes = document.getNodes()
            for node in nodes:
                # Check for nodes without definitions
                if not node.getNodeDef():
                    results['warnings'].append(f"Node '{node.getName()}' has no node definition")
                
                # Check for disconnected inputs
                for input_elem in node.getInputs():
                    if not input_elem.getNodeName() and not input_elem.getValueString():
                        results['warnings'].append(f"Input '{input_elem.getName()}' in node '{node.getName()}' is not connected or has no value")
            
            results['statistics']['validated_nodes'] = len(nodes)
            
        except Exception as e:
            results['errors'].append(f"Node validation error: {str(e)}")
    
    def _validate_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate connections in the document."""
        try:
            nodes = document.getNodes()
            for node in nodes:
                for input_elem in node.getInputs():
                    if input_elem.getNodeName():
                        # Check if the connected node exists
                        connected_node = document.getNode(input_elem.getNodeName())
                        if not connected_node:
                            results['errors'].append(f"Node '{node.getName()}' references non-existent node '{input_elem.getNodeName()}'")
            
            results['statistics']['validated_connections'] = len([n for n in nodes for i in n.getInputs() if i.getNodeName()])
            
        except Exception as e:
            results['errors'].append(f"Connection validation error: {str(e)}")
    
    def _validate_performance(self, document: mx.Document, results: Dict[str, Any]):
        """Validate performance aspects of the document."""
        try:
            nodes = document.getNodes()
            
            # Check for deeply nested nodegraphs
            for nodegraph in document.getNodeGraphs():
                depth = self._calculate_nesting_depth(nodegraph)
                if depth > 10:
                    results['warnings'].append(f"NodeGraph '{nodegraph.getName()}' has deep nesting (depth: {depth})")
            
            # Check for unused nodes
            unused_nodes = self._find_unused_nodes(document)
            if unused_nodes:
                results['warnings'].append(f"Found {len(unused_nodes)} unused nodes")
                results['details']['unused_nodes'] = [n.getName() for n in unused_nodes]
            
            results['statistics']['nesting_depth'] = max([self._calculate_nesting_depth(n) for n in document.getNodeGraphs()], default=0)
            results['statistics']['unused_nodes'] = len(unused_nodes)
            
        except Exception as e:
            results['errors'].append(f"Performance validation error: {str(e)}")
    
    def _calculate_nesting_depth(self, element: mx.Element, current_depth: int = 0) -> int:
        """Calculate the nesting depth of an element."""
        max_depth = current_depth
        
        for child in element.getChildren():
            if child.isA(mx.NodeGraph):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _find_unused_nodes(self, document: mx.Document) -> List[mx.Node]:
        """Find nodes that are not connected to any output."""
        all_nodes = set(document.getNodes())
        connected_nodes = set()
        
        # Find all nodes connected to outputs
        for nodegraph in document.getNodeGraphs():
            for output in nodegraph.getOutputs():
                if output.getNodeName():
                    self._collect_connected_nodes(document.getNode(output.getNodeName()), connected_nodes, document)
        
        # Also check material nodes
        for material in document.getMaterials():
            for shader in material.getShaders():
                if shader.getNodeName():
                    self._collect_connected_nodes(document.getNode(shader.getNodeName()), connected_nodes, document)
        
        return list(all_nodes - connected_nodes)
    
    def _collect_connected_nodes(self, element: mx.Element, connected_nodes: set, document: mx.Document):
        """Recursively collect all connected nodes."""
        if not element or element in connected_nodes:
            return
        
        connected_nodes.add(element)
        
        for input_elem in element.getInputs():
            if input_elem.getNodeName():
                connected_node = document.getNode(input_elem.getNodeName())
                if connected_node:
                    self._collect_connected_nodes(connected_node, connected_nodes, document)
    
    def _apply_custom_validators(self, document: mx.Document, results: Dict[str, Any]):
        """Apply custom validation rules."""
        for name, validator_func in self.custom_validators.items():
            try:
                validator_result = validator_func(document)
                if not validator_result.get('valid', True):
                    results['errors'].extend(validator_result.get('errors', []))
                    results['warnings'].extend(validator_result.get('warnings', []))
            except Exception as e:
                results['errors'].append(f"Custom validator '{name}' failed: {str(e)}")
    
    def add_custom_validator(self, name: str, validator_func):
        """Add a custom validation function."""
        self.custom_validators[name] = validator_func
    
    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """Get a summary of validation results."""
        summary = f"Validation {'PASSED' if results['valid'] else 'FAILED'}\n"
        summary += f"Errors: {len(results['errors'])}\n"
        summary += f"Warnings: {len(results['warnings'])}\n"
        summary += f"Info: {len(results['info'])}\n"
        
        if results['errors']:
            summary += "\nErrors:\n"
            for error in results['errors'][:5]:  # Show first 5 errors
                summary += f"  - {error}\n"
        
        if results['warnings']:
            summary += "\nWarnings:\n"
            for warning in results['warnings'][:5]:  # Show first 5 warnings
                summary += f"  - {warning}\n"
        
        return summary
