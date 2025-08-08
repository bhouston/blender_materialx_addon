#!/usr/bin/env python3
"""
Batch Exporter

This module provides batch export functionality for multiple materials.
"""

from typing import Dict, List, Optional, Any
import bpy
import MaterialX as mx
from .base_exporter import BaseExporter
from .material_exporter import MaterialExporter


class BatchExporter(BaseExporter):
    """
    Batch exporter for exporting multiple materials at once.
    """
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.material_exporter = MaterialExporter(self.logger)
    
    def can_export(self, blender_object: bpy.types.Object) -> bool:
        """Check if this exporter can handle the given Blender object."""
        # Batch exporter can handle any object with materials
        return blender_object is not None
    
    def export(self, blender_object: bpy.types.Object, export_path: str,
               options: Optional[Dict[str, Any]] = None) -> bool:
        """Export a Blender object using batch processing."""
        
        # Set options
        if options:
            self.set_export_options(options)
        
        # Pre-export validation
        if not self.pre_export(blender_object):
            return False
        
        try:
            # Get all materials from the object
            materials = self._get_materials_from_object(blender_object)
            if not materials:
                self.logger.warning(f"No materials found on object {blender_object.name}")
                return False
            
            # Export each material
            success_count = 0
            for material in materials:
                material_path = self._get_material_export_path(export_path, material.name)
                if self.material_exporter.export(blender_object, material_path, self.export_options):
                    success_count += 1
                    self.exported_materials[material.name] = material_path
            
            self.logger.info(f"Batch export completed: {success_count}/{len(materials)} materials exported")
            
            # Post-export operations
            return self.post_export(export_path)
            
        except Exception as e:
            self.logger.error(f"Batch export failed: {e}")
            return False
    
    def export_all_materials(self, export_directory: str, 
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Export all materials in the current Blender scene.
        
        Args:
            export_directory: Directory to export materials to
            options: Optional export options
            
        Returns:
            Dictionary mapping material names to export paths
        """
        exported_materials = {}
        
        try:
            # Get all materials in the scene
            materials = list(bpy.data.materials)
            if not materials:
                self.logger.warning("No materials found in scene")
                return exported_materials
            
            # Set options
            if options:
                self.set_export_options(options)
            
            self.logger.info(f"Starting batch export of {len(materials)} materials")
            
            # Export each material
            for material in materials:
                if not material.node_tree:
                    self.logger.warning(f"Material {material.name} has no node tree, skipping")
                    continue
                
                material_path = self._get_material_export_path(export_directory, material.name)
                
                # Create a temporary object for export
                temp_object = self._create_temp_object(material)
                if temp_object:
                    if self.material_exporter.export(temp_object, material_path, self.export_options):
                        exported_materials[material.name] = material_path
                        self.exported_materials[material.name] = material_path
                    
                    # Clean up temporary object
                    bpy.data.objects.remove(temp_object)
            
            self.logger.info(f"Batch export completed: {len(exported_materials)}/{len(materials)} materials exported")
            return exported_materials
            
        except Exception as e:
            self.logger.error(f"Batch export failed: {e}")
            return exported_materials
    
    def _get_materials_from_object(self, blender_object: bpy.types.Object) -> List[bpy.types.Material]:
        """Get all materials from a Blender object."""
        materials = []
        
        # Get active material
        if blender_object.active_material:
            materials.append(blender_object.active_material)
        
        # Get materials from material slots
        for slot in blender_object.material_slots:
            if slot.material and slot.material not in materials:
                materials.append(slot.material)
        
        return materials
    
    def _get_material_export_path(self, base_path: str, material_name: str) -> str:
        """Get the export path for a material."""
        import os
        
        # Clean material name for filename
        safe_name = "".join(c for c in material_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        # Create full path
        filename = f"{safe_name}.mtlx"
        return os.path.join(base_path, filename)
    
    def _create_temp_object(self, material: bpy.types.Material) -> Optional[bpy.types.Object]:
        """Create a temporary object for material export."""
        try:
            # Create a simple cube
            bpy.ops.mesh.primitive_cube_add()
            temp_object = bpy.context.active_object
            
            # Assign the material
            temp_object.active_material = material
            
            return temp_object
            
        except Exception as e:
            self.logger.error(f"Failed to create temporary object: {e}")
            return None
    
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
            'performance_monitoring': True,
            'batch_mode': True
        }
