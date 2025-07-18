"""
MaterialX validation system for real-time compatibility checking.

This module provides validation for materials, nodes, and objects,
plus handlers for real-time highlighting and filtering.
"""

import bpy
from bpy.app.handlers import persistent
from typing import List, Tuple, Set

from . import mapping

class ValidationResult:
    """Stores the result of a material validation check."""
    def __init__(self, material_name: str):
        self.material_name = material_name
        self.is_compatible = True
        self.errors: List[str] = []
        self.incompatible_nodes: List[Tuple[str, str]] = []

def is_node_type_compatible(node_bl_idname: str) -> bool:
    """
    Checks if a Blender node type is compatible with MaterialX by checking
    if it exists in the Blender-to-MaterialX mapping.
    """
    return mapping.get_materialx_equivalent(node_bl_idname) is not None

def validate_node(node) -> bool:
    """Check if a single node is MaterialX compatible."""
    return is_node_type_compatible(node.bl_idname)

def validate_material(material) -> ValidationResult:
    """
    Validates a single Blender material for MaterialX compatibility.
    """
    result = ValidationResult(material.name)
    
    if not material.use_nodes or not material.node_tree:
        result.is_compatible = True # No nodes, no incompatibility
        return result

    # Find the output node
    output_node = None
    for n in material.node_tree.nodes:
        if n.type == 'OUTPUT_MATERIAL' and n.is_active_output:
            output_node = n
            break
    
    if not output_node:
        result.is_compatible = False
        result.errors.append("No active 'Material Output' node found.")
        return result

    # Check 1: Ensure the main surface shader is a Principled BSDF
    surface_input = output_node.inputs.get("Surface")
    if not surface_input.is_linked:
        result.is_compatible = False
        result.errors.append("'Material Output' node is not connected to a shader.")
    else:
        root_shader_node = surface_input.links[0].from_node
        if root_shader_node.bl_idname != 'ShaderNodeBsdfPrincipled':
            result.is_compatible = False
            result.errors.append(f"Root shader is '{root_shader_node.bl_idname}', but must be 'Principled BSDF'.")
            result.incompatible_nodes.append((root_shader_node.name, root_shader_node.type))

    # Check 2: Find all other incompatible nodes in the tree
    for node in material.node_tree.nodes:
        if not validate_node(node):
            result.is_compatible = False
            error_msg = f"Node '{node.name}' (type: {node.type}) is not compatible."
            if error_msg not in result.errors:
                result.errors.append(error_msg)
                result.incompatible_nodes.append((node.name, node.type))
            
    return result

def is_material_compatible(material) -> bool:
    """A quick check if a material is compatible, for UI purposes."""
    return validate_material(material).is_compatible

def get_incompatible_nodes(material) -> List[Tuple[str, str]]:
    """Gets a list of incompatible node names and types for a material."""
    return validate_material(material).incompatible_nodes

def validate_scene():
    """
    Validates all materials in the current scene.
    """
    print("=== MaterialX Scene Validation ===")
    overall_compatible = True
    for material in bpy.data.materials:
        result = validate_material(material)
        if not result.is_compatible:
            overall_compatible = False
            print(f"✗ Material '{material.name}' has issues:")
            for error in result.errors:
                print(f"    {error}")
        else:
            print(f"✓ Material '{material.name}' is compatible.")
    
    if overall_compatible:
        print("\nAll materials in the scene are compatible with MaterialX.")
    else:
        print("\nSome materials have compatibility issues.")
        
    print("=== Validation Complete ===")

def get_incompatible_nodes_in_scene() -> Set[str]:
    """
    Returns a set of all node types in the scene that are incompatible.
    """
    incompatible_types = set()
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if not is_node_type_compatible(node.type):
                incompatible_types.add(node.type)
    return incompatible_types

def highlight_incompatible_nodes():
    """
    Highlights incompatible nodes in all visible node trees.
    """
    # This is a UI feature and might be better in a separate module,
    # but is here for simplicity for now.
    pass
