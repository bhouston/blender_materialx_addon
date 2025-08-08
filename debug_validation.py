#!/usr/bin/env python3
"""
Debug script to test MaterialX node creation and surface shader detection
"""

import sys
import os

# Add the materialx_addon to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'materialx_addon'))

try:
    import MaterialX as mx
    from materialx_addon.mappers.principled_mapper import PrincipledBSDFMapper
    from materialx_addon.utils.logging_utils import MaterialXLogger
    
    def test_materialx_node_creation():
        """Test creating a MaterialX standard_surface node."""
        print("Testing MaterialX node creation...")
        
        # Create a document
        document = mx.createDocument()
        document.setName("test_document")
        
        # Create a standard_surface node
        node = document.addNode("test_surface", "standard_surface", "surfaceshader")
        
        print(f"Node name: {node.getName()}")
        print(f"Node type: {node.getType()}")
        print(f"Node category: {node.getCategory()}")
        
        # Test the type check
        print(f"Is standard_surface: {node.getType() == 'standard_surface'}")
        
        # List all nodes in the document
        print("\nAll nodes in document:")
        for doc_node in document.getNodes():
            print(f"  - {doc_node.getName()} (type: {doc_node.getType()}, category: {doc_node.getCategory()})")
        
        return node
    
    def test_principled_mapper():
        """Test the Principled BSDF mapper."""
        print("\nTesting Principled BSDF mapper...")
        
        # Create a document
        document = mx.createDocument()
        document.setName("test_document")
        
        # Create a logger
        logger = MaterialXLogger("TestMapper")
        
        # Create the mapper
        mapper = PrincipledBSDFMapper(logger)
        
        # Create a mock Blender node (we'll simulate it)
        class MockNode:
            def __init__(self):
                self.name = "Principled BSDF"
                self.type = "BSDF_PRINCIPLED"
                self.bl_idname = "ShaderNodeBsdfPrincipled"
                self.inputs = {}
                self.outputs = {}
        
        mock_node = MockNode()
        
        # Test if the mapper can handle this node
        print(f"Can map node: {mapper.can_map_node(mock_node)}")
        
        # Map the node
        exported_nodes = {}
        materialx_node = mapper.map_node(mock_node, document, exported_nodes)
        
        print(f"Created MaterialX node: {materialx_node.getName()}")
        print(f"MaterialX node type: {materialx_node.getType()}")
        print(f"MaterialX node category: {materialx_node.getCategory()}")
        
        # Test the type check
        print(f"Is standard_surface: {materialx_node.getType() == 'standard_surface'}")
        
        # List all nodes in the document
        print("\nAll nodes in document:")
        for doc_node in document.getNodes():
            print(f"  - {doc_node.getName()} (type: {doc_node.getType()}, category: {doc_node.getCategory()})")
        
        return materialx_node
    
    def test_surface_shader_detection():
        """Test surface shader detection logic."""
        print("\nTesting surface shader detection...")
        
        # Create a document with a standard_surface node
        document = mx.createDocument()
        document.setName("test_document")
        
        # Create a standard_surface node
        surface_node = document.addNode("test_surface", "standard_surface", "surfaceshader")
        
        # Simulate the exported_nodes dictionary
        exported_nodes = {
            "Principled BSDF": "test_surface"
        }
        
        # Test the detection logic
        print("Testing detection logic:")
        for node_name, materialx_node_name in exported_nodes.items():
            print(f"  Checking: {node_name} -> {materialx_node_name}")
            materialx_node = document.getNode(materialx_node_name)
            if materialx_node:
                print(f"    Found node: {materialx_node.getName()}")
                print(f"    Node type: {materialx_node.getType()}")
                print(f"    Is standard_surface: {materialx_node.getType() == 'standard_surface'}")
                if materialx_node.getType() == "standard_surface":
                    print(f"    ✓ Found surface shader: {materialx_node.getName()}")
                    return materialx_node
            else:
                print(f"    ✗ Node not found: {materialx_node_name}")
        
        print("    ✗ No surface shader found")
        return None
    
    if __name__ == "__main__":
        print("=== MaterialX Node Creation Test ===")
        test_materialx_node_creation()
        
        print("\n=== Principled BSDF Mapper Test ===")
        test_principled_mapper()
        
        print("\n=== Surface Shader Detection Test ===")
        test_surface_shader_detection()
        
        print("\n=== Test Complete ===")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure MaterialX is installed and the materialx_addon is in the path")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
