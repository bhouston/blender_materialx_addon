bl_info = {
    "name": "MaterialX Export",
    "author": "Ben Houston (neuralsoft@gmail.com)",
    "website": "https://github.com/bhouston/blender-materialx",
    "support": "COMMUNITY",
    "version": (1, 1, 3),  # Updated version number
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
import logging

# Add addon directory to path for imports
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

from . import blender_materialx_exporter

# Version information
ADDON_VERSION = "1.1.3"
ADDON_NAME = "MaterialX Export"

# Set up logging
def log_message(message, level='INFO'):
    """Log message to both print and Blender's logging system"""

    print(f"WARNING: [MaterialX] {message}")
    
    # Also log to Blender's system
    if level == 'ERROR':
        print(f"ERROR: {message}")
    elif level == 'WARNING':
        print(f"WARNING: {message}")
    else:
        print(f"INFO: {message}")

def print_startup_message():
    """Print startup message when addon is loaded"""
    print("=" * 60)
    print(f"🎨 {ADDON_NAME} v{ADDON_VERSION} loaded successfully!")
    print("=" * 60)
    print("📁 Location: Properties > Material > MaterialX")
    print("🔧 Features:")
    print("   • Export individual materials to MaterialX format")
    print("   • Export all materials at once")
    print("   • Support for texture export and copying")
    print("   • MaterialX 1.38 specification compliance")
    print("   • Fixed mix node parameters (fg, bg, mix)")
    print("   • Added layer, add, multiply nodes")
    print("   • Added roughness_anisotropy and artistic_ior utilities")
    print("=" * 60)
    print("💡 Usage: Select a material and click 'Export MaterialX'")
    print("🌐 More info: https://github.com/bhouston/blender-materialx")
    print("=" * 60)

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
        log_message("=" * 60)
        log_message("MATERIALX EXPORT: Starting export process")
        log_message("=" * 60)
        
        if not context.material:
            log_message("No material selected", 'ERROR')
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        log_message(f"Material selected: {context.material.name}")
        log_message(f"Material uses nodes: {context.material.use_nodes}")
        log_message(f"Output filepath: {self.filepath}")
        log_message(f"Export textures: {self.export_textures}")
        log_message(f"Copy textures: {self.copy_textures}")
        log_message(f"Relative paths: {self.relative_paths}")
        
        # Export options
        options = {
            'export_textures': self.export_textures,
            'copy_textures': self.copy_textures,
            'relative_paths': self.relative_paths,
            'materialx_version': '1.38',
        }
        
        log_message("Export options prepared, calling exporter...")
        
        try:
            # Export the material
            log_message("Calling blender_materialx_exporter.export_material_to_materialx...")
            success = blender_materialx_exporter.export_material_to_materialx(
                context.material, 
                self.filepath, 
                options
            )
            log_message(f"Exporter returned: {success}")
            
            if success:
                log_message("SUCCESS: Material export completed successfully")
                self.report({'INFO'}, f"Successfully exported material '{context.material.name}'")
                return {'FINISHED'}
            else:
                log_message("FAILURE: Material export failed", 'ERROR')
                self.report({'ERROR'}, f"Failed to export material '{context.material.name}'")
                return {'CANCELLED'}
                
        except Exception as e:
            import traceback
            log_message(f"EXCEPTION during export: {type(e).__name__}: {str(e)}", 'ERROR')
            log_message("Full traceback:", 'ERROR')
            traceback.print_exc()
            self.report({'ERROR'}, f"Export failed with exception: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        print("MATERIALX EXPORT: Invoke called - opening file dialog")
        
        if not context.material:
            print("ERROR: No material selected during invoke")
            self.report({'ERROR'}, "No material selected")
            return {'CANCELLED'}
        
        print(f"Material for file dialog: {context.material.name}")
        
        # Set default filename based on material name
        default_filename = f"{context.material.name}.mtlx"
        self.filepath = default_filename
        print(f"Default filepath set to: {self.filepath}")
        
        print("Opening file dialog...")
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

        log_message(f"Export options: {options}")
        log_message(f"Directory: {self.directory}")
        log_message(f"Export textures: {self.export_textures}")
        log_message(f"Copy textures: {self.copy_textures}")
        log_message(f"Relative paths: {self.relative_paths}")
        
        # Export all materials
        results = blender_materialx_exporter.export_all_materials_to_materialx(
            self.directory, 
            options
        )
        log_message(f"Results: {results}")
        
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
        
        # Version info
        layout.separator()
        box = layout.box()
        box.label(text=f"MaterialX Export v{ADDON_VERSION}")
        box.label(text="MaterialX 1.38 compliant")

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
    print(f"🎨 {ADDON_NAME} v{ADDON_VERSION} unloaded")

if __name__ == "__main__":
    register()
