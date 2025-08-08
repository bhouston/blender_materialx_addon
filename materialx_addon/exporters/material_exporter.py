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
            
            # Export each node
            for node in node_tree.nodes:
                if not self.node_registry.can_map_node(node):
                    self.logger.warning(f"Unsupported node type: {node.type}")
                    continue
                
                try:
                    materialx_node = self.node_registry.map_node(node, document, self.exported_nodes)
                    self.exported_nodes[node.name] = materialx_node.getName()
                    self.logger.debug(f"Exported node: {node.name} -> {materialx_node.getName()}")
                except Exception as e:
                    self.logger.error(f"Failed to export node {node.name}: {e}")
                    continue
            
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
    
    def _connect_material_to_shader(self, materialx_material: mx.Material, document: mx.Document) -> bool:
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
            # Import MaterialX format module
            import MaterialX.Format as mxFormat
            
            # Write the document to file
            mxFormat.writeToXmlFile(document, export_path)
            
            self.logger.info(f"Saved MaterialX document to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save document: {e}")
            return False
    
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
