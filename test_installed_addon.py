#!/usr/bin/env python3
"""
Test script for the installed MaterialX addon with new format
"""

import bpy
import sys
import os

def create_simple_test_material():
    """Create a simple test material for the new format."""
    # Create a new material
    material = bpy.data.materials.new(name="SimpleTest")
    material.use_nodes = True
    
    # Get the node tree
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Create RGB node for base color
    rgb = nodes.new(type='ShaderNodeRGB')
    rgb.location = (-300, 0)
    rgb.outputs[0].default_value = (0.8, 0.2, 0.2, 1.0)  # Red color
    
    # Create Value node for roughness
    roughness = nodes.new(type='ShaderNodeValue')
    roughness.location = (-300, -200)
    roughness.outputs[0].default_value = 0.5
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes
    links.new(rgb.outputs[0], principled.inputs['Base Color'])
    links.new(roughness.outputs[0], principled.inputs['Roughness'])
    links.new(principled.outputs[0], output.inputs['Surface'])
    
    return material

def test_installed_addon():
    """Test the installed MaterialX addon with new format."""
    print("Testing installed MaterialX addon...")
    
    # Check if the addon is enabled
    if 'materialx_addon' not in bpy.context.preferences.addons:
        print("MaterialX addon is not enabled. Please enable it in Blender preferences.")
        return
    
    print("Creating test material...")
    material = create_simple_test_material()
    
    # Export options
    options = {
        'active_uvmap': 'UVMap',
        'export_textures': False,
        'materialx_version': '1.39',
        'relative_paths': True,
    }
    
    print("Exporting material...")
    
    # Import the function from the installed addon
    try:
        from materialx_addon.blender_materialx_exporter import export_material_to_materialx
        success = export_material_to_materialx(material, "test_installed_addon.mtlx", options)
        
        if success:
            print("Test export successful!")
            print("Check the generated 'test_installed_addon.mtlx' file")
            
            # Read and display the generated file
            try:
                with open("test_installed_addon.mtlx", 'r') as f:
                    content = f.read()
                    print("\nGenerated MaterialX content:")
                    print("=" * 50)
                    print(content)
                    print("=" * 50)
            except Exception as e:
                print(f"Error reading generated file: {e}")
            
            # Clean up test material
            bpy.data.materials.remove(material)
        else:
            print("Test export failed!")
            
    except ImportError as e:
        print(f"Error importing from installed addon: {e}")
        print("Make sure the MaterialX addon is installed and enabled in Blender.")

if __name__ == "__main__":
    test_installed_addon() 