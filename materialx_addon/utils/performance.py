#!/usr/bin/env python3
"""
MaterialX Addon Performance Monitoring

This module provides performance monitoring utilities for tracking timing
and performance metrics throughout the MaterialX export process.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from .constants import PERFORMANCE_THRESHOLDS
from .exceptions import PerformanceError


@dataclass
class PerformanceMetric:
    """Data class for storing performance metric information."""
    
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate duration when end_time is set."""
        if self.end_time is not None and self.duration is None:
            self.duration = self.end_time - self.start_time


class PerformanceMonitor:
    """
    Performance monitoring utility for tracking timing and performance metrics.
    
    This class provides methods to track the performance of various operations
    during the MaterialX export process, including timing, success rates, and
    performance threshold monitoring.
    """
    
    def __init__(self, enable_threshold_monitoring: bool = True):
        """
        Initialize the performance monitor.
        
        Args:
            enable_threshold_monitoring: Whether to monitor performance thresholds
        """
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.enable_threshold_monitoring = enable_threshold_monitoring
        self.operation_stack: List[str] = []
    
    def start_timer(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start timing an operation.
        
        Args:
            operation: Name of the operation to time
            metadata: Optional metadata to associate with the operation
        """
        start_time = time.time()
        self.metrics[operation] = PerformanceMetric(
            operation=operation,
            start_time=start_time,
            metadata=metadata or {}
        )
        self.operation_stack.append(operation)
    
    def end_timer(self, operation: str, success: bool = True) -> float:
        """
        End timing an operation and return duration.
        
        Args:
            operation: Name of the operation to end timing for
            success: Whether the operation was successful
            
        Returns:
            Duration of the operation in seconds
            
        Raises:
            ValueError: If no start time found for the operation
            PerformanceError: If performance threshold is exceeded
        """
        if operation not in self.metrics:
            raise ValueError(f"No start time found for operation: {operation}")
        
        end_time = time.time()
        metric = self.metrics[operation]
        metric.end_time = end_time
        metric.duration = end_time - metric.start_time
        metric.success = success
        
        # Remove from operation stack
        if operation in self.operation_stack:
            self.operation_stack.remove(operation)
        
        # Check performance threshold if monitoring is enabled
        if self.enable_threshold_monitoring:
            self._check_performance_threshold(operation, metric.duration)
        
        return metric.duration
    
    def _check_performance_threshold(self, operation: str, duration: float):
        """
        Check if an operation exceeds performance thresholds.
        
        Args:
            operation: Name of the operation
            duration: Duration of the operation
            
        Raises:
            PerformanceError: If threshold is exceeded
        """
        # Map operation names to threshold keys
        threshold_mapping = {
            'export': 'EXPORT_WARNING',
            'validation': 'VALIDATION_WARNING',
            'optimization': 'OPTIMIZATION_WARNING',
        }
        
        threshold_key = None
        for op_prefix, key in threshold_mapping.items():
            if operation.lower().startswith(op_prefix):
                threshold_key = key
                break
        
        if threshold_key and threshold_key in PERFORMANCE_THRESHOLDS:
            threshold = PERFORMANCE_THRESHOLDS[threshold_key]
            if duration > threshold:
                raise PerformanceError(operation, duration, threshold)
    
    def get_metrics(self) -> Dict[str, PerformanceMetric]:
        """
        Get all collected performance metrics.
        
        Returns:
            Dictionary of operation names to PerformanceMetric objects
        """
        return self.metrics.copy()
    
    def get_metric(self, operation: str) -> Optional[PerformanceMetric]:
        """
        Get a specific performance metric.
        
        Args:
            operation: Name of the operation
            
        Returns:
            PerformanceMetric object if found, None otherwise
        """
        return self.metrics.get(operation)
    
    def get_total_duration(self) -> float:
        """
        Get the total duration of all completed operations.
        
        Returns:
            Total duration in seconds
        """
        total = 0.0
        for metric in self.metrics.values():
            if metric.duration is not None:
                total += metric.duration
        return total
    
    def get_success_rate(self) -> float:
        """
        Get the success rate of all completed operations.
        
        Returns:
            Success rate as a percentage (0.0 to 1.0)
        """
        if not self.metrics:
            return 1.0
        
        successful = sum(1 for metric in self.metrics.values() 
                        if metric.end_time is not None and metric.success)
        total = sum(1 for metric in self.metrics.values() 
                   if metric.end_time is not None)
        
        return successful / total if total > 0 else 1.0
    
    def get_slowest_operation(self) -> Optional[PerformanceMetric]:
        """
        Get the slowest completed operation.
        
        Returns:
            PerformanceMetric of the slowest operation, or None if no operations completed
        """
        completed_metrics = [metric for metric in self.metrics.values() 
                           if metric.duration is not None]
        
        if not completed_metrics:
            return None
        
        return max(completed_metrics, key=lambda m: m.duration)
    
    def get_fastest_operation(self) -> Optional[PerformanceMetric]:
        """
        Get the fastest completed operation.
        
        Returns:
            PerformanceMetric of the fastest operation, or None if no operations completed
        """
        completed_metrics = [metric for metric in self.metrics.values() 
                           if metric.duration is not None]
        
        if not completed_metrics:
            return None
        
        return min(completed_metrics, key=lambda m: m.duration)
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all performance metrics.
        
        Returns:
            Dictionary containing performance summary statistics
        """
        completed_metrics = [metric for metric in self.metrics.values() 
                           if metric.duration is not None]
        
        if not completed_metrics:
            return {
                'total_operations': 0,
                'completed_operations': 0,
                'total_duration': 0.0,
                'success_rate': 1.0,
                'average_duration': 0.0,
                'slowest_operation': None,
                'fastest_operation': None
            }
        
        durations = [metric.duration for metric in completed_metrics]
        successful = sum(1 for metric in completed_metrics if metric.success)
        
        return {
            'total_operations': len(self.metrics),
            'completed_operations': len(completed_metrics),
            'total_duration': sum(durations),
            'success_rate': successful / len(completed_metrics),
            'average_duration': sum(durations) / len(durations),
            'slowest_operation': {
                'name': self.get_slowest_operation().operation,
                'duration': self.get_slowest_operation().duration
            },
            'fastest_operation': {
                'name': self.get_fastest_operation().operation,
                'duration': self.get_fastest_operation().duration
            }
        }
    
    def reset(self):
        """Reset all performance metrics."""
        self.metrics.clear()
        self.operation_stack.clear()
    
    def is_operation_running(self, operation: str) -> bool:
        """
        Check if an operation is currently running.
        
        Args:
            operation: Name of the operation to check
            
        Returns:
            True if the operation is running, False otherwise
        """
        return operation in self.operation_stack
    
    def get_running_operations(self) -> List[str]:
        """
        Get a list of currently running operations.
        
        Returns:
            List of operation names that are currently running
        """
        return self.operation_stack.copy()


class PerformanceContext:
    """
    Context manager for automatic performance monitoring.
    
    This class can be used as a context manager to automatically
    start and end timing for operations.
    """
    
    def __init__(self, monitor: PerformanceMonitor, operation: str, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize the performance context.
        
        Args:
            monitor: PerformanceMonitor instance to use
            operation: Name of the operation to monitor
            metadata: Optional metadata for the operation
        """
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata
        self.success = True
    
    def __enter__(self):
        """Start timing the operation."""
        self.monitor.start_timer(self.operation, self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing the operation."""
        # Mark as failed if an exception occurred
        if exc_type is not None:
            self.success = False
        
        try:
            self.monitor.end_timer(self.operation, self.success)
        except (ValueError, PerformanceError):
            # Don't let performance monitoring errors mask the original error
            pass


# Convenience function for creating performance contexts
def monitor_performance(monitor: PerformanceMonitor, operation: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> PerformanceContext:
    """
    Create a performance monitoring context.
    
    Args:
        monitor: PerformanceMonitor instance to use
        operation: Name of the operation to monitor
        metadata: Optional metadata for the operation
        
    Returns:
        PerformanceContext that can be used as a context manager
    """
    return PerformanceContext(monitor, operation, metadata)


# Example usage:
# with monitor_performance(perf_monitor, "export_material", {"material": "MyMaterial"}):
#     # Export operation here
#     pass
