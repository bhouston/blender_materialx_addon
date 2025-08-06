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
    """Create a glass material with transparency."""
    material = bpy.data.materials.new(name="GlassMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    fresnel = nodes.new(type='ShaderNodeFresnel')
    fresnel.location = (-200, 100)
    fresnel.inputs['IOR'].default_value = 1.45
    
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    principled.inputs['Roughness'].default_value = 0.0
    principled.inputs['Metallic'].default_value = 0.0
    principled.inputs['IOR'].default_value = 1.45
    principled.inputs['Alpha'].default_value = 0.3
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(fresnel.outputs['Fac'], principled.inputs['Metallic'])
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
    """Create an emission material."""
    material = bpy.data.materials.new(name="EmissionMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    emission = nodes.new(type='ShaderNodeEmission')
    emission.location = (0, 0)
    emission.inputs['Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    emission.inputs['Strength'].default_value = 5.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
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
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    
    print(f"Created: {output_path}")
    return output_path

def main():
    """Create all test materials."""
    print("Creating test materials for MaterialX addon testing...")
    
    # Create examples directory
    os.makedirs("examples/blender", exist_ok=True)
    
    # Define test materials
    test_materials = [
        (create_simple_principled_material, "SimplePrincipled"),
        (create_texture_based_material, "TextureBased"),
        (create_complex_procedural_material, "ComplexProcedural"),
        (create_glass_material, "GlassMaterial"),
        (create_metallic_material, "MetallicMaterial"),
        (create_emission_material, "EmissionMaterial"),
        (create_mixed_shader_material, "MixedShader"),
        (create_math_heavy_material, "MathHeavy"),
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