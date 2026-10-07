#!/usr/bin/env python3
"""
Test error handling for missing required fields.

These tests verify that missing required fields produce clear error messages
instead of Python stack traces.

Success Criteria:
✅ Clear error message with field name and location
❌ NO Python stack traces for user input errors
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
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..    # project root directory relative to project file - required

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
    Test that a YAML error produces the expected error message.
    
    Args:
        yaml_content: Invalid architecture YAML content
        expected_patterns: List of strings/patterns that should appear in error
        test_name: Name of test for reporting
        
    Returns:
        True if test passed, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"{'='*70}")
    
    if isinstance(expected_patterns, str):
        expected_patterns = [expected_patterns]
    
    project_path, arch_path = create_test_files(yaml_content)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    
    try:
        # Try to build database - should fail
        # Disable color output to prevent red flashing in test output
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        arch2code_path = os.path.join(base_dir, 'arch2code.py')
        cmd = [sys.executable, arch2code_path, '--yaml', project_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=test_dir, env=env)
        
        # Should have failed
        if result.returncode == 0:
            print(f"  ❌ FAIL: Expected error but build succeeded")
            return False
        
        # Check error message
        error_output = result.stderr + result.stdout
        
        # Check for stack trace (bad!)
        if 'Traceback (most recent call last)' in error_output:
            print(f"  ❌ FAIL: Got Python stack trace instead of clean error")
            print("\n  Stack trace snippet:")
            # Show just the traceback header and first few lines
            lines = error_output.split('\n')
            for i, line in enumerate(lines):
                if 'Traceback' in line:
                    print('  ' + '\n  '.join(lines[i:min(i+10, len(lines))]))
                    break
            return False
        
        # Check for expected error patterns
        all_patterns_found = True
        for pattern in expected_patterns:
            # Case-insensitive search
            if pattern.lower() not in error_output.lower():
                print(f"  ❌ FAIL: Expected pattern not found: '{pattern}'")
                all_patterns_found = False
        
        if all_patterns_found:
            print(f"  ✓ PASS: Got expected error message")
            print(f"     Patterns found: {expected_patterns}")
            # Show first line of error
            first_error_line = [line for line in error_output.split('\n') if 'error' in line.lower()]
            if first_error_line:
                print(f"     Error: {first_error_line[0][:80]}")
            return True
        else:
            print(f"  ❌ FAIL: Some expected patterns not found")
            print(f"\n  Full error output:")
            print('  ' + '\n  '.join(error_output.split('\n')[:20]))
            return False
            
    finally:
        # Cleanup temp files
        if os.path.exists(project_path):
            os.unlink(project_path)
        if os.path.exists(arch_path):
            os.unlink(arch_path)
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_type_missing_width():
    """Test 1: Type without width field"""
    yaml = """types:
  myType:
    desc: "This type is missing the required width field"
"""
    return test_error_case(
        yaml,
        ["missing", "width", "myType"],
        "Type missing width field"
    )


def test_constant_missing_value():
    """Test 2: Constant without value or eval"""
    yaml = """constants:
  MY_CONST:
    desc: "This constant is missing value or eval"
"""
    return test_error_case(
        yaml,
        ["MY_CONST", "value", "eval"],  # Actual message: "does not have a 'value' or 'eval' field"
        "Constant missing value field"
    )


def test_interface_missing_type():
    """Test 3: Interface without interfaceType"""
    yaml = """interfaces:
  myInterface:
    desc: "This interface is missing interfaceType"
    structures:
      - {structure: someSt, structureType: data_t}
"""
    return test_error_case(
        yaml,
        ["missing", "interfaceType", "myInterface"],
        "Interface missing interfaceType field"
    )


def test_structure_field_missing_type():
    """Test 4: Structure field without type specification"""
    yaml = """structures:
  mySt:
    missingType: {}
"""
    # Actual error: "reference missingType... does not reference a valid variable definition"
    return test_error_case(
        yaml,
        ["missingType", "variable", "structure"],
        "Structure field missing type"
    )


def test_instance_missing_type():
    """Test 5: Instance without instanceType"""
    yaml = """blocks:
  top: {desc: "Top block"}

instances:
  uTop:
    container: top
"""
    return test_error_case(
        yaml,
        ["missing", "instanceType", "uTop"],
        "Instance missing instanceType field"
    )


def test_connection_missing_src():
    """Test 6: Connection without src"""
    yaml = """# Define a complete setup but connection is missing src
constants:
  WIDTH: {value: 32, desc: "Width"}

types:
  dataT: {width: WIDTH, desc: "Data"}

variables:
  data:
    type: dataT
    desc: "Data variable"
  rdata:
    type: dataT
    desc: "Return data variable"

structures:
  mySt:
    data: {}
  rdataSt:
    rdata: {}

interfaces:
  myIf:
    interfaceType: req_ack
    desc: "Interface"
    structures:
      - {structure: mySt, structureType: data_t}
      - {structure: rdataSt, structureType: rdata_t}

blocks:
  top: {desc: "Top"}
  blockA: {desc: "Block A"}

instances:
  uTop: {container: top, instanceType: top}
  uA: {container: top, instanceType: blockA}

connections:
  - {interface: myIf, dst: uA}
"""
    # Connection processing expects src and dst
    return test_error_case(
        yaml,
        ["connection", "src"],  # Error should mention connection and src field
        "Connection missing src field"
    )


def test_register_missing_structure():
    """Test 7: Register without structure"""
    yaml = """blocks:
  top: {desc: "Top"}
  blockA: {desc: "Block A"}

instances:
  uTop: {container: top, instanceType: top}
  uA: {container: top, instanceType: blockA}

registers:
  - {register: myReg, regType: rw, block: blockA, desc: "Test register"}
"""
    # Register requires structure field
    return test_error_case(
        yaml,
        ["register", "structure"],  # Error message doesn't include specific register name
        "Register missing structure field"
    )


def test_memory_missing_wordlines():
    """Test 8: Memory without wordLines"""
    yaml = """constants:
  WIDTH: {value: 32, desc: "Width"}

types:
  dataT: {width: WIDTH, desc: "Data"}

variables:
  data:
    type: dataT
    desc: "Data variable"

structures:
  mySt:
    data: {}

blocks:
  top: {desc: "Top"}
  blockA: {desc: "Block A"}

instances:
  uTop: {container: top, instanceType: top}
  uA: {container: top, instanceType: blockA}

memories:
  - {memory: myMem, block: blockA, structure: mySt, desc: "Test memory"}
"""
    # Memory requires wordLines field
    return test_error_case(
        yaml,
        ["memories", "wordLines"],  # Error message doesn't include specific memory name
        "Memory missing wordLines field"
    )


def _reported_yaml_line(arch_content, test_name):
    """Build a project whose design YAML has an unknown section and return the
    line number the diagnostic reports, plus the fixture's own lines.

    The unknown-section error is the probe for the location contract because its
    line comes straight from the section body's ruamel lc with nothing else in
    between. Returns (reportedLine, fixtureLines) or (None, reason).
    """
    project_path = arch_path = db_path = None
    try:
        project_path, arch_path = create_test_files(arch_content)
        arch_basename = os.path.basename(arch_path)
        db_fd, db_path = tempfile.mkstemp(suffix='.db', prefix='test_', dir=test_dir)
        os.close(db_fd)
        os.unlink(db_path)

        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            ['python3', os.path.join(base_dir, 'arch2code.py'),
             '-y', project_path, '--db', db_path],
            capture_output=True, text=True, timeout=30, cwd=base_dir, env=env)
        output = result.stdout + '\n' + result.stderr

        if 'Traceback (most recent call last):' in output:
            return None, f"{test_name}: build raised a stack trace instead of a diagnostic:\n{output}"
        if result.returncode == 0:
            return None, f"{test_name}: build succeeded; the unknown section was not rejected:\n{output}"
        match = re.search(re.escape(arch_basename) + r':(\d+)', output)
        if not match:
            return None, (f"{test_name}: no '{arch_basename}:<line>' location in the diagnostic, "
                          f"so it does not name a line at all:\n{output}")
        # Read the fixture back rather than trusting the literal above it.
        with open(arch_path) as f:
            fixture_lines = f.read().split('\n')
        return int(match.group(1)), fixture_lines
    finally:
        for path in (project_path, arch_path, db_path):
            if path and os.path.exists(path):
                os.unlink(path)


def test_diagnostic_reports_1_based_yaml_line():
    """Test 9: a YAML diagnostic names the line as an editor numbers it.

    ruamel counts lines from 0, so a location built from a raw lc must add 1 or
    it sends the author one line too high. Both body shapes must report the
    section key's own line: a section's own lc is the lc of its BODY mapping,
    which sits a line lower in block style, so the key's position has to come
    from the parent map. Block style is the shape that distinguishes the two, and
    flow style is the shape that isolates the 1-based conversion. Both numbers
    are derived by reading the fixture back and locating the tokens, not written
    as literals.
    """
    print("=" * 70)
    print("Test: diagnostics report 1-based YAML line numbers")
    print("=" * 70)
    ok = True

    # Flow-style body: 'notASection:' and its body begin on the same line, so the
    # reported line must equal the line the author sees the section name on.
    flow_fixture = """constants:
  FOO:
    value: 1
    desc: "probe constant"
notASection: {alpha: {beta: 1}}
"""
    reported, info = _reported_yaml_line(flow_fixture, "flow-style body")
    if reported is None:
        print(f"  ❌ FAIL: {info}")
        ok = False
    else:
        expected = next(i + 1 for i, line in enumerate(info)
                        if line.startswith('notASection:'))
        if reported == expected:
            print(f"  ✓ PASS: flow-style body reported line {reported}, the line "
                  f"'notASection:' is on")
        else:
            print(f"  ❌ FAIL: flow-style body reported line {reported}, but "
                  f"'notASection:' is on line {expected} of the fixture. A "
                  f"0-based ruamel line was reported without converting it.")
            ok = False

    # Block-style body: the body mapping starts a line below the section key, so
    # this is the shape that fails if the position is taken from the body instead
    # of from the parent map.
    block_fixture = """constants:
  FOO:
    value: 1
    desc: "probe constant"
notASection:
  alpha:
    beta: 1
"""
    reported, info = _reported_yaml_line(block_fixture, "block-style body")
    if reported is None:
        print(f"  ❌ FAIL: {info}")
        ok = False
    else:
        section_line = next(i + 1 for i, line in enumerate(info)
                            if line.startswith('notASection:'))
        body_line = next(i + 1 for i, line in enumerate(info)
                         if line.startswith('  alpha:'))
        if reported == section_line and body_line == section_line + 1:
            print(f"  ✓ PASS: block-style body reported line {reported}, the line "
                  f"'notASection:' is on, not its body's first key on {body_line}")
        else:
            print(f"  ❌ FAIL: block-style body reported line {reported}; "
                  f"'notASection:' is on line {section_line} and its body's first "
                  f"key on line {body_line}. A section's own lc is its body "
                  f"mapping, so the key's line must come from the parent map.")
            ok = False

    return ok


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("TESTING ERROR HANDLING: Missing Required Fields")
    print("="*70)
    print("\nThese tests verify that missing required fields produce clear")
    print("error messages without Python stack traces.")
    
    tests = [
        test_type_missing_width,
        test_constant_missing_value,
        test_interface_missing_type,
        test_structure_field_missing_type,
        test_instance_missing_type,
        test_connection_missing_src,
        test_register_missing_structure,
        test_memory_missing_wordlines,
        test_diagnostic_reports_1_based_yaml_line,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n  ❌ EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Passed: {passed}/{total}")
    
    if passed == total:
        print("\n  ✅ ALL TESTS PASSED!")
        print("  Error messages are clear and user-friendly.")
        return 0
    else:
        print("\n  ⚠️  SOME TESTS FAILED")
        print("  Some error cases may need better error messages.")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

