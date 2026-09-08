#!/usr/bin/env python3
"""An instance's variant label resolves through the include chain of the file
holding the instance row, own file first, and needs exactly one visible
declaration of (block, variant). Zero or several is a db-time error naming the
declaring files, or the out-of-scope declarer.

Fixtures: a label declared both in an instance's own file and in a file it
includes; and a label declared only in a file that includes the instance's own
file, which is out of scope."""

import os
import shutil
import subprocess
import sys
import tempfile

import yaml

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')
TWO_DECLARERS_FIXTURE = os.path.join(test_dir, 'fixtures', 'param-variant-two-declarers')
OUT_OF_RANGE_FIXTURE = os.path.join(test_dir, 'fixtures', 'variant-scope-out-of-range')


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def _copy_fixture(fixture, prefix):
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(fixture, work, dirs_exist_ok=True)
    return work


def _build_db(project, db):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, ARCH2CODE, '--yaml', project, '--db', db],
        capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
    return result.stdout + result.stderr, result.returncode


def _close_db():
    if g.db is not None:
        g.db.close()
        g.db = None


def _read(path):
    with open(path) as f:
        return f.read()


def _write(path, content):
    with open(path, 'w') as f:
        f.write(content)


def test_two_visible_declarations_rejected():
    _header("a label visible in the instance's own file and an included file "
            "is rejected, naming both")
    work = _copy_fixture(TWO_DECLARERS_FIXTURE, 'variant_scope_two_declarers_')
    try:
        wrap = os.path.join(work, 'projWrap', 'yaml', 'wrapTop.yaml')
        parsed = yaml.safe_load(_read(wrap))
        if 'v0' not in (parsed.get('parameters') or {}).get('leafIp', {}):
            print("  FAIL: premise not met - wrapTop.yaml must declare leafIp v0 itself")
            return False
        ip = os.path.join(work, 'projIp', 'yaml', 'ipTop.yaml')
        parsedIp = yaml.safe_load(_read(ip))
        if 'v0' not in (parsedIp.get('parameters') or {}).get('leafIp', {}):
            print("  FAIL: premise not met - ipTop.yaml must declare leafIp v0 too")
            return False
        includes = parsed.get('include') or []
        if not any('ipTop.yaml' in inc for inc in includes):
            print("  FAIL: premise not met - wrapTop.yaml must include ipTop.yaml")
            return False
        print("  PASS: premise holds, wrapTop.yaml declares leafIp v0 itself and "
              "also includes ipTop.yaml, which declares it too")

        db = os.path.join(work, 'twoDeclarers.db')
        project = os.path.join(work, 'top', 'yaml', 'twoDeclarersProject.yaml')
        out, rc = _build_db(project, db)
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        missing = [p for p in ('wrapTop.yaml', 'ipTop.yaml',
                                'more than one visible declaration') if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming both wrapTop.yaml and ipTop.yaml")

        # Fault-inject: drop the included file's declaration, leaving the
        # wrapper's own. Dropping the wrapper's instead would leave the leaf at
        # 12 against wrapSt's hardcoded 8 and fail on that layout check, not this one.
        text = _read(ip)
        anchor = ("parameters:\n"
                  "    leafIp:\n"
                  "        v0:\n"
                  "            LEAF_W: 12\n")
        if anchor not in text:
            raise AssertionError("included file's leafIp v0 binding anchor is missing")
        _write(ip, text.replace(anchor, "", 1))
        out, rc = _build_db(project, db)
        if rc != 0:
            print("  FAIL: fault-injected copy (one declaration removed) should have built")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: fault-injected copy (included file's declaration removed) builds")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_out_of_scope_declaration_rejected():
    _header("a label declared only downstream of the instance's own file is "
            "rejected, naming the out-of-scope declarer")
    work = _copy_fixture(OUT_OF_RANGE_FIXTURE, 'variant_scope_out_of_range_')
    try:
        mid = os.path.join(work, 'yaml', 'vsrMid.yaml')
        top = os.path.join(work, 'yaml', 'vsrTop.yaml')
        midParsed = yaml.safe_load(_read(mid))
        topParsed = yaml.safe_load(_read(top))
        if 'parameters' in midParsed:
            print("  FAIL: premise not met - vsrMid.yaml must declare no v1 of its own")
            return False
        if 'v1' not in (topParsed.get('parameters') or {}).get('vsrLeaf', {}):
            print("  FAIL: premise not met - vsrTop.yaml must declare vsrLeaf v1")
            return False
        includes = topParsed.get('include') or []
        if not any('vsrMid.yaml' in inc for inc in includes):
            print("  FAIL: premise not met - vsrTop.yaml must include vsrMid.yaml")
            return False
        print("  PASS: premise holds, vsrTop.yaml (which includes vsrMid.yaml) "
              "declares vsrLeaf v1, and vsrMid.yaml declares none of its own")

        db = os.path.join(work, 'vsr.db')
        project = os.path.join(work, 'yaml', 'vsrProject.yaml')
        out, rc = _build_db(project, db)
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        missing = [p for p in ('vsrMid.yaml', 'vsrTop.yaml', "declared in",
                                "outside this instance's scope") if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming vsrTop.yaml as the out-of-scope declarer")

        # Fault-inject: move the declaration into vsrMid.yaml itself (the
        # instance's own file), which puts it back in scope.
        _move_declaration_to_mid(top, mid)
        out, rc = _build_db(project, db)
        if rc != 0:
            print("  FAIL: fault-injected copy (declaration moved in scope) should have built")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: fault-injected copy (declaration moved into vsrMid.yaml) builds")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_two_out_of_scope_declarers_both_named():
    """A second file declaring the same out-of-scope label, added only by
    this cell. Both files sit outside uLeaf's scope, so the message must name
    both, not just the first found."""
    _header("two out-of-scope declarers of one label are both named")
    work = _copy_fixture(OUT_OF_RANGE_FIXTURE, 'variant_scope_two_out_of_range_')
    try:
        project = os.path.join(work, 'yaml', 'vsrProject.yaml')
        second = os.path.join(work, 'yaml', 'vsrTop2.yaml')
        _write(second, "include:\n    - vsrLeaf.yaml\n\n"
                       "parameters:\n    vsrLeaf:\n        v1:\n"
                       "            VSR_W: 4\n")
        text = _read(project)
        anchor = "projectFiles:\n    - vsrTop.yaml\n"
        if anchor not in text:
            raise AssertionError("vsrProject.yaml's projectFiles anchor is missing")
        _write(project, text.replace(
            anchor, anchor + "    - vsrTop2.yaml\n", 1))

        db = os.path.join(work, 'vsr.db')
        out, rc = _build_db(project, db)
        if rc == 0:
            print("  FAIL: expected rejection, build succeeded")
            return False
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean error")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        missing = [p for p in ('vsrTop.yaml', 'vsrTop2.yaml') if p not in out]
        if missing:
            print(f"  FAIL: expected patterns not found: {missing}")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        print("  PASS: rejected, naming both vsrTop.yaml and vsrTop2.yaml")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


_DECLARATION = ("parameters:\n"
                "    vsrLeaf:\n"
                "        v1:\n"
                "            VSR_W: 4\n")


def _move_declaration_to_mid(top, mid):
    """Drop the label's declaration from vsrTop.yaml and append it to
    vsrMid.yaml instead, moving it into the instance's own scope."""
    text = _read(top)
    anchor = "\n" + _DECLARATION
    if anchor not in text:
        raise AssertionError("vsrTop.yaml's parameters: anchor is missing")
    _write(top, text.replace(anchor, "", 1))
    _write(mid, _read(mid) + "\n" + _DECLARATION)


def test_in_scope_declaration_resolves_to_its_own_project():
    _header("an instance resolving a label declared in an included file "
            "builds, and its persisted declarer is that file's project")
    work = _copy_fixture(OUT_OF_RANGE_FIXTURE, 'variant_scope_in_range_')
    try:
        mid = os.path.join(work, 'yaml', 'vsrMid.yaml')
        top = os.path.join(work, 'yaml', 'vsrTop.yaml')
        _move_declaration_to_mid(top, mid)

        db = os.path.join(work, 'vsr.db')
        project = os.path.join(work, 'yaml', 'vsrProject.yaml')
        out, rc = _build_db(project, db)
        if rc != 0:
            print("  FAIL: expected success, build failed")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        prj = projectOpen(db)
        declarers = {k: v for k, v in prj.instanceVariantDeclarers.items()
                    if k.startswith('uLeaf/')}
        if declarers != {'uLeaf/vsrMid.yaml': 'vsrScope'}:
            print(f"  FAIL: expected uLeaf's persisted declarer to be "
                  f"vsrMid.yaml's own project 'vsrScope', got {declarers}")
            return False
        print("  PASS: build succeeded, uLeaf's persisted declarer is "
              "vsrMid.yaml's own project")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("VARIANT SCOPE RESOLUTION TESTS")
    print("="*70)

    tests = [
        test_two_visible_declarations_rejected,
        test_out_of_scope_declaration_rejected,
        test_two_out_of_scope_declarers_both_named,
        test_in_scope_declaration_resolves_to_its_own_project,
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
