#!/usr/bin/env python3
"""
Test the MaterialX library core directly
"""

import bpy
import sys
import os

def test_materialx_core():
    """Test the MaterialX library core directly."""
    print("=" * 60)
    print("TESTING MATERIALX LIBRARY CORE")
    print("=" * 60)
    
    try:
        # Import the MaterialX library core
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from materialx_addon.materialx_library_core import MaterialXDocumentManager
        
        print("✓ MaterialX library core imported successfully")
        
        # Create a simple logger
        class SimpleLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def debug(self, msg): print(f"DEBUG: {msg}")
        
        # Create a document manager
        doc_manager = MaterialXDocumentManager(SimpleLogger(), version="1.39")
        print("✓ Document manager created")
        
        # Create a document
        doc = doc_manager.create_document()
        print("✓ Document created")
        
        # Check node definitions
        node_defs = doc.getNodeDefs()
        print(f"✓ Document has {len(node_defs)} node definitions")
        
        # Look for specific node definitions
        standard_surface_found = False
        surfacematerial_found = False
        
        for node_def in node_defs:
            name = node_def.getName()
            if 'standard_surface' in name:
                print(f"  ✓ Found standard_surface: {name}")
                standard_surface_found = True
            elif 'surfacematerial' in name:
                print(f"  ✓ Found surfacematerial: {name}")
                surfacematerial_found = True
        
        if not standard_surface_found:
            print("  ⚠ No standard_surface node definition found")
        if not surfacematerial_found:
            print("  ⚠ No surfacematerial node definition found")
        
        # Test node creation
        print("\nTesting node creation...")
        try:
            # Try to create a standard_surface node
            node = doc.addNode("standard_surface", "test_surface")
            if node:
                print("  ✓ Successfully created standard_surface node")
            else:
                print("  ✗ Failed to create standard_surface node")
        except Exception as e:
            print(f"  ✗ Error creating standard_surface node: {e}")
        
        try:
            # Try to create a surfacematerial node
            node = doc.addNode("surfacematerial", "test_material")
            if node:
                print("  ✓ Successfully created surfacematerial node")
            else:
                print("  ✗ Failed to create surfacematerial node")
        except Exception as e:
            print(f"  ✗ Error creating surfacematerial node: {e}")
        
        # Generate XML
        print("\nGenerating XML...")
        try:
            import MaterialX as mx
            xml_string = mx.writeToXmlString(doc)
            print(f"  ✓ Generated XML ({len(xml_string)} characters)")
            
            if "standard_surface" in xml_string:
                print("  ✓ standard_surface found in XML")
            else:
                print("  ⚠ standard_surface not found in XML")
                
            if "surfacematerial" in xml_string:
                print("  ✓ surfacematerial found in XML")
            else:
                print("  ⚠ surfacematerial not found in XML")
                
            print("  First 300 characters of XML:")
            print(f"  {xml_string[:300]}...")
            
        except Exception as e:
            print(f"  ✗ Error generating XML: {e}")
        
        print("\n" + "=" * 60)
        print("MATERIALX LIBRARY CORE TEST COMPLETED")
        print("=" * 60)
        
    except ImportError as e:
        print(f"✗ Failed to import MaterialX library core: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False

if __name__ == "__main__":
    test_materialx_core() 