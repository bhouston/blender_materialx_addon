#!/usr/bin/env python3
"""
Check what node definitions are available in the MaterialX library
"""

import bpy
import sys
import os

def check_node_definitions():
    """Check what node definitions are available."""
    print("=" * 60)
    print("CHECKING MATERIALX NODE DEFINITIONS")
    print("=" * 60)
    
    try:
        import MaterialX as mx
        
        # Create document and load libraries
        doc = mx.createDocument()
        doc.setVersionString("1.39")
        
        print(f"✓ Created document with version: {doc.getVersionString()}")
        
        # Get search paths
        search_path = mx.getDefaultDataSearchPath()
        
        # Convert search path to list of paths
        search_paths = []
        try:
            for i in range(search_path.size()):
                search_paths.append(search_path[i])
        except:
            search_paths = [str(search_path)]
        
        print(f"Search paths: {search_paths}")
        
        # Find all library files
        library_files = []
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.mtlx'):
                            library_files.append(os.path.join(root, file))
        
        print(f"Found {len(library_files)} library files")
        
        # Load all relevant libraries
        loaded_libraries = []
        
        # Load standard libraries
        stdlib_files = [lib for lib in library_files if 'stdlib' in lib and 'defs' in lib]
        for stdlib_file in stdlib_files[:3]:  # Load first 3 stdlib files
            try:
                print(f"Loading: {os.path.basename(stdlib_file)}")
                mx.readFromXmlFile(doc, stdlib_file)
                loaded_libraries.append(os.path.basename(stdlib_file))
            except Exception as e:
                print(f"Failed to load {os.path.basename(stdlib_file)}: {e}")
        
        # Load standard_surface libraries
        standard_surface_files = [lib for lib in library_files if 'standard_surface' in lib]
        for ss_file in standard_surface_files[:2]:  # Load first 2 standard_surface files
            try:
                print(f"Loading: {os.path.basename(ss_file)}")
                mx.readFromXmlFile(doc, ss_file)
                loaded_libraries.append(os.path.basename(ss_file))
            except Exception as e:
                print(f"Failed to load {os.path.basename(ss_file)}: {e}")
        
        # Load bxdf libraries
        bxdf_files = [lib for lib in library_files if 'bxdf' in lib and 'standard_surface' not in lib]
        for bxdf_file in bxdf_files[:3]:  # Load first 3 bxdf files
            try:
                print(f"Loading: {os.path.basename(bxdf_file)}")
                mx.readFromXmlFile(doc, bxdf_file)
                loaded_libraries.append(os.path.basename(bxdf_file))
            except Exception as e:
                print(f"Failed to load {os.path.basename(bxdf_file)}: {e}")
        
        print(f"Loaded {len(loaded_libraries)} libraries: {loaded_libraries}")
        
        # Get all node definitions
        node_defs = doc.getNodeDefs()
        print(f"\nFound {len(node_defs)} node definitions")
        
        # Categorize node definitions
        categories = {}
        surface_shaders = []
        materials = []
        other_nodes = []
        
        for node_def in node_defs:
            name = node_def.getName()
            category = node_def.getCategory()
            
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
            
            if 'surfaceshader' in category.lower():
                surface_shaders.append(name)
            elif 'material' in category.lower():
                materials.append(name)
            else:
                other_nodes.append(name)
        
        # Print categories
        print(f"\nNode definition categories:")
        for category, nodes in categories.items():
            print(f"  {category}: {len(nodes)} nodes")
        
        # Print surface shaders
        print(f"\nSurface shader nodes ({len(surface_shaders)}):")
        for node in surface_shaders[:10]:  # Show first 10
            print(f"  - {node}")
        if len(surface_shaders) > 10:
            print(f"  ... and {len(surface_shaders) - 10} more")
        
        # Print materials
        print(f"\nMaterial nodes ({len(materials)}):")
        for node in materials[:10]:  # Show first 10
            print(f"  - {node}")
        if len(materials) > 10:
            print(f"  ... and {len(materials) - 10} more")
        
        # Look for specific nodes
        print(f"\nLooking for specific nodes:")
        
        # Look for standard_surface
        standard_surface_nodes = [n for n in surface_shaders if 'standard_surface' in n.lower()]
        if standard_surface_nodes:
            print(f"  ✓ Found standard_surface nodes: {standard_surface_nodes}")
        else:
            print(f"  ✗ No standard_surface nodes found")
        
        # Look for surfacematerial
        surfacematerial_nodes = [n for n in materials if 'surfacematerial' in n.lower()]
        if surfacematerial_nodes:
            print(f"  ✓ Found surfacematerial nodes: {surfacematerial_nodes}")
        else:
            print(f"  ✗ No surfacematerial nodes found")
        
        # Test node creation
        print(f"\nTesting node creation:")
        
        # Try to create a standard_surface node
        if standard_surface_nodes:
            try:
                node = doc.addNode("standard_surface", "test_surface")
                if node:
                    print(f"  ✓ Successfully created standard_surface node")
                else:
                    print(f"  ✗ Failed to create standard_surface node")
            except Exception as e:
                print(f"  ✗ Error creating standard_surface node: {e}")
        
        # Try to create a surfacematerial node
        if surfacematerial_nodes:
            try:
                node = doc.addNode("surfacematerial", "test_material")
                if node:
                    print(f"  ✓ Successfully created surfacematerial node")
                else:
                    print(f"  ✗ Failed to create surfacematerial node")
            except Exception as e:
                print(f"  ✗ Error creating surfacematerial node: {e}")
        
        print("\n" + "=" * 60)
        print("NODE DEFINITION CHECK COMPLETED")
        print("=" * 60)
        
    except ImportError as e:
        print(f"✗ Failed to import MaterialX: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during check: {e}")
        return False

if __name__ == "__main__":
    check_node_definitions() 