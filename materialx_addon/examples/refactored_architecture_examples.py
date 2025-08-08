"""
Examples of Refactored Architecture Components

This file demonstrates how the MaterialX addon could be refactored
to improve maintainability, modularity, and extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

# ============================================================================
# 1. BASE CLASSES AND INTERFACES
# ============================================================================

class MaterialXExportError(Exception):
    """Base exception for MaterialX export errors"""
    pass

class UnsupportedNodeError(MaterialXExportError):
    """Raised when encountering unsupported node types"""
    pass

class ValidationError(MaterialXExportError):
    """Raised when MaterialX validation fails"""
    pass

@dataclass
class ExportOptions:
    """Configuration options for MaterialX export"""
    materialx_version: str = "1.39"
    export_textures: bool = True
    copy_textures: bool = True
    relative_paths: bool = True
    strict_mode: bool = True
    optimize_document: bool = True
    advanced_validation: bool = True
    performance_monitoring: bool = True

@dataclass
class ExportResult:
    """Result of a MaterialX export operation"""
    success: bool
    output_path: str
    error: Optional[str] = None
    unsupported_nodes: List[Dict[str, str]] = None
    performance_stats: Dict[str, Any] = None
    validation_results: Dict[str, Any] = None

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

# ============================================================================
# 2. ABSTRACT BASE CLASSES
# ============================================================================

class BaseNodeMapper(ABC):
    """Abstract base class for node mappers"""
    
    @abstractmethod
    def can_map(self, node_type: str) -> bool:
        """Check if this mapper can handle the given node type"""
        pass
    
    @abstractmethod
    def map_node(self, node: Any, builder: Any, context: Dict[str, Any]) -> str:
        """Map a Blender node to MaterialX format"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get list of supported node types"""
        pass

class BaseExporter(ABC):
    """Abstract base class for exporters"""
    
    def __init__(self, options: ExportOptions, logger: logging.Logger):
        self.options = options
        self.logger = logger
    
    @abstractmethod
    def export(self, source: Any, target_path: str) -> ExportResult:
        """Export the source to the target path"""
        pass

# ============================================================================
# 3. NODE MAPPER REGISTRY (DRY Pattern)
# ============================================================================

class NodeMapperRegistry:
    """Registry for node mappers with automatic discovery"""
    
    def __init__(self):
        self._mappers: Dict[str, Type[BaseNodeMapper]] = {}
        self._default_mapper: Optional[Type[BaseNodeMapper]] = None
        self._load_mappers()
    
    def register_mapper(self, node_type: str, mapper_class: Type[BaseNodeMapper]):
        """Register a mapper for a specific node type"""
        self._mappers[node_type] = mapper_class
        self.logger.debug(f"Registered mapper for node type: {node_type}")
    
    def register_default_mapper(self, mapper_class: Type[BaseNodeMapper]):
        """Register a default mapper for unsupported node types"""
        self._default_mapper = mapper_class
    
    def get_mapper(self, node_type: str) -> BaseNodeMapper:
        """Get the appropriate mapper for a node type"""
        mapper_class = self._mappers.get(node_type, self._default_mapper)
        if mapper_class is None:
            raise UnsupportedNodeError(f"No mapper found for node type: {node_type}")
        return mapper_class()
    
    def _load_mappers(self):
        """Automatically discover and load mappers"""
        # This would use importlib to discover mapper classes
        # and register them automatically
        pass

# ============================================================================
# 4. CONFIGURATION-DRIVEN NODE DEFINITIONS
# ============================================================================

NODE_DEFINITIONS = {
    "TEX_COORD": {
        "materialx_type": "texcoord",
        "category": "vector2",
        "inputs": {},
        "outputs": {
            "Generated": "out",
            "Normal": "out",
            "UV": "out",
            "Object": "out",
            "Camera": "out",
            "Window": "out",
            "Reflection": "out"
        }
    },
    "RGB": {
        "materialx_type": "constant",
        "category": "color3",
        "inputs": {},
        "outputs": {
            "Color": "out"
        }
    },
    "MIX": {
        "materialx_type": "mix",
        "category": "color3",
        "inputs": {
            "A": "fg",
            "B": "bg",
            "Factor": "mix",
            "Color1": "fg",
            "Color2": "bg",
            "Fac": "mix"
        },
        "outputs": {
            "Result": "out"
        }
    }
}

class ConfigurationDrivenMapper(BaseNodeMapper):
    """Mapper that uses configuration to handle node mapping"""
    
    def __init__(self, node_type: str):
        self.node_type = node_type
        self.definition = NODE_DEFINITIONS.get(node_type)
        if not self.definition:
            raise ValueError(f"No definition found for node type: {node_type}")
    
    def can_map(self, node_type: str) -> bool:
        return node_type == self.node_type
    
    def map_node(self, node: Any, builder: Any, context: Dict[str, Any]) -> str:
        """Map node using configuration definition"""
        # Implementation would use self.definition to map inputs/outputs
        return f"{self.node_type}_mapped"
    
    def get_supported_types(self) -> List[str]:
        return [self.node_type]

# ============================================================================
# 5. UTILITY CLASSES (DRY Pattern)
# ============================================================================

class NodeUtils:
    """Utility class for common node operations"""
    
    @staticmethod
    def get_input_value_or_connection(node: Any, input_name: str, 
                                    exported_nodes: Optional[Dict] = None) -> tuple[bool, Any, str]:
        """Get input value or connection for a node"""
        if not hasattr(node, 'inputs'):
            raise AttributeError(f"Node {node} has no 'inputs' attribute")
        
        if input_name not in node.inputs:
            raise KeyError(f"Input '{input_name}' not found in node {node.name}")
        
        input_socket = node.inputs[input_name]
        if input_socket.is_linked and input_socket.links:
            from_node = input_socket.links[0].from_node
            if exported_nodes is not None and from_node in exported_nodes:
                return True, exported_nodes[from_node], str(input_socket.type)
            else:
                return True, from_node.name, str(input_socket.type)
        else:
            value = getattr(input_socket, 'default_value', None)
            return False, value, str(input_socket.type)
    
    @staticmethod
    def format_socket_value(value: Any) -> str:
        """Format a socket value for MaterialX"""
        if isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        return str(value)

class PerformanceMonitor:
    """Utility for monitoring performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, float] = {}
    
    def start_timer(self, name: str):
        """Start timing an operation"""
        import time
        self.metrics[f"{name}_start"] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timing an operation and return duration"""
        import time
        start_time = self.metrics.get(f"{name}_start")
        if start_time is None:
            raise ValueError(f"No start time found for {name}")
        
        duration = time.time() - start_time
        self.metrics[name] = duration
        self.logger.debug(f"{name} took {duration:.3f} seconds")
        return duration
    
    def get_metrics(self) -> Dict[str, float]:
        """Get all collected metrics"""
        return self.metrics.copy()

# ============================================================================
# 6. REFACTORED MAIN EXPORTER
# ============================================================================

class MaterialExporter(BaseExporter):
    """Refactored material exporter with better separation of concerns"""
    
    def __init__(self, options: ExportOptions, logger: logging.Logger):
        super().__init__(options, logger)
        self.mapper_registry = NodeMapperRegistry()
        self.performance_monitor = PerformanceMonitor(logger)
        self.node_utils = NodeUtils()
    
    def export(self, material: Any, target_path: str) -> ExportResult:
        """Export a material to MaterialX format"""
        self.performance_monitor.start_timer("total_export")
        
        try:
            # Validate input
            if not material.use_nodes:
                return self._export_basic_material(material, target_path)
            
            # Find output node
            output_node = self._find_output_node(material)
            if not output_node:
                return ExportResult(
                    success=False,
                    output_path=target_path,
                    error="No output node found"
                )
            
            # Build dependency graph
            dependencies = self._build_dependencies(output_node)
            
            # Export nodes
            exported_nodes = self._export_nodes(dependencies)
            
            # Build MaterialX document
            document = self._build_document(material, exported_nodes, output_node)
            
            # Validate and optimize
            if self.options.advanced_validation:
                validation_result = self._validate_document(document)
                if not validation_result["valid"]:
                    return ExportResult(
                        success=False,
                        output_path=target_path,
                        error=f"Validation failed: {validation_result['errors']}"
                    )
            
            if self.options.optimize_document:
                self._optimize_document(document)
            
            # Write file
            self._write_document(document, target_path)
            
            # Export textures if needed
            if self.options.export_textures:
                self._export_textures(material, target_path)
            
            self.performance_monitor.end_timer("total_export")
            
            return ExportResult(
                success=True,
                output_path=target_path,
                performance_stats=self.performance_monitor.get_metrics()
            )
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return ExportResult(
                success=False,
                output_path=target_path,
                error=str(e)
            )
    
    def _export_nodes(self, nodes: List[Any]) -> Dict[str, str]:
        """Export a list of nodes using the mapper registry"""
        exported_nodes = {}
        
        for node in nodes:
            try:
                mapper = self.mapper_registry.get_mapper(node.type)
                node_name = mapper.map_node(node, None, {"exported_nodes": exported_nodes})
                exported_nodes[node] = node_name
            except UnsupportedNodeError as e:
                self.logger.warning(f"Unsupported node: {node.name} ({node.type})")
                # Continue with other nodes
            except Exception as e:
                self.logger.error(f"Failed to export node {node.name}: {e}")
                # Continue with other nodes
        
        return exported_nodes
    
    def _build_dependencies(self, output_node: Any) -> List[Any]:
        """Build dependency graph for nodes"""
        # Implementation would traverse the node graph
        # and return nodes in dependency order
        return []
    
    def _find_output_node(self, material: Any) -> Optional[Any]:
        """Find the material output node"""
        # Implementation would search for output node
        return None
    
    def _build_document(self, material: Any, exported_nodes: Dict, output_node: Any) -> Any:
        """Build the MaterialX document"""
        # Implementation would create MaterialX document
        return None
    
    def _validate_document(self, document: Any) -> Dict[str, Any]:
        """Validate the MaterialX document"""
        # Implementation would validate document
        return {"valid": True, "errors": []}
    
    def _optimize_document(self, document: Any):
        """Optimize the MaterialX document"""
        # Implementation would optimize document
        pass
    
    def _write_document(self, document: Any, path: str):
        """Write the MaterialX document to file"""
        # Implementation would write document to file
        pass
    
    def _export_textures(self, material: Any, base_path: str):
        """Export textures associated with the material"""
        # Implementation would export textures
        pass
    
    def _export_basic_material(self, material: Any, target_path: str) -> ExportResult:
        """Export a basic material without nodes"""
        # Implementation would export basic material
        return ExportResult(success=True, output_path=target_path)

# ============================================================================
# 7. FACTORY PATTERN FOR EXPORTERS
# ============================================================================

class ExporterFactory:
    """Factory for creating exporters"""
    
    @staticmethod
    def create_material_exporter(options: ExportOptions, logger: logging.Logger) -> MaterialExporter:
        """Create a material exporter"""
        return MaterialExporter(options, logger)
    
    @staticmethod
    def create_batch_exporter(options: ExportOptions, logger: logging.Logger) -> 'BatchExporter':
        """Create a batch exporter"""
        return BatchExporter(options, logger)

# ============================================================================
# 8. BATCH EXPORT WITH PARALLEL PROCESSING
# ============================================================================

class BatchExporter(BaseExporter):
    """Batch exporter for multiple materials"""
    
    def __init__(self, options: ExportOptions, logger: logging.Logger):
        super().__init__(options, logger)
        self.material_exporter = MaterialExporter(options, logger)
    
    def export(self, materials: List[Any], target_directory: str) -> ExportResult:
        """Export multiple materials"""
        results = {}
        
        # Could implement parallel processing here
        for material in materials:
            output_path = Path(target_directory) / f"{material.name}.mtlx"
            result = self.material_exporter.export(material, str(output_path))
            results[material.name] = result
        
        # Aggregate results
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)
        
        return ExportResult(
            success=success_count == total_count,
            output_path=target_directory,
            performance_stats={"success_count": success_count, "total_count": total_count}
        )

# ============================================================================
# 9. USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example of how the refactored architecture would be used"""
    
    # Setup
    options = ExportOptions(
        materialx_version="1.39",
        export_textures=True,
        strict_mode=True
    )
    
    logger = logging.getLogger("MaterialX")
    logger.setLevel(logging.INFO)
    
    # Create exporter
    exporter = ExporterFactory.create_material_exporter(options, logger)
    
    # Export material (assuming we have a material object)
    # material = bpy.data.materials["MyMaterial"]
    # result = exporter.export(material, "/path/to/output.mtlx")
    
    # Check result
    # if result.success:
    #     print(f"Export successful: {result.output_path}")
    #     print(f"Performance: {result.performance_stats}")
    # else:
    #     print(f"Export failed: {result.error}")

if __name__ == "__main__":
    example_usage()
