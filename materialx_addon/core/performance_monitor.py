#!/usr/bin/env python3
"""
MaterialX Performance Monitor

This module provides performance monitoring functionality for MaterialX operations.
"""

import time
import logging
from typing import Dict, List, Any

# Optional import for psutil (performance monitoring)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MaterialXPerformanceMonitor:
    """
    Monitors performance of MaterialX operations.
    
    This class tracks:
    - Operation timing
    - Memory usage
    - Performance bottlenecks
    - Optimization suggestions
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.operations = {}
        self.start_times = {}
        self.memory_usage = []
        self.initial_memory = self._get_memory_usage()
    
    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        self.start_times[operation_name] = time.time()
        if operation_name not in self.operations:
            self.operations[operation_name] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'avg_time': 0.0
            }
    
    def end_operation(self, operation_name: str):
        """End timing an operation and record statistics."""
        if operation_name in self.start_times:
            elapsed_time = time.time() - self.start_times[operation_name]
            del self.start_times[operation_name]
            
            op_stats = self.operations[operation_name]
            op_stats['count'] += 1
            op_stats['total_time'] += elapsed_time
            op_stats['min_time'] = min(op_stats['min_time'], elapsed_time)
            op_stats['max_time'] = max(op_stats['max_time'], elapsed_time)
            op_stats['avg_time'] = op_stats['total_time'] / op_stats['count']
            
            # Record memory usage
            current_memory = self._get_memory_usage()
            self.memory_usage.append({
                'operation': operation_name,
                'memory': current_memory,
                'timestamp': time.time()
            })
            
            self.logger.debug(f"Operation '{operation_name}' completed in {elapsed_time:.4f}s")
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        if not PSUTIL_AVAILABLE:
            return 0
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except:
            return 0
    
    def suggest_optimizations(self) -> List[str]:
        """Suggest performance optimizations based on collected data."""
        suggestions = []
        
        # Check for slow operations
        for op_name, stats in self.operations.items():
            if stats['avg_time'] > 1.0:  # Operations taking more than 1 second
                suggestions.append(f"Operation '{op_name}' is slow (avg: {stats['avg_time']:.2f}s). Consider optimization.")
            
            if stats['count'] > 100:  # Frequently called operations
                suggestions.append(f"Operation '{op_name}' is called frequently ({stats['count']} times). Consider caching.")
        
        # Check memory usage
        if self.memory_usage:
            latest_memory = self.memory_usage[-1]['memory']
            memory_increase = latest_memory - self.initial_memory
            if memory_increase > 100 * 1024 * 1024:  # 100MB increase
                suggestions.append(f"Memory usage increased by {memory_increase / (1024*1024):.1f}MB. Consider memory optimization.")
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            'operations': self.operations.copy(),
            'memory_usage': self.memory_usage[-10:] if self.memory_usage else [],  # Last 10 entries
            'suggestions': self.suggest_optimizations()
        }
        
        # Calculate overall statistics
        total_operations = sum(op['count'] for op in self.operations.values())
        total_time = sum(op['total_time'] for op in self.operations.values())
        
        stats['overall'] = {
            'total_operations': total_operations,
            'total_time': total_time,
            'avg_time_per_operation': total_time / total_operations if total_operations > 0 else 0
        }
        
        return stats
    
    def cleanup(self):
        """Clean up resources."""
        self.operations.clear()
        self.start_times.clear()
        self.memory_usage.clear()
