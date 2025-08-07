#!/usr/bin/env python3
"""
MaterialX Validator - Comprehensive validation for MaterialX documents

This module provides comprehensive validation functionality for MaterialX documents,
adapted from the MaterialX validation script to work within the Blender addon context.

Features:
- Document structure validation
- Node and connection validation
- Performance analysis
- Detailed reporting
- Integration with Blender logging
"""

import MaterialX as mx
import logging
from typing import Dict, List, Optional, Any, Tuple
import os
import sys


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
            
            # Update valid status based on all validation results
            if results['errors']:
                results['valid'] = False
            
        except Exception as e:
            results['errors'].append(f"Validation process failed: {str(e)}")
            self.logger.error(f"Validation exception: {str(e)}")
        
        return results
    
    def validate_file(self, filepath: str, resolve_inheritance: bool = True, 
                     verbose: bool = True, include_stdlib: bool = True) -> Dict[str, Any]:
        """
        Validate a MaterialX file by reading and validating it.
        
        Args:
            filepath: Path to the MaterialX file
            resolve_inheritance: Whether to resolve inheritance and string substitutions
            verbose: Whether to include detailed analysis
            include_stdlib: Whether to include standard library validation
            
        Returns:
            Dict containing validation results
        """
        results = {
            'valid': False,
            'filepath': filepath,
            'version': mx.getVersionString(),
            'errors': [],
            'warnings': [],
            'info': [],
            'statistics': {},
            'details': {}
        }
        
        try:
            # Read the document
            doc = mx.createDocument()
            mx.readFromXmlFile(doc, filepath)
            
            # Validate the document
            validation_results = self.validate_document(doc, resolve_inheritance, verbose, include_stdlib)
            
            # Merge results
            results.update(validation_results)
            results['filepath'] = filepath
            
        except mx.ExceptionFileMissing as err:
            results['errors'].append(f"File not found: {err}")
        except Exception as e:
            results['errors'].append(f"Failed to read file: {str(e)}")
            self.logger.error(f"File validation exception: {str(e)}")
        
        return results
    
    def _generate_detailed_analysis(self, document: mx.Document, results: Dict[str, Any], resolve: bool):
        """Generate detailed analysis of the document."""
        try:
            # Collect document elements
            nodegraphs = document.getNodeGraphs()
            materials = document.getMaterialNodes()
            looks = document.getLooks()
            lookgroups = document.getLookGroups()
            collections = document.getCollections()
            nodedefs = document.getNodeDefs()
            implementations = document.getImplementations()
            geominfos = document.getGeomInfos()
            geompropdefs = document.getGeomPropDefs()
            typedefs = document.getTypeDefs()
            propsets = document.getPropertySets()
            variantsets = document.getVariantSets()
            backdrops = document.getBackdrops()
            
            # Store statistics
            results['statistics'] = {
                'nodegraphs': len(nodegraphs),
                'materials': len(materials),
                'looks': len(looks),
                'lookgroups': len(lookgroups),
                'collections': len(collections),
                'nodedefs': len(nodedefs),
                'implementations': len(implementations),
                'geominfos': len(geominfos),
                'geompropdefs': len(geompropdefs),
                'typedefs': len(typedefs),
                'propsets': len(propsets),
                'variantsets': len(variantsets),
                'backdrops': len(backdrops),
                'document_version': f"{document.getVersionIntegers()[0]}.{document.getVersionIntegers()[1]:02d}"
            }
            
            # Generate detailed element analysis
            results['details'] = {
                'typedefs': self._analyze_elements(typedefs, resolve, 'typedef'),
                'geompropdefs': self._analyze_elements(geompropdefs, resolve, 'geompropdef'),
                'nodedefs': self._analyze_elements(nodedefs, resolve, 'nodedef'),
                'implementations': self._analyze_elements(implementations, resolve, 'implementation'),
                'nodegraphs': self._analyze_elements(nodegraphs, resolve, 'nodegraph'),
                'variantsets': self._analyze_elements(variantsets, resolve, 'variantset'),
                'materials': self._analyze_elements(materials, resolve, 'material'),
                'collections': self._analyze_elements(collections, resolve, 'collection'),
                'geominfos': self._analyze_elements(geominfos, resolve, 'geominfo'),
                'propsets': self._analyze_elements(propsets, resolve, 'propertyset'),
                'looks': self._analyze_elements(looks, resolve, 'look'),
                'lookgroups': self._analyze_elements(lookgroups, resolve, 'lookgroup'),
                'backdrops': self._analyze_elements(backdrops, resolve, 'backdrop')
            }
            
        except Exception as e:
            results['warnings'].append(f"Detailed analysis failed: {str(e)}")
            self.logger.warning(f"Detailed analysis exception: {str(e)}")
    
    def _analyze_elements(self, elements: List, resolve: bool, element_type: str) -> List[Dict]:
        """Analyze a list of elements and return detailed information."""
        analysis = []
        
        for elem in elements:
            try:
                info = {
                    'name': elem.getName(),
                    'type': element_type,
                    'details': {}
                }
                
                if elem.isA(mx.NodeDef):
                    info['details'] = self._analyze_nodedef(elem, resolve)
                elif elem.isA(mx.Implementation):
                    info['details'] = self._analyze_implementation(elem)
                elif elem.isA(mx.NodeGraph):
                    info['details'] = self._analyze_nodegraph(elem, resolve)
                elif elem.isA(mx.Node) and elem.isA(mx.SURFACE_MATERIAL_NODE_STRING):
                    info['details'] = self._analyze_material_node(elem, resolve)
                elif elem.isA(mx.GeomInfo):
                    info['details'] = self._analyze_geominfo(elem)
                elif elem.isA(mx.VariantSet):
                    info['details'] = self._analyze_variantset(elem)
                elif elem.isA(mx.PropertySet):
                    info['details'] = self._analyze_propertyset(elem)
                elif elem.isA(mx.LookGroup):
                    info['details'] = self._analyze_lookgroup(elem)
                elif elem.isA(mx.Look):
                    info['details'] = self._analyze_look(elem, resolve)
                elif elem.isA(mx.Backdrop):
                    info['details'] = self._analyze_backdrop(elem)
                else:
                    info['details'] = {'basic_info': f"Element of type {element_type}"}
                
                analysis.append(info)
                
            except Exception as e:
                analysis.append({
                    'name': elem.getName() if hasattr(elem, 'getName') else 'unknown',
                    'type': element_type,
                    'error': str(e)
                })
        
        return analysis
    
    def _analyze_nodedef(self, nodedef: mx.NodeDef, resolve: bool) -> Dict:
        """Analyze a NodeDef element."""
        details = {
            'node_type': nodedef.getNodeString(),
            'output_type': nodedef.getType(),
            'inputs': [],
            'tokens': []
        }
        
        # Analyze inputs
        for inp in nodedef.getActiveInputs():
            input_info = {
                'name': inp.getName(),
                'type': inp.getType()
            }
            details['inputs'].append(input_info)
        
        # Analyze tokens
        for tok in nodedef.getActiveTokens():
            token_info = {
                'name': tok.getName(),
                'type': tok.getType()
            }
            details['tokens'].append(token_info)
        
        # Handle multioutput nodes
        if nodedef.getType() == "multioutput":
            details['outputs'] = []
            for ot in nodedef.getOutputs():
                details['outputs'].append({
                    'name': ot.getName(),
                    'type': ot.getType()
                })
        
        return details
    
    def _analyze_implementation(self, impl: mx.Implementation) -> Dict:
        """Analyze an Implementation element."""
        details = {
            'target': impl.getTarget() if impl.hasTarget() else None,
            'function': impl.getFunction() if impl.hasFunction() else None,
            'file': impl.getFile() if impl.hasFile() else None
        }
        return details
    
    def _analyze_nodegraph(self, nodegraph: mx.NodeGraph, resolve: bool) -> Dict:
        """Analyze a NodeGraph element."""
        details = {
            'node_count': len(nodegraph.getChildren()) - nodegraph.getOutputCount(),
            'output_count': nodegraph.getOutputCount(),
            'backdrop_count': len(nodegraph.getBackdrops()),
            'outputs': [],
            'backdrops': []
        }
        
        # Analyze outputs
        for ot in nodegraph.getOutputs():
            details['outputs'].append({
                'name': ot.getName(),
                'type': ot.getType()
            })
        
        # Analyze backdrops
        for bd in nodegraph.getBackdrops():
            details['backdrops'].append({
                'name': bd.getName(),
                'contains': bd.getContainsString()
            })
        
        # Check if it's an implementation
        nd = nodegraph.getNodeDef()
        if nd:
            details['implements'] = nd.getName()
        
        return details
    
    def _analyze_material_node(self, material: mx.Node, resolve: bool) -> Dict:
        """Analyze a Material node."""
        shaders = mx.getShaderNodes(material)
        details = {
            'shader_count': len(shaders),
            'shaders': []
        }
        
        for shader in shaders:
            shader_info = {
                'name': shader.getName(),
                'category': shader.getCategory(),
                'bindings': self._analyze_shader_bindings(shader)
            }
            details['shaders'].append(shader_info)
        
        return details
    
    def _analyze_shader_bindings(self, shader: mx.Node) -> List[Dict]:
        """Analyze shader input bindings."""
        bindings = []
        
        for inp in shader.getInputs():
            binding = {
                'name': inp.getName(),
                'type': inp.getType()
            }
            
            if inp.hasOutputString():
                binding['connection'] = {
                    'output': inp.getOutputString(),
                    'nodegraph': inp.getNodeGraphString() if inp.hasNodeGraphString() else None
                }
            else:
                binding['value'] = self._get_converted_value(inp)
            
            bindings.append(binding)
        
        return bindings
    
    def _analyze_geominfo(self, geominfo: mx.GeomInfo) -> Dict:
        """Analyze a GeomInfo element."""
        details = {
            'geomprops': [],
            'tokens': []
        }
        
        # Analyze geomprops
        props = geominfo.getGeomProps()
        for prop in props:
            details['geomprops'].append({
                'name': prop.getName(),
                'value': self._get_converted_value(prop)
            })
        
        # Analyze tokens
        tokens = geominfo.getTokens()
        for token in tokens:
            details['tokens'].append({
                'name': token.getName(),
                'value': token.getValueString()
            })
        
        return details
    
    def _analyze_variantset(self, variantset: mx.VariantSet) -> Dict:
        """Analyze a VariantSet element."""
        variants = variantset.getVariants()
        details = {
            'variants': [var.getName() for var in variants] if variants else []
        }
        return details
    
    def _analyze_propertyset(self, propertyset: mx.PropertySet) -> Dict:
        """Analyze a PropertySet element."""
        props = propertyset.getProperties()
        details = {
            'properties': []
        }
        
        for prop in props:
            prop_info = {
                'name': prop.getName(),
                'type': prop.getType(),
                'target': prop.getTarget() if prop.hasTarget() else None
            }
            details['properties'].append(prop_info)
        
        return details
    
    def _analyze_lookgroup(self, lookgroup: mx.LookGroup) -> Dict:
        """Analyze a LookGroup element."""
        looks = lookgroup.getLooks()
        details = {
            'looks': looks if looks else []
        }
        return details
    
    def _analyze_look(self, look: mx.Look, resolve: bool) -> Dict:
        """Analyze a Look element."""
        details = {
            'material_assigns': [],
            'property_assigns': [],
            'propertyset_assigns': [],
            'variant_assigns': [],
            'visibilities': []
        }
        
        # Analyze material assigns
        if resolve:
            mtlassns = look.getActiveMaterialAssigns()
        else:
            mtlassns = look.getMaterialAssigns()
        
        for mtlassn in mtlassns:
            details['material_assigns'].append({
                'material': mtlassn.getMaterial(),
                'geom': self._get_geom_info(mtlassn, resolve)
            })
        
        # Analyze property assigns
        if resolve:
            propassns = look.getActivePropertyAssigns()
        else:
            propassns = look.getPropertyAssigns()
        
        for propassn in propassns:
            details['property_assigns'].append({
                'property': propassn.getAttribute("property"),
                'type': propassn.getType(),
                'geom': self._get_geom_info(propassn, resolve)
            })
        
        # Analyze propertyset assigns
        if resolve:
            propsetassns = look.getActivePropertySetAssigns()
        else:
            propsetassns = look.getPropertySetAssigns()
        
        for propsetassn in propsetassns:
            details['propertyset_assigns'].append({
                'propertyset': propsetassn.getAttribute("propertyset"),
                'geom': self._get_geom_info(propsetassn, resolve)
            })
        
        # Analyze variant assigns
        if resolve:
            variantassns = look.getActiveVariantAssigns()
        else:
            variantassns = look.getVariantAssigns()
        
        for varassn in variantassns:
            details['variant_assigns'].append({
                'variant': varassn.getVariantString(),
                'variantset': varassn.getVariantSetString()
            })
        
        # Analyze visibilities
        if resolve:
            visassns = look.getActiveVisibilities()
        else:
            visassns = look.getVisibilities()
        
        for vis in visassns:
            details['visibilities'].append({
                'type': vis.getVisibilityType(),
                'visible': vis.getVisible(),
                'geom': self._get_geom_info(vis, resolve)
            })
        
        return details
    
    def _analyze_backdrop(self, backdrop: mx.Backdrop) -> Dict:
        """Analyze a Backdrop element."""
        details = {
            'contains': backdrop.getContainsString()
        }
        return details
    
    def _get_converted_value(self, elem) -> str:
        """Get a converted value string for an element."""
        try:
            return elem.getValueString()
        except:
            return "unknown"
    
    def _get_geom_info(self, elem, resolve: bool) -> str:
        """Get geometry information for an element."""
        geom_info = ""
        
        if elem.hasGeom():
            if resolve:
                geom_info += f' geom "{elem.getActiveGeom()}"'
            else:
                geom_info += f' geom "{elem.getGeom()}"'
        
        if elem.hasCollectionString():
            geom_info += f' collection "{elem.getCollectionString()}"'
        
        return geom_info
    
    def _validate_document_structure(self, document: mx.Document, results: Dict[str, Any]):
        """Validate basic document structure."""
        try:
            # Check for required elements
            if not document.getMaterialNodes():
                results['warnings'].append("No material nodes found in document")
            
            if not document.getNodeGraphs():
                results['warnings'].append("No node graphs found in document")
            
            # Check document version
            version = document.getVersionIntegers()
            if version[0] < 1 or (version[0] == 1 and version[1] < 38):
                results['warnings'].append(f"Document version {version[0]}.{version[1]:02d} is older than recommended (1.38+)")
            
        except Exception as e:
            results['warnings'].append(f"Structure validation failed: {str(e)}")
    
    def _validate_node_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate node connections and references."""
        try:
            # Check for broken connections
            broken_connections = []
            
            for nodegraph in document.getNodeGraphs():
                for node in nodegraph.getNodes():
                    for inp in node.getInputs():
                        if inp.hasNodeName() and not nodegraph.getNode(inp.getNodeName()):
                            broken_connections.append(f"Broken connection in {nodegraph.getName()}.{node.getName()}.{inp.getName()}")
            
            if broken_connections:
                results['errors'].extend(broken_connections)
            
        except Exception as e:
            results['warnings'].append(f"Connection validation failed: {str(e)}")
    
    def _validate_performance_issues(self, document: mx.Document, results: Dict[str, Any]):
        """Check for potential performance issues."""
        try:
            # Check for deeply nested nodegraphs
            deep_nesting = []
            
            for nodegraph in document.getNodeGraphs():
                depth = self._calculate_nesting_depth(nodegraph)
                if depth > 5:
                    deep_nesting.append(f"Deep nesting detected in {nodegraph.getName()} (depth: {depth})")
            
            if deep_nesting:
                results['warnings'].extend(deep_nesting)
            
            # Check for large nodegraphs
            large_graphs = []
            
            for nodegraph in document.getNodeGraphs():
                node_count = len(nodegraph.getNodes())
                if node_count > 50:
                    large_graphs.append(f"Large nodegraph detected: {nodegraph.getName()} ({node_count} nodes)")
            
            if large_graphs:
                results['warnings'].extend(large_graphs)
            
        except Exception as e:
            results['warnings'].append(f"Performance validation failed: {str(e)}")
    
    def _calculate_nesting_depth(self, element: mx.Element, current_depth: int = 0) -> int:
        """Calculate the nesting depth of an element."""
        max_depth = current_depth
        
        for child in element.getChildren():
            if child.isA(mx.NodeGraph):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary."""
        summary_parts = []
        
        if results['valid']:
            summary_parts.append("✓ Document is valid")
        else:
            summary_parts.append("✗ Document has validation errors")
        
        if results['errors']:
            summary_parts.append(f"Errors: {len(results['errors'])}")
        
        if results['warnings']:
            summary_parts.append(f"Warnings: {len(results['warnings'])}")
        
        if results['statistics']:
            stats = results['statistics']
            summary_parts.append(f"Elements: {stats.get('materials', 0)} materials, {stats.get('nodegraphs', 0)} nodegraphs")
        
        return " | ".join(summary_parts)
    
    def print_validation_report(self, results: Dict[str, Any], verbose: bool = True):
        """Print a formatted validation report."""
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("MATERIALX VALIDATION REPORT")
        self.logger.info("=" * 60)
        self.logger.info(self.get_validation_summary(results))
        
        if verbose:
            # Print errors
            if results['errors']:
                self.logger.error("\nVALIDATION ERRORS:")
                for error in results['errors']:
                    self.logger.error(f"  ✗ {error}")
            
            # Print warnings
            if results['warnings']:
                self.logger.warning("\nVALIDATION WARNINGS:")
                for warning in results['warnings']:
                    self.logger.warning(f"  ⚠ {warning}")
            
            # Print statistics
            if results['statistics']:
                self.logger.info("\nDOCUMENT STATISTICS:")
                stats = results['statistics']
                self.logger.info(f"  Document Version: {stats.get('document_version', 'unknown')}")
                self.logger.info(f"  Materials: {stats.get('materials', 0)}")
                self.logger.info(f"  NodeGraphs: {stats.get('nodegraphs', 0)}")
                self.logger.info(f"  NodeDefs: {stats.get('nodedefs', 0)}")
                self.logger.info(f"  Implementations: {stats.get('implementations', 0)}")
                self.logger.info(f"  Looks: {stats.get('looks', 0)}")
                self.logger.info(f"  Collections: {stats.get('collections', 0)}")
        
        self.logger.info("=" * 60)


def validate_materialx_document(document: mx.Document, logger=None, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to validate a MaterialX document.
    
    Args:
        document: The MaterialX document to validate
        logger: Logger instance (optional)
        **kwargs: Additional validation options
        
    Returns:
        Dict containing validation results
    """
    validator = MaterialXValidator(logger)
    return validator.validate_document(document, **kwargs)


def validate_materialx_file(filepath: str, logger=None, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to validate a MaterialX file.
    
    Args:
        filepath: Path to the MaterialX file
        logger: Logger instance (optional)
        **kwargs: Additional validation options
        
    Returns:
        Dict containing validation results
    """
    validator = MaterialXValidator(logger)
    return validator.validate_file(filepath, **kwargs)
