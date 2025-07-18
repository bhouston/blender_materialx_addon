"""
MaterialX exporter for Blender materials.

This module handles the export of Blender materials to MaterialX format,
with validation and logging of incompatible nodes.
"""

import bpy
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Set, Optional
import os
from . import mapping
from . import validator

class MaterialXExporter:
    def __init__(self):
        self.exported_nodes: Dict[str, str] = {}  # node_name -> materialx_name
        self.materialx_doc = None
        self.incompatible_nodes: List[tuple] = []
        self.warnings: List[str] = []
        
    def export_material(self, material, materialx_doc):
        """Export a single Blender material to MaterialX."""
        if not material.use_nodes or not material.node_tree:
            self.warnings.append(f"Material '{material.name}' doesn't use nodes, skipping")
            return None
            
        print(f"Exporting material: {material.name}")
        
        # Validate material first
        validation = validator.validate_material(material)
        if not validation.is_compatible:
            print(f"Warning: Material '{material.name}' has incompatible nodes:")
            for node_name, node_type in validation.incompatible_nodes:
                print(f"  - {node_name} ({node_type})")
                self.incompatible_nodes.append((material.name, node_name, node_type))
        
        # Create material element
        mat_elem = ET.SubElement(materialx_doc, "surfacematerial")
        mat_elem.set("name", f"material_{material.name}")
        mat_elem.set("type", "material")
        
        # Find output node
        output_node = None
        for node in material.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
                break
                
        if not output_node:
            self.warnings.append(f"No output node found in material '{material.name}'")
            return None
            
        # Export connected surface shader
        if output_node.inputs['Surface'].is_linked:
            surface_link = output_node.inputs['Surface'].links[0]
            surface_node = surface_link.from_node
            
            shader_name = self.export_node(surface_node, material.node_tree, materialx_doc)
            if shader_name:
                surf_input = ET.SubElement(mat_elem, "input")
                surf_input.set("name", "surfaceshader")
                surf_input.set("type", "surfaceshader")
                surf_input.set("nodename", shader_name)
        
        return mat_elem
    
    def export_node(self, node, node_tree, materialx_doc):
        """Export a single node to MaterialX."""
        # Check if already exported
        if node.name in self.exported_nodes:
            return self.exported_nodes[node.name]
        
        # Check compatibility
        if not validator.validate_node(node):
            print(f"Skipping incompatible node: {node.name} ({node.type})")
            return None
        
        # Get MaterialX equivalent
        materialx_type = mapping.get_materialx_equivalent(node.bl_idname)
        if not materialx_type:
            print(f"No MaterialX equivalent for node: {node.name} ({node.bl_idname})")
            return None
        
        # Create MaterialX node
        node_name = f"node_{node.name}_{len(self.exported_nodes)}"
        materialx_node = ET.SubElement(materialx_doc, materialx_type)
        materialx_node.set("name", node_name)
        
        # The 'type' attribute in the Mtlx node definition should be the Mtlx type,
        # not the category tag. For instance, for a <constant> node, the type
        # might be 'color3' or 'float'.
        # We will need to infer this from the node's outputs.
        # This is a simplification for now.
        mtlx_type_val = "surfaceshader" # Default
        if len(node.outputs) > 0:
            # A simple inference based on the first output socket
             mtlx_type_val = self.get_materialx_type_for_socket(node.outputs[0])

        materialx_node.set("type", mtlx_type_val)
        
        # Export parameters
        for blender_input in node.inputs:
            # Skip hidden or unavailable sockets
            if not blender_input.enabled or blender_input.hide:
                continue

            materialx_param_name = mapping.get_materialx_param_name(node.bl_idname, blender_input.name)
            if not materialx_param_name:
                # This socket is not mapped, so we skip it.
                continue

            if blender_input.is_linked:
                # Connected input - export connected node
                link = blender_input.links[0]
                connected_node_name = self.export_node(link.from_node, node_tree, materialx_doc)
                
                if connected_node_name:
                    input_elem = ET.SubElement(materialx_node, "input")
                    input_elem.set("name", materialx_param_name)
                    input_elem.set("type", self.get_materialx_type_for_socket(blender_input))
                    input_elem.set("nodename", connected_node_name)
                    
                    # Handle output socket specification if needed
                    # MaterialX infers the output type, but we can specify if it's not the default
                    if link.from_socket.name != "Color" and link.from_socket.name != "Value" and link.from_socket.name != "BSDF":
                        input_elem.set("output", link.from_socket.name.lower())
            
            else:
                # Default value
                if blender_input.name == "Image" and node.bl_idname == "ShaderNodeTexImage":
                    if node.image:
                        # Handle file path for image textures
                        input_elem = ET.SubElement(materialx_node, "input")
                        input_elem.set("name", materialx_param_name)
                        input_elem.set("type", "filename")
                        # It is better to use relative path if possible
                        input_elem.set("value", node.image.filepath.replace("//", ""))
                else:
                    value = self.get_socket_value(blender_input)
                    if value is not None:
                        input_elem = ET.SubElement(materialx_node, "input")
                        input_elem.set("name", materialx_param_name)
                        input_elem.set("type", self.get_materialx_type_for_socket(blender_input))
                        input_elem.set("value", value)
        
        # Handle math node operation (for ShaderNodeMath and similar)
        if node.bl_idname == "ShaderNodeMath":
            op = getattr(node, "operation", None)
            if op:
                materialx_node.set("operation", op.lower())
        elif node.bl_idname == "ShaderNodeVectorMath":
            op = getattr(node, "operation", None)
            if op:
                materialx_node.set("operation", op.lower())
        
        # Handle special cases
        self.handle_special_node_cases(node, materialx_node)
        
        self.exported_nodes[node.name] = node_name
        return node_name
    
    def get_socket_value(self, socket):
        """Get the default value of a socket."""
        if hasattr(socket, 'default_value'):
            value = socket.default_value
            
            # Handle different value types
            if hasattr(value, '__len__') and len(value) > 1:
                # Vector/Color
                if len(value) == 3:
                    return f"{value[0]}, {value[1]}, {value[2]}"
                elif len(value) == 4:
                    return f"{value[0]}, {value[1]}, {value[2]}"  # Skip alpha for color
            else:
                # Single value
                return str(float(value))
        return None
    
    def get_materialx_type_for_socket(self, socket):
        """Get MaterialX type for a Blender socket."""
        if socket.type == 'RGBA':
            return 'color3'
        elif socket.type == 'VALUE':
            return 'float'
        elif socket.type == 'VECTOR':
            return 'vector3'
        elif socket.type == 'SHADER':
            return 'surfaceshader'
        else:
            return 'float'  # Default fallback
    
    def handle_special_node_cases(self, blender_node, materialx_node):
        """Handle special cases for specific node types."""
        
        # Principled BSDF special handling
        if blender_node.type == 'BSDF_PRINCIPLED':
            # MaterialX standard_surface has different parameter organization
            # Add any special parameter mappings here
            materialx_node.set("type", "surfaceshader")
            
        # Noise texture special handling
        elif blender_node.type == 'TEX_NOISE':
            # Set default noise type
            noise_input = ET.SubElement(materialx_node, "input")
            noise_input.set("name", "noisetype")
            noise_input.set("type", "string")
            noise_input.set("value", "perlin")
            
        # ColorRamp special handling  
        elif blender_node.type == 'VALTORGB':
            # Would need to convert ColorRamp to ramp4 control points
            # This is more complex and would require detailed conversion
            pass

def export_materialx(filepath):
    """Main export function."""
    try:
        print(f"Exporting MaterialX to: {filepath}")
        
        # Create MaterialX document
        materialx_doc = ET.Element("materialx")
        materialx_doc.set("version", "1.38")
        materialx_doc.set("namespace", "")
        
        exporter = MaterialXExporter()
        
        # Get materials to export
        materials_to_export = []
        
        # Export materials from selected objects if any are selected
        if bpy.context.selected_objects:
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH' and hasattr(obj.data, 'materials'):
                    for material in obj.data.materials:
                        if material and material not in materials_to_export:
                            materials_to_export.append(material)
        else:
            # Export all materials if nothing selected
            materials_to_export = list(bpy.data.materials)
        
        if not materials_to_export:
            print("No materials found to export")
            return {'CANCELLED'}
        
        print(f"Found {len(materials_to_export)} materials to export")
        
        # Export each material
        exported_count = 0
        for material in materials_to_export:
            if exporter.export_material(material, materialx_doc):
                exported_count += 1
        
        # Write the file
        if exported_count > 0:
            # Pretty print the XML
            rough_string = ET.tostring(materialx_doc, 'unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Remove empty lines
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            pretty_xml = '\n'.join(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            print(f"Successfully exported {exported_count} materials to {filepath}")
            
            # Report incompatible nodes
            if exporter.incompatible_nodes:
                print("\nIncompatible nodes encountered during export:")
                for material_name, node_name, node_type in exporter.incompatible_nodes:
                    print(f"  Material '{material_name}': {node_name} ({node_type})")
            
            # Report warnings
            if exporter.warnings:
                print("\nWarnings:")
                for warning in exporter.warnings:
                    print(f"  {warning}")
                    
        else:
            print("No materials could be exported")
            return {'CANCELLED'}
        
        return {'FINISHED'}
        
    except Exception as e:
        print(f"Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}
