#!/usr/bin/env python3
"""
Debug script to check if MaterialX libraries are being loaded correctly
"""

import bpy
import sys
import os

def debug_library_loading():
    """Debug MaterialX library loading."""
    print("=" * 60)
    print("DEBUGGING MATERIALX LIBRARY LOADING")
    print("=" * 60)
    
    try:
        import MaterialX as mx
        
        # Create document
        doc = mx.createDocument()
        doc.setVersionString("1.39")
        
        print(f"✓ Created document with version: {doc.getVersionString()}")
        
        # Get search paths
        search_path = mx.getDefaultDataSearchPath()
        search_paths = []
        try:
            for i in range(search_path.size()):
                search_paths.append(search_path[i])
        except:
            search_paths = [str(search_path)]
        
        print(f"Search paths: {search_paths}")
        
        # Find library files
        library_files = []
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.mtlx'):
                            library_files.append(os.path.join(root, file))
        
        print(f"Found {len(library_files)} library files")
        
        # Show first few library files
        print("First 10 library files:")
        for i, lib_file in enumerate(library_files[:10]):
            print(f"  {i+1}. {os.path.basename(lib_file)}")
        
        # Load libraries step by step
        loaded_libraries = []
        
        # Step 1: Load standard library
        stdlib_files = [lib for lib in library_files if 'stdlib' in lib and 'defs' in lib]
        if stdlib_files:
            print(f"\nStep 1: Loading standard library...")
            try:
                stdlib_file = stdlib_files[0]
                print(f"  Loading: {os.path.basename(stdlib_file)}")
                mx.readFromXmlFile(doc, stdlib_file)
                loaded_libraries.append(os.path.basename(stdlib_file))
                print(f"  ✓ Standard library loaded")
            except Exception as e:
                print(f"  ✗ Failed to load standard library: {e}")
        else:
            print(f"\nStep 1: No standard library found")
        
        # Step 2: Load standard_surface library
        standard_surface_files = [lib for lib in library_files if 'standard_surface' in lib]
        if standard_surface_files:
            print(f"\nStep 2: Loading standard_surface library...")
            try:
                ss_file = standard_surface_files[0]
                print(f"  Loading: {os.path.basename(ss_file)}")
                mx.readFromXmlFile(doc, ss_file)
                loaded_libraries.append(os.path.basename(ss_file))
                print(f"  ✓ Standard surface library loaded")
            except Exception as e:
                print(f"  ✗ Failed to load standard_surface library: {e}")
        else:
            print(f"\nStep 2: No standard_surface library found")
        
        # Step 3: Check node definitions after loading
        print(f"\nStep 3: Checking node definitions...")
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
                print(f"  ⚠ No standard_surface node definition found")
            if not surfacematerial_found:
                print(f"  ⚠ No surfacematerial node definition found")
                
        except Exception as e:
            print(f"  ✗ Failed to check node definitions: {e}")
        
        # Step 4: Test node creation
        print(f"\nStep 4: Testing node creation...")
        try:
            # Try to create a standard_surface node
            node = doc.addNode("standard_surface", "test_surface")
            if node:
                print(f"  ✓ Successfully created standard_surface node")
            else:
                print(f"  ✗ Failed to create standard_surface node")
        except Exception as e:
            print(f"  ✗ Error creating standard_surface node: {e}")
        
        try:
            # Try to create a surfacematerial node
            node = doc.addNode("surfacematerial", "test_material")
            if node:
                print(f"  ✓ Successfully created surfacematerial node")
            else:
                print(f"  ✗ Failed to create surfacematerial node")
        except Exception as e:
            print(f"  ✗ Error creating surfacematerial node: {e}")
        
        # Step 5: Generate XML to verify
        print(f"\nStep 5: Generating XML output...")
        try:
            xml_string = mx.writeToXmlString(doc)
            print(f"  Generated XML ({len(xml_string)} characters)")
            
            if "standard_surface" in xml_string:
                print(f"  ✓ standard_surface found in XML")
            else:
                print(f"  ⚠ standard_surface not found in XML")
                
            if "surfacematerial" in xml_string:
                print(f"  ✓ surfacematerial found in XML")
            else:
                print(f"  ⚠ surfacematerial not found in XML")
                
            print(f"  First 300 characters of XML:")
            print(f"  {xml_string[:300]}...")
            
        except Exception as e:
            print(f"  ✗ Failed to generate XML: {e}")
        
        print(f"\nSummary:")
        print(f"  - Loaded {len(loaded_libraries)} libraries: {loaded_libraries}")
        print(f"  - Found {len(node_defs) if 'node_defs' in locals() else 0} node definitions")
        print(f"  - standard_surface: {'✓' if standard_surface_found else '✗'}")
        print(f"  - surfacematerial: {'✓' if surfacematerial_found else '✗'}")
        
        print("\n" + "=" * 60)
        print("LIBRARY LOADING DEBUG COMPLETED")
        print("=" * 60)
        
    except ImportError as e:
        print(f"✗ Failed to import MaterialX: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during debug: {e}")
        return False

if __name__ == "__main__":
    debug_library_loading() 