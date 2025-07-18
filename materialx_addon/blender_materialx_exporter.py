#!/usr/bin/env python3
"""
Blender MaterialX Exporter

A Python script that exports Blender materials to MaterialX (.mtlx) format,
replicating the functionality of Blender's C++ MaterialX exporter.

Usage:
    import blender_materialx_exporter as mtlx_exporter
    mtlx_exporter.export_material_to_materialx(material, "output.mtlx")
"""

import bpy
import os
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import math


class MaterialXBuilder:
    """Builds MaterialX XML documents."""
    
    def __init__(self, material_name: str, version: str = "1.38"):
        self.material_name = material_name
        self.version = version
        self.node_counter = 0
        self.nodes = {}
        self.connections = []
        
        # Create root element
        self.root = ET.Element("materialx")
        self.root.set("version", version)
        
        # Create nodegraph
        self.nodegraph = ET.SubElement(self.root, "nodegraph")
        self.nodegraph.set("name", f"NG_{material_name}")
        
        # Create material
        self.material = ET.SubElement(self.root, "surfacematerial")
        self.material.set("name", material_name)
        self.material.set("type", "material")
    
    def add_node(self, node_type: str, name: str, node_type_category: str = None, **params) -> str:
        """Add a node to the nodegraph."""
        if not name:
            name = f"{node_type}_{self.node_counter}"
            self.node_counter += 1
        
        node = ET.SubElement(self.nodegraph, node_type)
        node.set("name", name)
        if node_type_category:
            node.set("type", node_type_category)
        
        # Add parameters
        for param_name, param_value in params.items():
            if param_value is not None:
                input_elem = ET.SubElement(node, "input")
                input_elem.set("name", param_name)
                input_elem.set("type", self._get_param_type(param_value))
                input_elem.set("value", self._format_value(param_value))
        
        self.nodes[name] = node
        return name
    
    def add_connection(self, from_node: str, from_output: str, to_node: str, to_input: str):
        """Add a connection between nodes."""
        connection = ET.SubElement(self.nodegraph, "connect")
        connection.set("from", f"{from_node}.{from_output}")
        connection.set("to", f"{to_node}.{to_input}")
        self.connections.append((from_node, from_output, to_node, to_input))
    
    def set_material_surface(self, surface_node_name: str):
        """Set the surface shader for the material."""
        input_elem = ET.SubElement(self.material, "input")
        input_elem.set("name", "surfaceshader")
        input_elem.set("type", "surfaceshader")
        input_elem.set("nodename", surface_node_name)
    
    def _get_param_type(self, value) -> str:
        """Determine the MaterialX type for a value."""
        if isinstance(value, (int, float)):
            return "float"
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                return "vector2"
            elif len(value) == 3:
                return "color3"
            elif len(value) == 4:
                return "color4"
        return "string"
    
    def _format_value(self, value) -> str:
        """Format a value for MaterialX XML."""
        if isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        else:
            return str(value)
    
    def to_string(self) -> str:
        """Convert the document to a formatted XML string."""
        rough_string = ET.tostring(self.root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


class NodeMapper:
    """Maps Blender nodes to MaterialX nodes."""
    
    @staticmethod
    def get_node_mapper(node_type: str):
        """Get the appropriate mapper for a node type."""
        mappers = {
            'BSDF_PRINCIPLED': NodeMapper.map_principled_bsdf,
            'TEX_IMAGE': NodeMapper.map_image_texture,
            'TEX_COORD': NodeMapper.map_tex_coord,
            'RGB': NodeMapper.map_rgb,
            'VALUE': NodeMapper.map_value,
            'NORMAL_MAP': NodeMapper.map_normal_map,
            'VECTOR_MATH': NodeMapper.map_vector_math,
            'MATH': NodeMapper.map_math,
            'MIX': NodeMapper.map_mix,
            'INVERT': NodeMapper.map_invert,
            'SEPARATE_COLOR': NodeMapper.map_separate_color,
            'COMBINE_COLOR': NodeMapper.map_combine_color,
            'BUMP': NodeMapper.map_bump,
            'TEX_CHECKER': NodeMapper.map_checker_texture,
            'TEX_GRADIENT': NodeMapper.map_gradient_texture,
            'TEX_NOISE': NodeMapper.map_noise_texture,
            'MAPPING': NodeMapper.map_mapping,
        }
        return mappers.get(node_type)
    
    @staticmethod
    def map_principled_bsdf(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Principled BSDF node to standard_surface."""
        node_name = builder.add_node("standard_surface", f"surface_{node.name}", "surfaceshader")
        
        # Map inputs to standard_surface parameters
        input_mappings = {
            'Base Color': 'base_color',
            'Metallic': 'metallic',
            'Roughness': 'roughness',
            'Specular': 'specular',
            'IOR': 'ior',
            'Transmission': 'transmission',
            'Alpha': 'opacity',
            'Normal': 'normal',
            'Emission Color': 'emission_color',
            'Emission Strength': 'emission',
            'Subsurface': 'subsurface',
            'Subsurface Radius': 'subsurface_radius',
            'Subsurface Scale': 'subsurface_scale',
            'Subsurface Anisotropy': 'subsurface_anisotropy',
            'Sheen': 'sheen',
            'Sheen Tint': 'sheen_tint',
            'Sheen Roughness': 'sheen_roughness',
            'Clearcoat': 'clearcoat',
            'Clearcoat Roughness': 'clearcoat_roughness',
            'Clearcoat IOR': 'clearcoat_ior',
            'Clearcoat Normal': 'clearcoat_normal',
            'Tangent': 'tangent',
            'Anisotropic': 'anisotropic',
            'Anisotropic Rotation': 'anisotropic_rotation',
        }
        
        for input_name, mtlx_param in input_mappings.items():
            if input_name in input_nodes:
                builder.add_connection(
                    input_nodes[input_name], "out",
                    node_name, mtlx_param
                )
        
        return node_name
    
    @staticmethod
    def map_image_texture(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Image Texture node to MaterialX image node."""
        node_name = builder.add_node("image", f"image_{node.name}", "color3")
        
        # Handle image file
        if node.image:
            image_path = node.image.filepath
            if image_path:
                builder.add_node("image", node_name, "color3", file=image_path)
        
        # Handle UV coordinates
        if 'Vector' in input_nodes:
            builder.add_connection(
                input_nodes['Vector'], "out",
                node_name, "texcoord"
            )
        
        return node_name
    
    @staticmethod
    def map_tex_coord(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Texture Coordinate node to MaterialX texcoord node."""
        node_name = builder.add_node("texcoord", f"texcoord_{node.name}", "vector2")
        return node_name
    
    @staticmethod
    def map_rgb(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map RGB node to MaterialX constant node."""
        color = [node.outputs[0].default_value[0], 
                node.outputs[0].default_value[1], 
                node.outputs[0].default_value[2]]
        node_name = builder.add_node("constant", f"rgb_{node.name}", "color3", value=color)
        return node_name
    
    @staticmethod
    def map_value(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Value node to MaterialX constant node."""
        value = node.outputs[0].default_value
        node_name = builder.add_node("constant", f"value_{node.name}", "float", value=value)
        return node_name
    
    @staticmethod
    def map_normal_map(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Normal Map node to MaterialX normalmap node."""
        node_name = builder.add_node("normalmap", f"normalmap_{node.name}", "vector3")
        
        # Handle color input
        if 'Color' in input_nodes:
            builder.add_connection(
                input_nodes['Color'], "out",
                node_name, "in"
            )
        
        # Handle strength
        if 'Strength' in input_nodes:
            builder.add_connection(
                input_nodes['Strength'], "out",
                node_name, "scale"
            )
        
        return node_name
    
    @staticmethod
    def map_vector_math(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Vector Math node to MaterialX math nodes."""
        operation = node.operation.lower()
        
        # Map operations to MaterialX node types
        operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'cross_product': 'crossproduct',
            'dot_product': 'dotproduct',
            'normalize': 'normalize',
            'length': 'magnitude',
            'distance': 'distance',
            'reflect': 'reflect',
            'refract': 'refract',
        }
        
        mtlx_operation = operation_map.get(operation, 'add')
        node_name = builder.add_node(mtlx_operation, f"vector_math_{node.name}", "vector3")
        
        # Handle inputs
        for i, input_name in enumerate(['A', 'B']):
            if input_name in input_nodes:
                builder.add_connection(
                    input_nodes[input_name], "out",
                    node_name, f"in{i+1}" if mtlx_operation in ['add', 'subtract', 'multiply', 'divide'] else input_name.lower()
                )
        
        return node_name
    
    @staticmethod
    def map_math(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Math node to MaterialX math nodes."""
        operation = node.operation.lower()
        
        # Map operations to MaterialX node types
        operation_map = {
            'add': 'add',
            'subtract': 'subtract',
            'multiply': 'multiply',
            'divide': 'divide',
            'power': 'power',
            'logarithm': 'log',
            'square_root': 'sqrt',
            'absolute': 'abs',
            'minimum': 'min',
            'maximum': 'max',
            'sine': 'sin',
            'cosine': 'cos',
            'tangent': 'tan',
            'arcsine': 'asin',
            'arccosine': 'acos',
            'arctangent': 'atan2',
            'floor': 'floor',
            'ceil': 'ceil',
            'modulo': 'modulo',
            'round': 'round',
            'sign': 'sign',
            'compare': 'compare',
        }
        
        mtlx_operation = operation_map.get(operation, 'add')
        node_name = builder.add_node(mtlx_operation, f"math_{node.name}", "float")
        
        # Handle inputs
        for i, input_name in enumerate(['A', 'B']):
            if input_name in input_nodes:
                builder.add_connection(
                    input_nodes[input_name], "out",
                    node_name, f"in{i+1}" if mtlx_operation in ['add', 'subtract', 'multiply', 'divide'] else input_name.lower()
                )
        
        return node_name
    
    @staticmethod
    def map_mix(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Mix node to MaterialX mix node."""
        node_name = builder.add_node("mix", f"mix_{node.name}", "color3")
        
        # Handle inputs
        for input_name in ['A', 'B', 'Factor']:
            if input_name in input_nodes:
                builder.add_connection(
                    input_nodes[input_name], "out",
                    node_name, input_name.lower()
                )
        
        return node_name
    
    @staticmethod
    def map_invert(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Invert node to MaterialX invert node."""
        node_name = builder.add_node("invert", f"invert_{node.name}", "color3")
        
        if 'Color' in input_nodes:
            builder.add_connection(
                input_nodes['Color'], "out",
                node_name, "in"
            )
        
        return node_name
    
    @staticmethod
    def map_separate_color(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Separate Color node to MaterialX separate3 node."""
        node_name = builder.add_node("separate3", f"separate_{node.name}", "float")
        
        if 'Color' in input_nodes:
            builder.add_connection(
                input_nodes['Color'], "out",
                node_name, "in"
            )
        
        return node_name
    
    @staticmethod
    def map_combine_color(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Combine Color node to MaterialX combine3 node."""
        node_name = builder.add_node("combine3", f"combine_{node.name}", "color3")
        
        for input_name in ['R', 'G', 'B']:
            if input_name in input_nodes:
                builder.add_connection(
                    input_nodes[input_name], "out",
                    node_name, input_name.lower()
                )
        
        return node_name
    
    @staticmethod
    def map_bump(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Bump node to MaterialX bump node."""
        node_name = builder.add_node("bump", f"bump_{node.name}", "vector3")
        
        if 'Height' in input_nodes:
            builder.add_connection(
                input_nodes['Height'], "out",
                node_name, "in"
            )
        
        if 'Strength' in input_nodes:
            builder.add_connection(
                input_nodes['Strength'], "out",
                node_name, "scale"
            )
        
        return node_name
    
    @staticmethod
    def map_checker_texture(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Checker Texture node to MaterialX checkerboard node."""
        node_name = builder.add_node("checkerboard", f"checker_{node.name}", "color3")
        
        # Handle scale
        if 'Scale' in input_nodes:
            builder.add_connection(
                input_nodes['Scale'], "out",
                node_name, "scale"
            )
        
        return node_name
    
    @staticmethod
    def map_gradient_texture(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Gradient Texture node to MaterialX ramplr node."""
        gradient_type = node.gradient_type.lower()
        
        if gradient_type == 'linear':
            node_name = builder.add_node("ramplr", f"gradient_{node.name}", "color3")
        else:
            node_name = builder.add_node("ramptb", f"gradient_{node.name}", "color3")
        
        return node_name
    
    @staticmethod
    def map_noise_texture(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Noise Texture node to MaterialX noise nodes."""
        noise_dimensions = node.noise_dimensions
        
        if noise_dimensions == '2D':
            node_name = builder.add_node("noise2d", f"noise_{node.name}", "color3")
        else:
            node_name = builder.add_node("noise3d", f"noise_{node.name}", "color3")
        
        # Handle scale
        if 'Scale' in input_nodes:
            builder.add_connection(
                input_nodes['Scale'], "out",
                node_name, "scale"
            )
        
        return node_name
    
    @staticmethod
    def map_mapping(node, builder: MaterialXBuilder, input_nodes: Dict) -> str:
        """Map Mapping node to MaterialX place2d node."""
        node_name = builder.add_node("place2d", f"mapping_{node.name}", "vector2")
        
        # Handle translation
        if 'Location' in input_nodes:
            builder.add_connection(
                input_nodes['Location'], "out",
                node_name, "translate"
            )
        
        # Handle rotation
        if 'Rotation' in input_nodes:
            builder.add_connection(
                input_nodes['Rotation'], "out",
                node_name, "rotate"
            )
        
        # Handle scale
        if 'Scale' in input_nodes:
            builder.add_connection(
                input_nodes['Scale'], "out",
                node_name, "scale"
            )
        
        return node_name


class MaterialXExporter:
    """Main MaterialX exporter class."""
    
    def __init__(self, material: bpy.types.Material, output_path: str, options: Dict = None):
        self.material = material
        self.output_path = Path(output_path)
        self.options = options or {}
        
        # Default options
        self.active_uvmap = self.options.get('active_uvmap', 'UVMap')
        self.export_textures = self.options.get('export_textures', True)
        self.texture_path = Path(self.options.get('texture_path', './textures'))
        self.materialx_version = self.options.get('materialx_version', '1.38')
        self.copy_textures = self.options.get('copy_textures', True)
        self.relative_paths = self.options.get('relative_paths', True)
        
        # Internal state
        self.exported_nodes = {}
        self.texture_paths = {}
        self.builder = None
    
    def export(self) -> bool:
        """Export the material to MaterialX format."""
        try:
            if not self.material.use_nodes:
                print(f"Material '{self.material.name}' does not use nodes. Creating basic material.")
                return self._export_basic_material()
            
            # Find the Principled BSDF node
            principled_node = self._find_principled_bsdf_node()
            if not principled_node:
                print(f"No Principled BSDF node found in material '{self.material.name}'")
                return False
            
            # Create MaterialX builder
            self.builder = MaterialXBuilder(self.material.name, self.materialx_version)
            
            # Export the node network
            surface_node_name = self._export_node_network(principled_node)
            
            # Set the surface shader
            self.builder.set_material_surface(surface_node_name)
            
            # Write the file
            self._write_file()
            
            # Export textures if requested
            if self.export_textures:
                self._export_textures()
            
            print(f"Successfully exported material '{self.material.name}' to '{self.output_path}'")
            return True
            
        except Exception as e:
            print(f"Error exporting material '{self.material.name}': {str(e)}")
            return False
    
    def _export_basic_material(self) -> bool:
        """Export a basic material without nodes."""
        self.builder = MaterialXBuilder(self.material.name, self.materialx_version)
        
        # Create a basic standard_surface shader
        surface_node = self.builder.add_node("standard_surface", "surface_basic", "surfaceshader",
                                           base_color=[self.material.diffuse_color[0],
                                                     self.material.diffuse_color[1],
                                                     self.material.diffuse_color[2]],
                                           roughness=self.material.roughness,
                                           metallic=self.material.metallic)
        
        self.builder.set_material_surface(surface_node)
        self._write_file()
        return True
    
    def _find_principled_bsdf_node(self) -> Optional[bpy.types.Node]:
        """Find the Principled BSDF node in the material."""
        for node in self.material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                return node
        return None
    
    def _export_node_network(self, output_node: bpy.types.Node) -> str:
        """Export the node network starting from the output node."""
        # Traverse the network and build dependencies
        dependencies = self._build_dependencies(output_node)
        
        # Export nodes in dependency order
        for node in dependencies:
            if node not in self.exported_nodes:
                self._export_node(node)
        
        return self.exported_nodes[output_node]
    
    def _build_dependencies(self, output_node: bpy.types.Node) -> List[bpy.types.Node]:
        """Build a list of nodes in dependency order."""
        visited = set()
        dependencies = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            
            # Visit input nodes first
            for input_socket in node.inputs:
                if input_socket.links:
                    input_node = input_socket.links[0].from_node
                    visit(input_node)
            
            dependencies.append(node)
        
        visit(output_node)
        return dependencies
    
    def _export_node(self, node: bpy.types.Node) -> str:
        """Export a single node."""
        # Get the mapper for this node type
        mapper = NodeMapper.get_node_mapper(node.type)
        if not mapper:
            print(f"Warning: No mapper found for node type '{node.type}' ({node.name})")
            return self._export_unknown_node(node)
        
        # Build input nodes dictionary
        input_nodes = {}
        for input_socket in node.inputs:
            if input_socket.links:
                input_node = input_socket.links[0].from_node
                input_nodes[input_socket.name] = self.exported_nodes.get(input_node)
        
        # Map the node
        node_name = mapper(node, self.builder, input_nodes)
        self.exported_nodes[node] = node_name
        
        return node_name
    
    def _export_unknown_node(self, node: bpy.types.Node) -> str:
        """Export an unknown node type as a placeholder."""
        node_name = self.builder.add_node("constant", f"unknown_{node.name}", "color3",
                                        value=[1.0, 0.0, 1.0])  # Magenta for unknown nodes
        self.exported_nodes[node] = node_name
        return node_name
    
    def _write_file(self):
        """Write the MaterialX document to file."""
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(self.builder.to_string())
    
    def _export_textures(self):
        """Export texture files."""
        if not self.export_textures:
            return
        
        # Ensure texture directory exists
        self.texture_path.mkdir(parents=True, exist_ok=True)
        
        # Find all image textures
        for node in self.material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                self._export_texture(node.image)
    
    def _export_texture(self, image: bpy.types.Image):
        """Export a single texture file."""
        if not image.filepath:
            return
        
        source_path = Path(bpy.path.abspath(image.filepath))
        if not source_path.exists():
            print(f"Warning: Texture file not found: {source_path}")
            return
        
        # Determine target path
        if self.relative_paths:
            target_path = self.texture_path / source_path.name
        else:
            target_path = self.texture_path / source_path.name
        
        # Copy the texture
        if self.copy_textures:
            try:
                shutil.copy2(source_path, target_path)
                print(f"Copied texture: {source_path.name}")
            except Exception as e:
                print(f"Error copying texture {source_path.name}: {str(e)}")


def export_material_to_materialx(material: bpy.types.Material, 
                                output_path: str, 
                                options: Dict = None) -> bool:
    """
    Export a Blender material to MaterialX format.
    
    Args:
        material: Blender material object
        output_path: Path to output .mtlx file
        options: Export options dictionary
    
    Returns:
        bool: Success status
    """
    exporter = MaterialXExporter(material, output_path, options)
    return exporter.export()


def export_all_materials_to_materialx(output_directory: str, options: Dict = None) -> Dict[str, bool]:
    """
    Export all materials in the current scene to MaterialX format.
    
    Args:
        output_directory: Directory to save .mtlx files
        options: Export options dictionary
    
    Returns:
        Dict[str, bool]: Dictionary mapping material names to success status
    """
    results = {}
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for material in bpy.data.materials:
        if material.users > 0:  # Only export materials that are actually used
            output_path = output_dir / f"{material.name}.mtlx"
            results[material.name] = export_material_to_materialx(material, str(output_path), options)
    
    return results


# Example usage and testing functions
def create_test_material():
    """Create a test material for demonstration."""
    # Create a new material
    material = bpy.data.materials.new(name="TestMaterial")
    material.use_nodes = True
    
    # Get the node tree
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    
    # Create RGB node for base color
    rgb = nodes.new(type='ShaderNodeRGB')
    rgb.location = (-300, 0)
    rgb.outputs[0].default_value = (0.8, 0.2, 0.2, 1.0)  # Red color
    
    # Create Value node for roughness
    roughness = nodes.new(type='ShaderNodeValue')
    roughness.location = (-300, -200)
    roughness.outputs[0].default_value = 0.5
    
    # Create Material Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Connect nodes
    links.new(rgb.outputs[0], principled.inputs['Base Color'])
    links.new(roughness.outputs[0], principled.inputs['Roughness'])
    links.new(principled.outputs[0], output.inputs['Surface'])
    
    return material


def test_export():
    """Test the MaterialX exporter with a simple material."""
    # Create test material
    material = create_test_material()
    
    # Export options
    options = {
        'active_uvmap': 'UVMap',
        'export_textures': False,
        'materialx_version': '1.38',
        'relative_paths': True,
    }
    
    # Export the material
    success = export_material_to_materialx(material, "test_material.mtlx", options)
    
    if success:
        print("Test export successful!")
        # Clean up test material
        bpy.data.materials.remove(material)
    else:
        print("Test export failed!")


if __name__ == "__main__":
    # This will run when the script is executed directly
    test_export() 