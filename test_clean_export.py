import bpy
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestExport')

# Create a simple test material
material = bpy.data.materials.new(name='TestMaterial')
material.use_nodes = True
nodes = material.node_tree.nodes
links = material.node_tree.links

# Clear default nodes
nodes.clear()

# Create a simple Principled BSDF
principled = nodes.new(type='ShaderNodeBsdfPrincipled')
principled.location = (0, 0)
principled.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)

# Create Material Output
output = nodes.new(type='ShaderNodeOutputMaterial')
output.location = (300, 0)

# Connect
links.new(principled.outputs['BSDF'], output.inputs['Surface'])

# Test export
try:
    from materialx_addon import blender_materialx_exporter
    
    # Export options
    options = {
        'export_textures': False,
        'copy_textures': False,
        'relative_paths': True,
        'optimize_document': True,
        'advanced_validation': True
    }
    
    # Export the material
    output_path = 'test_output_mtlx/TestMaterial_Clean.mtlx'
    print(f'Exporting to: {output_path}')
    
    result = blender_materialx_exporter.export_material_to_materialx(
        material, output_path, logger, options
    )
    
    print(f'Export result: {result}')
    
    if result['success']:
        print(f'✓ Export successful: {output_path}')
        
        # Check if xi:include lines are present
        with open(output_path, 'r') as f:
            content = f.read()
            if '<xi:include' in content:
                print('✗ xi:include lines are still present')
                # Show first few lines
                lines = content.split('\n')
                for i, line in enumerate(lines[:10]):
                    print(f'{i+1}: {line}')
            else:
                print('✓ No xi:include lines found - document is clean!')
                # Show first few lines of clean document
                lines = content.split('\n')
                for i, line in enumerate(lines[:10]):
                    print(f'{i+1}: {line}')
    else:
        print(f'✗ Export failed: {result.get("error", "Unknown error")}')
        
except Exception as e:
    print(f'✗ Export exception: {e}')
    import traceback
    traceback.print_exc()
