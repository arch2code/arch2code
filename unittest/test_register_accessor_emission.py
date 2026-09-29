#!/usr/bin/env python3
"""`registerFeatures` (templates/systemc/structures.py) emits a struct's
`_getValue`/`_setValue` register accessors, one packed-word term per field.

`_getValue` had two bugs. The per-field emission sat outside the loop over
`vars['vars']`, so only the last field (by dict order) ever contributed a
term. The surviving term also parenthesised the mask as
`(name & (mask << shift))` instead of `((name & mask) << shift)`, so `<<`
bound before `&` and every field not at bit 0 packed to zero.

This pins both: one term per field, each shaped `((name & mask) << shift)`,
against a plain (non-parameterizable) three-field register structure at
offsets 0, 8 and 40 (the same shape as apbDecode's `un0ARegSt`). `_setValue`
is unpacked correctly already; its line count and shape must stay unchanged.
"""

import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.systemcGen import genSystemC
from templates.systemc import structures

from _addrctl_helpers import build_database, cleanup, projectOpen


ARCH_YAML = """types:
    u8T:  { width: 8,  desc: "Byte" }
    u32T: { width: 32, desc: "Word" }

structures:
    un0RegSt:
        fa: { varType: u8T,  generator: register, desc: "[7:0]" }
        fb: { varType: u32T, generator: register, desc: "[39:8]" }
        fc: { varType: u8T,  generator: register, desc: "[47:40]" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true

instances:
    uTop: { container: top, instanceType: top }
"""


def _header(name):
    print("\n" + "=" * 70)
    print(f"Test: {name}")
    print("=" * 70)


def _getStructData(prj):
    """The decorated structures view `registerFeatures` renders from, exactly
    as `genSystemC` builds it: per-context data plus the `calcStructure`
    pass that fills in `bitshift`/`bitwidth`/`isArray`/`register`."""
    for context in prj.yamlContext:
        if context.startswith('_'):
            continue
        data = prj.getContextData([context], genSystemC.dataTypeMappings)
        genSystemC.calcStructure(genSystemC, data, prj)
        for structData in data['structures'].values():
            if structData['structure'] == 'un0RegSt':
                return structData
    raise AssertionError("un0RegSt was not rendered into any context")


def _getValueTerm(name, width, shift):
    return f"(( {name} & ((1ULL<<{width})-1) ) << {shift})"


def _setValueLine(name, typeName, width, shift):
    return (f"{name} = ( {typeName} ) (( packedValue >> {shift} ) & "
            f"(( (uint64_t)1 << {width} ) - 1)) ;")


def test_getvalue_one_term_per_field():
    """Every field contributes a `_getValue` term, correctly masked-then-shifted."""
    _header("_getValue emits one correctly masked term per field")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        structData = _getStructData(prj)
        rendered = '\n'.join(structures.registerFeatures(structData, '    ', prj, False))

        expected = [
            _getValueTerm('fa', 8, 0),
            _getValueTerm('fb', 32, 8),
            _getValueTerm('fc', 8, 40),
        ]
        for term in expected:
            count = rendered.count(term)
            if count != 1:
                print(f"  FAIL: term {term!r} appears {count} times, expected 1")
                ok = False
            else:
                print(f"  ok: {term}")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print("  PASS: three fields, three correctly masked-and-shifted terms")
    return ok


def test_setvalue_unchanged():
    """`_setValue` keeps its per-field unpacking, one line per field."""
    _header("_setValue is unchanged: one unpack line per field")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        structData = _getStructData(prj)
        out = structures.registerFeatures(structData, '    ', prj, False)
        rendered = '\n'.join(out)

        expected = [
            _setValueLine('fa', 'u8T', 8, 0),
            _setValueLine('fb', 'u32T', 32, 8),
            _setValueLine('fc', 'u8T', 8, 40),
        ]
        setValueLines = [line for line in out if 'packedValue >>' in line]
        if len(setValueLines) != 3:
            print(f"  FAIL: expected 3 _setValue lines, got {len(setValueLines)}")
            ok = False
        for line in expected:
            if line not in rendered:
                print(f"  FAIL: missing expected _setValue line: {line!r}")
                ok = False
            else:
                print(f"  ok: {line}")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print("  PASS: _setValue unpacking unchanged")
    return ok


def run_all_tests():
    print("=" * 70)
    print("TESTING: register _getValue/_setValue accessor emission")
    print("=" * 70)
    tests = [
        test_getvalue_one_term_per_field,
        test_setvalue_unchanged,
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

    print("\n" + "=" * 70 + "\nTEST SUMMARY\n" + "=" * 70)
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
