import bpy
from .data import MaterialXDocument, Node as MtlxNode
from .utils import MaterialHelper
from . import mapping

class MaterialBuilder:
    """Builds a Blender material from a MaterialX document."""
    
    def __init__(self, doc: MaterialXDocument, mtlx_mat, vertex_color_name=None):
        self._doc = doc
        self._mtlx_mat = mtlx_mat
        self._vertex_color_name = vertex_color_name
        
    def build(self):
        """
        Creates and builds a Blender material, returning the created material.
        """
        # 1. Create a new Blender material
        bl_mat_name = self._mtlx_mat.name or "MaterialX_Material"
        bl_mat = bpy.data.materials.new(name=bl_mat_name)
        bl_mat.use_nodes = True
        bl_mat.use_fake_user = True # Prevent garbage collection
        
        # 2. Clear the default node tree
        tree = bl_mat.node_tree
        tree.nodes.clear()
        
        # 3. Create the MaterialHelper
        mh = MaterialHelper(self._doc, self._mtlx_mat, bl_mat, self._vertex_color_name)
        
        # 4. Create the final output node
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (400, 0)
        
        # 5. Find the root shader node in the MaterialX data, resolving through containers
        root_shader_mtlx_node = None
        shader_ref_name = self._mtlx_mat.shader_node
        
        for _ in range(10): # Use a loop to resolve references, with a max depth of 10
            if not shader_ref_name:
                break
                
            candidate_node = self._doc.get_node(shader_ref_name)
            if not candidate_node:
                print(f"Error: Could not find referenced node '{shader_ref_name}'")
                break
            
            # If it's a container, get the next reference and continue looping
            if candidate_node.category == 'surfacematerial':
                shader_input = candidate_node.inputs.get('surfaceshader')
                if shader_input and shader_input.nodename:
                    shader_ref_name = shader_input.nodename
                    continue
                else:
                    # It's a container with no output, dead end.
                    break
            else:
                # This is a renderable shader node, we're done.
                root_shader_mtlx_node = candidate_node
                break

        if not root_shader_mtlx_node:
            print(f"Error: Could not find a renderable root shader for material '{self._mtlx_mat.name}'")
            return bl_mat # Return the empty material
            
        # 6. Recursively build the node tree starting from the root shader
        root_shader_bl_node = self._get_or_create_node(mh, root_shader_mtlx_node)
        
        # Check for and create UV map node if needed
        if self._is_uv_needed(mh):
            self._create_uv_map_node(mh)

        # 7. Connect the root shader to the material output
        if root_shader_bl_node:
            shader_output_socket = self._find_shader_output(root_shader_bl_node)
            if shader_output_socket:
                tree.links.new(shader_output_socket, output_node.inputs['Surface'])
            else:
                print(f"Warning: Could not find a suitable output socket on root shader node '{root_shader_bl_node.name}'")
        else:
            print(f"Error: Failed to create the root shader node for material '{self._mtlx_mat.name}'")
            
        return bl_mat

    def _is_uv_needed(self, mh: MaterialHelper) -> bool:
        """Checks if any node in the tree requires texture coordinates."""
        for graph in mh.doc.nodegraphs:
            for mtlx_node in graph.nodes:
                if mtlx_node.category in ['cellnoise3d', 'noise2d', 'noise3d'] or \
                   any(inp.type == 'vector2' and inp.name == 'texcoord' for inp in mtlx_node.inputs.values()):
                    # This is a strong hint that UVs are used.
                    # A more robust check might trace inputs of image texture nodes.
                    return True
        return False

    def _create_uv_map_node(self, mh: MaterialHelper):
        """Creates and connects a UV Map node to nodes that need it."""
        print("DEBUG: UV coordinates required, creating UV Map node.")
        
        # 1. Create the Texture Coordinate node
        tex_coord_node = mh.nodes.new('ShaderNodeTexCoord')
        tex_coord_node.location = (-800, 300) # Place it to the far left
        
        # Create a Combine XYZ node to convert UV (vec2) to a position (vec3)
        combine_xyz_node = mh.nodes.new('ShaderNodeCombineXYZ')
        combine_xyz_node.location = (-600, 300)
        mh.links.new(tex_coord_node.outputs['UV'], combine_xyz_node.inputs['X'])
        mh.links.new(tex_coord_node.outputs['UV'], combine_xyz_node.inputs['Y'])
        # Z is 0.0 by default, which is what we want.

        # 2. Find all MaterialX nodes that are placeholders for texture coordinates
        # In our case, these are often defined as an <input> in a nodegraph.
        for graph in mh.doc.nodegraphs:
            for mtlx_node in graph.nodes:
                if mtlx_node.category == 'input' and mtlx_node.type == 'vector2' and mtlx_node.name == 'texcoord':
                    # This represents the 'texcoord' input in the Mtlx nodegraph.
                    # We need to find all the nodes that *use* this input.
                    for downstream_graph in mh.doc.nodegraphs:
                        for downstream_mtlx_node in downstream_graph.nodes:
                            for mtlx_input in downstream_mtlx_node.inputs.values():
                                if mtlx_input.nodename == mtlx_node.name:
                                    # This downstream_mtlx_node is connected to our texcoord input.
                                    # Get the corresponding Blender node.
                                    downstream_bl_node = mh.get_blender_node(downstream_mtlx_node.name)
                                    if downstream_bl_node:
                                        print(f"DEBUG: Connecting UV-based Vector to {downstream_bl_node.name}")
                                        # Find the corresponding input socket on the Blender node
                                        # This mapping logic might need to be more robust.
                                        param_mapping = mapping.get_parameter_mapping(downstream_bl_node.bl_idname)
                                        bl_input_name = param_mapping.get(mtlx_input.name, mtlx_input.name)
                                        
                                        if bl_input_name in downstream_bl_node.inputs:
                                            mh.links.new(
                                                combine_xyz_node.outputs['Vector'],
                                                downstream_bl_node.inputs[bl_input_name]
                                            )
                                        else:
                                            print(f"WARN: Could not find input socket '{bl_input_name}' on node '{downstream_bl_node.name}'")


    def _get_or_create_node(self, mh: MaterialHelper, mtlx_node: MtlxNode):
        """
        Memoized/cached function to create a Blender node from a MaterialX node.
        This function is the heart of the recursive build process.
        """
        # If we have already created this node, return it from the cache
        cached_bl_node = mh.get_blender_node(mtlx_node.name)
        if cached_bl_node:
            return cached_bl_node
            
        # Handle the special case of 'ifgreater' which needs a custom subgraph
        if mtlx_node.category == 'ifgreater':
            return self._create_ifgreater_group(mh, mtlx_node)

        # 1. Find the Blender equivalent for the MaterialX node
        blender_node_type = mapping.get_blender_node_type(mtlx_node.category)
        if not blender_node_type:
            print(f"Warning: Unsupported MaterialX node category '{mtlx_node.category}'")
            return None
        
        # 2. Create the Blender node
        bl_node = mh.nodes.new(blender_node_type)
        bl_node.name = f"{mtlx_node.category}_{mtlx_node.name}"
        mh.add_blender_node(mtlx_node.name, bl_node)
        
        # 3. Set parameters and connect inputs
        for mtlx_input in mtlx_node.inputs.values():
            if mtlx_input.nodename:
                # This input is connected to another node.
                # Find the upstream MaterialX node.
                upstream_mtlx_node = mh.doc.get_node(mtlx_input.nodename)
                if upstream_mtlx_node:
                    # Recursively create the upstream Blender node
                    upstream_bl_node = self._get_or_create_node(mh, upstream_mtlx_node)
                    if upstream_bl_node:
                        # Connect the nodes
                        self._link_nodes(mh, upstream_bl_node, bl_node, mtlx_input)
            
            elif mtlx_input.value is not None:
                # This input has a static value.
                self._set_node_parameter(bl_node, mtlx_input)
                
        # Handle specific node properties after inputs are set
        mapping.set_special_node_properties(bl_node, mtlx_node)

        return bl_node
        
    def _create_ifgreater_group(self, mh: MaterialHelper, mtlx_node: MtlxNode):
        """Creates a node group to replicate the Mtlx 'ifgreater' functionality."""
        
        # This function builds: mix(in4, in3, greater_than(in1, in2))
        
        # 1. Create the Math (Greater Than) node
        math_node = mh.nodes.new('ShaderNodeMath')
        math_node.operation = 'GREATER_THAN'
        mh.add_blender_node(f"{mtlx_node.name}_math", math_node)
        
        # 2. Create the Mix node
        mix_node = mh.nodes.new('ShaderNodeMix')
        # We need to determine the data type (Color or Float)
        # This is a simplification; a robust implementation would trace input types.
        if mtlx_node.type in ['color3', 'color4']:
            mix_node.data_type = 'RGBA'
        else:
            mix_node.data_type = 'FLOAT'
        mh.add_blender_node(mtlx_node.name, mix_node) # Cache the main group node
        
        # 3. Connect the Math node to the Mix node's factor
        mh.links.new(math_node.outputs['Value'], mix_node.inputs['Factor'])
        
        # 4. Connect the Mtlx inputs to the correct nodes
        input_map = {
            'in1': (math_node, 'Value'),
            'in2': (math_node, 'Value_001'),
            'in3': (mix_node, 'B'), # Note: Mtlx in3 (if_true) maps to Blender's second socket
            'in4': (mix_node, 'A')  # Note: Mtlx in4 (if_false) maps to Blender's first socket
        }
        
        for mtlx_input_name, (bl_node, bl_socket_name) in input_map.items():
            mtlx_input = mtlx_node.inputs.get(mtlx_input_name)
            if not mtlx_input: continue
            
            if mtlx_input.nodename:
                upstream_mtlx_node = mh.doc.get_node(mtlx_input.nodename)
                if upstream_mtlx_node:
                    upstream_bl_node = self._get_or_create_node(mh, upstream_mtlx_node)
                    if upstream_bl_node:
                        # This linking needs to be more robust about finding the right output socket
                        output_socket = self._find_shader_output(upstream_bl_node) or upstream_bl_node.outputs[0]
                        mh.links.new(output_socket, bl_node.inputs[bl_socket_name])
            elif mtlx_input.value is not None:
                self._set_node_parameter(bl_node, mtlx_input, override_socket_name=bl_socket_name)

        return mix_node

    def _link_nodes(self, mh: MaterialHelper, upstream_bl_node, downstream_bl_node, mtlx_input):
        """Connects an output socket of an upstream node to an input socket of a downstream node."""
        
        # Get the mapping for the downstream node's parameters
        param_mapping = mapping.get_parameter_mapping(downstream_bl_node.bl_idname)
        blender_input_name = param_mapping.get(mtlx_input.name, mtlx_input.name)
        
        # Determine the correct output socket from the upstream node
        output_socket_name = 'Color' if mtlx_input.type == 'color3' else 'Value'
        if mtlx_input.output: # If an output is explicitly named
             output_socket_name = mtlx_input.output

        # A more robust implementation is needed here to map types correctly.
        if output_socket_name not in upstream_bl_node.outputs:
             # Fallback for common cases like BSDFs or simple value outputs
             if 'BSDF' in upstream_bl_node.outputs:
                 output_socket_name = 'BSDF'
             elif 'Shader' in upstream_bl_node.outputs:
                 output_socket_name = 'Shader'
             elif 'Color' in upstream_bl_node.outputs:
                 output_socket_name = 'Color'
             elif 'Value' in upstream_bl_node.outputs:
                 output_socket_name = 'Value'
             elif upstream_bl_node.outputs:
                 output_socket_name = upstream_bl_node.outputs[0].name
             else:
                 print(f"Warning: Could not find a suitable output socket on upstream node '{upstream_bl_node.name}'")
                 return
                 
        if blender_input_name in downstream_bl_node.inputs and output_socket_name in upstream_bl_node.outputs:
            mh.links.new(
                upstream_bl_node.outputs[output_socket_name],
                downstream_bl_node.inputs[blender_input_name]
            )
        else:
            print(f"Warning: Could not link {upstream_bl_node.name}.{output_socket_name} to {downstream_bl_node.name}.{blender_input_name}")

    def _set_node_parameter(self, bl_node, mtlx_input, override_socket_name=None):
        """Sets a static value on a Blender node's input socket."""
        param_mapping = mapping.get_parameter_mapping(bl_node.bl_idname)
        blender_param_name = override_socket_name or param_mapping.get(mtlx_input.name, mtlx_input.name)

        # A mapped value of None is a signal to skip this parameter, as it's
        # handled by a special case elsewhere (e.g., in set_special_node_properties)
        if blender_param_name is None:
            return
            
        # This is a bit of a patch. A better parser would distinguish
        # value attributes from connection attributes more cleanly.
        if isinstance(mtlx_input.value, str) and '.' in mtlx_input.value:
            # This looks like a connection (e.g., "nodename.output"), not a value.
            # The node linking logic should handle this.
            # We will attempt to parse it as a connection here as a fallback.
            parts = mtlx_input.value.split('.')
            if len(parts) == 2:
                upstream_node_name, output_socket = parts
                upstream_mtlx_node = self._doc.get_node(upstream_node_name)
                if upstream_mtlx_node:
                    # This should be handled by the nodename logic, but we can try to link it
                    # This indicates a parsing issue that should be fixed later.
                    print(f"DEBUG: Treating value '{mtlx_input.value}' as a connection.")
                    return # Skip trying to set as a value

        if blender_param_name in bl_node.inputs:
            # This is a simplified value parser. A real implementation would need
            # to handle types (color3, vector2, float, etc.) correctly.
            try:
                if 'color' in mtlx_input.type:
                    # e.g. "0.8, 0.8, 0.8"
                    parts = [float(p.strip()) for p in mtlx_input.value.split(',')]
                    bl_node.inputs[blender_param_name].default_value = (*parts, 1.0) # Add alpha
                elif mtlx_input.type == 'float':
                    bl_node.inputs[blender_param_name].default_value = float(mtlx_input.value)
                elif mtlx_input.type == 'integer':
                    bl_node.inputs[blender_param_name].default_value = int(mtlx_input.value)
                # Add more type conversions here (vector, etc.)
                else:
                    # Try a generic conversion for other types
                    bl_node.inputs[blender_param_name].default_value = float(mtlx_input.value)
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not set parameter '{blender_param_name}' on node '{bl_node.name}': {e}")
        else:
            print(f"Warning: Parameter '{blender_param_name}' not found on node '{bl_node.name}'")
            
    def _find_shader_output(self, node):
        """Find the most appropriate shader output socket."""
        preferred_outputs = ['BSDF', 'Shader', 'Emission', 'Surface']
        for out_name in preferred_outputs:
            if out_name in node.outputs:
                return node.outputs[out_name]
        
        if node.outputs:
            return node.outputs[0]
            
        return None 