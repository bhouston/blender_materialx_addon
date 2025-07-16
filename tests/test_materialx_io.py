import bpy
import os
import sys
import tempfile
import traceback
import argparse

# Add the project root to sys.path so materialx_addon can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(f"Project root: {project_root}")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the add-on's import/export functions
data_dir = os.path.join(os.path.dirname(__file__), "data")
print(f"Data dir: {data_dir}")
mtlx_files = [f for f in os.listdir(data_dir) if f.endswith(".mtlx")]
print(f"MTLX files: {mtlx_files}")

# Import functions from the add-on
from materialx_addon import importer, exporter

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def setup_scene_with_sphere_and_hdri(material, hdri_path, render_size=256):
    # Add sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    sphere = bpy.context.active_object
    # Assign the imported material by object reference
    if material:
        sphere.data.materials.clear()
        sphere.data.materials.append(material)
        sphere.active_material = material
    else:
        print(f"[WARN] No valid material provided to setup_scene_with_sphere_and_hdri.")

    # Set up camera
    bpy.ops.object.camera_add(location=(0, -4, 0), rotation=(1.5708, 0, 0))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    # Set up HDRI lighting
    bpy.context.scene.render.engine = 'CYCLES'
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    env_node = None
    nt = world.node_tree
    for node in nt.nodes:
        if node.type == 'TEX_ENVIRONMENT':
            env_node = node
            break
    if not env_node:
        env_node = nt.nodes.new('ShaderNodeTexEnvironment')
    env_node.image = bpy.data.images.load(hdri_path, check_existing=True)
    nt.nodes['Background'].inputs['Strength'].default_value = 1.0
    nt.links.new(env_node.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    # Set render resolution
    bpy.context.scene.render.resolution_x = render_size
    bpy.context.scene.render.resolution_y = render_size
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = 'WEBP'
    bpy.context.scene.render.image_settings.quality = 95

def render_image(output_path):
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

def test_import_export_roundtrip(mtlx_path, render_mode=True, hdri_path=None, output_dir=None, render_size=256):
    print(f"\n=== Testing: {os.path.basename(mtlx_path)} ===")
    clear_scene()
    try:
        # Import
        imported_materials = importer.import_materialx(mtlx_path)
        if not imported_materials:
            print(f"[FAIL] Import failed for {mtlx_path}")
            return False
        print("[PASS] Import succeeded")

        mat = imported_materials[0]
        
        # Print node tree of imported material for debugging
        if mat and mat.use_nodes:
            print(f"[DEBUG] Node tree for material '{mat.name}':")
            for node in mat.node_tree.nodes:
                print(f"  Node: {node.name} ({node.type})")
                for input_socket in node.inputs:
                    print(f"    Input: {input_socket.name} = {getattr(input_socket, 'default_value', None)}")
                for output_socket in node.outputs:
                    print(f"    Output: {output_socket.name}")
        else:
            print(f"[WARN] Material '{mat.name}' not found or has no nodes.")

        # Visual validation: render material on sphere
        if render_mode and hdri_path:
            setup_scene_with_sphere_and_hdri(mat, hdri_path, render_size=render_size)
            output_filename = f"{os.path.splitext(os.path.basename(mtlx_path))[0]}.webp"
            output_path = os.path.join(output_dir, output_filename)
            render_image(output_path)
            print(f"[PASS] Rendered image: {output_path}")

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix=".mtlx", delete=False) as tmp:
            export_path = tmp.name
        result = exporter.export_materialx(export_path)
        if result != {'FINISHED'}:
            print(f"[FAIL] Export failed for {mtlx_path}")
            return False
        print(f"[PASS] Export succeeded: {export_path}")

        # Optionally, re-import the exported file for round-trip check
        clear_scene()
        reimported_materials = importer.import_materialx(export_path)
        if not reimported_materials:
            print(f"[FAIL] Round-trip import failed for {export_path}")
            return False
        print("[PASS] Round-trip import succeeded")
        os.remove(export_path)
        return True
    except Exception as e:
        print(f"[ERROR] Exception during test: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Test MaterialX import/export and optionally render materials.")
    parser.add_argument('--render', type=str, default='true', help='Enable or disable rendering of materials to images (true/false, default: true)')
    parser.add_argument('--render-size', type=int, default=256, help='Render image size in pixels (default: 256)')
    parser.add_argument('--filter', type=str, default=None, help='Regex to filter which .mtlx files to test (default: all)')
    # Only parse args after '--' to avoid Blender's own args
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    render_mode = args.render.lower() in ('true', '1', 'yes', 'on')
    render_size = args.render_size
    hdri_path = os.path.join(data_dir, "abandoned_factory_canteen_01_1k.hdr")
    output_dir = data_dir
    all_passed = True

    import re
    file_filter = re.compile(args.filter) if args.filter else None

    for fname in mtlx_files:
        if file_filter and not file_filter.search(fname):
            continue
        mtlx_path = os.path.join(data_dir, fname)
        passed = test_import_export_roundtrip(mtlx_path, render_mode=render_mode, hdri_path=hdri_path, output_dir=output_dir, render_size=render_size)
        if not passed:
            all_passed = False
    if all_passed:
        print("\nAll MaterialX import/export tests passed!")
    else:
        print("\nSome MaterialX import/export tests failed.")

if __name__ == "__main__":
    main() 