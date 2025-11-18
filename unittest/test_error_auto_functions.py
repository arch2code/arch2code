#!/usr/bin/env python3
"""
Test error handling for auto functions and special logic.

These tests verify that errors in auto functions (_auto_*) and special logic
(constParse, variable lookups, etc.) produce clear error messages instead of
Python stack traces or exits.

Success Criteria:
✅ Clear error message with field name and location
❌ NO Python stack traces for user input errors
❌ NO unexpected exit() calls

Focus Areas:
- _auto_entryType (variable lookup in structures)
- constParse (constant resolution)
- _auto_width (enum validation, width calculation)
"""

import sys
import os
import tempfile
import subprocess
import re

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def create_test_files(arch_content):
    """
    Create temporary project file and architecture YAML file.
    
    Returns:
        tuple: (project_file_path, arch_file_path)
    """
    # Create architecture YAML file
    arch_fd, arch_path = tempfile.mkstemp(suffix='.yaml', prefix='arch_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)
    
    arch_basename = os.path.basename(arch_path)
    
    # Create project file that references the architecture file
    project_content = f"""projectName: error_test
topInstance: uTop

projectFiles:
  - {arch_basename}
"""
    
    project_fd, project_path = tempfile.mkstemp(suffix='_project.yaml', prefix='proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)
    
    return project_path, arch_path


def test_error_case(yaml_content, expected_patterns, test_name):
    """
    Test that an error YAML produces a clear error message without stack trace.
    
    Args:
        yaml_content: YAML content with an error
        expected_patterns: List of strings that should appear in error message (case-insensitive)
        test_name: Name of the test for reporting
    
    Returns:
        bool: True if test passed (clear error, no stack trace)
    """
    project_path = None
    arch_path = None
    db_path = None
    
    try:
        # Create test files
        project_path, arch_path = create_test_files(yaml_content)
        
        # Create temporary database path
        db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_', dir=test_dir)
        os.close(db_fd)
        os.unlink(db_path)  # Remove file, we just want the path
        
        # Run arch2code.py
        # Disable color output to prevent red flashing in test output
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            ['python3', os.path.join(base_dir, 'arch2code.py'), 
             '-y', project_path, '--db', db_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=base_dir,
            env=env
        )
        
        # Combine stdout and stderr
        full_output = result.stdout + '\n' + result.stderr
        
        # Check for Python stack trace
        has_traceback = 'Traceback (most recent call last):' in full_output
        
        # Check for expected error patterns
        patterns_found = []
        patterns_missing = []
        for pattern in expected_patterns:
            if pattern.lower() in full_output.lower():
                patterns_found.append(pattern)
            else:
                patterns_missing.append(pattern)
        
        # Test passes if:
        # 1. Build failed (exit code != 0)
        # 2. No Python traceback
        # 3. All expected patterns found
        
        success = (result.returncode != 0 and 
                   not has_traceback and 
                   len(patterns_missing) == 0)
        
        # Print results
        print("=" * 70)
        print(f"Test: {test_name}")
        print("=" * 70)
        
        if success:
            print("  ✓ PASS: Got expected error message")
            print(f"     Patterns found: {patterns_found}")
            # Show first few lines of error
            error_lines = [line for line in full_output.split('\n') if line.strip() and 'Error' in line]
            if error_lines:
                print(f"     Error: {error_lines[0][:100]}")
        else:
            if result.returncode == 0:
                print("  ❌ FAIL: Build succeeded when it should have failed")
            if has_traceback:
                print("  ❌ FAIL: Got Python stack trace instead of clean error")
                print("\n  Stack trace snippet:")
                lines = full_output.split('\n')
                tb_start = next((i for i, line in enumerate(lines) if 'Traceback' in line), -1)
                if tb_start >= 0:
                    print("  " + "\n  ".join(lines[tb_start:tb_start+10]))
            if patterns_missing:
                for pattern in patterns_missing:
                    print(f"  ❌ FAIL: Expected pattern not found: '{pattern}'")
                print("  ❌ FAIL: Some expected patterns not found")
            
            print("\n  Full error output:")
            print("  " + "\n  ".join(full_output.split('\n')[:50]))
        
        print()
        return success
        
    finally:
        # Cleanup
        for path in [project_path, arch_path, db_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except:
                    pass


# ============================================================================
# HIGH PRIORITY TESTS: Auto Functions & Special Logic
# ============================================================================

def test_undefined_variable_in_structure():
    """Test 1: Structure field references undefined variable (uses _auto_entryType)"""
    yaml = """constants:
  WIDTH: {value: 8, desc: "Width"}

types:
  dataT: {width: WIDTH, desc: "Data type"}

variables:
  validVar:
    type: dataT
    desc: "Valid variable"

structures:
  mySt:
    validVar: {}
    UNDEFINED_VAR: {}

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["UNDEFINED_VAR", "variable", "structure"],
        "Structure field references undefined variable"
    )


def test_undefined_constant_in_width():
    """Test 2: Type width references undefined constant (uses constParse)"""
    yaml = """types:
  myType:
    width: UNDEFINED_CONSTANT
    desc: "Type with undefined constant"

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["UNDEFINED_CONSTANT", "unresolved", "Constant"],
        "Type width references undefined constant"
    )


def test_enum_missing_value():
    """Test 3: Enum entry missing required 'value' field (eval field type validation)"""
    yaml = """types:
  myType:
    desc: "Type with enum"
    enum:
      - {enumName: VAL1, value: 1, desc: "Value 1"}
      - {enumName: VAL2, desc: "Value 2"}

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["must provide", "value", "eval"],
        "Enum entry missing required 'value' or 'eval'"
    )


def test_type_missing_width_no_enum():
    """Test 4: Type missing width when not auto-calculated from enum (uses _auto_width)"""
    yaml = """types:
  myType:
    desc: "Type missing width and no enum"

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["Missing", "width", "myType"],
        "Type missing width (no enum to calculate from)"
    )


def test_eval_expression_runtime_error():
    """Test 5: Eval expression with runtime error (division by zero)"""
    yaml = """types:
  myType:
    desc: "Type with runtime error"
    enum:
      - {enumName: VAL1, value: 1, desc: "Value 1"}
      - {enumName: VAL2, eval: "1 / 0", desc: "Division by zero"}

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["eval expression failed", "1 / 0", "ZeroDivisionError"],
        "Eval expression with runtime error (division by zero)"
    )


def test_eval_expression_syntax_error():
    """Test 6: Eval expression with Python syntax error"""
    yaml = """types:
  myType:
    desc: "Type with syntax error"
    enum:
      - {enumName: VAL1, value: 1, desc: "Value 1"}
      - {enumName: VAL2, eval: "1 +* 2", desc: "Invalid syntax"}

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["eval expression failed", "1 +* 2", "SyntaxError"],
        "Eval expression with Python syntax error"
    )


def test_eval_expression_undefined_name():
    """Test 7: Eval expression references undefined name"""
    yaml = """types:
  myType:
    desc: "Type with undefined name"
    enum:
      - {enumName: VAL1, value: 1, desc: "Value 1"}
      - {enumName: VAL2, eval: "UNDEFINED_VAR + 1", desc: "Undefined variable"}

blocks:
  top: {desc: "Top"}

instances:
  uTop: {instanceType: top, container: top}
"""
    return test_error_case(
        yaml,
        ["eval expression failed", "UNDEFINED_VAR", "NameError"],
        "Eval expression with undefined name"
    )


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("TESTING ERROR HANDLING: Auto Functions & Special Logic")
    print("="*70)
    print()
    print("These tests verify that auto functions and special logic produce")
    print("clear error messages without Python stack traces.")
    print()
    
    tests = [
        ("test_undefined_variable_in_structure", test_undefined_variable_in_structure),
        ("test_undefined_constant_in_width", test_undefined_constant_in_width),
        ("test_enum_missing_value", test_enum_missing_value),
        ("test_type_missing_width_no_enum", test_type_missing_width_no_enum),
        ("test_eval_expression_runtime_error", test_eval_expression_runtime_error),
        ("test_eval_expression_syntax_error", test_eval_expression_syntax_error),
        ("test_eval_expression_undefined_name", test_eval_expression_undefined_name),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    print()
    print(f"  Passed: {passed_count}/{total_count}")
    print()
    
    if passed_count == total_count:
        print("  ✅ ALL TESTS PASSED!")
        print("  Auto function and eval error handling is working correctly.")
        return 0
    else:
        print("  ⚠️  SOME TESTS FAILED")
        print("  Some auto functions or eval expressions may need better error handling.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())

