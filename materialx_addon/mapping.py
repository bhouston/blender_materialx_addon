"""
This module contains the mapping between MaterialX nodes and Blender nodes,
as well as functions to handle parameter and property conversions.
"""

import bpy

# A dictionary mapping MaterialX node categories to Blender node types.
# This is the primary lookup for creating the correct Blender node.
MATERIALX_TO_BLENDER_NODES = {
    # Shader nodes
    "standard_surface": "ShaderNodeBsdfPrincipled",
    "uniform_edf": "ShaderNodeEmission",
    # Texture nodes
    "image": "ShaderNodeTexImage",
    "noise3d": "ShaderNodeTexNoise",
    "cellnoise3d": "ShaderNodeTexVoronoi",
    "worleynoise3d": "ShaderNodeTexVoronoi",
    "fractal3d": "ShaderNodeTexMusgrave",
    # Math nodes
    "add": "ShaderNodeMath",
    "subtract": "ShaderNodeMath",
    "multiply": "ShaderNodeMath",
    "divide": "ShaderNodeMath",
    "modulo": "ShaderNodeMath",
    "abs": "ShaderNodeMath",
    "power": "ShaderNodeMath",
    "min": "ShaderNodeMath",
    "max": "ShaderNodeMath",
    "clamp": "ShaderNodeClamp",
    "ifgreater": "ShaderNodeMath", # M_if(A > B, C, D) can be done with mix(D, C, A > B)
    # Procedural / Pattern nodes
    "ramp4": "ShaderNodeValToRGB",
    "mix": "ShaderNodeMix",
    # Channel nodes
    "combine2": "ShaderNodeCombineXYZ",
    "combine3": "ShaderNodeCombineXYZ",
    "combine4": "ShaderNodeCombineColor",
    "separate2": "ShaderNodeSeparateXYZ",
    "separate3": "ShaderNodeSeparateXYZ",
    "separate4": "ShaderNodeSeparateColor",
    # Utility / Constant nodes
    "constant": "ShaderNodeRGB",
    "texcoord": "ShaderNodeTexCoord",
    "place2d": "ShaderNodeMapping",
}

# Mapping for node-specific operations or modes
MATERIALX_TO_BLENDER_OPERATIONS = {
    "add": "ADD",
    "subtract": "SUBTRACT",
    "multiply": "MULTIPLY",
    "divide": "DIVIDE",
    "modulo": "MODULO",
    "abs": "ABSOLUTE",
    "power": "POWER",
    "min": "MINIMUM",
    "max": "MAXIMUM",
    "ifgreater": "GREATER_THAN",
}

# Mapping for MaterialX parameter names to Blender input socket names.
# This is used when a direct name match is not possible.
# Key: Blender Node Identifier (bl_idname), Value: Dict of {Mtlx Param: Blender Param}
PARAMETER_MAPPING = {
    "ShaderNodeBsdfPrincipled": {
        "base": "Base",
        "base_color": "Base Color",
        "specular_roughness": "Roughness",
    },
    "ShaderNodeMath": {
        "in1": "Value",
        "in2": "Value_001",
    },
    "ShaderNodeMix": {
        "fg": "A",
        "bg": "B",
        "amount": "Factor"
    },
    "ShaderNodeTexImage": {
        "file": "Image"
    },
    "ShaderNodeRGB": {
        # This is a special case. The 'value' is not an input socket but is
        # set directly on the node's output. We map it to None to signal
        # to the builder that it should be skipped by the generic setter.
        "value": None
    }
    # Add more mappings as needed
}

def get_blender_node_type(materialx_category: str) -> str:
    """Returns the Blender node type for a given MaterialX node category."""
    return MATERIALX_TO_BLENDER_NODES.get(materialx_category)

def get_parameter_mapping(blender_node_idname: str) -> dict:
    """Returns the parameter name mapping for a given Blender node type."""
    return PARAMETER_MAPPING.get(blender_node_idname, {})

def set_special_node_properties(blender_node, mtlx_node):
    """
    Sets special properties on a Blender node that can't be handled
    by simple parameter mapping, such as the operation on a Math node.
    """
    # Handle Math node operations
    if blender_node.bl_idname == 'ShaderNodeMath':
        operation = MATERIALX_TO_BLENDER_OPERATIONS.get(mtlx_node.category)
        if operation:
            blender_node.operation = operation
            
    # Handle Mix node data type
    if blender_node.bl_idname == 'ShaderNodeMix':
        # The Mtlx `ifgreater` is implemented as a mix shader driven by a math node
        # so we need to check the upstream connection to set the type correctly.
        fg_input = mtlx_node.inputs.get('fg')
        if fg_input and fg_input.nodename:
            fg_node = next((n for n in mtlx_node.doc.nodes if n.name == fg_input.nodename), None)
            if fg_node and (fg_node.type == 'color3' or fg_node.type == 'color4'):
                 blender_node.data_type = 'RGBA'
                 return # Already handled

        if mtlx_node.type == 'color3' or mtlx_node.type == 'color4':
            blender_node.data_type = 'RGBA'
        else:
            blender_node.data_type = 'FLOAT'
            
    # Handle Texture Image node
    if blender_node.bl_idname == 'ShaderNodeTexImage':
        # This is a simplification. In a real scenario, you would need to
        # resolve the file path, load the image into Blender, and then
        # assign it to the node.
        file_input = mtlx_node.inputs.get('file')
        if file_input and file_input.value:
            try:
                # This part of the code assumes the image is already loaded
                # in Blender. A full implementation would need to handle image loading.
                img = bpy.data.images.get(file_input.value)
                if img:
                    blender_node.image = img
            except Exception as e:
                print(f"Error setting image for node {blender_node.name}: {e}")
                
    # Handle Constant/RGB node color
    if blender_node.bl_idname == 'ShaderNodeRGB':
        value_input = mtlx_node.inputs.get('value')
        if value_input and value_input.value:
            try:
                # The value is a string like "1.0, 0.0, 0.0"
                parts = [float(p.strip()) for p in value_input.value.split(',')]
                if len(parts) == 3:
                    # The 'Color' output socket holds the value for an RGB node
                    blender_node.outputs['Color'].default_value = (*parts, 1.0) # Add alpha
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not set color for constant node {blender_node.name}: {e}")
