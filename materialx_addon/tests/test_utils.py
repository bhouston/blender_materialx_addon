#!/usr/bin/env python3
"""
MaterialX Addon Unit Test Utilities

This module provides a unit testing framework that can run within Blender's environment.
"""

import bpy
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from ..utils.logging_utils import MaterialXLogger


@dataclass
class TestResult:
    """Result of a unit test."""
    
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BlenderTestCase:
    """
    Base class for unit tests that can run within Blender.
    
    This class provides common functionality for testing components
    that require Blender's environment.
    """
    
    def __init__(self, name: str):
        """
        Initialize the test case.
        
        Args:
            name: Name of the test case
        """
        self.name = name
        self.logger = MaterialXLogger(f"Test.{name}")
        self.setup_complete = False
    
    def setUp(self):
        """
        Set up the test environment.
        
        Override this method in subclasses to set up test-specific resources.
        """
        self.logger.debug(f"Setting up test: {self.name}")
        self.setup_complete = True
    
    def tearDown(self):
        """
        Clean up the test environment.
        
        Override this method in subclasses to clean up test-specific resources.
        """
        self.logger.debug(f"Tearing down test: {self.name}")
    
    def run(self) -> TestResult:
        """
        Run the test case.
        
        Returns:
            TestResult object with the test results
        """
        start_time = time.time()
        
        try:
            # Set up test environment
            self.setUp()
            
            # Run the actual test
            self.test()
            
            # Test passed
            duration = time.time() - start_time
            self.logger.info(f"Test PASSED: {self.name} (took {duration:.3f}s)")
            
            return TestResult(
                test_name=self.name,
                success=True,
                duration=duration
            )
            
        except Exception as e:
            # Test failed
            duration = time.time() - start_time
            error_message = str(e)
            self.logger.error(f"Test FAILED: {self.name} - {error_message}")
            
            return TestResult(
                test_name=self.name,
                success=False,
                duration=duration,
                error_message=error_message
            )
        
        finally:
            # Always clean up
            try:
                self.tearDown()
            except Exception as e:
                self.logger.warning(f"Error during tearDown for {self.name}: {e}")
    
    def test(self):
        """
        The actual test method.
        
        Override this method in subclasses to implement the test logic.
        """
        raise NotImplementedError("Subclasses must implement the test() method")
    
    def assertTrue(self, condition: bool, message: str = "Assertion failed"):
        """Assert that a condition is True."""
        if not condition:
            raise AssertionError(message)
    
    def assertFalse(self, condition: bool, message: str = "Assertion failed"):
        """Assert that a condition is False."""
        if condition:
            raise AssertionError(message)
    
    def assertEqual(self, actual: Any, expected: Any, message: str = "Values not equal"):
        """Assert that two values are equal."""
        if actual != expected:
            raise AssertionError(f"{message}: expected {expected}, got {actual}")
    
    def assertNotEqual(self, actual: Any, expected: Any, message: str = "Values should not be equal"):
        """Assert that two values are not equal."""
        if actual == expected:
            raise AssertionError(f"{message}: both values are {actual}")
    
    def assertIsNone(self, value: Any, message: str = "Value should be None"):
        """Assert that a value is None."""
        if value is not None:
            raise AssertionError(f"{message}: value is {value}")
    
    def assertIsNotNone(self, value: Any, message: str = "Value should not be None"):
        """Assert that a value is not None."""
        if value is None:
            raise AssertionError(message)
    
    def assertIn(self, item: Any, container: Any, message: str = "Item not found in container"):
        """Assert that an item is in a container."""
        if item not in container:
            raise AssertionError(f"{message}: {item} not found in {container}")
    
    def assertNotIn(self, item: Any, container: Any, message: str = "Item should not be in container"):
        """Assert that an item is not in a container."""
        if item in container:
            raise AssertionError(f"{message}: {item} found in {container}")
    
    def assertIsInstance(self, obj: Any, cls: type, message: str = "Object is not instance of expected class"):
        """Assert that an object is an instance of a specific class."""
        if not isinstance(obj, cls):
            raise AssertionError(message)
    
    def assertIs(self, first: Any, second: Any, message: str = "Objects are not the same"):
        """Assert that two objects are the same (identity comparison)."""
        if first is not second:
            raise AssertionError(message)
    
    def assertGreater(self, first: Any, second: Any, message: str = "First value is not greater than second"):
        """Assert that first value is greater than second value."""
        if not first > second:
            raise AssertionError(message)
    
    def assertLess(self, first: Any, second: Any, message: str = "First value is not less than second"):
        """Assert that first value is less than second value."""
        if not first < second:
            raise AssertionError(message)
    
    def assertRaises(self, exception_type: type, callable_obj: Callable, *args, **kwargs):
        """Assert that a callable raises a specific exception."""
        try:
            callable_obj(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__} to be raised")
        except exception_type:
            # Expected exception was raised
            pass
        except Exception as e:
            # Unexpected exception was raised
            raise AssertionError(f"Expected {exception_type.__name__}, but got {type(e).__name__}: {e}")


class TestRunner:
    """
    Test runner for executing unit tests within Blender.
    
    This class manages the execution of multiple test cases and provides
    reporting functionality.
    """
    
    def __init__(self, logger: Optional[MaterialXLogger] = None):
        """
        Initialize the test runner.
        
        Args:
            logger: Optional logger instance to use
        """
        self.logger = logger or MaterialXLogger("TestRunner")
        self.test_cases: List[BlenderTestCase] = []
        self.results: List[TestResult] = []
    
    def add_test(self, test_case: BlenderTestCase):
        """
        Add a test case to the runner.
        
        Args:
            test_case: The test case to add
        """
        self.test_cases.append(test_case)
        self.logger.debug(f"Added test case: {test_case.name}")
    
    def add_tests(self, test_cases: List[BlenderTestCase]):
        """
        Add multiple test cases to the runner.
        
        Args:
            test_cases: List of test cases to add
        """
        for test_case in test_cases:
            self.add_test(test_case)
    
    def run_tests(self) -> List[TestResult]:
        """
        Run all registered test cases.
        
        Returns:
            List of TestResult objects
        """
        self.logger.info(f"Starting test run with {len(self.test_cases)} test cases")
        self.results = []
        
        start_time = time.time()
        
        for i, test_case in enumerate(self.test_cases, 1):
            self.logger.info(f"Running test {i}/{len(self.test_cases)}: {test_case.name}")
            result = test_case.run()
            self.results.append(result)
        
        total_duration = time.time() - start_time
        self.logger.info(f"Test run completed in {total_duration:.3f}s")
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the test results.
        
        Returns:
            Dictionary containing test summary statistics
        """
        if not self.results:
            return {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0.0,
                'total_duration': 0.0,
                'average_duration': 0.0
            }
        
        total_tests = len(self.results)
        passed = sum(1 for result in self.results if result.success)
        failed = total_tests - passed
        success_rate = passed / total_tests if total_tests > 0 else 0.0
        total_duration = sum(result.duration for result in self.results)
        average_duration = total_duration / total_tests if total_tests > 0 else 0.0
        
        return {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate,
            'total_duration': total_duration,
            'average_duration': average_duration
        }
    
    def print_summary(self):
        """Print a formatted summary of the test results."""
        summary = self.get_summary()
        
        self.logger.info("=" * 60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Tests: {summary['total_tests']}")
        self.logger.info(f"Passed: {summary['passed']}")
        self.logger.info(f"Failed: {summary['failed']}")
        self.logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        self.logger.info(f"Total Duration: {summary['total_duration']:.3f}s")
        self.logger.info(f"Average Duration: {summary['average_duration']:.3f}s")
        self.logger.info("=" * 60)
        
        # Print failed tests
        failed_tests = [result for result in self.results if not result.success]
        if failed_tests:
            self.logger.error("FAILED TESTS:")
            for result in failed_tests:
                self.logger.error(f"  - {result.test_name}: {result.error_message}")
        
        self.logger.info("=" * 60)
    
    def clear_results(self):
        """Clear all test results."""
        self.results.clear()


def run_all_tests() -> Dict[str, Any]:
    """
    Run all available unit tests.
    
    Returns:
        Summary of test results
    """
    runner = TestRunner()
    
    # Import test configuration
    from .test_config import is_test_category_enabled, get_test_modules
    
    # Import and add test cases based on configuration
    if is_test_category_enabled('unit_tests'):
        try:
            from .test_node_utils import create_node_utils_tests
            runner.add_tests(create_node_utils_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import node_utils tests: {e}")
        
        try:
            from .test_logging import create_logging_tests
            runner.add_tests(create_logging_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import logging tests: {e}")
        
        try:
            from .test_performance import create_performance_tests
            runner.add_tests(create_performance_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import performance tests: {e}")
        
        try:
            from .test_exporters import create_exporter_tests
            runner.add_tests(create_exporter_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import exporter tests: {e}")
        
        try:
            from .test_mappers import create_mapper_tests
            runner.add_tests(create_mapper_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import mapper tests: {e}")
        
        try:
            from .test_core import create_core_tests
            runner.add_tests(create_core_tests())
        except ImportError as e:
            logger = MaterialXLogger("TestRunner")
            logger.warning(f"Could not import core tests: {e}")
    
    # Run tests
    runner.run_tests()
    
    # Print summary
    runner.print_summary()
    
    return runner.get_summary()


# Convenience function for running tests from Blender's Python console
def run_tests():
    """Run all unit tests and return the summary."""
    return run_all_tests()


if __name__ == "__main__":
    # This can be run from Blender's Python console
    run_tests()
