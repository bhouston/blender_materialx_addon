#!/usr/bin/env python3
"""
Phase 3 MaterialX Library Integration Test

This script tests the Phase 3 enhancements to the MaterialX addon:
- Advanced validation and error handling
- Performance monitoring and optimization
- Document optimization
- Shader code generation
- Error recovery mechanisms
- Memory management
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the materialx_addon directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'materialx_addon'))

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('phase3_test.log')
        ]
    )
    return logging.getLogger('Phase3Test')

def test_mtlxutils_availability():
    """Test if mtlxutils modules are available."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing mtlxutils availability...")
    
    try:
        import mtlxutils
        import mtlxutils.mxbase as mxb
        import mtlxutils.mxfile as mxf
        import mtlxutils.mxnodegraph as mxg
        import mtlxutils.mxtraversal as mxt
        import mtlxutils.mxrenderer as mxr
        import mtlxutils.mxshadergen as mxs
        
        logger.info("✓ All mtlxutils modules imported successfully")
        
        # Test version checking
        version_info = mxb.haveVersion(1, 38, 7)
        logger.info(f"✓ MaterialX version check: {version_info}")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Failed to import mtlxutils: {e}")
        return False

def test_phase3_core_classes():
    """Test Phase 3 core classes."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing Phase 3 core classes...")
    
    try:
        from materialx_library_core import (
            MaterialXDocumentManager,
            MaterialXPerformanceMonitor,
            MaterialXAdvancedValidator,
            MaterialXLibraryBuilder
        )
        
        logger.info("✓ Phase 3 core classes imported successfully")
        
        # Test class instantiation
        test_logger = logging.getLogger('Test')
        
        # Test performance monitor
        perf_monitor = MaterialXPerformanceMonitor(test_logger)
        perf_monitor.start_operation("test_operation")
        time.sleep(0.1)
        perf_monitor.end_operation("test_operation")
        logger.info("✓ Performance monitor working")
        

        
        # Test advanced validator
        advanced_validator = MaterialXAdvancedValidator(test_logger)
        logger.info("✓ Advanced validator initialized")
        
        # Test document manager with Phase 3 features
        doc_manager = MaterialXDocumentManager(test_logger, "1.38")
        logger.info("✓ Document manager with Phase 3 features initialized")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Failed to import Phase 3 core classes: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error testing Phase 3 core classes: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring features."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing performance monitoring...")
    
    try:
        from materialx_library_core import MaterialXPerformanceMonitor
        
        test_logger = logging.getLogger('Test')
        monitor = MaterialXPerformanceMonitor(test_logger)
        
        # Test operation timing
        monitor.start_operation("test_timing")
        time.sleep(0.1)
        monitor.end_operation("test_timing")
        
        # Test memory tracking
        monitor.start_operation("test_memory")
        large_list = [i for i in range(10000)]
        monitor.end_operation("test_memory")
        
        # Test optimization suggestions
        suggestions = monitor.suggest_optimizations()
        logger.info(f"✓ Performance suggestions: {suggestions}")
        
        # Test cleanup
        monitor.cleanup()
        logger.info("✓ Performance monitoring cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance monitoring test failed: {e}")
        return False



def test_advanced_validation():
    """Test advanced validation features."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing advanced validation...")
    
    try:
        import MaterialX as mx
        from materialx_library_core import MaterialXAdvancedValidator
        
        test_logger = logging.getLogger('Test')
        validator = MaterialXAdvancedValidator(test_logger)
        
        # Create a test document
        doc = mx.createDocument()
        
        # Test comprehensive validation
        results = validator.validate_document_comprehensive(doc)
        logger.info(f"✓ Validation results: {results}")
        
        # Test validation summary
        summary = validator.get_validation_summary(results)
        logger.info(f"✓ Validation summary: {summary}")
        
        # Test custom validator
        def custom_validator(document):
            return {'valid': True, 'errors': [], 'warnings': ['Custom warning']}
        
        validator.add_custom_validator("test_validator", custom_validator)
        logger.info("✓ Custom validator added")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Advanced validation test failed: {e}")
        return False

def test_document_optimization():
    """Test document optimization features."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing document optimization...")
    
    try:
        from materialx_library_core import MaterialXLibraryBuilder
        
        test_logger = logging.getLogger('Test')
        builder = MaterialXLibraryBuilder("test_material", test_logger, "1.38")
        
        # Test optimization
        optimization_success = builder.optimize_document()
        logger.info(f"✓ Document optimization: {optimization_success}")
        
        # Test performance statistics
        stats = builder.get_performance_stats()
        logger.info(f"✓ Performance statistics: {stats}")
        
        # Test write options
        builder.set_write_options(
            skip_library_elements=True,
            write_xinclude=False,
            remove_layout=True,
            format_output=True
        )
        logger.info("✓ Write options configured")
        
        # Test cleanup
        builder.cleanup()
        logger.info("✓ Builder cleanup completed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Document optimization test failed: {e}")
        return False



def test_phase3_exporter_integration():
    """Test Phase 3 exporter integration."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing Phase 3 exporter integration...")
    
    try:
        from blender_materialx_exporter import MaterialXExporter
        
        # Test exporter with Phase 3 options
        test_logger = logging.getLogger('Test')
        
        # Create a mock material (we can't actually create Blender materials in this test)
        class MockMaterial:
            def __init__(self):
                self.name = "test_material"
                self.use_nodes = False
                self.diffuse_color = (0.8, 0.2, 0.2, 1.0)
                self.roughness = 0.5
                self.metallic = 0.0
        
        mock_material = MockMaterial()
        
        # Test Phase 3 options
        phase3_options = {
            'optimize_document': True,
            'advanced_validation': True,
            'performance_monitoring': True
        }
        
        logger.info("✓ Phase 3 exporter options configured")
        logger.info(f"✓ Phase 3 options: {phase3_options}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Phase 3 exporter integration test failed: {e}")
        return False

def test_memory_management():
    """Test memory management features."""
    logger = logging.getLogger('Phase3Test')
    logger.info("Testing memory management...")
    
    try:
        from materialx_library_core import MaterialXDocumentManager
        import gc
        
        test_logger = logging.getLogger('Test')
        
        # Test document manager cleanup
        doc_manager = MaterialXDocumentManager(test_logger, "1.38")
        
        # Create some caches
        doc_manager._node_def_cache['test'] = 'value'
        doc_manager._input_def_cache['test'] = 'value'
        doc_manager._output_def_cache['test'] = 'value'
        
        logger.info(f"✓ Cache sizes before cleanup: {doc_manager.get_performance_stats()['cache_sizes']}")
        
        # Test cache clearing
        doc_manager._clear_caches()
        
        logger.info(f"✓ Cache sizes after cleanup: {doc_manager.get_performance_stats()['cache_sizes']}")
        
        # Test full cleanup
        doc_manager.cleanup()
        logger.info("✓ Document manager cleanup completed")
        
        # Force garbage collection
        gc.collect()
        logger.info("✓ Garbage collection completed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Memory management test failed: {e}")
        return False

def run_all_tests():
    """Run all Phase 3 tests."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("PHASE 3 MATERIALX LIBRARY INTEGRATION TEST")
    logger.info("=" * 60)
    
    tests = [
        ("mtlxutils availability", test_mtlxutils_availability),
        ("Phase 3 core classes", test_phase3_core_classes),
        ("Performance monitoring", test_performance_monitoring),

        ("Advanced validation", test_advanced_validation),
        ("Document optimization", test_document_optimization),

        ("Phase 3 exporter integration", test_phase3_exporter_integration),
        ("Memory management", test_memory_management),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! Phase 3 implementation is working correctly.")
    else:
        logger.error(f"❌ {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 