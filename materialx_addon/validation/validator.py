#!/usr/bin/env python3
"""
MaterialX Validator

This module provides validation functionality for MaterialX documents.
"""

import MaterialX as mx
import logging
from typing import Dict, List, Optional, Any


class MaterialXValidator:
    """
    Comprehensive MaterialX document validator adapted for Blender addon use.
    
    This class provides validation functionality similar to the MaterialX validation script,
    but designed to work within the Blender addon context and integrate with the existing
    validation infrastructure.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the MaterialX validator.
        
        Args:
            logger: Logger instance for output (optional)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.stdlib = None
        
    def load_standard_libraries(self) -> bool:
        """
        Load standard MaterialX libraries for validation.
        
        Returns:
            bool: True if libraries loaded successfully
        """
        try:
            self.stdlib = mx.createDocument()
            mx.loadLibraries(mx.getDefaultDataLibraryFolders(), mx.getDefaultDataSearchPath(), self.stdlib)
            self.logger.info("Standard MaterialX libraries loaded successfully")
            return True
        except Exception as err:
            self.logger.error(f"Failed to load standard libraries: {err}")
            return False
    
    def validate_document(self, document: mx.Document, resolve_inheritance: bool = True, 
                         verbose: bool = True, include_stdlib: bool = True) -> Dict[str, Any]:
        """
        Validate a MaterialX document comprehensively.
        
        Args:
            document: The MaterialX document to validate
            resolve_inheritance: Whether to resolve inheritance and string substitutions
            verbose: Whether to include detailed analysis
            include_stdlib: Whether to include standard library validation
            
        Returns:
            Dict containing validation results
        """
        results = {
            'valid': False,
            'version': mx.getVersionString(),
            'errors': [],
            'warnings': [],
            'info': [],
            'statistics': {},
            'details': {}
        }
        
        try:
            # Set up document with standard libraries if requested
            if include_stdlib and self.stdlib:
                document.setDataLibrary(self.stdlib)
            
            # Basic validation
            valid, message = document.validate()
            results['valid'] = valid
            
            if valid:
                results['info'].append(f"Document is valid MaterialX v{results['version']}")
            else:
                results['errors'].append(f"Document validation failed: {message}")
            
            # Generate detailed analysis if verbose
            if verbose:
                self._generate_detailed_analysis(document, results, resolve_inheritance)
            
            # Additional validation checks
            self._validate_document_structure(document, results)
            self._validate_node_connections(document, results)
            self._validate_performance_issues(document, results)
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            results['errors'].append(f"Validation error: {str(e)}")
            results['valid'] = False
        
        return results
    
    def validate_file(self, filepath: str, resolve_inheritance: bool = True, 
                     verbose: bool = True, include_stdlib: bool = True) -> Dict[str, Any]:
        """
        Validate a MaterialX file.
        
        Args:
            filepath: Path to the MaterialX file
            resolve_inheritance: Whether to resolve inheritance and string substitutions
            verbose: Whether to include detailed analysis
            include_stdlib: Whether to include standard library validation
            
        Returns:
            Dict containing validation results
        """
        try:
            # Load the document
            document = mx.createDocument()
            mx.readFromXmlFile(document, filepath)
            
            # Validate the loaded document
            return self.validate_document(document, resolve_inheritance, verbose, include_stdlib)
            
        except Exception as e:
            self.logger.error(f"Failed to load file {filepath}: {e}")
            return {
                'valid': False,
                'errors': [f"Failed to load file: {str(e)}"],
                'warnings': [],
                'info': [],
                'statistics': {},
                'details': {}
            }
    
    def _generate_detailed_analysis(self, document: mx.Document, results: Dict[str, Any], resolve: bool):
        """Generate detailed analysis of the document."""
        try:
            # Analyze node definitions
            nodedefs = document.getNodeDefs()
            results['details']['nodedefs'] = self._analyze_elements(nodedefs, resolve, "NodeDef")
            
            # Analyze implementations
            implementations = document.getImplementations()
            results['details']['implementations'] = self._analyze_elements(implementations, resolve, "Implementation")
            
            # Analyze nodegraphs
            nodegraphs = document.getNodeGraphs()
            results['details']['nodegraphs'] = self._analyze_elements(nodegraphs, resolve, "NodeGraph")
            
            # Analyze materials
            materials = document.getMaterials()
            results['details']['materials'] = self._analyze_elements(materials, resolve, "Material")
            
            # Analyze other elements
            results['details']['geominfo'] = [self._analyze_geominfo(gi) for gi in document.getGeomInfos()]
            results['details']['variantsets'] = [self._analyze_variantset(vs) for vs in document.getVariantSets()]
            results['details']['propertysets'] = [self._analyze_propertyset(ps) for ps in document.getPropertySets()]
            results['details']['lookgroups'] = [self._analyze_lookgroup(lg) for lg in document.getLookGroups()]
            results['details']['looks'] = [self._analyze_look(look) for look in document.getLooks()]
            results['details']['backdrops'] = [self._analyze_backdrop(bd) for bd in document.getBackdrops()]
            
        except Exception as e:
            self.logger.error(f"Error during detailed analysis: {e}")
            results['errors'].append(f"Analysis error: {str(e)}")
    
    def _analyze_elements(self, elements: List, resolve: bool, element_type: str) -> List[Dict]:
        """Analyze a list of elements."""
        analyzed = []
        for elem in elements:
            try:
                if element_type == "NodeDef":
                    analyzed.append(self._analyze_nodedef(elem, resolve))
                elif element_type == "Implementation":
                    analyzed.append(self._analyze_implementation(elem))
                elif element_type == "NodeGraph":
                    analyzed.append(self._analyze_nodegraph(elem, resolve))
                elif element_type == "Material":
                    analyzed.append(self._analyze_material_node(elem, resolve))
                else:
                    analyzed.append({
                        'name': elem.getName(),
                        'type': element_type,
                        'category': elem.getCategory()
                    })
            except Exception as e:
                self.logger.warning(f"Error analyzing {element_type} {elem.getName()}: {e}")
                analyzed.append({
                    'name': elem.getName(),
                    'type': element_type,
                    'error': str(e)
                })
        return analyzed
    
    def _analyze_nodedef(self, nodedef: mx.NodeDef, resolve: bool) -> Dict:
        """Analyze a node definition."""
        return {
            'name': nodedef.getName(),
            'type': nodedef.getType(),
            'node': nodedef.getNodeString(),
            'category': nodedef.getNodeGroup(),
            'version': nodedef.getVersionString(),
            'inputs': [{'name': inp.getName(), 'type': inp.getType()} for inp in nodedef.getInputs()],
            'outputs': [{'name': out.getName(), 'type': out.getType()} for out in nodedef.getOutputs()],
            'inheritance': self._get_converted_value(nodedef) if resolve else nodedef.getInheritString()
        }
    
    def _analyze_implementation(self, impl: mx.Implementation) -> Dict:
        """Analyze an implementation."""
        return {
            'name': impl.getName(),
            'node': impl.getNodeString(),
            'file': impl.getFile(),
            'language': impl.getLanguage()
        }
    
    def _analyze_nodegraph(self, nodegraph: mx.NodeGraph, resolve: bool) -> Dict:
        """Analyze a nodegraph."""
        return {
            'name': nodegraph.getName(),
            'type': nodegraph.getType(),
            'nodes': len(nodegraph.getNodes()),
            'inputs': [{'name': inp.getName(), 'type': inp.getType()} for inp in nodegraph.getInputs()],
            'outputs': [{'name': out.getName(), 'type': out.getType()} for out in nodegraph.getOutputs()],
            'inheritance': self._get_converted_value(nodegraph) if resolve else nodegraph.getInheritString()
        }
    
    def _analyze_material_node(self, material: mx.Node, resolve: bool) -> Dict:
        """Analyze a material node."""
        return {
            'name': material.getName(),
            'type': material.getType(),
            'category': material.getCategory(),
            'shaders': [self._analyze_shader_bindings(shader) for shader in material.getShaders()],
            'inheritance': self._get_converted_value(material) if resolve else material.getInheritString()
        }
    
    def _analyze_shader_bindings(self, shader: mx.ShaderRef) -> List[Dict]:
        """Analyze shader bindings."""
        bindings = []
        for binding in shader.getBindInputs():
            bindings.append({
                'name': binding.getName(),
                'type': binding.getType(),
                'geom': self._get_geom_info(binding, False),
                'value': binding.getValueString()
            })
        return bindings
    
    def _analyze_geominfo(self, geominfo: mx.GeomInfo) -> Dict:
        """Analyze geometry info."""
        return {
            'name': geominfo.getName(),
            'type': geominfo.getType(),
            'geom': self._get_geom_info(geominfo, False),
            'value': geominfo.getValueString()
        }
    
    def _analyze_variantset(self, variantset: mx.VariantSet) -> Dict:
        """Analyze a variant set."""
        return {
            'name': variantset.getName(),
            'variants': [var.getName() for var in variantset.getVariants()]
        }
    
    def _analyze_propertyset(self, propertyset: mx.PropertySet) -> Dict:
        """Analyze a property set."""
        return {
            'name': propertyset.getName(),
            'properties': [{'name': prop.getName(), 'type': prop.getType(), 'value': prop.getValueString()} 
                          for prop in propertyset.getProperties()]
        }
    
    def _analyze_lookgroup(self, lookgroup: mx.LookGroup) -> Dict:
        """Analyze a look group."""
        return {
            'name': lookgroup.getName(),
            'looks': [look.getName() for look in lookgroup.getLooks()]
        }
    
    def _analyze_look(self, look: mx.Look, resolve: bool) -> Dict:
        """Analyze a look."""
        return {
            'name': look.getName(),
            'type': look.getType(),
            'materials': [mat.getName() for mat in look.getMaterialAssigns()],
            'properties': [prop.getName() for prop in look.getPropertyAssigns()],
            'inheritance': self._get_converted_value(look) if resolve else look.getInheritString()
        }
    
    def _analyze_backdrop(self, backdrop: mx.Backdrop) -> Dict:
        """Analyze a backdrop."""
        return {
            'name': backdrop.getName(),
            'width': backdrop.getWidth(),
            'height': backdrop.getHeight()
        }
    
    def _get_converted_value(self, elem) -> str:
        """Get converted value for an element."""
        try:
            return elem.getResolvedValueString()
        except:
            return elem.getValueString()
    
    def _get_geom_info(self, elem, resolve: bool) -> str:
        """Get geometry info for an element."""
        try:
            if resolve:
                return elem.getResolvedGeomString()
            else:
                return elem.getGeomString()
        except:
            return ""
    
    def _validate_document_structure(self, document: mx.Document, results: Dict[str, Any]):
        """Validate document structure."""
        try:
            # Check for required elements
            materials = document.getMaterials()
            if not materials:
                results['warnings'].append("No materials found in document")
            
            # Check for orphaned elements
            nodes = document.getNodes()
            if nodes:
                results['statistics']['nodes'] = len(nodes)
            
        except Exception as e:
            results['errors'].append(f"Structure validation error: {str(e)}")
    
    def _validate_node_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate node connections."""
        try:
            nodes = document.getNodes()
            for node in nodes:
                for input_elem in node.getInputs():
                    if input_elem.getNodeName():
                        # Check if referenced node exists
                        referenced_node = document.getNode(input_elem.getNodeName())
                        if not referenced_node:
                            results['warnings'].append(f"Node '{node.getName()}' references non-existent node '{input_elem.getNodeName()}'")
            
        except Exception as e:
            results['errors'].append(f"Connection validation error: {str(e)}")
    
    def _validate_performance_issues(self, document: mx.Document, results: Dict[str, Any]):
        """Validate for performance issues."""
        try:
            # Check for deeply nested nodegraphs
            nodegraphs = document.getNodeGraphs()
            for nodegraph in nodegraphs:
                depth = self._calculate_nesting_depth(nodegraph)
                if depth > 10:
                    results['warnings'].append(f"NodeGraph '{nodegraph.getName()}' has deep nesting (depth: {depth})")
            
        except Exception as e:
            results['errors'].append(f"Performance validation error: {str(e)}")
    
    def _calculate_nesting_depth(self, element: mx.Element, current_depth: int = 0) -> int:
        """Calculate nesting depth of an element."""
        max_depth = current_depth
        for child in element.getChildren():
            if child.isA(mx.NodeGraph):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth
    
    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """Get a summary of validation results."""
        summary = f"MaterialX Validation Summary\n"
        summary += f"Version: {results.get('version', 'Unknown')}\n"
        summary += f"Status: {'VALID' if results['valid'] else 'INVALID'}\n"
        summary += f"Errors: {len(results['errors'])}\n"
        summary += f"Warnings: {len(results['warnings'])}\n"
        summary += f"Info: {len(results['info'])}\n"
        
        if results['errors']:
            summary += "\nErrors:\n"
            for error in results['errors'][:5]:
                summary += f"  - {error}\n"
        
        if results['warnings']:
            summary += "\nWarnings:\n"
            for warning in results['warnings'][:5]:
                summary += f"  - {warning}\n"
        
        return summary
    
    def print_validation_report(self, results: Dict[str, Any], verbose: bool = True):
        """Print a validation report."""
        summary = self.get_validation_summary(results)
        self.logger.info(summary)
        
        if verbose and results.get('details'):
            self.logger.info("Detailed Analysis:")
            for category, items in results['details'].items():
                if items:
                    self.logger.info(f"  {category}: {len(items)} items")
                    for item in items[:3]:  # Show first 3 items
                        self.logger.info(f"    - {item.get('name', 'Unknown')}")


def validate_materialx_document(document: mx.Document, logger=None, **kwargs) -> Dict[str, Any]:
    """Convenience function to validate a MaterialX document."""
    validator = MaterialXValidator(logger)
    return validator.validate_document(document, **kwargs)


def validate_materialx_file(filepath: str, logger=None, **kwargs) -> Dict[str, Any]:
    """Convenience function to validate a MaterialX file."""
    validator = MaterialXValidator(logger)
    return validator.validate_file(filepath, **kwargs)
