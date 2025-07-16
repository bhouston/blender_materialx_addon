"""
MaterialX validation system for real-time compatibility checking.

This module provides validation for materials, nodes, and objects,
plus handlers for real-time highlighting and filtering.
"""

import bpy
from bpy.app.handlers import persistent
from typing import List, Tuple, Set

class ValidationResult:
    """Stores the result of a material validation check."""
    def __init__(self, material_name: str):
        self.material_name = material_name
        self.is_compatible = True
        self.errors: List[str] = []

def is_node_type_compatible(node_type: str) -> bool:
    """
    Checks if a Blender node type is generally compatible with MaterialX.
    NOTE: This is a placeholder and will be replaced with a more robust
    check that uses the new mapping system.
    """
    # For now, we'll just check against the old incompatible list.
    # This will be updated in the exporter refactor.
    INCOMPATIBLE_BLENDER_NODES = [
        "TEX_WAVE", "TEX_MAGIC", "TEX_CHECKER", "TEX_BRICK", "TEX_GRADIENT",
        "TEX_SKY", "TEX_POINTDENSITY", "TEX_IES", "BSDF_TRANSPARENT",
        "BSDF_GLASS", "BSDF_GLOSSY", "BSDF_DIFFUSE", "BSDF_TRANSLUCENT",
        "BSDF_SUBSURFACE_SCATTERING", "BSDF_VELVET", "BSDF_TOON",
        "BSDF_ANISOTROPIC", "BSDF_HAIR", "BSDF_HAIR_PRINCIPLED",
        "VOLUME_ABSORPTION", "VOLUME_SCATTER", "VOLUME_PRINCIPLED",
        "EEVEE_SPECULAR", "AMBIENT_OCCLUSION", "HOLDOUT", "DISPLACEMENT",
        "VECTOR_DISPLACEMENT", "SCRIPT", "GROUP", "FRAME", "REROUTE"
    ]
    return node_type not in INCOMPATIBLE_BLENDER_NODES

def validate_node(node) -> bool:
    """Check if a single node is MaterialX compatible."""
    return is_node_type_compatible(node.type)

def validate_material(material) -> ValidationResult:
    """
    Validates a single Blender material for MaterialX compatibility.
    """
    result = ValidationResult(material.name)
    
    if not material.use_nodes or not material.node_tree:
        result.is_compatible = True # No nodes, no incompatibility
        return result
        
    for node in material.node_tree.nodes:
        if not validate_node(node):
            result.is_compatible = False
            result.errors.append(f"Node '{node.name}' (type: {node.type}) is not compatible with MaterialX.")
            
    return result

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
