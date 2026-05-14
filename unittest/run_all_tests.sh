#!/bin/bash
# Run all unit tests

FAILED=0

echo "========================================================================"
echo "Running All Unit Tests"
echo "========================================================================"

# Test 1: Nested loading
echo ""
echo "Test Suite 1: Nested Table Loading"
echo "------------------------------------------------------------------------"
python3 test_nested_loading.py || FAILED=1

# Test 2: APB validation  
echo ""
echo "Test Suite 2: APB Interface Validation"
echo "------------------------------------------------------------------------"
python3 test_apb_validation.py || FAILED=1

# Test 3: Interface loading
echo ""
echo "Test Suite 3: Interface Loading"
echo "------------------------------------------------------------------------"
python3 test_interface_loading.py || FAILED=1

# Test 4: Data by parent logic
echo ""
echo "Test Suite 4: Data by Parent Logic"
echo "------------------------------------------------------------------------"
python3 test_data_by_parent_logic.py || FAILED=1

# Test 5: Mixed project
echo ""
echo "Test Suite 5: Mixed Project Build"
echo "------------------------------------------------------------------------"
python3 test_mixed_project.py || FAILED=1

# Test 6: Error handling - missing fields
echo ""
echo "Test Suite 6: Error Handling (Missing Fields)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_missing_fields.py; then
    FAILED=1
    echo "⚠️  Note: Some error tests failed"
    echo "    This indicates bugs in error handling that need fixing."
fi

# Test 7: Error handling - auto functions
echo ""
echo "Test Suite 7: Error Handling (Auto Functions)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_auto_functions.py; then
    FAILED=1
    echo "⚠️  Note: Some error tests failed"
    echo "    This indicates bugs in auto function error handling."
fi

# Test 8: Duplicate interface handling
echo ""
echo "Test Suite 8: Duplicate Interface Handling"
echo "------------------------------------------------------------------------"
python3 test_duplicate_interface.py || FAILED=1

# Test 9: ContextKey schema validation
echo ""
echo "Test Suite 9: ContextKey Validation"
echo "------------------------------------------------------------------------"
python3 test_contextkey_validation.py || FAILED=1

# Test 10: Error handling - parameterizable constants (F2/F3)
echo ""
echo "Test Suite 10: Error Handling (Parameterizable Constants)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_parameterizable.py; then
    FAILED=1
    echo "Note: Some parameterizable-constant error tests failed"
fi

# Test 11: Config template generation
echo ""
echo "Test Suite 11: Config Template Generation"
echo "------------------------------------------------------------------------"
python3 test_config_template.py || FAILED=1

# Test 12: Error handling - declared ports
echo ""
echo "Test Suite 12: Error Handling (Declared Ports)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_declared_ports.py; then
    FAILED=1
    echo "Note: Some declared-port error tests failed"
fi

# Test 13: Thunker view derivation
echo ""
echo "Test Suite 13: Thunker View Derivation"
echo "------------------------------------------------------------------------"
python3 test_thunker_view.py || FAILED=1

# Test 14: Error handling - RTL hierarchy implementation
echo ""
echo "Test Suite 14: Error Handling (RTL Hierarchy)"
echo "------------------------------------------------------------------------"
if ! python3 test_error_rtl_hierarchy.py; then
    FAILED=1
    echo "Note: Some RTL hierarchy error tests failed"
fi

echo ""
echo "========================================================================"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TEST SUITES PASSED!"
    echo "========================================================================"
    exit 0
else
    echo "❌ SOME TEST SUITES FAILED!"
    echo "========================================================================"
    exit 1
fi
