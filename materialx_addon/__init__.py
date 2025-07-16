bl_info = {
    "name": "MaterialX Import-Export",
    "author": "Ben Houston (neuralsoft@gmail.com)",
    "website": "https://github.com/bhouston/blender-materialx",
    "support": "COMMUNITY",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Properties > Material",
    "description": "Import/Export MaterialX files with compatibility validation",
    "category": "Material",
}

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Panel, Operator, AddonPreferences
import os
import sys

# Add addon directory to path for imports
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

from . import mapping
from . import importer
from . import exporter
from . import validator

class MaterialXAddonPreferences(AddonPreferences):
    bl_idname = __name__

    enable_node_filtering: BoolProperty(
        name="Filter Non-MaterialX Nodes",
        description="Hide non-MaterialX compatible nodes in shader editor",
        default=False,
    )

    enable_node_highlighting: BoolProperty(
        name="Highlight Incompatible Nodes",
        description="Highlight non-MaterialX compatible nodes with red outline",
        default=True,
    )

    enable_object_highlighting: BoolProperty(
        name="Highlight Objects with Incompatible Materials",
        description="Highlight objects using non-MaterialX compatible materials in viewport",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_node_filtering")
        layout.prop(self, "enable_node_highlighting")
        layout.prop(self, "enable_object_highlighting")

class MATERIALX_OT_import(Operator):
    """Import MaterialX file"""
    bl_idname = "materialx.import"
    bl_label = "Import MaterialX"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing MaterialX file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default="*.mtlx",
        options={'HIDDEN'},
    )

    def execute(self, context):
        return importer.import_materialx(self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

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

    def execute(self, context):
        return exporter.export_materialx(self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MATERIALX_OT_validate_scene(Operator):
    """Validate current scene for MaterialX compatibility"""
    bl_idname = "materialx.validate_scene"
    bl_label = "Validate Scene"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return validator.validate_scene()

class MATERIALX_PT_panel(Panel):
    """MaterialX panel in Properties > Material"""
    bl_label = "MaterialX"
    bl_idname = "MATERIALX_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("materialx.import", text="Import MaterialX")
        row.operator("materialx.export", text="Export MaterialX")

        layout.separator()
        layout.operator("materialx.validate_scene", text="Validate Scene")

        # Show compatibility info for current material
        if context.material:
            mat = context.material
            is_compatible = validator.is_material_compatible(mat)
            
            box = layout.box()
            box.label(text=f"Material: {mat.name}")
            
            if is_compatible:
                box.label(text="✓ MaterialX Compatible", icon='CHECKMARK')
            else:
                box.label(text="✗ Not MaterialX Compatible", icon='ERROR')
                
                # Show incompatible nodes
                incompatible_nodes = validator.get_incompatible_nodes(mat)
                if incompatible_nodes:
                    box.label(text="Incompatible nodes:")
                    for node_name, node_type in incompatible_nodes:
                        box.label(text=f"  • {node_name} ({node_type})")

classes = (
    MaterialXAddonPreferences,
    MATERIALX_OT_import,
    MATERIALX_OT_export,
    MATERIALX_OT_validate_scene,
    MATERIALX_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Start validation handlers
    validator.register_handlers()

def unregister():
    # Stop validation handlers
    validator.unregister_handlers()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
