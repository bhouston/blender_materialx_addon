#!/usr/bin/env python3
"""
MaterialX NodeDef Introspection Script

This script runs within Blender to introspect MaterialX NodeDef objects
and understand their available methods and attributes.
"""

import bpy
import sys
import os

# Add the MaterialX library path to sys.path
materialx_path = os.path.join(os.path.dirname(__file__), 'MaterialX_Reference', 'python')
if materialx_path not in sys.path:
    sys.path.insert(0, materialx_path)

try:
    import MaterialX as mx
    print("✓ MaterialX library imported successfully")
except ImportError as e:
    print(f"✗ Failed to import MaterialX: {e}")
    sys.exit(1)

def introspect_nodedef():
    """Introspect a MaterialX NodeDef object to understand its structure."""
    
    print("\n" + "="*60)
    print("MATERIALX NODEDEF INTROSPECTION")
    print("="*60)
    
    # Create a document
    doc = mx.createDocument()
    
    # Try to create a simple node definition
    try:
        # Create a basic node definition
        nodedef = doc.addNodeDef("ND_test_node", "color3", "test_node")
        print(f"✓ Created test NodeDef: {nodedef.getName()}")
        
        # Introspect the NodeDef object
        print(f"\nNodeDef type: {type(nodedef)}")
        print(f"NodeDef class: {nodedef.__class__}")
        print(f"NodeDef module: {nodedef.__class__.__module__}")
        
        # Get all attributes
        print(f"\n--- NodeDef Attributes ---")
        for attr in dir(nodedef):
            if not attr.startswith('_'):
                try:
                    value = getattr(nodedef, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except Exception as e:
                    print(f"  {attr}: <error accessing: {e}>")
        
        # Get all methods
        print(f"\n--- NodeDef Methods ---")
        for attr in dir(nodedef):
            if not attr.startswith('_') and callable(getattr(nodedef, attr)):
                print(f"  {attr}()")
        
        # Test specific methods we're interested in
        print(f"\n--- Testing Specific Methods ---")
        
        # Test setImplementationName
        try:
            nodedef.setImplementationName("IM_test")
            print("✓ setImplementationName() works")
        except Exception as e:
            print(f"✗ setImplementationName() failed: {e}")
        
        # Test setAttribute
        try:
            nodedef.setAttribute("implname", "IM_test")
            print("✓ setAttribute('implname', ...) works")
        except Exception as e:
            print(f"✗ setAttribute('implname', ...) failed: {e}")
        
        # Test getAttribute
        try:
            value = nodedef.getAttribute("implname")
            print(f"✓ getAttribute('implname') works: {value}")
        except Exception as e:
            print(f"✗ getAttribute('implname') failed: {e}")
        
        # Test addInput
        try:
            input_elem = nodedef.addInput("test_input", "color3")
            print(f"✓ addInput() works: {input_elem}")
        except Exception as e:
            print(f"✗ addInput() failed: {e}")
        
        # Test addOutput
        try:
            output_elem = nodedef.addOutput("test_output", "color3")
            print(f"✓ addOutput() works: {output_elem}")
        except Exception as e:
            print(f"✗ addOutput() failed: {e}")
        
        # Test setNodeDefString
        try:
            nodedef.setNodeDefString("ND_test_node")
            print("✓ setNodeDefString() works")
        except Exception as e:
            print(f"✗ setNodeDefString() failed: {e}")
        
        # Test getNodeDefString
        try:
            value = nodedef.getNodeDefString()
            print(f"✓ getNodeDefString() works: {value}")
        except Exception as e:
            print(f"✗ getNodeDefString() failed: {e}")
        
        # Test setType
        try:
            nodedef.setType("color3")
            print("✓ setType() works")
        except Exception as e:
            print(f"✗ setType() failed: {e}")
        
        # Test getType
        try:
            value = nodedef.getType()
            print(f"✓ getType() works: {value}")
        except Exception as e:
            print(f"✗ getType() failed: {e}")
        
        # Test setCategory
        try:
            nodedef.setCategory("test_category")
            print("✓ setCategory() works")
        except Exception as e:
            print(f"✗ setCategory() failed: {e}")
        
        # Test getCategory
        try:
            value = nodedef.getCategory()
            print(f"✓ getCategory() works: {value}")
        except Exception as e:
            print(f"✗ getCategory() failed: {e}")
        
        # Test setNodeGroup
        try:
            nodedef.setNodeGroup("test_group")
            print("✓ setNodeGroup() works")
        except Exception as e:
            print(f"✗ setNodeGroup() failed: {e}")
        
        # Test getNodeGroup
        try:
            value = nodedef.getNodeGroup()
            print(f"✓ getNodeGroup() works: {value}")
        except Exception as e:
            print(f"✗ getNodeGroup() failed: {e}")
        
        # Test setName
        try:
            nodedef.setName("ND_new_name")
            print("✓ setName() works")
        except Exception as e:
            print(f"✗ setName() failed: {e}")
        
        # Test getName
        try:
            value = nodedef.getName()
            print(f"✓ getName() works: {value}")
        except Exception as e:
            print(f"✗ getName() failed: {e}")
        
        # Test getInput
        try:
            input_elem = nodedef.getInput("test_input")
            print(f"✓ getInput() works: {input_elem}")
        except Exception as e:
            print(f"✗ getInput() failed: {e}")
        
        # Test getOutput
        try:
            output_elem = nodedef.getOutput("test_output")
            print(f"✓ getOutput() works: {output_elem}")
        except Exception as e:
            print(f"✗ getOutput() failed: {e}")
        
        # Test getInputs
        try:
            inputs = nodedef.getInputs()
            print(f"✓ getInputs() works: {len(inputs)} inputs")
        except Exception as e:
            print(f"✗ getInputs() failed: {e}")
        
        # Test getOutputs
        try:
            outputs = nodedef.getOutputs()
            print(f"✓ getOutputs() works: {len(outputs)} outputs")
        except Exception as e:
            print(f"✗ getOutputs() failed: {e}")
        
        # Test inheritance
        print(f"\n--- Inheritance Chain ---")
        current_class = nodedef.__class__
        while current_class:
            print(f"  {current_class.__name__} ({current_class.__module__})")
            current_class = current_class.__bases__[0] if current_class.__bases__ else None
        
        # Test if it's an Element
        print(f"\n--- Element Compatibility ---")
        print(f"Is Element: {isinstance(nodedef, mx.Element)}")
        print(f"Is NodeDef: {isinstance(nodedef, mx.NodeDef)}")
        
        # Test Element methods
        if isinstance(nodedef, mx.Element):
            try:
                parent = nodedef.getParent()
                print(f"✓ getParent() works: {parent}")
            except Exception as e:
                print(f"✗ getParent() failed: {e}")
            
            try:
                children = nodedef.getChildren()
                print(f"✓ getChildren() works: {len(children)} children")
            except Exception as e:
                print(f"✗ getChildren() failed: {e}")
        
    except Exception as e:
        print(f"✗ Failed to create or introspect NodeDef: {e}")
        import traceback
        traceback.print_exc()

def introspect_nodegraph():
    """Introspect a MaterialX NodeGraph object."""
    
    print(f"\n" + "="*60)
    print("MATERIALX NODEGRAPH INTROSPECTION")
    print("="*60)
    
    doc = mx.createDocument()
    
    try:
        # Create a nodegraph
        nodegraph = doc.addNodeGraph("IM_test_implementation")
        print(f"✓ Created test NodeGraph: {nodegraph.getName()}")
        
        # Test NodeGraph methods
        print(f"\n--- NodeGraph Methods ---")
        
        # Test addNode
        try:
            node = nodegraph.addNode("mix", "test_mix")
            print(f"✓ addNode() works: {node}")
        except Exception as e:
            print(f"✗ addNode() failed: {e}")
        
        # Test addOutput
        try:
            output = nodegraph.addOutput("out", "color3")
            print(f"✓ addOutput() works: {output}")
        except Exception as e:
            print(f"✗ addOutput() failed: {e}")
        
        # Test setNodeName
        try:
            output.setNodeName("test_mix")
            print("✓ setNodeName() works")
        except Exception as e:
            print(f"✗ setNodeName() failed: {e}")
        
        # Test getNodeName
        try:
            value = output.getNodeName()
            print(f"✓ getNodeName() works: {value}")
        except Exception as e:
            print(f"✗ getNodeName() failed: {e}")
        
        # Test setConnectedNode
        try:
            output.setConnectedNode("test_mix")
            print("✓ setConnectedNode() works")
        except Exception as e:
            print(f"✗ setConnectedNode() failed: {e}")
        
        # Test getConnectedNode
        try:
            value = output.getConnectedNode()
            print(f"✓ getConnectedNode() works: {value}")
        except Exception as e:
            print(f"✗ getConnectedNode() failed: {e}")
        
    except Exception as e:
        print(f"✗ Failed to create or introspect NodeGraph: {e}")
        import traceback
        traceback.print_exc()

def introspect_node():
    """Introspect a MaterialX Node object."""
    
    print(f"\n" + "="*60)
    print("MATERIALX NODE INTROSPECTION")
    print("="*60)
    
    doc = mx.createDocument()
    
    try:
        # Create a node
        node = doc.addNode("mix", "test_mix")
        print(f"✓ Created test Node: {node.getName()}")
        
        # Test Node methods
        print(f"\n--- Node Methods ---")
        
        # Test addInput
        try:
            input_elem = node.addInput("fg", "color3")
            print(f"✓ addInput() works: {input_elem}")
        except Exception as e:
            print(f"✗ addInput() failed: {e}")
        
        # Test setNodeName
        try:
            input_elem.setNodeName("source_node")
            print("✓ setNodeName() works")
        except Exception as e:
            print(f"✗ setNodeName() failed: {e}")
        
        # Test getNodeName
        try:
            value = input_elem.getNodeName()
            print(f"✓ getNodeName() works: {value}")
        except Exception as e:
            print(f"✗ getNodeName() failed: {e}")
        
        # Test setConnectedNode
        try:
            input_elem.setConnectedNode("source_node")
            print("✓ setConnectedNode() works")
        except Exception as e:
            print(f"✗ setConnectedNode() failed: {e}")
        
        # Test getConnectedNode
        try:
            value = input_elem.getConnectedNode()
            print(f"✓ getConnectedNode() works: {value}")
        except Exception as e:
            print(f"✗ getConnectedNode() failed: {e}")
        
        # Test setValueString
        try:
            input_elem.setValueString("1,0,0")
            print("✓ setValueString() works")
        except Exception as e:
            print(f"✗ setValueString() failed: {e}")
        
        # Test getValueString
        try:
            value = input_elem.getValueString()
            print(f"✓ getValueString() works: {value}")
        except Exception as e:
            print(f"✗ getValueString() failed: {e}")
        
        # Test setType
        try:
            node.setType("color3")
            print("✓ setType() works")
        except Exception as e:
            print(f"✗ setType() failed: {e}")
        
        # Test getType
        try:
            value = node.getType()
            print(f"✓ getType() works: {value}")
        except Exception as e:
            print(f"✗ getType() failed: {e}")
        
    except Exception as e:
        print(f"✗ Failed to create or introspect Node: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run all introspection tests."""
    
    print("MaterialX Introspection Script")
    print("Running within Blender...")
    
    # Check MaterialX version
    try:
        version = mx.getVersionString()
        print(f"MaterialX version: {version}")
    except Exception as e:
        print(f"Could not get MaterialX version: {e}")
    
    # Run introspection tests
    introspect_nodedef()
    introspect_nodegraph()
    introspect_node()
    
    print(f"\n" + "="*60)
    print("INTROSPECTION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
