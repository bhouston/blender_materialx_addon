#!/usr/bin/env python3
"""
MaterialX Document Manager

This module provides document management functionality for MaterialX operations,
including document creation, modification, and optimization.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import MaterialX as mx
from ..utils.logging_utils import MaterialXLogger
from ..utils.exceptions import MaterialXLibraryError, ValidationError


class DocumentManager:
    """
    Manages MaterialX document operations including creation, modification, and optimization.
    
    This class provides a clean interface for MaterialX document operations,
    with proper error handling.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the document manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or MaterialXLogger("DocumentManager")
        self._documents: Dict[str, mx.Document] = {}
        self._document_metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_document(self, name: str, version: str = "1.39") -> mx.Document:
        """
        Create a new MaterialX document.
        
        Args:
            name: Name for the document
            version: MaterialX version to use
            
        Returns:
            New MaterialX document
            
        Raises:
            MaterialXLibraryError: If document creation fails
        """
        try:
            doc = mx.createDocument()
            doc.setVersionString(version)
            
            # Store document reference
            self._documents[name] = doc
            self._document_metadata[name] = {
                'version': version,
                'created_at': datetime.now().isoformat(),
                'node_count': 0,
                'material_count': 0
            }
            
            self.logger.debug(f"Created MaterialX document: {name} (version {version})")
            return doc
            
        except Exception as e:
            raise MaterialXLibraryError("document_creation", e)
    
    def get_document(self, name: str) -> Optional[mx.Document]:
        """
        Get a document by name.
        
        Args:
            name: Name of the document
            
        Returns:
            MaterialX document if found, None otherwise
        """
        return self._documents.get(name)
    
    def add_material(self, doc: mx.Document, material_name: str, 
                    material_type: str = "standard_surface") -> Any:
        """
        Add a material to the document.
        
        Args:
            doc: MaterialX document
            material_name: Name for the material
            material_type: Type of material to create
            
        Returns:
            Created MaterialX material
            
        Raises:
            MaterialXLibraryError: If material creation fails
        """
        try:
            material = doc.addMaterial(material_name)
            
            # Create shader reference
            shader_ref = material.addShaderRef("", material_type)
            
            # Update metadata
            for doc_name, doc_obj in self._documents.items():
                if doc_obj == doc:
                    self._document_metadata[doc_name]['material_count'] += 1
                    break
            
            self.logger.debug(f"Added material to document: {material_name} ({material_type})")
            return material
            
        except Exception as e:
            raise MaterialXLibraryError("material_creation", e)
    
    def add_node(self, doc: mx.Document, node_name: str, node_type: str, 
                category: str = "color3") -> Any:
        """
        Add a node to the document.
        
        Args:
            doc: MaterialX document
            node_name: Name for the node
            node_type: Type of node to create
            category: Category of the node
            
        Returns:
            Created MaterialX node
            
        Raises:
            MaterialXLibraryError: If node creation fails
        """
        try:
            node = doc.addNode(node_name, node_type, category)
            
            # Update metadata
            for doc_name, doc_obj in self._documents.items():
                if doc_obj == doc:
                    self._document_metadata[doc_name]['node_count'] += 1
                    break
            
            self.logger.debug(f"Added node to document: {node_name} ({node_type})")
            return node
            
        except Exception as e:
            raise MaterialXLibraryError("node_creation", e)
    
    def add_input(self, node: Any, input_name: str, input_type: str = "float",
                  value: Optional[Union[str, float, List[float]]] = None) -> Any:
        """
        Add an input to a node.
        
        Args:
            node: MaterialX node
            input_name: Name for the input
            input_type: Type of the input
            value: Optional default value
            
        Returns:
            Created MaterialX input
            
        Raises:
            MaterialXLibraryError: If input creation fails
        """
        try:
            input_port = node.addInput(input_name, input_type)
            
            if value is not None:
                if isinstance(value, (list, tuple)):
                    input_port.setValueString(" ".join(str(v) for v in value))
                else:
                    input_port.setValueString(str(value))
            
            self.logger.debug(f"Added input to node {node.getName()}: {input_name} ({input_type})")
            return input_port
            
        except Exception as e:
            raise MaterialXLibraryError("input_creation", e)
    
    def add_output(self, node: Any, output_name: str, output_type: str = "color3") -> Any:
        """
        Add an output to a node.
        
        Args:
            node: MaterialX node
            output_name: Name for the output
            output_type: Type of the output
            
        Returns:
            Created MaterialX output
            
        Raises:
            MaterialXLibraryError: If output creation fails
        """
        try:
            output_port = node.addOutput(output_name, output_type)
            
            self.logger.debug(f"Added output to node {node.getName()}: {output_name} ({output_type})")
            return output_port
            
        except Exception as e:
            raise MaterialXLibraryError("output_creation", e)
    
    def connect_nodes(self, from_node: Any, from_output: str, 
                     to_node: Any, to_input: str) -> bool:
        """
        Connect two nodes.
        
        Args:
            from_node: Source node
            from_output: Source output name
            to_node: Target node
            to_input: Target input name
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            MaterialXLibraryError: If connection fails
        """
        try:
            # Get the output and input ports
            output_port = from_node.getOutput(from_output)
            input_port = to_node.getInput(to_input)
            
            if not output_port:
                self.logger.warning(f"Output '{from_output}' not found on node '{from_node.getName()}'")
                return False
            
            if not input_port:
                self.logger.warning(f"Input '{to_input}' not found on node '{to_node.getName()}'")
                return False
            
            # Create the connection
            input_port.setConnectedOutput(output_port)
            
            self.logger.debug(f"Connected {from_node.getName()}.{from_output} -> {to_node.getName()}.{to_input}")
            return True
            
        except Exception as e:
            raise MaterialXLibraryError("node_connection", e)
    
    def optimize_document(self, doc: mx.Document) -> bool:
        """
        Optimize a MaterialX document.
        
        Args:
            doc: MaterialX document to optimize
            
        Returns:
            True if optimization successful, False otherwise
            
        Raises:
            MaterialXLibraryError: If optimization fails
        """
        try:
            # Remove unused nodes
            unused_nodes = []
            for node in doc.getNodes():
                if not node.getConnectedInputs() and not node.getConnectedOutputs():
                    if node.getType() != "material":
                        unused_nodes.append(node)
            
            for node in unused_nodes:
                doc.removeNode(node.getName())
                self.logger.debug(f"Removed unused node: {node.getName()}")
            
            # Update metadata
            for doc_name, doc_obj in self._documents.items():
                if doc_obj == doc:
                    self._document_metadata[doc_name]['node_count'] = len(doc.getNodes())
                    break
            
            self.logger.info(f"Document optimization completed. Removed {len(unused_nodes)} unused nodes.")
            return True
            
        except Exception as e:
            raise MaterialXLibraryError("document_optimization", e)
    
    def validate_document(self, doc: mx.Document) -> Dict[str, Any]:
        """
        Validate a MaterialX document.
        
        Args:
            doc: MaterialX document to validate
            
        Returns:
            Validation results dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Basic validation
            errors = []
            warnings = []
            
            # Check for materials
            materials = doc.getMaterials()
            if not materials:
                warnings.append("No materials found in document")
            
            # Check for orphaned nodes
            for node in doc.getNodes():
                if node.getType() != "material":
                    inputs = node.getConnectedInputs()
                    outputs = node.getConnectedOutputs()
                    
                    if not inputs and not outputs:
                        warnings.append(f"Orphaned node: {node.getName()}")
            
            # Check for cycles (basic check)
            # This is a simplified cycle detection
            visited = set()
            rec_stack = set()
            
            def has_cycle(node_name):
                if node_name in rec_stack:
                    return True
                if node_name in visited:
                    return False
                
                visited.add(node_name)
                rec_stack.add(node_name)
                
                node = doc.getNode(node_name)
                if node:
                    for input_port in node.getInputs():
                        if input_port.getConnectedOutput():
                            connected_node = input_port.getConnectedOutput().getParent()
                            if has_cycle(connected_node.getName()):
                                return True
                
                rec_stack.remove(node_name)
                return False
            
            for node in doc.getNodes():
                if has_cycle(node.getName()):
                    errors.append(f"Cycle detected involving node: {node.getName()}")
                    break
            
            result = {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'material_count': len(materials),
                'node_count': len(doc.getNodes())
            }
            
            if result['valid']:
                self.logger.info("Document validation passed")
            else:
                self.logger.error(f"Document validation failed: {len(errors)} errors")
            
            return result
            
        except Exception as e:
            raise ValidationError([f"Validation error: {str(e)}"])
    
    def get_document_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a document.
        
        Args:
            name: Name of the document
            
        Returns:
            Document information dictionary or None if not found
        """
        if name not in self._documents:
            return None
        
        doc = self._documents[name]
        metadata = self._document_metadata[name]
        
        return {
            'name': name,
            'version': metadata['version'],
            'created_at': metadata['created_at'],
            'material_count': len(doc.getMaterials()),
            'node_count': len(doc.getNodes()),
            'metadata': metadata
        }
    
    def clear_documents(self):
        """Clear all stored documents."""
        self._documents.clear()
        self._document_metadata.clear()
        self.logger.debug("Cleared all documents")
    
    def list_documents(self) -> List[str]:
        """
        Get a list of all document names.
        
        Returns:
            List of document names
        """
        return list(self._documents.keys())
