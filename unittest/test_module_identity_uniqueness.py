#!/usr/bin/env python3
"""projectCreate guard: no two distinct contexts may resolve to the same
module/package identity (contextModuleIdentity).

That identity names each context's generated SystemC module and namespace and
its SystemVerilog package, so two contexts sharing one identity would emit the
same module/package name and silently clobber each other's output. The guard
fails fast at database creation with a clear, traceback-free error naming both
colliding contexts and their owning projects.

Negative case: two context files sharing an explicit `includeName:` collide and
projectCreate must exit with the collision error.
Positive case: distinct includeNames build cleanly (guard does not over-fire).
"""

import os
import sys
import tempfile
import subprocess

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import qualifyModuleIdentity

PROJECT_NAME = 'module_identity_test'


def _write_temp(content, suffix, prefix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=test_dir)
    os.close(fd)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


def _run_project(arch_a, arch_b):
    """Write two context files plus a project that includes both, run
    projectCreate as a subprocess, and return (returncode, combined output)."""
    arch_a_path = _write_temp(arch_a, '.yaml', 'arch_ident_a_')
    arch_b_path = _write_temp(arch_b, '.yaml', 'arch_ident_b_')
    project_content = f"""projectName: {PROJECT_NAME}
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_a_path)}
  - {os.path.basename(arch_b_path)}
"""
    project_path = _write_temp(project_content, '_project.yaml', 'proj_ident_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        cmd = [sys.executable, os.path.join(base_dir, 'arch2code.py'),
               '--yaml', project_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=test_dir, env=env)
        return result.returncode, result.stderr + result.stdout
    finally:
        _cleanup([arch_a_path, arch_b_path, project_path, db_path])


# A minimal design (blocks + instances) plus a second content-bearing context.
_ARCH_DESIGN = """blocks:
  ip: { desc: "ip" }
  top: { desc: "top" }
instances:
  uTop: { container: top, instanceType: top }
  uIp: { container: top, instanceType: ip }
"""

_ARCH_TYPES = """constants:
  SOME_C: { value: 4, desc: "a constant giving this context content" }
"""


def test_identity_collision_rejected():
    print(f"\n{'='*70}\nTest: duplicate module identity rejected\n{'='*70}")
    # Both context files carry the same explicit includeName, so both resolve to
    # the same module/package identity - a collision the guard must catch. The
    # reported identity is the shared include stem project-qualified by the
    # owning project, derived here from the generator's own identity function so
    # this expectation cannot drift from the identity rule.
    arch_a = "includeName: dupctx\n" + _ARCH_DESIGN
    arch_b = "includeName: dupctx\n" + _ARCH_TYPES
    identity = qualifyModuleIdentity('dupctx', PROJECT_NAME)
    rc, out = _run_project(arch_a, arch_b)
    if rc == 0:
        print("  FAIL: expected error but build succeeded")
        return False
    if 'Traceback (most recent call last)' in out:
        print("  FAIL: got Python stack trace instead of clean error")
        print('  ' + '\n  '.join(out.split('\n')[:25]))
        return False
    expected = [f"Module/package identity '{identity}'",
                "two distinct contexts",
                PROJECT_NAME,
                "distinct includeName"]
    missing = [p for p in expected if p.lower() not in out.lower()]
    if missing:
        print(f"  FAIL: expected patterns not found: {missing}")
        print('  ' + '\n  '.join(out.split('\n')[:25]))
        return False
    print("  PASS: guard fired with the collision error")
    return True


def test_distinct_identities_ok():
    print(f"\n{'='*70}\nTest: distinct module identities build cleanly\n{'='*70}")
    # Same content, but the two contexts keep distinct includeNames, so no
    # collision and the guard stays silent.
    arch_a = "includeName: ctxDesign\n" + _ARCH_DESIGN
    arch_b = "includeName: ctxTypes\n" + _ARCH_TYPES
    rc, out = _run_project(arch_a, arch_b)
    if rc != 0:
        print("  FAIL: expected success but build failed")
        print('  ' + '\n  '.join(out.split('\n')[:25]))
        return False
    print("  PASS: distinct identities built without the guard firing")
    return True


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: module/package identity uniqueness guard")
    print("="*70)
    tests = [
        test_identity_collision_rejected,
        test_distinct_identities_ok,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "="*70 + "\nTEST SUMMARY\n" + "="*70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
