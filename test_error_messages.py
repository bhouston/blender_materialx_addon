#!/usr/bin/env python3
"""
Test script to verify enhanced error messages for unsupported node types.
"""

import bpy
import os
import tempfile

def create_test_material_with_emission():
    """Create a material with an Emission shader to test error messages."""
    material = bpy.data.materials.new(name="TestEmission")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Emission shader (unsupported)
    emission = nodes.new(type='ShaderNodeEmission')
    emission.location = (0, 0)
    emission.inputs['Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    emission.inputs['Strength'].default_value = 5.0
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return material

def create_test_material_with_fresnel():
    """Create a material with a Fresnel node to test error messages."""
    material = bpy.data.materials.new(name="TestFresnel")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Fresnel node (unsupported)
    fresnel = nodes.new(type='ShaderNodeFresnel')
    fresnel.location = (-200, 0)
    fresnel.inputs['IOR'].default_value = 1.45
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(fresnel.outputs['Fac'], principled.inputs['Metallic'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def test_error_messages():
    """Test the enhanced error messages."""
    print("Testing enhanced error messages...")
    
    # Test 1: Material with Emission shader
    print("\n🧪 Test 1: Material with Emission shader")
    material1 = create_test_material_with_emission()
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mtlx', delete=False) as f:
        output_path = f.name
    
    try:
        # Try to export (should fail with helpful message)
        from materialx_addon import blender_materialx_exporter
        
        result = blender_materialx_exporter.export_material_to_materialx(
            material1, output_path, None, {'strict_mode': False}
        )
        
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Test 2: Material with Fresnel node
    print("\n🧪 Test 2: Material with Fresnel node")
    material2 = create_test_material_with_fresnel()
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mtlx', delete=False) as f:
        output_path2 = f.name
    
    try:
        # Try to export (should fail with helpful message)
        result2 = blender_materialx_exporter.export_material_to_materialx(
            material2, output_path2, None, {'strict_mode': False}
        )
        
        print(f"Result: {result2}")
        
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Cleanup
    os.unlink(output_path)
    os.unlink(output_path2)
    
    print("\n✅ Error message tests completed!")

if __name__ == "__main__":
    test_error_messages() 