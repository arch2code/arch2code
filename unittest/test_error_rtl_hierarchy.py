#!/usr/bin/env python3
"""
Test DB-time error handling for invalid RTL hierarchy.

An RTL-enabled block cannot instantiate a block that has no RTL implementation.
"""

import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def create_test_files(arch_content):
    arch_fd, arch_path = tempfile.mkstemp(
        suffix='.yaml', prefix='rtl_hierarchy_', dir=test_dir)
    os.close(arch_fd)
    with open(arch_path, 'w') as f:
        f.write(arch_content)

    project_content = f"""projectName: rtl_hierarchy_error_test
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""

    project_fd, project_path = tempfile.mkstemp(
        suffix='_project.yaml', prefix='rtl_hierarchy_proj_', dir=test_dir)
    os.close(project_fd)
    with open(project_path, 'w') as f:
        f.write(project_content)

    return project_path, arch_path


def test_error_case(yaml_content, expected_patterns, test_name):
    print(f"\n{'='*70}")
    print(f"Test: {test_name}")
    print(f"{'='*70}")

    project_path, arch_path = create_test_files(yaml_content)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)

    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '-y', project_path, '--db', db_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=base_dir,
            env=env,
        )

        full_output = result.stdout + '\n' + result.stderr
        if result.returncode == 0:
            print("  FAIL: Build succeeded when it should have failed")
            return False

        if 'Traceback (most recent call last):' in full_output:
            print("  FAIL: Got Python stack trace instead of clean error")
            print("  " + "\n  ".join(full_output.split('\n')[:20]))
            return False

        missing = [
            pattern for pattern in expected_patterns
            if pattern.lower() not in full_output.lower()
        ]
        if missing:
            print(f"  FAIL: Missing expected patterns: {missing}")
            print("  " + "\n  ".join(full_output.split('\n')[:40]))
            return False

        print("  PASS: Got expected DB-time error")
        return True

    finally:
        for path in (project_path, arch_path, db_path):
            if path and os.path.exists(path):
                os.unlink(path)


def test_rtl_parent_with_model_only_child():
    yaml = """blocks:
  top:
    desc: "RTL top"
    hasRtl: true
  modelOnly:
    desc: "Model-only child"
    hasRtl: false

instances:
  uTop: {container: top, instanceType: top}
  uModelOnly: {container: top, instanceType: modelOnly}
"""
    return test_error_case(
        yaml,
        [
            "RTL block 'top'",
            "instance 'uModelOnly'",
            "hasRtl: false",
            "RTL hierarchy requires",
        ],
        "RTL parent contains model-only child",
    )


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING ERROR HANDLING: RTL Hierarchy")
    print("="*70)

    tests = [
        test_rtl_parent_with_model_only_child,
    ]

    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
