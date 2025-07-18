#!/usr/bin/env python3
"""
Simple test script for the MaterialX Export addon.
Run this in Blender to test the addon functionality.
"""

import bpy
import os
import tempfile

def test_addon():
    """Test the MaterialX Export addon."""
    print("=== Testing MaterialX Export Addon ===")
    
    # Test 1: Check if addon is registered
    try:
        from materialx_addon import blender_materialx_exporter
        print("✓ Addon module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import addon: {e}")
        return
    
    # Test 2: Create a test material
    material = bpy.data.materials.new(name="TestMaterial")
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
    
    print("✓ Test material created successfully")
    
    # Test 3: Export the material
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mtlx', delete=False) as tmp:
            output_path = tmp.name
        
        # Export options
        options = {
            'export_textures': False,
            'copy_textures': False,
            'relative_paths': True,
            'materialx_version': '1.38',
        }
        
        # Export the material
        success = blender_materialx_exporter.export_material_to_materialx(
            material, output_path, options
        )
        
        if success:
            print(f"✓ Material exported successfully to {output_path}")
            
            # Read and verify the exported content
            with open(output_path, 'r') as f:
                content = f.read()
                if 'standard_surface' in content and 'TestMaterial' in content:
                    print("✓ Exported MaterialX content looks correct")
                else:
                    print("✗ Exported content seems incorrect")
            
            # Clean up
            os.unlink(output_path)
        else:
            print("✗ Material export failed")
        
    except Exception as e:
        print(f"✗ Error during export: {e}")
    
    # Test 4: Test export all materials
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Export all materials
        results = blender_materialx_exporter.export_all_materials_to_materialx(
            temp_dir, options
        )
        
        if results:
            print(f"✓ Export all materials completed: {len(results)} materials processed")
        else:
            print("✗ Export all materials failed")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"✗ Error during export all: {e}")
    
    # Clean up test material
    bpy.data.materials.remove(material)
    print("✓ Test material cleaned up")
    
    print("=== Test completed ===")

if __name__ == "__main__":
    test_addon() 