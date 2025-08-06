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
        print(f"Default search path type: {type(search_path)}")
        print(f"Default search path: {search_path}")
        
        # Try to convert search path to list
        search_paths = []
        try:
            # Try different ways to access the search path
            if hasattr(search_path, 'size'):
                print(f"Search path has size() method, size: {search_path.size()}")
                for i in range(search_path.size()):
                    search_paths.append(str(search_path[i]))
            elif hasattr(search_path, '__iter__'):
                print("Search path is iterable")
                for path in search_path:
                    search_paths.append(str(path))
            else:
                print("Search path is not iterable, converting to string")
                search_paths = [str(search_path)]
        except Exception as e:
            print(f"Error converting search path: {e}")
            search_paths = [str(search_path)]
        
        print(f"Converted search paths: {search_paths}")
        
        # Try to find library files manually
        library_files = []
        for path in search_paths:
            print(f"Checking path: {path}")
            if os.path.exists(path):
                print(f"  Path exists: {path}")
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.mtlx'):
                            full_path = os.path.join(root, file)
                            library_files.append(full_path)
                            print(f"  Found library: {file}")
            else:
                print(f"  Path does not exist: {path}")
        
        print(f"Found {len(library_files)} library files manually")
        
        # Try to load libraries using MaterialX API
        print(f"\nTrying to load libraries using MaterialX API...")
        
        # Method 1: Try loadLibraries
        try:
            print("Method 1: Using loadLibraries...")
            lib_folders = mx.getDefaultDataLibraryFolders()
            print(f"Library folders: {lib_folders}")
            loaded_files = mx.loadLibraries(lib_folders, search_path, doc)
            print(f"Loaded {len(loaded_files)} files using loadLibraries")
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: Try reading individual files
        try:
            print("Method 2: Reading individual files...")
            loaded_count = 0
            for lib_file in library_files[:5]:  # Try first 5 files
                try:
                    print(f"  Reading: {os.path.basename(lib_file)}")
                    mx.readFromXmlFile(doc, lib_file)
                    loaded_count += 1
                except Exception as e:
                    print(f"  Failed to read {os.path.basename(lib_file)}: {e}")
            print(f"Loaded {loaded_count} files using readFromXmlFile")
        except Exception as e:
            print(f"Method 2 failed: {e}")
        
        # Test importLibrary method
        print(f"\nTesting importLibrary method...")
        try:
            # Create a separate libraries document
            libraries_doc = mx.createDocument()
            lib_folders = mx.getDefaultDataLibraryFolders()
            loaded_files = mx.loadLibraries(lib_folders, search_path, libraries_doc)
            print(f"Loaded {len(loaded_files)} files into libraries document")
            
            # Check node definitions in libraries document
            lib_node_defs = libraries_doc.getNodeDefs()
            print(f"Libraries document has {len(lib_node_defs)} node definitions")
            
            # Create working document
            working_doc = mx.createDocument()
            print(f"Working document has {len(working_doc.getNodeDefs())} node definitions before import")
            
            # Import libraries into working document
            working_doc.importLibrary(libraries_doc)
            print(f"Working document has {len(working_doc.getNodeDefs())} node definitions after import")
            
            # Check for specific node definitions
            standard_surface_found = False
            surfacematerial_found = False
            
            for node_def in working_doc.getNodeDefs():
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
            print(f"importLibrary test failed: {e}")
        
        # Check node definitions after loading
        print(f"\nChecking node definitions after loading...")
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
        
        # Test node creation
        print(f"\nTesting node creation...")
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
        
        # Generate XML to verify
        print(f"\nGenerating XML output...")
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
        print(f"  - Found {len(library_files)} library files manually")
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