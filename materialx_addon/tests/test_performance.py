#!/usr/bin/env python3
"""
Unit Tests for Performance Monitoring

This module contains unit tests for the performance monitoring utilities.
"""

import time
from typing import List
from .test_utils import BlenderTestCase
from ..utils.performance import PerformanceMonitor, PerformanceMetric, monitor_performance


class TestPerformanceMonitor(BlenderTestCase):
    """Test PerformanceMonitor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.monitor = PerformanceMonitor()
    
    def test(self):
        """Test PerformanceMonitor functionality."""
        # Test basic timing
        self.monitor.start_timer("test_operation")
        time.sleep(0.1)  # Simulate some work
        duration = self.monitor.end_timer("test_operation")
        
        self.assertGreater(duration, 0.0)
        self.assertLess(duration, 1.0)  # Should be around 0.1 seconds
        
        # Test metrics retrieval
        metrics = self.monitor.get_metrics()
        self.assertIn("test_operation", metrics)
        self.assertIsInstance(metrics["test_operation"], PerformanceMetric)
        
        # Test success/failure tracking
        self.monitor.start_timer("success_operation")
        time.sleep(0.01)
        self.monitor.end_timer("success_operation", success=True)
        
        self.monitor.start_timer("failure_operation")
        time.sleep(0.01)
        self.monitor.end_timer("failure_operation", success=False)
        
        # Test success rate
        success_rate = self.monitor.get_success_rate()
        self.assertEqual(success_rate, 0.5)  # 2 operations, 1 success, 1 failure
        
        # Test total duration
        total_duration = self.monitor.get_total_duration()
        self.assertGreater(total_duration, 0.0)


class TestPerformanceMonitorThresholds(BlenderTestCase):
    """Test PerformanceMonitor threshold functionality."""
    
    def test(self):
        """Test PerformanceMonitor threshold functionality."""
        monitor = PerformanceMonitor(enable_threshold_monitoring=True)
        
        # Test operation that doesn't exceed threshold
        monitor.start_timer("fast_operation")
        time.sleep(0.01)
        duration = monitor.end_timer("fast_operation")
        self.assertGreater(duration, 0.0)
        
        # Test operation that exceeds threshold
        monitor.start_timer("slow_export_operation")
        time.sleep(0.1)  # This should exceed the export warning threshold
        
        # This should raise a PerformanceError
        self.assertRaises(Exception, monitor.end_timer, "slow_export_operation")
        
        # Test with threshold monitoring disabled
        monitor_disabled = PerformanceMonitor(enable_threshold_monitoring=False)
        monitor_disabled.start_timer("slow_operation")
        time.sleep(0.1)
        duration = monitor_disabled.end_timer("slow_operation")
        self.assertGreater(duration, 0.0)


class TestPerformanceMonitorStatistics(BlenderTestCase):
    """Test PerformanceMonitor statistics functionality."""
    
    def test(self):
        """Test PerformanceMonitor statistics functionality."""
        monitor = PerformanceMonitor()
        
        # Add some test operations
        monitor.start_timer("fast_operation")
        time.sleep(0.01)
        monitor.end_timer("fast_operation")
        
        monitor.start_timer("medium_operation")
        time.sleep(0.05)
        monitor.end_timer("medium_operation")
        
        monitor.start_timer("slow_operation")
        time.sleep(0.1)
        monitor.end_timer("slow_operation")
        
        # Test statistics
        summary = monitor.get_operation_summary()
        
        self.assertEqual(summary['total_operations'], 3)
        self.assertEqual(summary['completed_operations'], 3)
        self.assertGreater(summary['total_duration'], 0.0)
        self.assertEqual(summary['success_rate'], 1.0)
        self.assertGreater(summary['average_duration'], 0.0)
        
        # Test slowest and fastest operations
        slowest = monitor.get_slowest_operation()
        fastest = monitor.get_fastest_operation()
        
        self.assertIsNotNone(slowest)
        self.assertIsNotNone(fastest)
        self.assertEqual(slowest.operation, "slow_operation")
        self.assertEqual(fastest.operation, "fast_operation")
        self.assertGreater(slowest.duration, fastest.duration)


class TestPerformanceMonitorOperations(BlenderTestCase):
    """Test PerformanceMonitor operation tracking."""
    
    def test(self):
        """Test PerformanceMonitor operation tracking."""
        monitor = PerformanceMonitor()
        
        # Test operation stack
        self.assertFalse(monitor.is_operation_running("test_op"))
        self.assertEqual(len(monitor.get_running_operations()), 0)
        
        monitor.start_timer("test_op")
        self.assertTrue(monitor.is_operation_running("test_op"))
        self.assertIn("test_op", monitor.get_running_operations())
        
        monitor.end_timer("test_op")
        self.assertFalse(monitor.is_operation_running("test_op"))
        self.assertEqual(len(monitor.get_running_operations()), 0)
        
        # Test multiple operations
        monitor.start_timer("op1")
        monitor.start_timer("op2")
        
        self.assertTrue(monitor.is_operation_running("op1"))
        self.assertTrue(monitor.is_operation_running("op2"))
        self.assertEqual(len(monitor.get_running_operations()), 2)
        
        monitor.end_timer("op1")
        self.assertFalse(monitor.is_operation_running("op1"))
        self.assertTrue(monitor.is_operation_running("op2"))
        self.assertEqual(len(monitor.get_running_operations()), 1)
        
        monitor.end_timer("op2")
        self.assertFalse(monitor.is_operation_running("op2"))
        self.assertEqual(len(monitor.get_running_operations()), 0)


class TestPerformanceMonitorReset(BlenderTestCase):
    """Test PerformanceMonitor reset functionality."""
    
    def test(self):
        """Test PerformanceMonitor reset functionality."""
        monitor = PerformanceMonitor()
        
        # Add some operations
        monitor.start_timer("test_op")
        time.sleep(0.01)
        monitor.end_timer("test_op")
        
        # Verify operations exist
        metrics = monitor.get_metrics()
        self.assertIn("test_op", metrics)
        
        # Reset
        monitor.reset()
        
        # Verify operations are cleared
        metrics = monitor.get_metrics()
        self.assertEqual(len(metrics), 0)
        self.assertEqual(len(monitor.get_running_operations()), 0)


class TestPerformanceMetric(BlenderTestCase):
    """Test PerformanceMetric data class."""
    
    def test(self):
        """Test PerformanceMetric data class."""
        # Test creation
        metric = PerformanceMetric(
            operation="test_op",
            start_time=time.time(),
            metadata={"key": "value"}
        )
        
        self.assertEqual(metric.operation, "test_op")
        self.assertIsInstance(metric.start_time, float)
        self.assertIsNone(metric.end_time)
        self.assertIsNone(metric.duration)
        self.assertTrue(metric.success)
        self.assertEqual(metric.metadata, {"key": "value"})
        
        # Test duration calculation
        metric.end_time = metric.start_time + 1.0
        # The __post_init__ should calculate duration
        self.assertEqual(metric.duration, 1.0)


class TestPerformanceContext(BlenderTestCase):
    """Test PerformanceContext context manager."""
    
    def test(self):
        """Test PerformanceContext context manager."""
        monitor = PerformanceMonitor()
        
        # Test successful operation
        with monitor_performance(monitor, "context_test"):
            time.sleep(0.01)
        
        # Verify operation was recorded
        metrics = monitor.get_metrics()
        self.assertIn("context_test", metrics)
        self.assertTrue(metrics["context_test"].success)
        self.assertGreater(metrics["context_test"].duration, 0.0)
        
        # Test operation with exception
        try:
            with monitor_performance(monitor, "exception_test"):
                time.sleep(0.01)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify operation was recorded as failed
        metrics = monitor.get_metrics()
        self.assertIn("exception_test", metrics)
        self.assertFalse(metrics["exception_test"].success)


class TestPerformanceMonitorErrorHandling(BlenderTestCase):
    """Test PerformanceMonitor error handling."""
    
    def test(self):
        """Test PerformanceMonitor error handling."""
        monitor = PerformanceMonitor()
        
        # Test ending timer that wasn't started
        self.assertRaises(ValueError, monitor.end_timer, "nonexistent_operation")
        
        # Test getting metric that doesn't exist
        metric = monitor.get_metric("nonexistent")
        self.assertIsNone(metric)
        
        # Test statistics with no operations
        summary = monitor.get_operation_summary()
        self.assertEqual(summary['total_operations'], 0)
        self.assertEqual(summary['completed_operations'], 0)
        self.assertEqual(summary['total_duration'], 0.0)
        self.assertEqual(summary['success_rate'], 1.0)
        self.assertEqual(summary['average_duration'], 0.0)
        
        # Test slowest/fastest with no operations
        slowest = monitor.get_slowest_operation()
        fastest = monitor.get_fastest_operation()
        self.assertIsNone(slowest)
        self.assertIsNone(fastest)


def create_performance_tests() -> List[BlenderTestCase]:
    """
    Create all performance test cases.
    
    Returns:
        List of performance test cases
    """
    return [
        TestPerformanceMonitor("PerformanceMonitor"),
        TestPerformanceMonitorThresholds("PerformanceMonitorThresholds"),
        TestPerformanceMonitorStatistics("PerformanceMonitorStatistics"),
        TestPerformanceMonitorOperations("PerformanceMonitorOperations"),
        TestPerformanceMonitorReset("PerformanceMonitorReset"),
        TestPerformanceMetric("PerformanceMetric"),
        TestPerformanceContext("PerformanceContext"),
        TestPerformanceMonitorErrorHandling("PerformanceMonitorErrorHandling")
    ]
