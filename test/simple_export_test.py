#!/usr/bin/env python3
"""
Simple test to export a basic material and see the output
"""

import bpy
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SimpleExportTest')

def create_test_material():
    """Create a simple test material with Principled BSDF."""
    # Create a new material
    material = bpy.data.materials.new(name="TestMaterial")
    material.use_nodes = True
    
    # Clear default nodes
    nodes = material.node_tree.nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
    principled.inputs['Roughness'].default_value = 0.5
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes
    links = material.node_tree.links
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def test_export():
    """Test the MaterialX export functionality."""
    print("=" * 60)
    print("SIMPLE MATERIALX EXPORT TEST")
    print("=" * 60)
    
    # Create test material
    print("\n1. Creating test material...")
    material = create_test_material()
    print(f"✓ Created material: {material.name}")
    
    # Import the exporter
    print("\n2. Importing MaterialX exporter...")
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from materialx_addon.blender_materialx_exporter import MaterialXExporter
        print("✓ MaterialX exporter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import exporter: {e}")
        return False
    
    # Create exporter instance
    print("\n3. Creating exporter instance...")
    try:
        exporter = MaterialXExporter()
        print("✓ Exporter instance created")
    except Exception as e:
        print(f"✗ Failed to create exporter: {e}")
        return False
    
    # Create temporary output file
    print("\n4. Creating output file...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.mtlx', delete=False) as tmp_file:
            output_path = tmp_file.name
        print(f"✓ Output file: {output_path}")
    except Exception as e:
        print(f"✗ Failed to create output file: {e}")
        return False
    
    # Export the material
    print("\n5. Exporting material...")
    try:
        result = exporter.export_material_to_materialx(material, output_path, options={})
        print(f"✓ Export result: {result}")
    except Exception as e:
        print(f"✗ Export failed: {e}")
        return False
    
    # Check the output file
    print("\n6. Checking output file...")
    try:
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                content = f.read()
            print(f"✓ File exists, size: {len(content)} characters")
            print("  First 500 characters:")
            print(f"  {content[:500]}...")
            
            if "<?xml" in content:
                print("  ✓ XML header found")
            else:
                print("  ⚠ XML header not found")
                
            if "materialx" in content:
                print("  ✓ MaterialX root element found")
            else:
                print("  ⚠ MaterialX root element not found")
                
            if "standard_surface" in content:
                print("  ✓ standard_surface node found")
            else:
                print("  ⚠ standard_surface node not found")
                
            if "surfacematerial" in content:
                print("  ✓ surfacematerial node found")
            else:
                print("  ⚠ surfacematerial node not found")
        else:
            print("✗ Output file does not exist")
            return False
    except Exception as e:
        print(f"✗ Failed to check output file: {e}")
        return False
    
    # Clean up
    print("\n7. Cleaning up...")
    try:
        os.unlink(output_path)
        print("✓ Temporary file cleaned up")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("SIMPLE EXPORT TEST COMPLETED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_export() 