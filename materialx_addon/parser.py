import xml.etree.ElementTree as ET
from .data import MaterialXDocument, NodeGraph, Node, Input, Material

class MaterialXParser:
    def __init__(self, filepath: str):
        self._filepath = filepath

    def parse(self) -> MaterialXDocument:
        """Parses the MaterialX file and returns a MaterialXDocument object."""
        tree = ET.parse(self._filepath)
        root = tree.getroot()

        doc = MaterialXDocument(
            version=root.get('version', 'unknown'),
            nodegraphs=self._parse_nodegraphs(root),
            materials=self._parse_materials(root)
        )
        return doc

    def _parse_nodegraphs(self, root: ET.Element):
        nodegraphs = []
        for graph_elem in root.findall('nodegraph'):
            graph = NodeGraph(name=graph_elem.get('name'), elem=graph_elem)
            # Find all elements inside the nodegraph that are node definitions.
            # We iterate through all descendants of the nodegraph.
            for node_elem in graph_elem.iter():
                # A node definition is an element with a 'name' attribute that is not
                # a nodegraph itself or an input/parameter element (which are handled by _parse_node).
                if node_elem.tag not in ['nodegraph', 'input', 'parameter'] and node_elem.get('name'):
                    # Make sure we haven't already parsed this node
                    if not any(n.name == node_elem.get('name') for n in graph.nodes):
                        node = self._parse_node(node_elem)
                        if node:
                            graph.nodes.append(node)
            nodegraphs.append(graph)
        return nodegraphs

    def _parse_node(self, elem: ET.Element) -> Node:
        """Parses a single XML element into a Node object."""
        node = Node(
            category=elem.tag,
            name=elem.get('name'),
            type=elem.get('type')
        )

        for attr_name, attr_value in elem.attrib.items():
            if attr_name not in ['name', 'type']:
                # These are treated as inputs with values
                input_obj = Input(
                    name=attr_name,
                    type='attribute', # The type is inferred from context, can be improved
                    value=attr_value
                )
                node.inputs[attr_name] = input_obj

        for input_elem in elem.findall('input'):
            input_obj = self._parse_input(input_elem)
            node.inputs[input_obj.name] = input_obj
            
        # Handle parameters defined as child elements (e.g., in <constant>)
        param_elem = elem.find('parameter')
        if param_elem is not None:
             input_obj = self._parse_input(param_elem, is_parameter=True)
             node.inputs[input_obj.name] = input_obj
            
        return node

    def _parse_input(self, elem, is_parameter=False):
        """Helper to parse <input> or <parameter> elements."""
        name = elem.get('name')
        nodename = elem.get('nodename')

        # If nodename is missing, check for a nested node element which is the reference
        if not nodename:
            child_node = elem.find('*')
            if child_node is not None:
                nodename = child_node.get('name')

        if is_parameter:
            value = elem.get('value')
        else:
            value = elem.get('value')

        return Input(
            name=name,
            type=elem.get('type'),
            value=value,
            nodename=nodename,
            output=elem.get('output')
        )
        
    def _parse_materials(self, root: ET.Element):
        materials = []
        # Find all possible material tags at the top level.
        material_elements = root.findall('material') + root.findall('surfacematerial')

        for elem in material_elements:
            mat_name = elem.get('name')
            shader_node_name = None

            shader_input = elem.find("input[@name='surfaceshader']")
            if shader_input is not None:
                shader_node_name = shader_input.get('nodename')
                if not shader_node_name:
                    # Look for a nested shader definition
                    internal_shader_elem = shader_input.find('*')
                    if internal_shader_elem is not None:
                        shader_node_name = internal_shader_elem.get('name')

            if shader_node_name:
                mat = Material(name=mat_name, shader_node=shader_node_name)
                materials.append(mat)
            else:
                print(f"Warning: Could not determine shader for material '{mat_name}'")
        return materials 