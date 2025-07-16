"""
MaterialX importer for Blender materials.

This module handles the import of MaterialX files into Blender,
with validation and logging of unsupported MaterialX nodes.
"""

import bpy
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import mathutils
from .parser import MaterialXParser
from .builder import MaterialBuilder

def import_materialx(filepath: str, vertex_color_name: str = None):
    """
    High-level function to import a MaterialX file into Blender.

    This function orchestrates the process:
    1. Parses the .mtlx file into a structured MaterialXDocument.
    2. Iterates through the materials defined in the document.
    3. Uses the MaterialBuilder to construct a Blender material for each.

    Args:
        filepath (str): The path to the .mtlx file.
        vertex_color_name (str, optional): The name of the vertex color attribute
                                           to use. Defaults to None.

    Returns:
        list: A list of the newly created Blender materials.
    """
    # 1. Parse the MaterialX file into a data-only representation
    parser = MaterialXParser(filepath)
    doc = parser.parse()
    
    if not doc.materials:
        print("No materials found in the MaterialX document.")
        return []

    print(f"Found {len(doc.materials)} material(s) to import.")
    
    created_materials = []
    # 2. Iterate through and build each material
    for mtlx_mat in doc.materials:
        print(f"Building material: {mtlx_mat.name}")
        builder = MaterialBuilder(doc, mtlx_mat, vertex_color_name)
        bl_mat = builder.build()
        if bl_mat:
            created_materials.append(bl_mat)
            
    print(f"Successfully created {len(created_materials)} Blender material(s).")
    return created_materials
