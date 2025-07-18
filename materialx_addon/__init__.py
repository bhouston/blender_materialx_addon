bl_info = {
    "name": "MaterialX Export",
    "author": "Ben Houston (neuralsoft@gmail.com)",
    "website": "https://github.com/bhouston/blender-materialx",
    "support": "COMMUNITY",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Properties > Material",
    "description": "Export Blender materials to MaterialX format",
    "category": "Material",
}

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Panel, Operator
import os
import sys

# Add addon directory to path for imports
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

from . import blender_materialx_exporter

class MATERIALX_OT_export(Operator):
    """Export MaterialX file"""
    bl_idname = "materialx.export"
    bl_label = "Export MaterialX"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting MaterialX file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default="*.mtlx",
        options={'HIDDEN'},
    )

    export_textures: BoolProperty(
        name="Export Textures",
        description="Export texture files along with the MaterialX file",
        default=True,
    )

    copy_textures: BoolProperty(
        name="Copy Textures",
        description="Copy texture files to the export directory",
        default=True,
    )

    relative_paths: BoolProperty(
        name="Relative Paths",
        description="Use relative paths for texture references",
        default=True,
    )

    def execute(self, context):
        if not context.material:
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        # Export options
        options = {
            'export_textures': self.export_textures,
            'copy_textures': self.copy_textures,
            'relative_paths': self.relative_paths,
            'materialx_version': '1.38',
        }
        
        # Export the material
        success = blender_materialx_exporter.export_material_to_materialx(
            context.material, 
            self.filepath, 
            options
        )
        
        if success:
            self.report({'INFO'}, f"Successfully exported material '{context.material.name}'")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to export material '{context.material.name}'")
            return {'CANCELLED'}

    def invoke(self, context, event):
        if not context.material:
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        # Set default filename based on material name
        default_filename = f"{context.material.name}.mtlx"
        self.filepath = default_filename
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MATERIALX_OT_export_all(Operator):
    """Export all materials to MaterialX files"""
    bl_idname = "materialx.export_all"
    bl_label = "Export All Materials"
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name="Directory",
        description="Directory to export MaterialX files",
        maxlen=1024,
        subtype='DIR_PATH',
    )

    export_textures: BoolProperty(
        name="Export Textures",
        description="Export texture files along with the MaterialX files",
        default=True,
    )

    copy_textures: BoolProperty(
        name="Copy Textures",
        description="Copy texture files to the export directory",
        default=True,
    )

    relative_paths: BoolProperty(
        name="Relative Paths",
        description="Use relative paths for texture references",
        default=True,
    )

    def execute(self, context):
        if not self.directory:
            self.report({'ERROR'}, "No directory selected")
            return {'CANCELLED'}
        
        # Export options
        options = {
            'export_textures': self.export_textures,
            'copy_textures': self.copy_textures,
            'relative_paths': self.relative_paths,
            'materialx_version': '1.38',
        }
        
        # Export all materials
        results = blender_materialx_exporter.export_all_materials_to_materialx(
            self.directory, 
            options
        )
        
        # Report results
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        if successful == total:
            self.report({'INFO'}, f"Successfully exported all {total} materials")
        else:
            failed = total - successful
            self.report({'WARNING'}, f"Exported {successful}/{total} materials ({failed} failed)")
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MATERIALX_PT_panel(Panel):
    """MaterialX panel in Properties > Material"""
    bl_label = "MaterialX"
    bl_idname = "MATERIALX_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        if context.material:
            # Export current material
            row = layout.row()
            row.operator("materialx.export", text="Export MaterialX")
            
            # Material info
            box = layout.box()
            box.label(text=f"Material: {context.material.name}")
            
            if context.material.use_nodes:
                box.label(text="✓ Uses nodes", icon='CHECKMARK')
            else:
                box.label(text="✗ No nodes", icon='ERROR')
        else:
            layout.label(text="No material selected")

        layout.separator()
        
        # Export all materials
        layout.operator("materialx.export_all", text="Export All Materials")

classes = (
    MATERIALX_OT_export,
    MATERIALX_OT_export_all,
    MATERIALX_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
