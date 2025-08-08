#!/usr/bin/env python3
"""
Material Exporter

This module provides the main material export functionality.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_exporter import BaseExporter
from ..mappers.node_mapper_registry import get_registry
from ..validation.validator import MaterialXValidator


class MaterialExporter(BaseExporter):
    """
    Main material exporter for converting Blender materials to MaterialX.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.node_registry = get_registry()
    
    def can_export(self, blender_object: bpy.types.Object) -> bool:
        """Check if this exporter can handle the given Blender object."""
        return blender_object and blender_object.active_material
    
    def export(self, blender_object: bpy.types.Object, export_path: str,
               options: Optional[Dict[str, Any]] = None) -> bool:
        """Export a Blender object's material to MaterialX."""
        
        # Set options
        if options:
            self.set_export_options(options)
        
        # Pre-export validation
        if not self.pre_export(blender_object):
            return False
        
        try:
            # Get the material
            material = blender_object.active_material
            if not material:
                self.logger.error(f"No active material found on object {blender_object.name}")
                return False
            
            # Create MaterialX document
            document = self.document_manager.create_document(
                f"material_{material.name}", 
                self.export_options.get('materialx_version', '1.39')
            )
            
            # Add colorspace declaration
            document.setColorSpace("lin_rec709")
            
            # Export the material
            success = self._export_material(material, document)
            if not success:
                return False
            
            # Save the document
            success = self._save_document(document, export_path)
            if not success:
                return False
            
            # Validate the exported document
            validation_results = self._validate_exported_document(document, export_path)
            if validation_results:
                self.logger.info("Export validation completed")
                if validation_results.get('valid', False):
                    self.logger.info(f"✅ Export quality score: {validation_results.get('statistics', {}).get('quality_score', 'N/A')}/100")
                else:
                    self.logger.warning("⚠️ Export completed but validation found issues")
            
            # Post-export operations
            return self.post_export(export_path)
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _export_material(self, material: bpy.types.Material, document: mx.Document) -> bool:
        """Export a Blender material to MaterialX."""
        try:
            self.logger.info(f"Exporting material: {material.name}")
            
            # Get the material's node tree
            if not material.node_tree:
                self.logger.warning(f"Material {material.name} has no node tree")
                return False
            
            # Export nodes first
            success = self._export_nodes(material.node_tree, document)
            if not success:
                return False
            
            # Find the main surface shader node
            surface_shader_node = self._find_surface_shader_node(document)
            if not surface_shader_node:
                self.logger.error("No surface shader node found")
                return False
            
            # Create MaterialX material and connect to shader
            success = self._create_and_connect_material(material.name, surface_shader_node, document)
            if not success:
                return False
            
            self.logger.info(f"Successfully exported material: {material.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export material {material.name}: {e}")
            return False
    
    def _export_nodes(self, node_tree: bpy.types.NodeTree, document: mx.Document) -> bool:
        """Export nodes from a Blender node tree to MaterialX."""
        try:
            self.logger.debug(f"Exporting {len(node_tree.nodes)} nodes")
            
            # Track processed and unsupported nodes
            processed_nodes = set()
            unsupported_nodes = []
            
            # First pass: export all nodes
            for node in node_tree.nodes:
                if node.name in processed_nodes:
                    continue
                
                # Skip Material Output nodes - they're not needed in MaterialX
                if node.type == 'OUTPUT_MATERIAL':
                    processed_nodes.add(node.name)
                    continue
                
                # Check if node is supported
                if not self.node_registry.can_map_node(node):
                    unsupported_nodes.append({
                        'name': node.name,
                        'type': node.type,
                        'bl_idname': node.bl_idname
                    })
                    processed_nodes.add(node.name)
                    continue
                
                try:
                    # Check if node already exists in exported_nodes
                    if node.name in self.exported_nodes:
                        self.logger.debug(f"Node {node.name} already exported, skipping")
                        processed_nodes.add(node.name)
                        continue
                    
                    self.logger.debug(f"Attempting to export node: {node.name} (type: {node.type})")
                    
                    # Get the mapper for this node
                    mapper = self.node_registry.get_mapper_for_node(node)
                    if mapper:
                        self.logger.debug(f"Found mapper: {mapper.__class__.__name__}")
                    else:
                        self.logger.error(f"No mapper found for node type: {node.type}")
                        continue
                    
                    materialx_node = self.node_registry.map_node(node, document, self.exported_nodes)
                    self.exported_nodes[node.name] = materialx_node.getName()
                    processed_nodes.add(node.name)
                    self.logger.debug(f"Successfully exported node: {node.name} -> {materialx_node.getName()}")
                except Exception as e:
                    self.logger.error(f"Failed to export node {node.name}: {e}")
                    processed_nodes.add(node.name)  # Mark as processed to avoid infinite retries
                    continue
            
            # If we have unsupported nodes, log them but don't fail the export
            if unsupported_nodes:
                self.logger.warning(f"Found {len(unsupported_nodes)} unsupported nodes, but continuing export")
                # Store unsupported nodes for error reporting
                self.unsupported_nodes = unsupported_nodes
            
            # Connect nodes
            success = self._connect_nodes(node_tree, document)
            if not success:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export nodes: {e}")
            return False
    
    def _connect_nodes(self, node_tree: bpy.types.NodeTree, document: mx.Document) -> bool:
        """Connect nodes in the MaterialX document."""
        try:
            self.logger.debug("Connecting nodes")
            
            # Connect each node's outputs to inputs
            for node in node_tree.nodes:
                if node.name not in self.exported_nodes:
                    continue
                
                materialx_node = document.getNode(self.exported_nodes[node.name])
                if not materialx_node:
                    continue
                
                # Connect outputs to inputs
                for output in node.outputs:
                    if output.is_linked:
                        for link in output.links:
                            to_node = link.to_node
                            if to_node.name in self.exported_nodes:
                                to_materialx_node = document.getNode(self.exported_nodes[to_node.name])
                                if to_materialx_node:
                                    # Get the MaterialX input and output names
                                    from_output_name = self._get_materialx_output_name(output.name, node)
                                    to_input_name = self._get_materialx_input_name(link.to_socket.name, to_node)
                                    
                                    # Connect the nodes
                                    success = self._connect_materialx_nodes(
                                        materialx_node, from_output_name,
                                        to_materialx_node, to_input_name
                                    )
                                    if success:
                                        self.logger.debug(f"Connected {node.name}.{output.name} -> {to_node.name}.{link.to_socket.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect nodes: {e}")
            return False
    
    def _connect_materialx_nodes(self, from_node: Any, from_output: str,
                                to_node: Any, to_input: str) -> bool:
        """Connect two MaterialX nodes."""
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
            
            # Connect the input to the output
            input_port.setConnectedOutput(output_port)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect MaterialX nodes: {e}")
            return False
    
    def _find_surface_shader_node(self, document: mx.Document) -> Optional[Any]:
        """Find the main surface shader node in the document."""
        try:
            # Look for standard_surface nodes
            for node_name, materialx_node_name in self.exported_nodes.items():
                materialx_node = document.getNode(materialx_node_name)
                if materialx_node and materialx_node.getType() == "standard_surface":
                    return materialx_node
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find surface shader node: {e}")
            return None
    
    def _create_and_connect_material(self, material_name: str, surface_shader_node: Any, 
                                   document: mx.Document) -> bool:
        """Create a MaterialX material and connect it to the surface shader."""
        try:
            # Create the material
            material = document.addMaterial(material_name)
            
            # Add the surfaceshader input and connect it to the surface shader node
            shader_input = material.addInput("surfaceshader", "surfaceshader")
            shader_input.setConnectedNode(surface_shader_node)
            
            self.logger.debug(f"Created material '{material_name}' and connected to shader '{surface_shader_node.getName()}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create and connect material: {e}")
            return False
    
    def _get_materialx_output_name(self, blender_output_name: str, blender_node: bpy.types.Node) -> str:
        """Get the MaterialX output name for a Blender output."""
        # Get the mapper for this node type
        mapper = self.node_registry.get_mapper_for_node(blender_node)
        if mapper:
            output_mapping = mapper.get_output_mapping()
            return output_mapping.get(blender_output_name, blender_output_name)
        return blender_output_name
    
    def _get_materialx_input_name(self, blender_input_name: str, blender_node: bpy.types.Node) -> str:
        """Get the MaterialX input name for a Blender input."""
        # Get the mapper for this node type
        mapper = self.node_registry.get_mapper_for_node(blender_node)
        if mapper:
            input_mapping = mapper.get_input_mapping()
            return input_mapping.get(blender_input_name, blender_input_name)
        return blender_input_name
    
    def _save_document(self, document: mx.Document, export_path: str) -> bool:
        """Save the MaterialX document to file."""
        try:
            # Try different ways to save the document
            try:
                # Method 1: Try MaterialX.Format
                import MaterialX.Format as mxFormat
                mxFormat.writeToXmlFile(document, export_path)
            except ImportError:
                try:
                    # Method 2: Try direct MaterialX writeToXmlFile
                    mx.writeToXmlFile(document, export_path)
                except AttributeError:
                    try:
                        # Method 3: Try using the document's writeToXmlFile method
                        document.writeToXmlFile(export_path)
                    except AttributeError:
                        # Method 4: Manual XML writing as fallback
                        self._write_document_manually(document, export_path)
            
            self.logger.info(f"Saved MaterialX document to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save document: {e}")
            return False
    
    def _write_document_manually(self, document: mx.Document, export_path: str):
        """Write MaterialX document manually as XML."""
        try:
            # Create a simple XML representation
            xml_content = f"""<?xml version="1.0"?>
<materialx version="1.39">
  <material name="{document.getName() or 'material'}">
    <shaderref name="surface" nodetype="standard_surface"/>
  </material>
</materialx>"""
            
            with open(export_path, 'w') as f:
                f.write(xml_content)
                
        except Exception as e:
            self.logger.error(f"Failed to write document manually: {e}")
            raise
    
    def _validate_exported_document(self, document: mx.Document, export_path: str) -> Optional[Dict[str, Any]]:
        """Validate the exported MaterialX document."""
        try:
            validator = MaterialXValidator(self.logger)
            validation_results = validator.validate_document(document, verbose=True)
            
            if validation_results:
                self.logger.info(f"Validation results for {export_path}:")
                
                # Log validation summary
                if validation_results.get('valid', False):
                    self.logger.info("✅ Document is valid")
                else:
                    self.logger.warning("⚠️ Document has validation issues")
                
                # Log errors and warnings
                for error in validation_results.get('errors', []):
                    self.logger.error(f"Validation error: {error}")
                
                for warning in validation_results.get('warnings', []):
                    self.logger.warning(f"Validation warning: {warning}")
                
                # Log quality score if available
                quality_score = validation_results.get('statistics', {}).get('quality_score', None)
                if quality_score is not None:
                    self.logger.info(f"Export quality score: {quality_score}/100")
                
                return validation_results
            else:
                self.logger.info(f"No validation issues found for {export_path}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to validate document {export_path}: {e}")
            return None
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default export options."""
        return {
            'materialx_version': '1.39',
            'export_textures': True,
            'texture_path': '',
            'relative_paths': True,
            'copy_textures': False
        }
    
    def get_option_types(self) -> Dict[str, type]:
        """Get option types for validation."""
        return {
            'materialx_version': str,
            'export_textures': bool,
            'texture_path': str,
            'relative_paths': bool,
            'copy_textures': bool
        }
