#!/usr/bin/env python3
"""
Test the MaterialX exporter directly to debug the issue
"""

import bpy
import sys
import os

def test_exporter_direct():
    """Test the MaterialX exporter directly."""
    print("=" * 60)
    print("TESTING MATERIALX EXPORTER DIRECTLY")
    print("=" * 60)
    
    try:
        # Import the MaterialX exporter
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from materialx_addon.blender_materialx_exporter import MaterialXExporter
        
        print("✓ MaterialX exporter imported successfully")
        
        # Create a simple test material
        material = bpy.data.materials.new(name="TestMaterial")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        
        # Create Principled BSDF
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        principled.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
        
        print("✓ Test material created")
        
        # Create exporter
        logger = type('Logger', (), {
            'info': lambda self, msg: print(f"INFO: {msg}"),
            'error': lambda self, msg: print(f"ERROR: {msg}"),
            'warning': lambda self, msg: print(f"WARNING: {msg}"),
            'debug': lambda self, msg: print(f"DEBUG: {msg}")
        })()
        
        exporter = MaterialXExporter(material, "/tmp/test.mtlx", logger, options={"materialx_version": "1.39"})
        print("✓ Exporter created")
        
        # Run the export to create the builder
        print("\nRunning export to create builder...")
        result = exporter.export()
        print(f"✓ Export completed: {result['success']}")
        
        if exporter.builder:
            print("✓ Builder created")
            
            # Test node definition lookup
            print("\nTesting node definition lookup...")
            
            # First, let's see what node definitions are available
            doc = exporter.builder.library_builder.doc_manager.document
            all_node_defs = doc.getNodeDefs()
            print(f"Total node definitions in document: {len(all_node_defs)}")
            
            # Look for standard_surface node definitions
            standard_surface_defs = [nd for nd in all_node_defs if "standard_surface" in nd.getType()]
            print(f"Standard surface node definitions found: {len(standard_surface_defs)}")
            for nd in standard_surface_defs[:5]:  # Show first 5
                print(f"  - {nd.getName()}: {nd.getType()} (category: {nd.getCategory()})")
            
            # Look for surfacematerial node definitions
            surfacematerial_defs = [nd for nd in all_node_defs if "surfacematerial" in nd.getType()]
            print(f"Surface material node definitions found: {len(surfacematerial_defs)}")
            for nd in surfacematerial_defs[:5]:  # Show first 5
                print(f"  - {nd.getName()}: {nd.getType()} (category: {nd.getCategory()})")
            
            # Let's see what node types are actually available
            print("\nSample of available node types:")
            node_types = set()
            for nd in all_node_defs[:20]:  # Look at first 20
                node_types.add(nd.getType())
            for node_type in sorted(list(node_types)):
                print(f"  - {node_type}")
            
            # Look for any node definitions with "surface" in the name
            surface_defs = [nd for nd in all_node_defs if "surface" in nd.getName().lower()]
            print(f"\nNode definitions with 'surface' in name: {len(surface_defs)}")
            for nd in surface_defs[:10]:  # Show first 10
                print(f"  - {nd.getName()}: {nd.getType()} (category: {nd.getCategory()})")
            
            # Now test the get_node_definition method
            node_def = exporter.builder.library_builder.doc_manager.get_node_definition("standard_surface", "surfaceshader")
            if node_def:
                print(f"✓ Found standard_surface node definition: {node_def.getName()}")
            else:
                print("✗ No standard_surface node definition found")
            
            node_def = exporter.builder.library_builder.doc_manager.get_node_definition("surfacematerial", "material")
            if node_def:
                print(f"✓ Found surfacematerial node definition: {node_def.getName()}")
            else:
                print("✗ No surfacematerial node definition found")
            
            # Test document creation
            print("\nTesting document creation...")
            doc = exporter.builder.library_builder.doc_manager.create_document()
            print(f"✓ Document created with {len(doc.getNodeDefs())} node definitions")
            
            # Test XML generation
            print("\nTesting XML generation...")
            xml_content = exporter.builder.to_string()
            print(f"✓ Generated XML ({len(xml_content)} characters)")
            print(f"First 300 characters: {xml_content[:300]}")
            
            # Check for required nodes in XML
            if "standard_surface" in xml_content:
                print("✓ standard_surface found in XML")
            else:
                print("✗ standard_surface not found in XML")
            
            if "surfacematerial" in xml_content:
                print("✓ surfacematerial found in XML")
            else:
                print("✗ surfacematerial not found in XML")
        else:
            print("✗ Builder not created")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DIRECT EXPORTER TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_exporter_direct() 