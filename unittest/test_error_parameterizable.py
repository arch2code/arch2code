#!/usr/bin/env python3
"""
Test error handling for parameterizable constants (F2/F3).

These tests verify the negative cases around isParameterizable / maxValue
on constants, ensuring users get clear errors when:
- A constant is declared in ipParameters but maxValue is missing
- A constant is marked isParameterizable: true outside ipParameters
  but maxValue is missing
- A derived (eval-based) constant has a hand-written maxValue
- maxValue is non-positive when parameterizable
- A constant's nominal value exceeds its maxValue

Success Criteria:
- Clear error message naming the constant and the rule violated
- NO Python stack traces for user input errors
"""

import sys
import os
import tempfile
import subprocess

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def create_test_files(arch_content):
    """Create temporary project file and architecture YAML file."""
    arch_fd, arch_path = tempfile.mkstemp(suffix='.yaml', prefix='arch_param_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    arch_basename = os.path.basename(arch_path)

    project_content = f"""projectName: param_error_test
topInstance: uTop

dirs:
  root: ..    # project root directory relative to project file - required

projectFiles:
  - {arch_basename}
"""

    project_fd, project_path = tempfile.mkstemp(suffix='_project.yaml', prefix='proj_param_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)

    return project_path, arch_path


def test_error_case(yaml_content, expected_patterns, test_name):
    """Run arch2code on the given YAML and verify it fails with expected error patterns."""
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"{'='*70}")

    if isinstance(expected_patterns, str):
        expected_patterns = [expected_patterns]

    project_path, arch_path = create_test_files(yaml_content)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)

    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        arch2code_path = os.path.join(base_dir, 'arch2code.py')
        cmd = [sys.executable, arch2code_path, '--yaml', project_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=test_dir, env=env)

        if result.returncode == 0:
            print(f"  FAIL: Expected error but build succeeded")
            return False

        error_output = result.stderr + result.stdout

        if 'Traceback (most recent call last)' in error_output:
            print(f"  FAIL: Got Python stack trace instead of clean error")
            lines = error_output.split('\n')
            for i, line in enumerate(lines):
                if 'Traceback' in line:
                    print('  ' + '\n  '.join(lines[i:min(i+10, len(lines))]))
                    break
            return False

        all_found = True
        for pattern in expected_patterns:
            if pattern.lower() not in error_output.lower():
                print(f"  FAIL: Expected pattern not found: '{pattern}'")
                all_found = False

        if all_found:
            print(f"  PASS: Got expected error message")
            print(f"     Patterns found: {expected_patterns}")
            err_lines = [ln for ln in error_output.split('\n') if 'error' in ln.lower() or 'maxvalue' in ln.lower()]
            if err_lines:
                print(f"     Error: {err_lines[0][:120]}")
            return True
        else:
            print(f"  FAIL: Some expected patterns not found")
            print(f"\n  Full error output (first 25 lines):")
            print('  ' + '\n  '.join(error_output.split('\n')[:25]))
            return False

    finally:
        for p in (project_path, arch_path, db_path):
            if os.path.exists(p):
                os.unlink(p)


# ----------------------------------------------------------------------------
# Test cases
# ----------------------------------------------------------------------------

def test_ipparameter_const_missing_maxvalue():
    """ipParameters constant without maxValue must error."""
    yaml = """blocks:
  ip: {desc: "IP block"}

ipParameters:
  constants:
    MY_PARAM: { value: 8, desc: "Parameter without maxValue" }
"""
    return test_error_case(
        yaml,
        ["MY_PARAM", "ipParameters", "maxValue"],
        "ipParameters constant missing maxValue"
    )


def test_isparameterizable_flag_missing_maxvalue():
    """A constant marked isParameterizable: true outside ipParameters without maxValue must error."""
    yaml = """constants:
  MY_PARAM:
    value: 8
    isParameterizable: true
    desc: "Marked parameterizable but no maxValue"
"""
    return test_error_case(
        yaml,
        ["MY_PARAM", "isParameterizable", "maxValue"],
        "isParameterizable flag without maxValue"
    )


def test_derived_const_user_maxvalue_rejected():
    """A derived (eval) constant with hand-written maxValue must error."""
    yaml = """blocks:
  ip: {desc: "IP block"}

ipParameters:
  constants:
    BASE: { value: 8, maxValue: 16, desc: "Base width" }

constants:
  DERIVED:
    eval: "$BASE * 2"
    maxValue: 32
    desc: "Derived; user must NOT hand-write maxValue"
"""
    return test_error_case(
        yaml,
        ["DERIVED", "auto-derived", "do not hand-write"],
        "Derived constant with user maxValue"
    )


def test_ipparameter_const_zero_maxvalue():
    """ipParameters constant with maxValue = 0 must error (treated as missing)."""
    # maxValue: 0 is the schema default and is treated by code as "not provided",
    # so this also surfaces the missing-maxValue error.
    yaml = """blocks:
  ip: {desc: "IP block"}

ipParameters:
  constants:
    MY_PARAM: { value: 8, maxValue: 0, desc: "maxValue is zero" }
"""
    return test_error_case(
        yaml,
        ["MY_PARAM", "maxValue"],
        "ipParameters constant with maxValue=0"
    )


def test_ipparameter_value_exceeds_maxvalue():
    """A parameterizable constant whose nominal value exceeds maxValue must error."""
    yaml = """blocks:
  ip: {desc: "IP block"}

ipParameters:
  constants:
    MY_PARAM: { value: 32, maxValue: 16, desc: "value exceeds maxValue" }
"""
    return test_error_case(
        yaml,
        ["MY_PARAM", "value", "exceeds", "maxValue"],
        "Parameterizable constant value exceeds maxValue"
    )


# ----------------------------------------------------------------------------
# Type-side parallels (F2.2): silent fallback to nominal width was a footgun
# equivalent to the constants case. Tests below lock in the hard-error.
# ----------------------------------------------------------------------------

def test_ipparameter_type_missing_maxbitwidth_literal_width():
    """A type in ipParameters with a literal/non-param width and no
    explicit maxBitwidth must error. (Without the check, downstream worst-case
    sizing would silently fall back to nominal width.)"""
    yaml = """blocks:
  ip: {desc: "IP block"}

ipParameters:
  types:
    badT:
      width: 8
      desc: "literal width, no maxBitwidth"
"""
    return test_error_case(
        yaml,
        ["badT", "ipParameters", "maxBitwidth"],
        "ipParameters type missing maxBitwidth (literal width)"
    )


def test_isparameterizable_type_missing_maxbitwidth():
    """A type marked isParameterizable: true outside ipParameters with no
    explicit maxBitwidth and no parameterizable constant width must error."""
    yaml = """types:
  badT:
    width: 8
    isParameterizable: true
    desc: "marked param but no maxBitwidth"
"""
    return test_error_case(
        yaml,
        ["badT", "isParameterizable", "maxBitwidth"],
        "isParameterizable type without maxBitwidth"
    )


def test_type_maxbitwidth_less_than_width():
    """A type whose explicit maxBitwidth is smaller than its resolved width
    must error."""
    yaml = """types:
  badT:
    width: 16
    maxBitwidth: 8
    desc: "maxBitwidth less than width"
"""
    return test_error_case(
        yaml,
        ["badT", "maxBitwidth", "less than"],
        "Type maxBitwidth less than width"
    )


def test_malformed_maxvalue_string():
    """A constant with maxValue: 'not_a_number' must produce a clean error,
    not a Python TypeError. String forms of integers ('16', '0x10') are
    accepted; arbitrary strings are not."""
    yaml = """constants:
  BAD_MAX: { value: 8, maxValue: "not_a_number", desc: "malformed maxValue" }
"""
    return test_error_case(
        yaml,
        ["BAD_MAX", "maxValue", "integer"],
        "Malformed maxValue (non-numeric string)"
    )


def test_malformed_maxvalue_list():
    """A constant with maxValue: [1, 2] must produce a clean error."""
    yaml = """constants:
  BAD_MAX: { value: 8, maxValue: [1, 2], desc: "list maxValue" }
"""
    return test_error_case(
        yaml,
        ["BAD_MAX", "maxValue", "integer"],
        "Malformed maxValue (list)"
    )


def test_malformed_maxbitwidth_string():
    """A type with maxBitwidth: 'not_a_number' must produce a clean error."""
    yaml = """types:
  BAD_WIDTH:
    width: 8
    maxBitwidth: "not_a_number"
    desc: "malformed maxBitwidth"
"""
    return test_error_case(
        yaml,
        ["BAD_WIDTH", "maxBitwidth", "integer"],
        "Malformed maxBitwidth (non-numeric string)"
    )


def test_unresolved_derived_constant_reference():
    """A derived constant that references an unknown $TOKEN must be a user-facing error."""
    yaml = """constants:
  DERIVED:
    eval: "$MISSING_CONST + 1"
    desc: "bad derived constant"
"""
    return test_error_case(
        yaml,
        ["DERIVED", "unresolved", "MISSING_CONST"],
        "Derived constant references unresolved token"
    )


def test_structure_array_size_float_constant():
    """A parameterizable structure arraySize must resolve to a positive integer."""
    yaml = """constants:
  WIDTH: {value: 8, desc: "Width"}
  ARR:
    value: 1.5
    valueType: real
    isParameterizable: true
    maxValue: 2
    desc: "Bad array size"

types:
  dataT: {width: WIDTH, desc: "Data"}

variables:
  data:
    type: dataT
    desc: "Data variable"

structures:
  badSt:
    data:
      arraySize: ARR
"""
    return test_error_case(
        yaml,
        ["badSt", "arraySize", "positive integer"],
        "Structure arraySize resolves to float"
    )


def test_memory_register_wordlines_float_constant():
    """A memory register wordLines constant must resolve to a positive integer."""
    yaml = """constants:
  WIDTH: {value: 32, desc: "Width"}
  WORDS:
    value: 1.5
    valueType: real
    desc: "Bad wordLines"

types:
  dataT: {width: WIDTH, desc: "Data"}

variables:
  data:
    type: dataT
    desc: "Data variable"

structures:
  dataSt:
    data: {}
  addrSt:
    data: {}

blocks:
  top: {desc: "Top"}
  blockA: {desc: "Block A"}

instances:
  uTop: {container: top, instanceType: top}
  uA: {container: top, instanceType: blockA}

registers:
  - register: badMemReg
    regType: memory
    block: blockA
    desc: "Bad memory register"
    structure: dataSt
    addressStruct: addrSt
    wordLines: WORDS
"""
    return test_error_case(
        yaml,
        ["badMemReg", "wordLines", "positive integer"],
        "Memory register wordLines resolves to float"
    )


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING ERROR HANDLING: Parameterizable Constants (F2/F3)")
    print("="*70)
    print("\nThese tests verify that misuse of isParameterizable / maxValue")
    print("on constants produces clear error messages.")

    tests = [
        test_ipparameter_const_missing_maxvalue,
        test_isparameterizable_flag_missing_maxvalue,
        test_derived_const_user_maxvalue_rejected,
        test_ipparameter_const_zero_maxvalue,
        test_ipparameter_value_exceeds_maxvalue,
        test_ipparameter_type_missing_maxbitwidth_literal_width,
        test_isparameterizable_type_missing_maxbitwidth,
        test_type_maxbitwidth_less_than_width,
        test_malformed_maxvalue_string,
        test_malformed_maxvalue_list,
        test_malformed_maxbitwidth_string,
        test_unresolved_derived_constant_reference,
        test_structure_array_size_float_constant,
        test_memory_register_wordlines_float_constant,
    ]

    results = []
    for test_func in tests:
        try:
            ok = test_func()
            results.append((test_func.__name__, ok))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")
    print(f"\n  Passed: {passed}/{total}")

    if passed == total:
        print("\n  ALL TESTS PASSED!")
        return 0
    else:
        print("\n  SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
