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
            self._validate_surface_shader_setup(document, results)
            self._validate_node_types(document, results)
            self._validate_default_values(document, results)
            self._validate_material_structure(document, results)
            self._validate_texture_coordinates(document, results)
            self._validate_export_quality(document, results)
    
            
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
    
    def _analyze_nodedef(self, nodedef, resolve: bool) -> Dict:
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
    
    def _analyze_implementation(self, impl) -> Dict:
        """Analyze an implementation."""
        return {
            'name': impl.getName(),
            'node': impl.getNodeString(),
            'file': impl.getFile(),
            'language': impl.getLanguage()
        }
    
    def _analyze_nodegraph(self, nodegraph, resolve: bool) -> Dict:
        """Analyze a nodegraph."""
        return {
            'name': nodegraph.getName(),
            'type': nodegraph.getType(),
            'nodes': len(nodegraph.getNodes()),
            'inputs': [{'name': inp.getName(), 'type': inp.getType()} for inp in nodegraph.getInputs()],
            'outputs': [{'name': out.getName(), 'type': out.getType()} for out in nodegraph.getOutputs()],
            'inheritance': self._get_converted_value(nodegraph) if resolve else nodegraph.getInheritString()
        }
    
    def _analyze_material_node(self, material, resolve: bool) -> Dict:
        """Analyze a material node."""
        return {
            'name': material.getName(),
            'type': material.getType(),
            'category': material.getCategory(),
            'shaders': [self._analyze_shader_bindings(shader) for shader in material.getShaders()],
            'inheritance': self._get_converted_value(material) if resolve else material.getInheritString()
        }
    
    def _analyze_shader_bindings(self, shader) -> List[Dict]:
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
    
    def _analyze_geominfo(self, geominfo) -> Dict:
        """Analyze geometry info."""
        try:
            return {
                'name': geominfo.getName(),
                'type': geominfo.getType(),
                'geom': self._get_geom_info(geominfo, False),
                'value': geominfo.getValueString()
            }
        except:
            return {'name': 'unknown', 'type': 'unknown', 'error': 'Failed to analyze GeomInfo'}
    
    def _analyze_variantset(self, variantset) -> Dict:
        """Analyze a variant set."""
        try:
            return {
                'name': variantset.getName(),
                'variants': [var.getName() for var in variantset.getVariants()]
            }
        except:
            return {'name': 'unknown', 'error': 'Failed to analyze VariantSet'}
    
    def _analyze_propertyset(self, propertyset) -> Dict:
        """Analyze a property set."""
        try:
            return {
                'name': propertyset.getName(),
                'properties': [{'name': prop.getName(), 'type': prop.getType(), 'value': prop.getValueString()} 
                              for prop in propertyset.getProperties()]
            }
        except:
            return {'name': 'unknown', 'error': 'Failed to analyze PropertySet'}
    
    def _analyze_lookgroup(self, lookgroup) -> Dict:
        """Analyze a look group."""
        try:
            return {
                'name': lookgroup.getName(),
                'looks': [look.getName() for look in lookgroup.getLooks()]
            }
        except:
            return {'name': 'unknown', 'error': 'Failed to analyze LookGroup'}
    
    def _analyze_look(self, look, resolve: bool) -> Dict:
        """Analyze a look."""
        try:
            return {
                'name': look.getName(),
                'type': look.getType(),
                'materials': [mat.getName() for mat in look.getMaterialAssigns()],
                'properties': [prop.getName() for prop in look.getPropertyAssigns()],
                'inheritance': self._get_converted_value(look) if resolve else look.getInheritString()
            }
        except:
            return {'name': 'unknown', 'error': 'Failed to analyze Look'}
    
    def _analyze_backdrop(self, backdrop) -> Dict:
        """Analyze a backdrop."""
        try:
            return {
                'name': backdrop.getName(),
                'width': backdrop.getWidth(),
                'height': backdrop.getHeight()
            }
        except:
            return {'name': 'unknown', 'error': 'Failed to analyze Backdrop'}
    
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
            
            # Check for colorspace declaration
            colorspace = document.getColorSpace()
            if not colorspace:
                results['warnings'].append("No colorspace declaration found - should set colorspace for proper rendering")
            
        except Exception as e:
            results['errors'].append(f"Structure validation error: {str(e)}")
    
    def _validate_node_connections(self, document: mx.Document, results: Dict[str, Any]):
        """Validate node connections."""
        try:
            nodes = document.getNodes()
            disconnected_nodes = []
            orphaned_inputs = []
            
            for node in nodes:
                node_has_connections = False
                
                for input_elem in node.getInputs():
                    if input_elem.getNodeName():
                        node_has_connections = True
                        # Check if referenced node exists
                        referenced_node = document.getNode(input_elem.getNodeName())
                        if not referenced_node:
                            results['warnings'].append(f"Node '{node.getName()}' references non-existent node '{input_elem.getNodeName()}'")
                    elif not input_elem.getValueString() and not input_elem.getConnectedOutput():
                        # Input has no value and no connection
                        orphaned_inputs.append(f"Node '{node.getName()}' input '{input_elem.getName()}' has no value or connection")
                
                if not node_has_connections and node.getType() != "standard_surface":
                    disconnected_nodes.append(node.getName())
            
            if disconnected_nodes:
                results['warnings'].append(f"Found {len(disconnected_nodes)} disconnected nodes: {', '.join(disconnected_nodes[:5])}")
            
            if orphaned_inputs:
                results['warnings'].append(f"Found {len(orphaned_inputs)} inputs without values or connections")
            
        except Exception as e:
            results['errors'].append(f"Connection validation error: {str(e)}")
    
    def _validate_surface_shader_setup(self, document: mx.Document, results: Dict[str, Any]):
        """Validate surface shader setup and connections."""
        try:
            # Check for surface shader elements (only direct standard_surface elements are valid)
            surface_shaders = []
            
            # Check for standard_surface elements (direct elements, not nodes)
            for elem in document.getChildren():
                if elem.getCategory() == "standard_surface":
                    surface_shaders.append(elem.getName())
            
            # Check for incorrect node-based standard_surface usage
            for node in document.getNodes():
                if node.getType() == "standard_surface":
                    results['errors'].append(f"Invalid standard_surface node '{node.getName()}' found - standard_surface should be a direct element, not a node")
            
            if not surface_shaders:
                results['errors'].append("No standard_surface elements found - material will not render properly")
                return
            
            # Check material connections to surface shaders
            materials = document.getMaterials()
            for material in materials:
                material_has_shader = False
                for input_elem in material.getInputs():
                    if input_elem.getType() == "surfaceshader" and input_elem.getNodeName():
                        material_has_shader = True
                        # Verify the referenced element is a surface shader
                        shader_elem = document.getChild(input_elem.getNodeName())
                        if shader_elem:
                            if shader_elem.getCategory() == "standard_surface":
                                # This is a correct direct standard_surface element
                                break
                            else:
                                results['errors'].append(f"Material '{material.getName()}' connected to non-standard_surface element '{input_elem.getNodeName()}' (type: {shader_elem.getCategory()})")
                        else:
                            results['warnings'].append(f"Material '{material.getName()}' references non-existent surface shader '{input_elem.getNodeName()}'")
                        break
                
                if not material_has_shader:
                    results['errors'].append(f"Material '{material.getName()}' has no surfaceshader input connection")
            
        except Exception as e:
            results['errors'].append(f"Surface shader validation error: {str(e)}")
    
    def _validate_node_types(self, document: mx.Document, results: Dict[str, Any]):
        """Validate correct node types and categories."""
        try:
            for node in document.getNodes():
                node_type = node.getType()
                node_category = node.getCategory()
                
                # Check for incorrect standard_surface nodes (should be direct elements, not nodes)
                if node_type == "standard_surface":
                    results['errors'].append(f"Invalid standard_surface node '{node.getName()}' found - standard_surface should be a direct element, not a node")
                
                # Check for surface nodes that should be surfaceshader
                if node_type == "surface" and node_category == "surface":
                    results['warnings'].append(f"Node '{node.getName()}' uses deprecated 'surface' type (should be 'surfaceshader')")
            
        except Exception as e:
            results['errors'].append(f"Node type validation error: {str(e)}")
    
    def _validate_default_values(self, document: mx.Document, results: Dict[str, Any]):
        """Validate that nodes have appropriate default values."""
        try:
            for node in document.getNodes():
                node_type = node.getType()
                
                # Check standard_surface nodes for essential inputs
                if node_type == "standard_surface":
                    essential_inputs = ['base_color', 'base', 'specular_roughness']
                    for input_name in essential_inputs:
                        input_elem = node.getInput(input_name)
                        if input_elem:
                            value = input_elem.getValueString()
                            if not value and not input_elem.getNodeName():
                                results['warnings'].append(f"Standard surface node '{node.getName()}' missing default value for '{input_name}'")
                
                # Check constant nodes for values
                elif node_type in ['constant', 'ramplr', 'ramp4']:
                    has_value = False
                    for input_elem in node.getInputs():
                        if input_elem.getValueString() or input_elem.getNodeName():
                            has_value = True
                            break
                    
                    if not has_value:
                        results['warnings'].append(f"Constant node '{node.getName()}' has no values or connections")
            
        except Exception as e:
            results['errors'].append(f"Default value validation error: {str(e)}")
    
    def _validate_material_structure(self, document: mx.Document, results: Dict[str, Any]):
        """Validate proper material structure."""
        try:
            materials = document.getMaterials()
            
            for material in materials:
                # Check for surfaceshader input
                surfaceshader_input = None
                for input_elem in material.getInputs():
                    if input_elem.getType() == "surfaceshader":
                        surfaceshader_input = input_elem
                        break
                
                if not surfaceshader_input:
                    results['errors'].append(f"Material '{material.getName()}' missing surfaceshader input")
                elif not surfaceshader_input.getNodeName():
                    results['errors'].append(f"Material '{material.getName()}' surfaceshader input not connected to any node")
                
                # Check for proper material type
                if material.getType() != "material":
                    results['warnings'].append(f"Material '{material.getName()}' has incorrect type '{material.getType()}' (should be 'material')")
            
        except Exception as e:
            results['errors'].append(f"Material structure validation error: {str(e)}")
    
    def _validate_texture_coordinates(self, document: mx.Document, results: Dict[str, Any]):
        """Validate texture coordinate setup."""
        try:
            # Check for texture nodes without texcoord inputs
            texture_nodes = []
            for node in document.getNodes():
                if node.getType() in ['image', 'noise2d', 'checker2d', 'brick2d', 'voronoi2d', 'wave2d', 'musgrave2d']:
                    texture_nodes.append(node)
            
            for node in texture_nodes:
                texcoord_input = node.getInput('texcoord')
                if texcoord_input and not texcoord_input.getNodeName():
                    results['warnings'].append(f"Texture node '{node.getName()}' has texcoord input but no connection")
            
        except Exception as e:
            results['errors'].append(f"Texture coordinate validation error: {str(e)}")
    
    def _validate_export_quality(self, document: mx.Document, results: Dict[str, Any]):
        """Validate overall export quality and provide recommendations."""
        try:
            # Analyze node connectivity
            nodes = document.getNodes()
            connected_nodes = 0
            for node in nodes:
                has_connection = False
                for input_elem in node.getInputs():
                    if input_elem.getNodeName() or input_elem.getValueString():
                        has_connection = True
                        break
                if has_connection:
                    connected_nodes += 1
            
            if nodes:
                connection_ratio = connected_nodes / len(nodes)
                if connection_ratio < 0.5:
                    results['warnings'].append(f"Low node connectivity ({connection_ratio:.1%}) - many nodes may be disconnected")
            
            # Check for common export issues
            materials = document.getMaterials()
            
            # Check for surface shaders (only direct standard_surface elements are valid)
            surface_shaders = [e for e in document.getChildren() if e.getCategory() == "standard_surface"]
            
            # Check for incorrect node-based standard_surface usage
            invalid_nodes = [n for n in nodes if n.getType() == "standard_surface"]
            if invalid_nodes:
                results['errors'].append(f"Found {len(invalid_nodes)} invalid standard_surface nodes - standard_surface should be direct elements, not nodes")
            
            if not materials:
                results['errors'].append("No materials found - export may be incomplete")
            
            if not surface_shaders:
                results['errors'].append("No surface shaders found - material will not render")
            
            if materials and not surface_shaders:
                results['errors'].append("Materials exist but no surface shaders - materials cannot render")
            
            # Check for proper material-shader connections
            for material in materials:
                has_shader_connection = False
                for input_elem in material.getInputs():
                    if input_elem.getType() == "surfaceshader" and input_elem.getNodeName():
                        has_shader_connection = True
                        break
                
                if not has_shader_connection:
                    results['errors'].append(f"Material '{material.getName()}' not connected to any surface shader")
            
        except Exception as e:
            results['errors'].append(f"Export quality validation error: {str(e)}")
    
    def get_validation_summary(self, results: Dict[str, Any]) -> str:
        """Get a summary of validation results."""
        summary = f"MaterialX Validation Summary\n"
        summary += f"Version: {results.get('version', 'Unknown')}\n"
        summary += f"Status: {'VALID' if results['valid'] else 'INVALID'}\n"
        summary += f"Errors: {len(results['errors'])}\n"
        summary += f"Warnings: {len(results['warnings'])}\n"
        summary += f"Info: {len(results['info'])}\n"
        
        if results['errors']:
            summary += "\nCritical Issues:\n"
            for error in results['errors'][:5]:
                summary += f"  ❌ {error}\n"
        
        if results['warnings']:
            summary += "\nWarnings:\n"
            for warning in results['warnings'][:5]:
                summary += f"  ⚠️  {warning}\n"
        
        if results['info']:
            summary += "\nInfo:\n"
            for info in results['info'][:3]:
                summary += f"  ℹ️  {info}\n"
        
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
