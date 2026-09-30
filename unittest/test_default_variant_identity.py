#!/usr/bin/env python3
"""A variant literally labelled 'default', declared by a block's own owner, is
the block's default Config: its bound values win over a synthetic default built
from the constant's declared value, and one Config struct is persisted under
that identity.

Fixture `fixtures/default-variant-identity`: `dvCont` binds a `default:` variant
at DV_ALGO 6 against a declared value of 1; the persisted struct must carry 6."""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'default-variant-identity')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _copy_fixture(prefix):
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
    return work


def _build_db(work):
    """Build the fixture's database. Returns (db_path, combined output, returncode)."""
    db = os.path.join(work, 'dvIdentity.db')
    project = os.path.join(work, 'yaml', 'dvProject.yaml')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project, '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return db, result.stdout + result.stderr, result.returncode


def _close_db():
    if g.db is not None:
        g.db.close()
        g.db = None


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def test_declared_default_variant_takes_over_the_default_identity():
    _header("an owner-declared 'default' variant supersedes the synthetic default")
    work = _copy_fixture('default_variant_identity_')
    try:
        db, out, rc = _build_db(work)
        if rc != 0:
            print("  FAIL: the fixture did not build")
            print('  ' + '\n  '.join(out.split('\n')[:25]))
            return False
        prj = projectOpen(db)
        blockKey = prj.getQualBlock('dvCont')

        default = prj.defaultConfigDescriptors[blockKey]
        if default['values'] != {'DV_ALGO': 6, 'DV_WIDTH': 8}:
            print(f"  FAIL: the block's default Config carries {default['values']}, "
                  f"expected the declared 'default' variant's {{'DV_ALGO': 6, "
                  f"'DV_WIDTH': 8}}, not the constant's own declared value")
            return False
        print("  PASS: the block's default Config carries the declared variant's values")

        variants = prj.variantConfigDescriptors[blockKey]
        if len(variants) != 1 or variants[0]['variant'] != 'default':
            print(f"  FAIL: expected exactly one declared variant ('default'), "
                  f"found {[d['variant'] for d in variants]}")
            return False
        print("  PASS: no separate synthetic descriptor is persisted alongside it")

        # The view a Config module renders from must also carry one entry, not the struct twice.
        moduleData = prj.getConfigModuleData(blockKey, prj.getQualBlock('dvCont'))
        if len(moduleData['descriptors']) != 1:
            print(f"  FAIL: getConfigModuleData returned "
                  f"{len(moduleData['descriptors'])} descriptors for one declared "
                  f"variant, expected 1 (would emit the struct twice)")
            return False
        print("  PASS: getConfigModuleData emits the struct once")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("DEFAULT VARIANT IDENTITY TESTS")
    print("="*70)

    tests = [
        test_declared_default_variant_takes_over_the_default_identity,
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
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
