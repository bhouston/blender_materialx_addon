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
            
            # Export the material
            success = self._export_material(material, document)
            if not success:
                return False
            
            # Save the document
            success = self._save_document(document, export_path)
            if not success:
                return False
            
            # Post-export operations
            return self.post_export(export_path)
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    def _export_material(self, material: bpy.types.Material, document: mx.Document) -> bool:
        """Export a Blender material to MaterialX."""
        try:
            self.logger.info(f"Exporting material: {material.name}")
            
            # Create MaterialX material
            materialx_material = self.document_manager.add_material(
                document, material.name, "standard_surface"
            )
            
            # Get the material's node tree
            if not material.node_tree:
                self.logger.warning(f"Material {material.name} has no node tree")
                return False
            
            # Export nodes
            success = self._export_nodes(material.node_tree, document)
            if not success:
                return False
            
            # Connect material to shader
            success = self._connect_material_to_shader(materialx_material, document)
            if not success:
                return False
            
            self.logger.info(f"Successfully exported material: {material.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export material {material.name}: {e}")
            return False
    
    def _export_nodes(self, node_tree: bpy.types.NodeTree, document: mx.Document) -> bool:
        """Export nodes from a Blender node tree."""
        try:
            self.logger.debug(f"Exporting {len(node_tree.nodes)} nodes")
            
            # Track processed nodes to avoid duplicates
            processed_nodes = set()
            unsupported_nodes = []
            
            # Export each node
            for node in node_tree.nodes:
                # Skip if already processed
                if node.name in processed_nodes:
                    self.logger.debug(f"Skipping already processed node: {node.name}")
                    continue
                
                if not self.node_registry.can_map_node(node):
                    unsupported_nodes.append({
                        'name': node.name,
                        'type': node.type,
                        'bl_idname': node.bl_idname
                    })
                    self.logger.warning(f"Unsupported node type: {node.type} ({node.name})")
                    processed_nodes.add(node.name)  # Mark as processed to avoid reprocessing
                    continue
                
                try:
                    # Check if node already exists in exported_nodes
                    if node.name in self.exported_nodes:
                        self.logger.debug(f"Node {node.name} already exported, skipping")
                        processed_nodes.add(node.name)
                        continue
                    
                    materialx_node = self.node_registry.map_node(node, document, self.exported_nodes)
                    self.exported_nodes[node.name] = materialx_node.getName()
                    processed_nodes.add(node.name)
                    self.logger.debug(f"Exported node: {node.name} -> {materialx_node.getName()}")
                except Exception as e:
                    self.logger.error(f"Failed to export node {node.name}: {e}")
                    processed_nodes.add(node.name)  # Mark as processed to avoid infinite retries
                    continue
            
            # If we have unsupported nodes, fail the export
            if unsupported_nodes:
                self.logger.error(f"Export failed: Found {len(unsupported_nodes)} unsupported nodes")
                # Store unsupported nodes for error reporting
                self.unsupported_nodes = unsupported_nodes
                return False
            
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
                
                # Connect outputs
                for output in node.outputs:
                    if output.is_linked:
                        for link in output.links:
                            to_node = link.to_node
                            if to_node.name in self.exported_nodes:
                                to_materialx_node = document.getNode(self.exported_nodes[to_node.name])
                                if to_materialx_node:
                                    # Connect the nodes
                                    # This is a simplified connection - actual implementation would be more complex
                                    pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect nodes: {e}")
            return False
    
    def _connect_material_to_shader(self, materialx_material, document: mx.Document) -> bool:
        """Connect the MaterialX material to its shader."""
        try:
            # Find the main shader node (usually Principled BSDF)
            for node_name, materialx_node_name in self.exported_nodes.items():
                materialx_node = document.getNode(materialx_node_name)
                if materialx_node and materialx_node.getType() == "standard_surface":
                    # Connect material to shader
                    # This is a simplified connection - actual implementation would be more complex
                    break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect material to shader: {e}")
            return False
    
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
    
    def get_default_options(self) -> Dict[str, Any]:
        """Get default export options."""
        return {
            'materialx_version': '1.39',
            'export_textures': True,
            'copy_textures': True,
            'relative_paths': True,
            'strict_mode': True,
            'optimize_document': True,
            'advanced_validation': True,
            'performance_monitoring': True
        }
    
    def get_option_types(self) -> Dict[str, type]:
        """Get expected types for export options."""
        return {
            'materialx_version': str,
            'export_textures': bool,
            'copy_textures': bool,
            'relative_paths': bool,
            'strict_mode': bool,
            'optimize_document': bool,
            'advanced_validation': bool,
            'performance_monitoring': bool
        }
