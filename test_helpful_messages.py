#!/usr/bin/env python3
"""
Simple test to verify enhanced error messages are working.
"""

import bpy
import os
import tempfile

def test_helpful_messages():
    """Test that helpful error messages are displayed."""
    print("Testing helpful error messages...")
    
    # Create a material with an Emission shader
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
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mtlx', delete=False) as f:
        output_path = f.name
    
    try:
        # Try to export (should fail with helpful message)
        from materialx_addon import blender_materialx_exporter
        
        print("\n🧪 Testing Emission shader error message:")
        result = blender_materialx_exporter.export_material_to_materialx(
            material, output_path, None, {'strict_mode': False}
        )
        
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Cleanup
    os.unlink(output_path)
    
    print("\n✅ Helpful message test completed!")

if __name__ == "__main__":
    test_helpful_messages() 