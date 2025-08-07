#!/usr/bin/env python3
"""
Create test materials for MaterialX addon testing

This script creates various Blender materials with different complexity levels
and saves them as .blend files for testing the MaterialX exporter.
"""

import bpy
import os
import sys
from pathlib import Path

def clear_scene():
    """Clear the current scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Remove all materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

def create_simple_principled_material():
    """Create a simple material with just Principled BSDF."""
    material = bpy.data.materials.new(name="SimplePrincipled")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
    principled.inputs['Roughness'].default_value = 0.5
    principled.inputs['Metallic'].default_value = 0.0
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_texture_based_material():
    """Create a material with texture nodes."""
    material = bpy.data.materials.new(name="TextureBased")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    noise_tex = nodes.new(type='ShaderNodeTexNoise')
    noise_tex.location = (-400, 100)
    noise_tex.inputs['Scale'].default_value = 5.0
    
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-200, 100)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.1, 0.1, 0.1, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1.0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(tex_coord.outputs['Generated'], noise_tex.inputs['Vector'])
    links.new(noise_tex.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_complex_procedural_material():
    """Create a complex procedural material with multiple nodes."""
    material = bpy.data.materials.new(name="ComplexProcedural")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # First noise layer
    noise1 = nodes.new(type='ShaderNodeTexNoise')
    noise1.location = (-600, 200)
    noise1.inputs['Scale'].default_value = 10.0
    noise1.inputs['Detail'].default_value = 8.0
    
    # Second noise layer
    noise2 = nodes.new(type='ShaderNodeTexNoise')
    noise2.location = (-600, -200)
    noise2.inputs['Scale'].default_value = 3.0
    noise2.inputs['Detail'].default_value = 4.0
    
    # Mix the noises
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.location = (-400, 0)
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs['Fac'].default_value = 0.7
    
    # Color ramp for final look
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[0].color = (0.1, 0.05, 0.02, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.7
    color_ramp.color_ramp.elements[1].color = (0.8, 0.6, 0.4, 1.0)
    
    # Normal map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = (-200, -200)
    normal_map.inputs['Strength'].default_value = 0.5
    
    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Roughness'].default_value = 0.8
    principled.inputs['Metallic'].default_value = 0.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(tex_coord.outputs['Generated'], noise1.inputs['Vector'])
    links.new(tex_coord.outputs['Generated'], noise2.inputs['Vector'])
    links.new(noise1.outputs['Fac'], mix_rgb.inputs[1])
    links.new(noise2.outputs['Fac'], mix_rgb.inputs[2])
    links.new(mix_rgb.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(mix_rgb.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_glass_material():
    """Create a glass material with transparency using Principled BSDF built-in fresnel."""
    material = bpy.data.materials.new(name="GlassMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    principled.inputs['Roughness'].default_value = 0.0
    principled.inputs['Metallic'].default_value = 0.0
    principled.inputs['IOR'].default_value = 1.45
    principled.inputs['Alpha'].default_value = 0.3
    principled.inputs['Transmission Weight'].default_value = 0.95
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # Enable transparency
    material.blend_method = 'BLEND'
    
    return material

def create_metallic_material():
    """Create a metallic material with anisotropy."""
    material = bpy.data.materials.new(name="MetallicMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    # Anisotropic roughness
    roughness_tex = nodes.new(type='ShaderNodeTexNoise')
    roughness_tex.location = (-400, 100)
    roughness_tex.inputs['Scale'].default_value = 20.0
    
    # Color variation
    color_tex = nodes.new(type='ShaderNodeTexNoise')
    color_tex.location = (-400, -100)
    color_tex.inputs['Scale'].default_value = 5.0
    
    # Color ramp for metallic look
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-200, -100)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.7, 0.5, 0.3, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.9, 0.8, 0.6, 1.0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.2
    principled.inputs['Anisotropic'].default_value = 0.8
    principled.inputs['Anisotropic Rotation'].default_value = 0.5
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(tex_coord.outputs['Generated'], roughness_tex.inputs['Vector'])
    links.new(tex_coord.outputs['Generated'], color_tex.inputs['Vector'])
    links.new(color_tex.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(roughness_tex.outputs['Fac'], principled.inputs['Roughness'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_emission_material():
    """Create an emission material using Principled BSDF with emission input."""
    material = bpy.data.materials.new(name="EmissionMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    principled.inputs['Emission Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    principled.inputs['Emission Strength'].default_value = 5.0
    principled.inputs['Roughness'].default_value = 1.0
    principled.inputs['Metallic'].default_value = 0.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mixed_shader_material():
    """Create a material that mixes different shaders."""
    material = bpy.data.materials.new(name="MixedShader")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    principled1 = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled1.location = (-200, 100)
    principled1.inputs['Base Color'].default_value = (0.8, 0.2, 0.2, 1.0)
    principled1.inputs['Roughness'].default_value = 0.8
    
    principled2 = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled2.location = (-200, -100)
    principled2.inputs['Base Color'].default_value = (0.2, 0.2, 0.8, 1.0)
    principled2.inputs['Roughness'].default_value = 0.2
    principled2.inputs['Metallic'].default_value = 1.0
    
    mix_shader = nodes.new(type='ShaderNodeMixShader')
    mix_shader.location = (0, 0)
    mix_shader.inputs['Fac'].default_value = 0.5
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled1.outputs['BSDF'], mix_shader.inputs[1])
    links.new(principled2.outputs['BSDF'], mix_shader.inputs[2])
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
    
    return material

def create_math_heavy_material():
    """Create a material with lots of math operations."""
    material = bpy.data.materials.new(name="MathHeavy")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Math operations
    math1 = nodes.new(type='ShaderNodeMath')
    math1.location = (-600, 200)
    math1.operation = 'SINE'
    
    math2 = nodes.new(type='ShaderNodeMath')
    math2.location = (-600, 0)
    math2.operation = 'COSINE'
    
    math3 = nodes.new(type='ShaderNodeMath')
    math3.location = (-600, -200)
    math3.operation = 'TANGENT'
    
    # Vector math
    vec_math = nodes.new(type='ShaderNodeVectorMath')
    vec_math.location = (-400, 0)
    vec_math.operation = 'ADD'
    
    # More math
    math4 = nodes.new(type='ShaderNodeMath')
    math4.location = (-200, 0)
    math4.operation = 'ABSOLUTE'
    
    # Color ramp
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (0, 0)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (500, 0)
    
    # Connect
    links.new(tex_coord.outputs['Generated'], math1.inputs[0])
    links.new(tex_coord.outputs['Generated'], math2.inputs[0])
    links.new(tex_coord.outputs['Generated'], math3.inputs[0])
    links.new(math1.outputs[0], vec_math.inputs[0])
    links.new(math2.outputs[0], vec_math.inputs[1])
    links.new(math3.outputs[0], vec_math.inputs[2])
    links.new(vec_math.outputs[0], math4.inputs[0])
    links.new(math4.outputs[0], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material



def create_musgrave_texture_material():
    """Create a material with Musgrave Texture node."""
    material = bpy.data.materials.new(name="MusgraveTexture")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    musgrave_tex = nodes.new(type='ShaderNodeTexMusgrave')
    musgrave_tex.location = (-400, 0)
    musgrave_tex.inputs['Scale'].default_value = 5.0
    musgrave_tex.inputs['Detail'].default_value = 2.0
    musgrave_tex.inputs['Dimension'].default_value = 2.0
    musgrave_tex.inputs['Lacunarity'].default_value = 2.0
    
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.1, 0.1, 0.1, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1.0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(tex_coord.outputs['Generated'], musgrave_tex.inputs['Vector'])
    links.new(musgrave_tex.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_geometry_info_material():
    """Create a material with Geometry Info node."""
    material = bpy.data.materials.new(name="GeometryInfo")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    geometry = nodes.new(type='ShaderNodeNewGeometry')
    geometry.location = (-600, 0)
    
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-400, 0)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect - use position data
    links.new(geometry.outputs['Position'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_object_info_material():
    """Create a material with Object Info node."""
    material = bpy.data.materials.new(name="ObjectInfo")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    object_info = nodes.new(type='ShaderNodeObjectInfo')
    object_info.location = (-600, 0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect - use object color
    links.new(object_info.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_light_path_material():
    """Create a material with Light Path node."""
    material = bpy.data.materials.new(name="LightPath")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    light_path = nodes.new(type='ShaderNodeLightPath')
    light_path.location = (-600, 0)
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect - use camera ray info to control emission
    links.new(light_path.outputs['Is Camera Ray'], principled.inputs['Emission Strength'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

# New functions to replicate official MaterialX reference files

def create_mtlx_gold_material():
    """Create a gold material that replicates standard_surface_gold.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Gold")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF with exact values from the MTX file
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    # base = 1.0 (default)
    principled.inputs['Base Color'].default_value = (0.944, 0.776, 0.373, 1.0)  # base_color
    # Note: Blender doesn't have separate 'Specular' input, it's built into the shader
    principled.inputs['Roughness'].default_value = 0.02  # specular_roughness
    principled.inputs['Metallic'].default_value = 1.0  # metalness
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mtlx_glass_material():
    """Create a glass material that replicates standard_surface_glass.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Glass")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF with exact values from the MTX file
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    # Note: Blender doesn't have separate 'Base' input, it's controlled by base_color
    principled.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)  # base = 0.0 (black)
    # Note: Blender doesn't have separate 'Specular' input, it's built into the shader
    principled.inputs['Roughness'].default_value = 0.01  # specular_roughness
    principled.inputs['IOR'].default_value = 1.52  # specular_IOR
    principled.inputs['Transmission Weight'].default_value = 1.0  # transmission
    # Note: Blender doesn't have separate transmission color/depth/scatter inputs
    # These are handled internally by the Principled BSDF
    principled.inputs['Alpha'].default_value = 1.0  # opacity (note: Blender uses Alpha, MTX uses opacity)
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # Enable transparency
    material.blend_method = 'BLEND'
    
    return material

def create_mtlx_checkerboard_material():
    """Create a checkerboard material that replicates checkerboard_test.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Checkerboard")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes to replicate the MTX nodegraph more accurately
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Use a simpler noise for cell-like pattern (closer to cellnoise3d)
    cell_noise = nodes.new(type='ShaderNodeTexNoise')
    cell_noise.location = (-600, 0)
    cell_noise.inputs['Scale'].default_value = 10.0  # Higher scale for more cell-like pattern
    cell_noise.noise_dimensions = '2D'
    cell_noise.inputs['Detail'].default_value = 0.0  # No detail for cell-like appearance
    
    # Modulo operation (replicates modulo)
    modulo = nodes.new(type='ShaderNodeMath')
    modulo.location = (-400, 0)
    modulo.operation = 'MODULO'
    modulo.inputs[1].default_value = 2.0
    
    # Greater than operation (replicates ifgreater)
    greater = nodes.new(type='ShaderNodeMath')
    greater.location = (-200, 0)
    greater.operation = 'GREATER_THAN'
    greater.inputs[1].default_value = 1.0
    
    # Mix operation (replicates mix)
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.location = (0, 0)
    mix_rgb.blend_type = 'MIX'
    mix_rgb.inputs['Color1'].default_value = (1.0, 1.0, 1.0, 1.0)  # white
    mix_rgb.inputs['Color2'].default_value = (0.0, 0.0, 0.0, 1.0)  # black
    
    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (200, 0)
    
    # Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Connect - this should create a proper nodegraph that the exporter can handle
    links.new(tex_coord.outputs['Generated'], cell_noise.inputs['Vector'])
    links.new(cell_noise.outputs['Fac'], modulo.inputs[0])
    links.new(modulo.outputs[0], greater.inputs[0])
    links.new(greater.outputs[0], mix_rgb.inputs['Fac'])
    links.new(mix_rgb.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mtlx_single_color_material():
    """Create a single color material that replicates single_color_test.mtlx."""
    material = bpy.data.materials.new(name="MTLX_SingleColor")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create RGB node (replicates red_constant)
    rgb = nodes.new(type='ShaderNodeRGB')
    rgb.location = (-200, 0)
    rgb.outputs[0].default_value = (1.0, 0.0, 0.0, 1.0)  # red color
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(rgb.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mtlx_chrome_material():
    """Create a chrome material that replicates standard_surface_chrome.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Chrome")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF with chrome properties
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)  # chrome color
    principled.inputs['Metallic'].default_value = 1.0  # fully metallic
    principled.inputs['Roughness'].default_value = 0.0  # very smooth
    # Note: Blender doesn't have separate 'Specular' input, it's built into the shader
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mtlx_copper_material():
    """Create a copper material that replicates standard_surface_copper.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Copper")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF with copper properties
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.722, 0.451, 0.2, 1.0)  # copper color
    principled.inputs['Metallic'].default_value = 1.0  # fully metallic
    principled.inputs['Roughness'].default_value = 0.1  # slightly rough
    # Note: Blender doesn't have separate 'Specular' input, it's built into the shader
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_mtlx_jade_material():
    """Create a jade material that replicates standard_surface_jade.mtlx."""
    material = bpy.data.materials.new(name="MTLX_Jade")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF with jade properties
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.2, 0.8, 0.4, 1.0)  # jade green
    principled.inputs['Metallic'].default_value = 0.0  # non-metallic
    principled.inputs['Roughness'].default_value = 0.3  # semi-rough
    # Note: Blender doesn't have separate 'Specular' input, it's built into the shader
    principled.inputs['Subsurface Weight'].default_value = 0.1  # slight subsurface scattering
    # Note: Blender doesn't have separate 'Subsurface Color' input, it uses the base color
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_brick_texture_material():
    """Create a material using the Brick Texture node to test custom node definitions."""
    material = bpy.data.materials.new(name="BrickTexture")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Brick Texture node
    brick_tex = nodes.new(type='ShaderNodeTexBrick')
    brick_tex.location = (-400, 0)
    
    # Configure brick texture parameters
    brick_tex.inputs['Color1'].default_value = (0.8, 0.2, 0.2, 1.0)  # Red bricks
    brick_tex.inputs['Color2'].default_value = (0.2, 0.2, 0.8, 1.0)  # Blue bricks
    brick_tex.inputs['Mortar'].default_value = (0.2, 0.2, 0.2, 1.0)  # Dark mortar
    brick_tex.inputs['Scale'].default_value = 5.0
    brick_tex.inputs['Mortar Size'].default_value = 0.02
    brick_tex.inputs['Bias'].default_value = 0.0
    brick_tex.inputs['Brick Width'].default_value = 0.5
    brick_tex.inputs['Row Height'].default_value = 0.25
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Roughness'].default_value = 0.8
    principled.inputs['Metallic'].default_value = 0.0
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect brick texture to base color
    links.new(brick_tex.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_brick_texture_complex_material():
    """Create a complex material using Brick Texture with additional processing."""
    material = bpy.data.materials.new(name="BrickTextureComplex")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Texture Coordinate node
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Create Brick Texture node
    brick_tex = nodes.new(type='ShaderNodeTexBrick')
    brick_tex.location = (-600, 0)
    
    # Configure brick texture parameters
    brick_tex.inputs['Color1'].default_value = (0.9, 0.6, 0.3, 1.0)  # Orange bricks
    brick_tex.inputs['Color2'].default_value = (0.7, 0.4, 0.2, 1.0)  # Brown bricks
    brick_tex.inputs['Mortar'].default_value = (0.1, 0.1, 0.1, 1.0)  # Dark mortar
    brick_tex.inputs['Scale'].default_value = 8.0
    brick_tex.inputs['Mortar Size'].default_value = 0.015
    brick_tex.inputs['Bias'].default_value = 0.5
    brick_tex.inputs['Brick Width'].default_value = 0.6
    brick_tex.inputs['Row Height'].default_value = 0.3
    
    # Create Color Ramp for additional processing
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-400, 0)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[0].color = (0.1, 0.1, 0.1, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.7
    color_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    
    # Create Mix RGB node for color variation
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.location = (-200, 0)
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs['Fac'].default_value = 0.3
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Roughness'].default_value = 0.7
    principled.inputs['Metallic'].default_value = 0.0
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes
    links.new(tex_coord.outputs['Generated'], brick_tex.inputs['Vector'])
    links.new(brick_tex.outputs['Color'], color_ramp.inputs['Fac'])
    links.new(brick_tex.outputs['Color'], mix_rgb.inputs['Color1'])
    links.new(color_ramp.outputs['Color'], mix_rgb.inputs['Color2'])
    links.new(mix_rgb.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_type_conversion_test_material():
    """Create a material that tests various type conversions."""
    material = bpy.data.materials.new(name="TypeConversionTest")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Texture Coordinate node (vector2)
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    # Create Vector Math node that expects vector3
    vector_math = nodes.new(type='ShaderNodeVectorMath')
    vector_math.location = (-600, 0)
    vector_math.operation = 'NORMALIZE'
    
    # Create Color Ramp that expects float
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-400, 0)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.1, 0.1, 0.1, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1.0)
    
    # Create Mix RGB node
    mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    mix_rgb.location = (-200, 0)
    mix_rgb.blend_type = 'MULTIPLY'
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes (this will test type conversions)
    links.new(tex_coord.outputs['UV'], vector_math.inputs['Vector'])  # vector2 -> vector3
    links.new(vector_math.outputs['Vector'], color_ramp.inputs['Fac'])  # vector3 -> float
    links.new(color_ramp.outputs['Color'], mix_rgb.inputs['Color1'])
    links.new(mix_rgb.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return material

def create_test_scene_and_save(material_func, filename):
    """Create a test scene with the given material and save it."""
    clear_scene()
    
    # Create a cube
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    cube = bpy.context.active_object
    
    # Create material
    material = material_func()
    
    # Assign material to cube
    if cube.data.materials:
        cube.data.materials[0] = material
    else:
        cube.data.materials.append(material)
    
    # Save the file
    output_path = f"examples/blender/{filename}.blend"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Remove any existing backup files
    backup_path = f"{output_path}1"
    if os.path.exists(backup_path):
        os.remove(backup_path)
    
    # Save to a temporary location first to avoid backup creation
    temp_path = f"examples/blender/temp_{filename}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=temp_path)
    
    # Move the file to overwrite the existing one
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(temp_path, output_path)
    
    # Clean up any other temporary files that might exist
    for temp_file in os.listdir("examples/blender"):
        if temp_file.startswith("temp_") and temp_file.endswith(".blend"):
            temp_file_path = os.path.join("examples/blender", temp_file)
            if temp_file_path != temp_path:  # Don't delete the one we just moved
                os.remove(temp_file_path)
    
    print(f"Created: {output_path}")
    return output_path

def main():
    """Create all test materials."""
    print("Creating test materials for MaterialX addon testing...")
    
    # Create examples directory
    os.makedirs("examples/blender", exist_ok=True)
    
    # Define test materials
    test_materials = [
        # Original test materials
        (create_simple_principled_material, "SimplePrincipled"),
        (create_texture_based_material, "TextureBased"),
        (create_complex_procedural_material, "ComplexProcedural"),
        (create_glass_material, "GlassMaterial"),
        (create_metallic_material, "MetallicMaterial"),
        (create_emission_material, "EmissionMaterial"),
        (create_mixed_shader_material, "MixedShader"),
        (create_math_heavy_material, "MathHeavy"),
        (create_musgrave_texture_material, "MusgraveTexture"),
        (create_geometry_info_material, "GeometryInfo"),
        (create_object_info_material, "ObjectInfo"),
        (create_light_path_material, "LightPath"),
        
        # New MaterialX reference replicas
        (create_mtlx_gold_material, "MTLX_Gold"),
        (create_mtlx_glass_material, "MTLX_Glass"),
        (create_mtlx_checkerboard_material, "MTLX_Checkerboard"),
        (create_mtlx_single_color_material, "MTLX_SingleColor"),
        (create_mtlx_chrome_material, "MTLX_Chrome"),
        (create_mtlx_copper_material, "MTLX_Copper"),
        (create_mtlx_jade_material, "MTLX_Jade"),
        
        # New custom node and type conversion tests
        (create_brick_texture_material, "BrickTexture"),
        (create_brick_texture_complex_material, "BrickTextureComplex"),
        (create_type_conversion_test_material, "TypeConversionTest"),
    ]
    
    created_files = []
    
    for material_func, filename in test_materials:
        try:
            filepath = create_test_scene_and_save(material_func, filename)
            created_files.append(filepath)
        except Exception as e:
            print(f"Error creating {filename}: {e}")
    
    print(f"\nCreated {len(created_files)} test files:")
    for filepath in created_files:
        print(f"  - {filepath}")
    
    print("\nTest materials created successfully!")
    return created_files

if __name__ == "__main__":
    main() 