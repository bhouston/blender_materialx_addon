from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Input:
    """Represents an input on a MaterialX node."""
    name: str
    type: str
    value: Any = None
    nodename: str = None
    output: str = None
    
@dataclass
class Node:
    """Represents a generic node in a MaterialX nodegraph."""
    category: str
    name: str
    type: str
    inputs: Dict[str, Input] = field(default_factory=dict)

@dataclass
class NodeGraph:
    """Represents a MaterialX nodegraph."""
    name: str
    nodes: List[Node] = field(default_factory=list)
    inputs: List[Input] = field(default_factory=list)
    outputs: List[Any] = field(default_factory=list) # Not used yet, but good for future
    elem: Any = None # Keep a reference to the XML element for post-processing

@dataclass
class Material:
    """Represents a MaterialX surfacematerial."""
    name: str
    shader_node: str

@dataclass
class MaterialXDocument:
    """Represents the entire parsed MaterialX document."""
    version: str
    nodegraphs: List[NodeGraph] = field(default_factory=list)
    materials: List[Material] = field(default_factory=list)

    def get_node(self, node_name: str):
        """
        Find a node by name. Handles both direct names and scoped names
        (e.g., 'nodegraph_name.node_name').
        """
        if not node_name:
            return None
            
        if '.' in node_name:
            graph_name, n_name = node_name.split('.', 1)
            for graph in self.nodegraphs:
                if graph.name == graph_name:
                    for node in graph.nodes:
                        if node.name == n_name:
                            return node
        else:
            # Fallback for non-scoped names
            for graph in self.nodegraphs:
                for node in graph.nodes:
                    if node.name == node_name:
                        return node
                        
        return None 