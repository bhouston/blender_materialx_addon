#!/usr/bin/env python3
"""
Test MaterialX library functionality directly in Blender
"""

import bpy
import sys
import os

def test_materialx_library():
    """Test MaterialX library functionality."""
    print("=" * 60)
    print("TESTING MATERIALX LIBRARY IN BLENDER")
    print("=" * 60)
    
    # Test 1: Check if MaterialX is available
    print("\n1. Checking MaterialX library availability...")
    try:
        import MaterialX as mx
        print(f"✓ MaterialX library imported successfully")
        print(f"  MaterialX version: {mx.__version__ if hasattr(mx, '__version__') else 'Unknown'}")
    except ImportError as e:
        print(f"✗ Failed to import MaterialX: {e}")
        return False
    
    # Test 2: Create a basic MaterialX document
    print("\n2. Creating basic MaterialX document...")
    try:
        doc = mx.createDocument()
        doc.setVersionString("1.39")
        print(f"✓ Created document with version: {doc.getVersionString()}")
    except Exception as e:
        print(f"✗ Failed to create document: {e}")
        return False
    
    # Test 3: Load libraries
    print("\n3. Loading MaterialX libraries...")
    try:
        # Get default search path
        search_path = mx.getDefaultDataSearchPath()
        
        # Convert search path to list of paths
        search_paths = []
        try:
            for i in range(search_path.size()):
                search_paths.append(search_path[i])
        except:
            search_paths = [str(search_path)]
        
        print(f"  Search paths: {search_paths}")
        
        # Find library files
        library_files = []
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.mtlx'):
                            library_files.append(os.path.join(root, file))
        
        print(f"  Found {len(library_files)} library files")
        
        # Load standard libraries
        stdlib_files = [lib for lib in library_files if 'stdlib' in lib and 'defs' in lib]
        if stdlib_files:
            print(f"  Loading standard library: {os.path.basename(stdlib_files[0])}")
            mx.readFromXmlFile(doc, stdlib_files[0])
        
        # Load standard_surface library
        standard_surface_files = [lib for lib in library_files if 'standard_surface' in lib]
        if standard_surface_files:
            print(f"  Loading standard_surface library: {os.path.basename(standard_surface_files[0])}")
            mx.readFromXmlFile(doc, standard_surface_files[0])
        
        print("✓ Libraries loaded successfully")
        
    except Exception as e:
        print(f"✗ Failed to load libraries: {e}")
        return False
    
    # Test 4: Check node definitions
    print("\n4. Checking node definitions...")
    try:
        node_defs = doc.getNodeDefs()
        print(f"  Found {len(node_defs)} node definitions")
        
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
            
    except Exception as e:
        print(f"✗ Failed to check node definitions: {e}")
        return False
    
    # Test 5: Create nodes
    print("\n5. Creating test nodes...")
    try:
        # Create a standard_surface node
        standard_surface_node = doc.addNode("standard_surface", "test_surface")
        if standard_surface_node:
            print("  ✓ Created standard_surface node")
        else:
            print("  ✗ Failed to create standard_surface node")
        
        # Create a material node
        material_node = doc.addNode("surfacematerial", "test_material")
        if material_node:
            print("  ✓ Created material node")
        else:
            print("  ✗ Failed to create material node")
            
    except Exception as e:
        print(f"✗ Failed to create nodes: {e}")
        return False
    
    # Test 6: Generate XML output
    print("\n6. Generating XML output...")
    try:
        xml_string = mx.writeToXmlString(doc)
        print(f"  Generated XML ({len(xml_string)} characters)")
        print("  First 200 characters:")
        print(f"  {xml_string[:200]}...")
        
        if "standard_surface" in xml_string:
            print("  ✓ standard_surface node found in XML")
        else:
            print("  ⚠ standard_surface node not found in XML")
            
        if "surfacematerial" in xml_string:
            print("  ✓ surfacematerial node found in XML")
        else:
            print("  ⚠ surfacematerial node not found in XML")
            
    except Exception as e:
        print(f"✗ Failed to generate XML: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("MATERIALX LIBRARY TEST COMPLETED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_materialx_library() 