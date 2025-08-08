#!/usr/bin/env python3
"""
Unit Tests for Logging Utilities

This module contains unit tests for the logging utilities.
"""

import logging
from typing import List
from .test_utils import BlenderTestCase
from ..utils.logging_utils import MaterialXLogger, ValidationLogger


class TestMaterialXLogger(BlenderTestCase):
    """Test MaterialXLogger functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.logger = MaterialXLogger("TestLogger", "DEBUG")
    
    def test(self):
        """Test MaterialXLogger functionality."""
        # Test basic logging methods
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        
        # Test logging with context
        self.logger.info("Message with context", key1="value1", key2="value2")
        
        # Test specialized logging methods
        self.logger.log_export_start("TestMaterial", "/path/to/output.mtlx")
        self.logger.log_export_complete("TestMaterial", "/path/to/output.mtlx", 1.5, True)
        self.logger.log_node_export("RGB", "TestNode", True)
        self.logger.log_unsupported_node("EMISSION", "EmissionNode", "Use Principled BSDF instead")
        self.logger.log_validation_result(True, [], [])

        self.logger.log_texture_export("test.jpg", "/source/path", "/target/path", True)
        
        # Verify logger was created
        self.assertIsInstance(self.logger.logger, logging.Logger)
        self.assertEqual(self.logger.logger.name, "TestLogger")


class TestValidationLogger(BlenderTestCase):
    """Test ValidationLogger functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.base_logger = MaterialXLogger("TestValidationLogger")
        self.validation_logger = ValidationLogger(self.base_logger)
    
    def test(self):
        """Test ValidationLogger functionality."""
        # Test validation logging
        self.validation_logger.log_validation_start("test_document")
        self.validation_logger.log_validation_end("test_document", True, 0, 2)
        self.validation_logger.log_validation_error("Test error message")
        self.validation_logger.log_validation_warning("Test warning message")
        
        # Test with context
        self.validation_logger.log_validation_error("Error with context", {"line": 10, "column": 5})
        self.validation_logger.log_validation_warning("Warning with context", {"severity": "low"})
        
        # Verify logger was created
        self.assertIsInstance(self.validation_logger.logger, MaterialXLogger)


class TestLoggerIntegration(BlenderTestCase):
    """Test logger integration and message formatting."""
    
    def test(self):
        """Test logger integration and message formatting."""
        logger = MaterialXLogger("IntegrationTest")
        
        # Test message formatting
        logger.info("Simple message")
        logger.info("Message with one param", param1="value1")
        logger.info("Message with multiple params", param1="value1", param2="value2", param3=123)
        
        # Test that messages are properly formatted
        # Note: We can't easily test the actual output without capturing it,
        # but we can test that the methods don't raise exceptions
        try:
            logger.debug("Debug test")
            logger.info("Info test")
            logger.warning("Warning test")
            logger.error("Error test")
            logger.critical("Critical test")
        except Exception as e:
            self.fail(f"Logger methods should not raise exceptions: {e}")


class TestLoggerLevels(BlenderTestCase):
    """Test logger level functionality."""
    
    def test(self):
        """Test logger level functionality."""
        # Test different log levels
        debug_logger = MaterialXLogger("DebugLogger", "DEBUG")
        info_logger = MaterialXLogger("InfoLogger", "INFO")
        warning_logger = MaterialXLogger("WarningLogger", "WARNING")
        error_logger = MaterialXLogger("ErrorLogger", "ERROR")
        
        # Test that loggers are created with correct levels
        self.assertEqual(debug_logger.logger.level, logging.DEBUG)
        self.assertEqual(info_logger.logger.level, logging.INFO)
        self.assertEqual(warning_logger.logger.level, logging.WARNING)
        self.assertEqual(error_logger.logger.level, logging.ERROR)
        
        # Test that methods don't raise exceptions
        try:
            debug_logger.debug("Debug message")
            info_logger.info("Info message")
            warning_logger.warning("Warning message")
            error_logger.error("Error message")
        except Exception as e:
            self.fail(f"Logger methods should not raise exceptions: {e}")


class TestLoggerSingleton(BlenderTestCase):
    """Test logger singleton functionality."""
    
    def test(self):
        """Test logger singleton functionality."""
        from ..utils.logging_utils import get_logger, set_log_level
        
        # Test get_logger returns same instance
        logger1 = get_logger("SingletonTest")
        logger2 = get_logger("SingletonTest")
        self.assertIs(logger1, logger2)
        
        # Test set_log_level
        set_log_level("DEBUG")
        self.assertEqual(logger1.logger.level, logging.DEBUG)
        
        set_log_level("INFO")
        self.assertEqual(logger1.logger.level, logging.INFO)


class TestStartupMessage(BlenderTestCase):
    """Test startup message functionality."""
    
    def test(self):
        """Test startup message functionality."""
        from ..utils.logging_utils import log_startup_message
        
        # Test that startup message doesn't raise exceptions
        try:
            log_startup_message()
        except Exception as e:
            self.fail(f"Startup message should not raise exceptions: {e}")


def create_logging_tests() -> List[BlenderTestCase]:
    """
    Create all logging test cases.
    
    Returns:
        List of logging test cases
    """
    return [
        TestMaterialXLogger("MaterialXLogger"),

        TestValidationLogger("ValidationLogger"),
        TestLoggerIntegration("LoggerIntegration"),
        TestLoggerLevels("LoggerLevels"),
        TestLoggerSingleton("LoggerSingleton"),
        TestStartupMessage("StartupMessage")
    ]
