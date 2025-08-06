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

MATERIALX_VERSION = '1.39'

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
    logger.info("   • MaterialX 1.39 specification compliance")
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
        
        try:
            # Enhanced export with better error handling
            from . import blender_materialx_exporter
            
            # Configure export options
            options = {
                'export_textures': self.export_textures,
                'copy_textures': self.copy_textures,
                'relative_paths': self.relative_paths,
                'optimize_document': True,
                'advanced_validation': True,
                'performance_monitoring': True
            }
            
            result = blender_materialx_exporter.export_material_to_materialx(
                context.material, self.filepath, logger, options
            )
            
            if result['success']:
                # Success with detailed information
                message = f"Successfully exported '{context.material.name}' to MaterialX"
                
                # Add performance info if available
                if 'performance_stats' in result and result['performance_stats']:
                    stats = result['performance_stats']
                    if 'total_time' in stats:
                        message += f" (took {stats['total_time']:.2f}s)"
                
                # Add validation info if available
                if 'validation_results' in result and result['validation_results']:
                    validation = result['validation_results']
                    if validation.get('warnings'):
                        message += f" with {len(validation['warnings'])} warnings"
                
                self.report({'INFO'}, message)
                logger.info(f"✓ Export successful: {message}")
                
                # Show warnings in UI if any
                if 'validation_results' in result and result['validation_results'].get('warnings'):
                    for warning in result['validation_results']['warnings'][:3]:  # Show first 3 warnings
                        self.report({'WARNING'}, f"Warning: {warning}")
                
                return {'FINISHED'}
            else:
                # Handle export failure with specific error information
                error_message = "Export failed"
                
                if 'error' in result and result['error']:
                    error_message = result['error']
                elif 'unsupported_nodes' in result and result['unsupported_nodes']:
                    unsupported = result['unsupported_nodes']
                    if len(unsupported) == 1:
                        error_message = f"Unsupported node: {unsupported[0]['type']}"
                    else:
                        error_message = f"Unsupported nodes: {len(unsupported)} nodes not supported"
                
                self.report({'ERROR'}, error_message)
                logger.error(f"✗ Export failed: {error_message}")
                return {'CANCELLED'}
                
        except Exception as e:
            # Enhanced exception handling with specific error types
            error_message = str(e)
            
            # Check if it's a MaterialX-specific error
            if hasattr(e, 'error_type') and hasattr(e, 'get_user_friendly_message'):
                error_message = e.get_user_friendly_message()
                error_type = e.error_type
                
                # Provide specific guidance based on error type
                if error_type == "library_loading":
                    self.report({'ERROR'}, f"{error_message} Please ensure MaterialX is properly installed.")
                elif error_type == "unsupported_node":
                    self.report({'ERROR'}, f"{error_message} Consider using supported node types.")
                elif error_type == "validation_error":
                    self.report({'ERROR'}, f"{error_message} Check your material node setup.")
                else:
                    self.report({'ERROR'}, error_message)
            else:
                # Generic error handling
                self.report({'ERROR'}, f"Export failed: {error_message}")
            
            logger.error(f"✗ Export exception: {error_message}")
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
        
        if not context.material:
            layout.label(text="No material selected")
            return
        
        # Main export section
        box = layout.box()
        box.label(text="Export MaterialX", icon='EXPORT')
        
        col = box.column(align=True)
        col.operator("materialx.export", text="Export MaterialX", icon='EXPORT')
        
        # Export all materials section
        box = layout.box()
        box.label(text="Export All Materials", icon='MATERIAL')
        
        col = box.column(align=True)
        col.operator("materialx.export_all", text="Export All Materials", icon='MATERIAL')
        
        # Configuration section
        box = layout.box()
        box.label(text="Configuration", icon='SETTINGS')
        
        # Get current configuration
        config = getattr(context.scene, 'materialx_config', None)
        if not config:
            # Initialize default configuration
            config = context.scene.materialx_config = {
                'optimize_document': True,
                'advanced_validation': True,
                'performance_monitoring': True,
                'strict_mode': False,
                'continue_on_unsupported_nodes': True
            }
        
        col = box.column(align=True)
        
        # Core settings
        col.prop(context.scene, 'materialx_optimize_document', text="Optimize Document")
        col.prop(context.scene, 'materialx_advanced_validation', text="Advanced Validation")
        col.prop(context.scene, 'materialx_performance_monitoring', text="Performance Monitoring")
        
        # Error handling
        col.separator()
        col.prop(context.scene, 'materialx_strict_mode', text="Strict Mode")
        col.prop(context.scene, 'materialx_continue_on_unsupported_nodes', text="Continue on Unsupported Nodes")
        
        # Status information
        if hasattr(context.scene, 'materialx_last_export_result'):
            result = context.scene.materialx_last_export_result
            if result:
                box = layout.box()
                box.label(text="Last Export Status", icon='INFO')
                
                if result.get('success'):
                    col = box.column(align=True)
                    col.label(text="✓ Export Successful", icon='CHECKMARK')
                    
                    if 'performance_stats' in result:
                        stats = result['performance_stats']
                        if 'total_time' in stats:
                            col.label(text=f"Time: {stats['total_time']:.2f}s")
                    
                    if 'validation_results' in result:
                        validation = result['validation_results']
                        if validation.get('warnings'):
                            col.label(text=f"Warnings: {len(validation['warnings'])}", icon='ERROR')
                else:
                    col = box.column(align=True)
                    col.label(text="✗ Export Failed", icon='ERROR')
                    
                    if 'error' in result:
                        col.label(text=f"Error: {result['error']}")
                    
                    if 'unsupported_nodes' in result and result['unsupported_nodes']:
                        unsupported = result['unsupported_nodes']
                        col.label(text=f"Unsupported: {len(unsupported)} nodes")


# Add properties to scene for configuration
def register_properties():
    bpy.types.Scene.materialx_optimize_document = BoolProperty(
        name="Optimize Document",
        description="Optimize MaterialX document by removing unused nodes",
        default=True
    )
    
    bpy.types.Scene.materialx_advanced_validation = BoolProperty(
        name="Advanced Validation",
        description="Enable comprehensive MaterialX document validation",
        default=True
    )
    
    bpy.types.Scene.materialx_performance_monitoring = BoolProperty(
        name="Performance Monitoring",
        description="Track performance metrics during export",
        default=True
    )
    
    bpy.types.Scene.materialx_strict_mode = BoolProperty(
        name="Strict Mode",
        description="Fail export on any error (not just unsupported nodes)",
        default=False
    )
    
    bpy.types.Scene.materialx_continue_on_unsupported_nodes = BoolProperty(
        name="Continue on Unsupported Nodes",
        description="Continue export even when encountering unsupported nodes",
        default=True
    )
    
    bpy.types.Scene.materialx_last_export_result = bpy.props.StringProperty(
        name="Last Export Result",
        description="Result of the last MaterialX export operation",
        default=""
    )


def unregister_properties():
    del bpy.types.Scene.materialx_optimize_document
    del bpy.types.Scene.materialx_advanced_validation
    del bpy.types.Scene.materialx_performance_monitoring
    del bpy.types.Scene.materialx_strict_mode
    del bpy.types.Scene.materialx_continue_on_unsupported_nodes
    del bpy.types.Scene.materialx_last_export_result

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

    # Register properties
    register_properties()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Print unload message
    logger.info(f"🎨 {bl_info['name']} v{bl_info['version']} unloaded")

    # Unregister properties
    unregister_properties()

if __name__ == "__main__":
    register()
