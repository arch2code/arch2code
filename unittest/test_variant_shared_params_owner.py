#!/usr/bin/env python3
"""A variant descriptor's isForeign, and the foreign-Config-header selection,
key on the BLOCK's owner (the project owning the file declaring the block),
not on the owner of the ipParameters context. They differ only when a block's
ipParameters live in a definitions-only file another project owns.

Fixture `fixtures/param-variant-shared-params-owner`: projIp declares leafIp,
but leafIp's LEAF_W parameter is declared in projParams, a definitions-only
project projIp includes. projIp and projWrap each bind their own v0 of leafIp,
at LEAF_W 12 and 8 respectively."""

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
from pysrc import artifactPaths
from pysrc.processYaml import projectOpen

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')
FIXTURE = os.path.join(test_dir, 'fixtures', 'param-variant-shared-params-owner')


def _header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def _copy_fixture():
    work = tempfile.mkdtemp(prefix='variant_shared_params_owner_', dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
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


def _leaf_key(prj):
    return next(key for key, row in prj.data['blocks'].items() if row['block'] == 'leafIp')


def test_shared_params_owner():
    _header("a block's isForeign and foreign-Config-header selection key on "
            "the block's own owner, not its ipParameters context's owner")
    work = _copy_fixture()
    try:
        db = os.path.join(work, 'sharedParamsOwner.db')
        project = os.path.join(work, 'top', 'yaml', 'sharedParamsOwnerProject.yaml')
        out, rc = _build_db(project, db)
        if 'Traceback (most recent call last)' in out:
            print("  FAIL: got a Python stack trace instead of a clean build")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False
        if rc != 0:
            print("  FAIL: expected build to succeed")
            print('  ' + '\n  '.join(out.split('\n')[:20]))
            return False

        prj = projectOpen(db)
        leafKey = _leaf_key(prj)
        leafRow = prj.data['blocks'][leafKey]
        paramsOwner = prj.contextOwningProject[leafRow['configContext']]
        blockOwner = prj.contextOwningProject[leafRow['_context']]

        # (a) Premise: leafIp's ipParameters context and its own declaring
        # context are owned by different projects.
        if paramsOwner == blockOwner:
            print(f"  FAIL: premise not met - leafIp's params owner "
                  f"('{paramsOwner}') and block owner ('{blockOwner}') must differ")
            return False
        if paramsOwner != 'projParams' or blockOwner != 'projIp':
            print(f"  FAIL: premise not met - expected params owner 'projParams' "
                  f"and block owner 'projIp', got '{paramsOwner}' and '{blockOwner}'")
            return False
        print(f"  PASS: premise holds, leafIp's params owner is '{paramsOwner}' "
              f"and its block owner is '{blockOwner}'")

        problems = list()

        # (b) projIp's own v0 is not foreign; projWrap's v0 of the same block is.
        descriptors = prj.config.getConfig('VARIANTCONFIGDESCRIPTORS')[leafKey]
        byProjectVariant = {(d['declaringProject'], d['variant']): d for d in descriptors}
        ipDescriptor = byProjectVariant.get(('projIp', 'v0'))
        wrapDescriptor = byProjectVariant.get(('projWrap', 'v0'))
        if ipDescriptor is None or ipDescriptor['isForeign']:
            problems.append(f"expected projIp's v0 descriptor isForeign False, "
                            f"got {ipDescriptor}")
        if wrapDescriptor is None or not wrapDescriptor['isForeign']:
            problems.append(f"expected projWrap's v0 descriptor isForeign True, "
                            f"got {wrapDescriptor}")

        # (c) The bare standalone-variant map holds only the block owner's own v0.
        standalone = prj.getStandaloneVariants(leafKey)
        if standalone != {'v0': {'LEAF_W': 12}}:
            problems.append(f"expected standalone variants {{'v0': {{'LEAF_W': 12}}}}, "
                            f"got {standalone}")

        # (d) FOREIGNCONFIGHEADERS carries projWrap's declaration, not projIp's
        # own or projParams' (projParams declares no variant of the block at all).
        headers = prj.config.getConfig('FOREIGNCONFIGHEADERS')
        if ('projWrap', leafKey) not in headers:
            problems.append("expected ('projWrap', leafKey) in FOREIGNCONFIGHEADERS")
        if ('projIp', leafKey) in headers:
            problems.append("did not expect ('projIp', leafKey) in FOREIGNCONFIGHEADERS")
        if ('projParams', leafKey) in headers:
            problems.append("did not expect ('projParams', leafKey) in FOREIGNCONFIGHEADERS")

        # (e) A block-mode vlSvWrap row exists for projIp's own v0; no
        # registrar-mode vlSvWrapForeign row is emitted under projIp's name.
        blockCondData = {k: prj.getBlockCondRow(k) for k in prj.data['blocks']}
        rows = artifactPaths.artifactRows(prj, blockCondData, prj.data['instances'],
                                          artifactPaths.projectFileMaps(prj))
        ownV0Row = any(r['fileType'] == 'vlSvWrap' and r['mode'] == 'block'
                       and r['blockKey'] == leafKey and r['variant'] == 'v0'
                       and r['owner'] == 'projIp' for r in rows)
        foreignIpRow = any(r['fileType'] == 'vlSvWrapForeign' and r['mode'] == 'registrar'
                           and r['blockKey'] == leafKey and r['owner'] == 'projIp'
                           for r in rows)
        if not ownV0Row:
            problems.append("expected a block-mode vlSvWrap row for leafIp v0 owned by projIp")
        if foreignIpRow:
            problems.append("did not expect a registrar-mode vlSvWrapForeign row owned by projIp")

        if problems:
            print("  FAIL:")
            for problem in problems:
                print(f"    - {problem}")
            return False
        print("  PASS: leafIp's own v0 is not foreign, projWrap's v0 is, "
              "FOREIGNCONFIGHEADERS and the emitted artifact rows agree")
        return True
    finally:
        _close_db()
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("VARIANT SHARED-PARAMS-OWNER TESTS")
    print("="*70)

    tests = [
        test_shared_params_owner,
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
