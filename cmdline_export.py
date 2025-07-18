#!/usr/bin/env python3
"""
Command-line MaterialX Exporter for Blender

This script runs Blender in headless mode to export a specific material
from a .blend file to MaterialX format.

Usage:
    python cmdline_export.py <blend_file> <material_name> <output_mtlx_file> [options]

Examples:
    python cmdline_export.py scene.blend "MyMaterial" output.mtlx
    python cmdline_export.py scene.blend "MyMaterial" output.mtlx --export-textures --texture-path ./textures
    python cmdline_export.py scene.blend "MyMaterial" output.mtlx --version 1.38 --relative-paths

Arguments:
    blend_file      Path to the .blend file containing the material
    material_name   Name of the material to export
    output_mtlx_file Path for the output .mtlx file

Options:
    --export-textures    Export texture files (default: False)
    --texture-path PATH  Directory to export textures to (default: ./textures)
    --version VERSION    MaterialX version (default: 1.38)
    --relative-paths     Use relative paths for textures (default: True)
    --copy-textures      Copy texture files (default: True)
    --active-uvmap NAME  Active UV map name (default: UVMap)
    --blender-path PATH  Path to Blender executable (auto-detected if not specified)
    --help              Show this help message
"""

import argparse
import subprocess
import sys
import os
import tempfile
from pathlib import Path
import json


def find_blender_executable():
    """Find the Blender executable on the system."""
    # Common Blender installation paths
    possible_paths = []
    
    # macOS
    possible_paths.extend([
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender/blender.app/Contents/MacOS/blender",
    ])
    
    # Linux
    possible_paths.extend([
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/opt/blender/blender",
    ])
    
    # Windows
    possible_paths.extend([
        "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",
        "C:\\Program Files (x86)\\Blender Foundation\\Blender\\blender.exe",
    ])
    
    # Check if blender is in PATH
    try:
        result = subprocess.run(["which", "blender"], capture_output=True, text=True)
        if result.returncode == 0:
            possible_paths.append(result.stdout.strip())
    except FileNotFoundError:
        pass
    
    # Check each possible path
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None


def create_blender_script(blend_file, material_name, output_mtlx_file, options):
    """Create a temporary Blender Python script to perform the export."""
    
    # Convert options to Python literal format
    options_str = str(options).replace("'", '"')
    
    script_content = f'''
import bpy
import sys
import os

# Add the current directory to Python path to find the exporter
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import the MaterialX exporter
    from materialx_addon.blender_materialx_exporter import export_material_to_materialx
    
    # Load the blend file
    print(f"Loading blend file: {blend_file}")
    bpy.ops.wm.open_mainfile(filepath="{blend_file}")
    
    # Find the material
    material = bpy.data.materials.get("{material_name}")
    if not material:
        print(f"ERROR: Material '{material_name}' not found in the blend file")
        print("Available materials:")
        for mat in bpy.data.materials:
            print(f"  - {{mat.name}}")
        sys.exit(1)
    
    print(f"Found material: {{material.name}}")
    
    # Export options
    export_options = {options_str}
    
    # Export the material
    print(f"Exporting material to: {output_mtlx_file}")
    success = export_material_to_materialx(material, "{output_mtlx_file}", export_options)
    
    if success:
        print("SUCCESS: Material exported successfully")
        sys.exit(0)
    else:
        print("ERROR: Failed to export material")
        sys.exit(1)
        
except ImportError as e:
    print(f"ERROR: Failed to import MaterialX exporter: {{e}}")
    print("Make sure the materialx_addon directory is in the same directory as this script")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    return script_content


def run_blender_export(blend_file, material_name, output_mtlx_file, options, blender_path=None):
    """Run Blender in headless mode to export the material."""
    
    # Find Blender executable if not provided
    if not blender_path:
        blender_path = find_blender_executable()
        if not blender_path:
            print("ERROR: Blender executable not found!")
            print("Please install Blender or specify the path with --blender-path")
            return False
    
    print(f"Using Blender executable: {blender_path}")
    
    # Create temporary script file
    script_content = create_blender_script(blend_file, material_name, output_mtlx_file, options)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        script_path = f.name
        f.write(script_content)
    
    try:
        # Prepare Blender command
        cmd = [
            blender_path,
            "--background",  # Run in headless mode
            "--python", script_path,
            "--",  # End of Blender options
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run Blender
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))  # Run from script directory
        )
        
        # Print output
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check if export was successful
        if result.returncode == 0:
            if os.path.exists(output_mtlx_file):
                print(f"SUCCESS: Material exported to {output_mtlx_file}")
                return True
            else:
                print(f"ERROR: Output file {output_mtlx_file} was not created")
                return False
        else:
            print(f"ERROR: Blender process failed with return code {result.returncode}")
            return False
            
    finally:
        # Clean up temporary script
        try:
            os.unlink(script_path)
        except:
            pass


def main():
    """Main function to handle command-line arguments and run the export."""
    parser = argparse.ArgumentParser(
        description="Export a material from a Blender file to MaterialX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Required arguments
    parser.add_argument("blend_file", help="Path to the .blend file")
    parser.add_argument("material_name", help="Name of the material to export")
    parser.add_argument("output_mtlx_file", help="Path for the output .mtlx file")
    
    # Optional arguments
    parser.add_argument("--export-textures", action="store_true", 
                       help="Export texture files (default: False)")
    parser.add_argument("--texture-path", default="./textures",
                       help="Directory to export textures to (default: ./textures)")
    parser.add_argument("--version", default="1.38",
                       help="MaterialX version (default: 1.38)")
    parser.add_argument("--relative-paths", action="store_true", default=True,
                       help="Use relative paths for textures (default: True)")
    parser.add_argument("--copy-textures", action="store_true", default=True,
                       help="Copy texture files (default: True)")
    parser.add_argument("--active-uvmap", default="UVMap",
                       help="Active UV map name (default: UVMap)")
    parser.add_argument("--blender-path",
                       help="Path to Blender executable (auto-detected if not specified)")
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.blend_file):
        print(f"ERROR: Blend file not found: {args.blend_file}")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_mtlx_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Prepare export options
    options = {
        'export_textures': args.export_textures,
        'texture_path': args.texture_path,
        'materialx_version': args.version,
        'relative_paths': args.relative_paths,
        'copy_textures': args.copy_textures,
        'active_uvmap': args.active_uvmap,
    }
    
    print("=" * 60)
    print("MaterialX Command-Line Exporter")
    print("=" * 60)
    print(f"Blend file: {args.blend_file}")
    print(f"Material name: {args.material_name}")
    print(f"Output file: {args.output_mtlx_file}")
    print(f"Options: {options}")
    print("=" * 60)
    
    # Run the export
    success = run_blender_export(
        args.blend_file,
        args.material_name,
        args.output_mtlx_file,
        options,
        args.blender_path
    )
    
    if success:
        print("Export completed successfully!")
        return 0
    else:
        print("Export failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 