#!/usr/bin/env python3
"""
Debug script to test validator on specific files
"""

import bpy
import sys
import os

# Add the addon directory to the path
addon_dir = os.path.abspath("materialx_addon")
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

def debug_validation():
    """Debug validation on specific files."""
    try:
        from materialx_addon.validation.validator import MaterialXValidator
        
        print("=" * 80)
        print("🔍 Debug Validation")
        print("=" * 80)
        
        # Initialize validator
        validator = MaterialXValidator()
        
        # Load standard libraries
        if not validator.load_standard_libraries():
            print("❌ Failed to load standard MaterialX libraries")
            return
        
        # Test the two files that are still passing
        files = [
            'MaterialX_Reference/BadExamples/bad_disconnected_nodes.mtlx',
            'MaterialX_Reference/BadExamples/bad_texture_no_texcoord.mtlx'
        ]
        
        for file in files:
            print(f"\n=== {file} ===")
            try:
                # Load the document manually to inspect
                import MaterialX as mx
                document = mx.createDocument()
                mx.readFromXmlFile(document, file)
                
                print(f"Document loaded successfully")
                print(f"Number of nodes: {len(document.getNodes())}")
                
                # List all nodes
                for node in document.getNodes():
                    print(f"  Node: {node.getName()}, Type: {node.getType()}, Inputs: {len(node.getInputs())}")
                    for input_elem in node.getInputs():
                        print(f"    Input: {input_elem.getName()}, Value: '{input_elem.getValueString()}', Node: '{input_elem.getNodeName()}'")
                
                # Now run validation
                results = validator.validate_file(file, verbose=False)
                print(f"Valid: {results['valid']}")
                print(f"Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")
                print(f"Warnings: {len(results['warnings'])}")
                for warning in results['warnings']:
                    print(f"  - {warning}")
            except Exception as e:
                print(f"Exception: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_validation()
