#!/usr/bin/env python3
"""Stage E5 - eval-derived parameterizable constants emit symbolically into the
SystemC ``Config`` structs, so each variant recomputes them from that struct's
own members instead of freezing the default-variant value.

Two functionality-executing checks, no committed database read-back:

1. The template-layer emitter ``emitCStyleCanonical`` translates canonical eval
   strings to C/C++ RHS text for a stubbed per-symbol spelling. It exercises
   operator pass-through, precedence-driven parenthesization, ``$clog2`` ->
   ``clog2``, authored-base literal re-spelling (hex ``0x..`` / binary ``0b..``),
   and a non-member symbol spelled as a literal.
2. The real emission path on the ``ip_test`` parity vehicle: ``projectCreate``
   builds a fresh database (the only place evals are parsed/evaluated and the
   canonical string is persisted), ``projectOpen`` + ``getContextData`` assemble
   the context view the cppConfig generator consumes, and ``includeConfig``
   renders the per-variant Config structs. An eval-derived member's RHS must be
   symbolic in the struct's own members (``IP_DATA_WIDTH_X2 = IP_DATA_WIDTH *
   2``), the second-level chain must reference the first-level member, and a
   variant whose base param differs must NOT freeze the default-variant value.
"""

import os
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate, projectOpen
from pysrc.systemcGen import genSystemC
from templates.systemc import config

IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'arch', 'yaml', 'project.yaml')


def test_emit_c_style_canonical_translation():
    print(f"\n{'='*70}\nTest: emitCStyleCanonical translates canonical eval -> C RHS"
          f"\n{'='*70}")
    # A stub spelling: A and B are struct members (stay symbolic as their bare
    # member name), C is a non-member symbol (spelled from a persisted value as
    # a literal).
    spell = {'A/f': 'IP_DATA_WIDTH', 'B/f': 'B', 'C/f': '5'}
    symSpelling = lambda key: spell[key]
    cases = [
        ('${A/f} * 2', 'IP_DATA_WIDTH * 2'),                   # operator pass-through, symbolic member
        ('(${A/f} + ${B/f}) * 2', '(IP_DATA_WIDTH + B) * 2'),  # precedence restores parens
        ('$clog2(${A/f} + 1)', 'clog2(IP_DATA_WIDTH + 1)'),    # $clog2 -> clog2
        ("${A/f} + 8'hff", 'IP_DATA_WIDTH + 0xff'),            # authored hex -> C 0x..
        ("${A/f} & 'b1010", 'IP_DATA_WIDTH & 0b1010'),         # authored binary -> C 0b..
        ('${A/f} + ${C/f}', 'IP_DATA_WIDTH + 5'),              # non-member symbol -> literal
    ]
    ok = True
    for canonical, expected in cases:
        got = config.emitCStyleCanonical(canonical, symSpelling)
        if got != expected:
            print(f"  FAIL: {canonical!r} -> {got!r}, expected {expected!r}")
            ok = False
        else:
            print(f"  PASS: {canonical!r} -> {got!r}")
    return ok


def _reset_project_create_class_state():
    projectCreate.data = dict()
    projectCreate.flatData = dict()
    projectCreate.counterGroup = {}
    projectCreate.counterGroupControl = {}
    projectCreate.counterData = {}
    projectCreate.addressObjects = {}
    projectCreate.yamlAllFiles = {}
    projectCreate.yamlUnread = []
    projectCreate.yamlRaw = {}
    projectCreate.yamlDependancies = {}
    projectCreate.yamlContext = {}
    projectCreate.enums = {}
    projectCreate.qualEnums = {}
    projectCreate.includeName = {}
    projectCreate.includeValid = {}
    projectCreate.ipParametersConstants = {}
    projectCreate.errorState = False


def _build_fresh_db():
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    try:
        _reset_project_create_class_state()
        projectCreate(IP_TEST_PROJECT, db_path)
    finally:
        os.chdir(original_cwd)
    g.db = None
    g.cur = None
    return db_path


def _config_member(out, structName, constName):
    """Return the RHS text of `static constexpr ... constName` inside the named
    struct block, or None if absent. Walks the rendered text structurally rather
    than re-parsing C++."""
    lines = out.splitlines()
    inStruct = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"struct {structName} "):
            inStruct = True
            continue
        if inStruct:
            if stripped.startswith("};"):
                return None
            marker = f" {constName} = "
            if marker in line:
                return line.split(marker, 1)[1].rstrip(';').strip()
    return None


def test_config_struct_symbolic_per_variant():
    print(f"\n{'='*70}\nTest: eval-derived Config members emit symbolic, "
          f"per-variant correct\n{'='*70}")
    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)
        data = prj.getContextData(['ip'], genSystemC.dataTypeMappings)
        out = config.includeConfig(None, prj, data)

        # First-level and second-level eval-derived members must be symbolic in
        # the struct's own members, not frozen to the default value (140 / 280).
        expectations = [
            ('ipDefaultConfig', 'IP_DATA_WIDTH_X2', 'IP_DATA_WIDTH * 2'),
            ('ipDefaultConfig', 'IP_DATA_WIDTH_X4', 'IP_DATA_WIDTH_X2 * 2'),
            ('ipDefaultConfig', 'IP_MEM_DEPTH_X2', 'IP_MEM_DEPTH * 2'),
            ('ipDefaultConfig', 'IP_MEM_DEPTH_X4', 'IP_MEM_DEPTH_X2 * 2'),
            # Variant0 overrides IP_DATA_WIDTH=8: the symbolic RHS is unchanged
            # (the variant's own IP_DATA_WIDTH=8 member drives the value to 16).
            ('ipVariant0Config', 'IP_DATA_WIDTH_X2', 'IP_DATA_WIDTH * 2'),
            ('ipVariant0Config', 'IP_DATA_WIDTH_X4', 'IP_DATA_WIDTH_X2 * 2'),
            # Variant1 overrides IP_MEM_DEPTH=8: again symbolic, not the frozen 32.
            ('ipVariant1Config', 'IP_MEM_DEPTH_X2', 'IP_MEM_DEPTH * 2'),
        ]
        ok = True
        for structName, constName, expectedRhs in expectations:
            rhs = _config_member(out, structName, constName)
            if rhs != expectedRhs:
                print(f"  FAIL: {structName}.{constName} RHS {rhs!r}, "
                      f"expected {expectedRhs!r}")
                ok = False
            else:
                print(f"  PASS: {structName}.{constName} = {rhs}")

        # Lock the bug this fixes: variant0's derived member must not freeze the
        # default-variant literal (140 corresponds to default IP_DATA_WIDTH=70).
        v0_x2 = _config_member(out, 'ipVariant0Config', 'IP_DATA_WIDTH_X2')
        if v0_x2 is not None and v0_x2.strip().isdigit():
            print(f"  FAIL: ipVariant0Config.IP_DATA_WIDTH_X2 froze a literal {v0_x2!r}")
            ok = False

        # Dependency ordering inside the struct: a member must be declared before
        # any later member references it (C++ constexpr requires prior decl).
        def _index(structName, constName):
            block = out.split(f"struct {structName} ", 1)[1]
            return block.index(f" {constName} = ")
        for structName in ('ipDefaultConfig', 'ipVariant0Config', 'ipVariant1Config'):
            if _index(structName, 'IP_DATA_WIDTH') > _index(structName, 'IP_DATA_WIDTH_X2'):
                print(f"  FAIL: {structName} declares IP_DATA_WIDTH after IP_DATA_WIDTH_X2")
                ok = False
            if _index(structName, 'IP_DATA_WIDTH_X2') > _index(structName, 'IP_DATA_WIDTH_X4'):
                print(f"  FAIL: {structName} declares IP_DATA_WIDTH_X2 after IP_DATA_WIDTH_X4")
                ok = False
        return ok
    finally:
        if g.db is not None:
            try:
                g.db.close()
            except Exception:
                pass
        g.db = None
        g.cur = None
        if os.path.exists(db_path):
            os.unlink(db_path)


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: Stage E5 - eval-derived constants emit symbolic into Config")
    print("="*70)
    tests = [
        test_emit_c_style_canonical_translation,
        test_config_struct_symbolic_per_variant,
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
