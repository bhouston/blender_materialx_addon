bl_info = {
    "name": "MaterialX Export",
    "author": "Ben Houston (neuralsoft@gmail.com)",
    "website": "https://github.com/bhouston/blender-materialx",
    "support": "COMMUNITY",
    "version": (1, 1, 4),  # Updated version number
    "blender": (4, 0, 0),
    "location": "Properties > Material",
    "description": "Export Blender materials to MaterialX format",
    "category": "Material",
}

MATERIALX_VERSION = '1.38'

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Panel, Operator
import os
import sys
import logging
                

logger = logging.getLogger(bl_info["name"])
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


# Add addon directory to path for imports
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

from . import blender_materialx_exporter


def print_startup_message():
    """Print startup message when addon is loaded"""
    logger.info("=" * 60)
    logger.info(f"🎨 {bl_info['name']} v{bl_info['version']} loaded successfully!")
    logger.info("=" * 60)
    logger.info("📁 Location: Properties > Material > MaterialX")
    logger.info("🔧 Features:")
    logger.info("   • Export individual materials to MaterialX format")
    logger.info("   • Export all materials at once")
    logger.info("   • Support for texture export and copying")
    logger.info("   • MaterialX 1.38 specification compliance")
    logger.info("   • Fixed mix node parameters (fg, bg, mix)")
    logger.info("   • Added layer, add, multiply nodes")
    logger.info("   • Added roughness_anisotropy and artistic_ior utilities")
    logger.info("=" * 60)
    logger.info("💡 Usage: Select a material and click 'Export MaterialX'")
    logger.info("🌐 More info: https://github.com/bhouston/blender-materialx")
    logger.info("=" * 60)

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
        logger.info("=" * 60)
        logger.info("MATERIALX EXPORT: Starting export process")
        logger.info("=" * 60)
        
        if not context.material:
            logger.error("No material selected")
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        logger.info(f"Material selected: {context.material.name}")
        logger.info(f"Material uses nodes: {context.material.use_nodes}")
        logger.info(f"Output filepath: {self.filepath}")
        logger.info(f"Export textures: {self.export_textures}")
        logger.info(f"Copy textures: {self.copy_textures}")
        logger.info(f"Relative paths: {self.relative_paths}")
        
        # Export options
        options = {
            'export_textures': self.export_textures,
            'copy_textures': self.copy_textures,
            'relative_paths': self.relative_paths,
            'materialx_version': MATERIALX_VERSION,
        }
        
        logger.info("Export options prepared, calling exporter...")
        
        try:
            # Export the material
            logger.info("Calling blender_materialx_exporter.export_material_to_materialx...")
            result = blender_materialx_exporter.export_material_to_materialx(
                context.material, 
                self.filepath, 
                logger,
                options
            )
            logger.info(f"Exporter returned: {result}")
            
            if isinstance(result, dict) and result.get('success'):
                logger.info("SUCCESS: Material export completed successfully")
                self.report({'INFO'}, f"Successfully exported material '{context.material.name}'")
                return {'FINISHED'}
            else:
                error_msg = result.get('error') if isinstance(result, dict) else str(result)
                logger.error(f"FAILURE: Material export failed: {error_msg}")
                self.report({'ERROR'}, f"Failed to export material '{context.material.name}': {error_msg}")
                return {'CANCELLED'}
                
        except Exception as e:
            import traceback
            logger.error(f"EXCEPTION during export: {type(e).__name__}: {str(e)}")
            logger.error("Full traceback:")
            traceback.print_exc()
            self.report({'ERROR'}, f"Export failed with exception: {str(e)}, {traceback.format_exc()}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        logger.info("MATERIALX EXPORT: Invoke called - opening file dialog")
        
        if not context.material:
            logger.error("ERROR: No material selected during invoke")
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        logger.info(f"Material for file dialog: {context.material.name}")
        
        # Set default filename based on material name
        default_filename = f"{context.material.name}.mtlx"
        self.filepath = default_filename
        logger.info(f"Default filepath set to: {self.filepath}")
        
        logger.info("Opening file dialog...")
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
            'materialx_version': MATERIALX_VERSION,
        }

        logger.info(f"Export options: {options}")
        logger.info(f"Directory: {self.directory}")
        logger.info(f"Export textures: {self.export_textures}")
        logger.info(f"Copy textures: {self.copy_textures}")
        logger.info(f"Relative paths: {self.relative_paths}")
        
        # Export all materials
        results = blender_materialx_exporter.export_all_materials_to_materialx(
            self.directory, 
            logger,
            options
        )
        logger.info(f"Results: {results}")
        
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
            box.label(text=f"SelectedMaterial: {context.material.name}")
            
            if context.material.use_nodes:
                box.label(text="✓ Uses nodes", icon='CHECKMARK')
            else:
                box.label(text="✗ No nodes, not supported", icon='ERROR')
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
    
    # Print startup message
    print_startup_message()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Print unload message
    logger.info(f"🎨 {bl_info['name']} v{bl_info['version']} unloaded")

if __name__ == "__main__":
    register()
