#!/usr/bin/env python3
"""
Test the get_node_definition method directly
"""

import bpy
import sys
import os

def test_node_definition():
    """Test the get_node_definition method directly."""
    print("=" * 60)
    print("TESTING NODE DEFINITION METHOD")
    print("=" * 60)
    
    try:
        # Import the MaterialX library core
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Force reload the module
        if 'materialx_addon.materialx_library_core' in sys.modules:
            del sys.modules['materialx_addon.materialx_library_core']
        if 'materialx_addon' in sys.modules:
            del sys.modules['materialx_addon']
        
        # Check the file path
        import materialx_addon.materialx_library_core
        print(f"DEBUG: Module file path: {materialx_addon.materialx_library_core.__file__}")
        
        from materialx_addon.materialx_library_core import MaterialXDocumentManager
        
        print("✓ MaterialX library core imported successfully")
        
        # Create a document manager
        logger = type('Logger', (), {
            'info': lambda self, msg: print(f"INFO: {msg}"),
            'error': lambda self, msg: print(f"ERROR: {msg}"),
            'warning': lambda self, msg: print(f"WARNING: {msg}"),
            'debug': lambda self, msg: print(f"DEBUG: {msg}")
        })()
        
        doc_manager = MaterialXDocumentManager(logger, version="1.39")
        print("✓ Document manager created")
        
        # Create a document
        doc = doc_manager.create_document()
        print(f"✓ Document created with {len(doc.getNodeDefs())} node definitions")
        
        # Test node definition lookup
        print("\nTesting node definition lookup...")
        node_def = doc_manager.get_node_definition("standard_surface", "surfaceshader")
        if node_def:
            print(f"✓ Found standard_surface node definition: {node_def.getName()}")
        else:
            print("✗ No standard_surface node definition found")
        
        node_def = doc_manager.get_node_definition("surfacematerial", "material")
        if node_def:
            print(f"✓ Found surfacematerial node definition: {node_def.getName()}")
        else:
            print("✗ No surfacematerial node definition found")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("NODE DEFINITION TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_node_definition() 