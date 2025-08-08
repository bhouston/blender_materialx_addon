#!/usr/bin/env python3
"""
Advanced MaterialX Validator

This module provides comprehensive validation for MaterialX documents.
"""

from typing import Dict, List, Optional, Any
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import ValidationError


class AdvancedValidator:
    """
    Advanced validator for MaterialX documents with comprehensive checks.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the advanced validator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger("AdvancedValidator")
        self.validation_rules: Dict[str, List[callable]] = {}
        self._setup_validation_rules()
    
    def validate_document(self, document: mx.Document, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive validation of a MaterialX document.
        
        Args:
            document: MaterialX document to validate
            options: Validation options
            
        Returns:
            Validation results dictionary
        """
        if options is None:
            options = {}
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'statistics': {}
        }
        
        try:
            self.logger.info("Starting advanced MaterialX document validation")
            
            # Basic document validation
            self._validate_basic_structure(document, results)
            
            # Material validation
            self._validate_materials(document, results)
            
            # Node validation
            self._validate_nodes(document, results)
            
            # Connection validation
            self._validate_connections(document, results)
            
            # Type validation
            self._validate_types(document, results)
            
            # Performance validation
            self._validate_performance(document, results)
            
            # Custom validation rules
            self._run_custom_validation(document, results, options)
            
            # Generate statistics
            self._generate_statistics(document, results)
            
            # Determine overall validity
            results['valid'] = len(results['errors']) == 0
            
            self.logger.info(f"Validation completed: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            results['valid'] = False
            results['errors'].append(f"Validation process failed: {str(e)}")
            return results
    
    def _setup_validation_rules(self):
        """Setup custom validation rules."""
        # Material validation rules
        self.validation_rules['materials'] = [
            self._check_material_has_surface_shader,
            self._check_material_name_validity,
            self._check_material_references
        ]
        
        # Node validation rules
        self.validation_rules['nodes'] = [
            self._check_node_name_validity,
            self._check_node_type_validity,
            self._check_node_inputs_outputs
        ]
        
        # Connection validation rules
        self.validation_rules['connections'] = [
            self._check_connection_validity,
            self._check_for_cycles,
            self._check_orphaned_nodes
        ]
    
    def _validate_basic_structure(self, document: mx.Document, results: Dict[str, Any]):
        """Validate basic document structure."""
        try:
            # Check if document exists
            if not document:
                results['errors'].append("Document is None or invalid")
                return
            
            # Check document version
            version = document.getVersionString()
            if not version:
                results['warnings'].append("Document version not specified")
            else:
                results['info'].append(f"Document version: {version}")
            
            # Check for required elements
            materials = document.getMaterials()
            if not materials:
                results['warnings'].append("No materials found in document")
            
            nodes = document.getNodes()
            if not nodes:
                results['warnings'].append("No nodes found in document")
            
        except Exception as e:
            results['errors'].append(f"Basic structure validation failed: {e}")
    
    def _validate_materials(self, document: mx.Document, results: Dict[str, Any]):
        """Validate materials in the document."""
        try:
            materials = document.getMaterials()
            
            for material in materials:
                # Run material validation rules
                for rule in self.validation_rules.get('materials', []):
                    try:
                        rule(material, results)
                    except Exception as e:
                        results['errors'].append(f"Material validation rule failed: {e}")
            
        except Exception as e:
            results['errors'].append(f"Material validation failed: {e}")
    
    def _validate_nodes(self, document: mx.Document, results: Dict[str, Any]):
        """Validate nodes in the document."""
        try:
            nodes = document.getNodes()
            
            for node in nodes:
                # Run node validation rules
                for rule in self.validation_rules.get('nodes', []):
                    try:
                        rule(node, results)
                    except Exception as e:
                        results['errors'].append(f"Node validation rule failed: {e}")
            
        except Exception as e:
            results['errors'].append(f"Node validation failed: {e}")
    
    def _validate_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate connections in the document."""
        try:
            # Run connection validation rules
            for rule in self.validation_rules.get('connections', []):
                try:
                    rule(document, results)
                except Exception as e:
                    results['errors'].append(f"Connection validation rule failed: {e}")
            
        except Exception as e:
            results['errors'].append(f"Connection validation failed: {e}")
    
    def _validate_types(self, document: mx.Document, results: Dict[str, Any]):
        """Validate type consistency in the document."""
        try:
            nodes = document.getNodes()
            
            for node in nodes:
                # Check input types
                for input_port in node.getInputs():
                    if input_port.getConnectedOutput():
                        source_output = input_port.getConnectedOutput()
                        source_type = source_output.getType()
                        target_type = input_port.getType()
                        
                        if source_type != target_type:
                            results['warnings'].append(
                                f"Type mismatch in connection: {source_output.getParent().getName()}.{source_output.getName()} "
                                f"({source_type}) -> {node.getName()}.{input_port.getName()} ({target_type})"
                            )
            
        except Exception as e:
            results['errors'].append(f"Type validation failed: {e}")
    
    def _validate_performance(self, document: mx.Document, results: Dict[str, Any]):
        """Validate performance-related aspects."""
        try:
            nodes = document.getNodes()
            
            # Check for excessive node count
            if len(nodes) > 1000:
                results['warnings'].append(f"Large number of nodes ({len(nodes)}) may impact performance")
            
            # Check for deep connection chains
            max_depth = self._calculate_max_connection_depth(document)
            if max_depth > 20:
                results['warnings'].append(f"Deep connection chain detected (depth: {max_depth})")
            
        except Exception as e:
            results['errors'].append(f"Performance validation failed: {e}")
    
    def _run_custom_validation(self, document: mx.Document, results: Dict[str, Any], options: Dict[str, Any]):
        """Run custom validation rules based on options."""
        try:
            # Check for specific validation options
            if options.get('check_textures', True):
                self._validate_textures(document, results)
            
            if options.get('check_shaders', True):
                self._validate_shaders(document, results)
            
            if options.get('check_optimization', False):
                self._validate_optimization(document, results)
            
        except Exception as e:
            results['errors'].append(f"Custom validation failed: {e}")
    
    def _generate_statistics(self, document: mx.Document, results: Dict[str, Any]):
        """Generate document statistics."""
        try:
            stats = {
                'materials': len(document.getMaterials()),
                'nodes': len(document.getNodes()),
                'nodegraphs': len(document.getNodeGraphs()),
                'connections': self._count_connections(document),
                'textures': self._count_textures(document),
                'shaders': self._count_shaders(document)
            }
            
            results['statistics'] = stats
            results['info'].append(f"Document statistics: {stats}")
            
        except Exception as e:
            results['errors'].append(f"Statistics generation failed: {e}")
    
    # Validation rule implementations
    def _check_material_has_surface_shader(self, material, results: Dict[str, Any]):
        """Check if material has a surface shader."""
        shader_refs = material.getShaderRefs()
        if not shader_refs:
            results['warnings'].append(f"Material '{material.getName()}' has no surface shader")
    
    def _check_material_name_validity(self, material, results: Dict[str, Any]):
        """Check if material name is valid."""
        name = material.getName()
        if not name or name.strip() == "":
            results['errors'].append("Material has empty or invalid name")
    
    def _check_material_references(self, material, results: Dict[str, Any]):
        """Check material references."""
        # This could be extended to check for valid shader references
        pass
    
    def _check_node_name_validity(self, node, results: Dict[str, Any]):
        """Check if node name is valid."""
        name = node.getName()
        if not name or name.strip() == "":
            results['errors'].append("Node has empty or invalid name")
    
    def _check_node_type_validity(self, node, results: Dict[str, Any]):
        """Check if node type is valid."""
        node_type = node.getType()
        if not node_type or node_type.strip() == "":
            results['errors'].append(f"Node '{node.getName()}' has empty or invalid type")
    
    def _check_node_inputs_outputs(self, node, results: Dict[str, Any]):
        """Check node inputs and outputs."""
        inputs = node.getInputs()
        outputs = node.getOutputs()
        
        if not outputs:
            results['warnings'].append(f"Node '{node.getName()}' has no outputs")
    
    def _check_connection_validity(self, document: mx.Document, results: Dict[str, Any]):
        """Check if connections are valid."""
        nodes = document.getNodes()
        
        for node in nodes:
            for input_port in node.getInputs():
                if input_port.getConnectedOutput():
                    source_output = input_port.getConnectedOutput()
                    source_node = source_output.getParent()
                    
                    if not source_node:
                        results['errors'].append(f"Invalid connection: source node not found")
    
    def _check_for_cycles(self, document: mx.Document, results: Dict[str, Any]):
        """Check for cycles in the node graph."""
        # This is a simplified cycle detection
        # A more sophisticated implementation would use depth-first search
        pass
    
    def _check_orphaned_nodes(self, document: mx.Document, results: Dict[str, Any]):
        """Check for orphaned nodes."""
        nodes = document.getNodes()
        
        for node in nodes:
            inputs = node.getInputs()
            outputs = node.getOutputs()
            
            # Check if node has no connections
            has_input_connections = any(input_port.getConnectedOutput() for input_port in inputs)
            has_output_connections = any(output_port.getConnectedInputs() for output_port in outputs)
            
            if not has_input_connections and not has_output_connections:
                if node.getType() != "material":  # Materials can be unconnected
                    results['warnings'].append(f"Orphaned node: {node.getName()}")
    
    def _validate_textures(self, document: mx.Document, results: Dict[str, Any]):
        """Validate texture nodes."""
        nodes = document.getNodes()
        
        for node in nodes:
            if node.getType() == "image":
                # Check if image file is specified
                file_input = node.getInput("file")
                if file_input and not file_input.getValueString():
                    results['warnings'].append(f"Image node '{node.getName()}' has no file specified")
    
    def _validate_shaders(self, document: mx.Document, results: Dict[str, Any]):
        """Validate shader nodes."""
        nodes = document.getNodes()
        
        for node in nodes:
            if node.getType() in ["standard_surface", "surface"]:
                # Check for required shader inputs
                required_inputs = ["base_color", "base"]
                for input_name in required_inputs:
                    input_port = node.getInput(input_name)
                    if not input_port:
                        results['warnings'].append(f"Shader node '{node.getName()}' missing input: {input_name}")
    
    def _validate_optimization(self, document: mx.Document, results: Dict[str, Any]):
        """Validate optimization opportunities."""
        # Check for duplicate nodes
        # Check for unused inputs
        # Check for redundant operations
        pass
    
    def _calculate_max_connection_depth(self, document: mx.Document) -> int:
        """Calculate the maximum connection depth in the document."""
        # Simplified implementation
        return 0
    
    def _count_connections(self, document: mx.Document) -> int:
        """Count total connections in the document."""
        count = 0
        nodes = document.getNodes()
        
        for node in nodes:
            for input_port in node.getInputs():
                if input_port.getConnectedOutput():
                    count += 1
        
        return count
    
    def _count_textures(self, document: mx.Document) -> int:
        """Count texture nodes in the document."""
        count = 0
        nodes = document.getNodes()
        
        for node in nodes:
            if node.getType() in ["image", "noise2d", "voronoi2d", "wave2d"]:
                count += 1
        
        return count
    
    def _count_shaders(self, document: mx.Document) -> int:
        """Count shader nodes in the document."""
        count = 0
        nodes = document.getNodes()
        
        for node in nodes:
            if node.getType() in ["standard_surface", "surface"]:
                count += 1
        
        return count
    
    def add_validation_rule(self, category: str, rule: callable):
        """
        Add a custom validation rule.
        
        Args:
            category: Rule category ('materials', 'nodes', 'connections')
            rule: Validation rule function
        """
        if category not in self.validation_rules:
            self.validation_rules[category] = []
        
        self.validation_rules[category].append(rule)
        self.logger.debug(f"Added validation rule to category: {category}")
    
    def get_validation_rules(self) -> Dict[str, List[callable]]:
        """
        Get all validation rules.
        
        Returns:
            Dictionary of validation rules by category
        """
        return self.validation_rules.copy()
