from .data import MaterialXDocument, Material as MtlxMaterial

class MaterialHelper:
    """
    A helper class that stores context for building a single Blender material.
    This makes it easier to pass around state instead of passing many
    arguments to every function.
    """
    def __init__(self, doc: MaterialXDocument, mtlx_mat: MtlxMaterial, bl_mat, vertex_color_name: str = None):
        self.doc = doc
        self.mtlx_mat = mtlx_mat
        self.bl_mat = bl_mat
        self.node_tree = bl_mat.node_tree
        self.nodes = bl_mat.node_tree.nodes
        self.links = bl_mat.node_tree.links
        self.vertex_color_name = vertex_color_name
        
        # A cache to store created Blender nodes corresponding to MaterialX nodes
        # Key: MaterialX node name, Value: Blender node
        self.node_cache = {}

    def get_blender_node(self, mtlx_node_name: str):
        """Retrieves a Blender node from the cache."""
        return self.node_cache.get(mtlx_node_name)

    def add_blender_node(self, mtlx_node_name: str, blender_node):
        """Adds a newly created Blender node to the cache."""
        self.node_cache[mtlx_node_name] = blender_node

    def is_opaque(self):
        """
        Determines if the material is opaque.
        (This is a placeholder for future logic based on material properties)
        """
        # In a real scenario, you would inspect the shader graph to determine this.
        # For now, we assume all materials are opaque.
        return True 