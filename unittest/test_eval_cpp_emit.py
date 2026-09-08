#!/usr/bin/env python3
"""A block's Config struct carries exactly the parameters it declares; an
eval-derived constant is computed in the Base class instead, symbolic in the
block's own Config params.

Pins the C++ expression translation, the parenthesization of a derived
constant substituted into a larger expression, and the real Config and Base
renders on the ip_test tree."""

import os
import sys
import tempfile
from types import SimpleNamespace

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate, projectOpen
from pysrc.systemcGen import genSystemC
from templates.systemc import baseClassDecl
from templates.systemc import config
from templates.systemc import includes
from templates.systemc import structures

IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'prj', 'yaml', 'ip_testProject.yaml')


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


def test_const_reference_cpp_parenthesizes_compound_derived():
    print(f"\n{'='*70}\nTest: constReference_cpp parenthesizes a compound "
          f"derived constant substituted at its call site\n{'='*70}")
    # A sum: substituted bare into a surrounding multiplication it would rebind
    # the operator.
    constants = {
        'DEBAYER_DIMENSION/d': {
            'isParameterizable': True, 'evalCanonical': '',
            'constant': 'DEBAYER_DIMENSION'},
        'PIXELS_PER_CLOCK/d': {
            'isParameterizable': True, 'evalCanonical': '',
            'constant': 'PIXELS_PER_CLOCK'},
        'PREPROCESS_GRID_WIDTH/d': {
            'isParameterizable': True,
            'evalCanonical': '${DEBAYER_DIMENSION/d} + ${PIXELS_PER_CLOCK/d} - 1',
            'constant': 'PREPROCESS_GRID_WIDTH'},
    }
    prj = SimpleNamespace(data={'constants': constants})

    emitted = includes.constReference_cpp('PREPROCESS_GRID_WIDTH/d', prj, useConfig=True)
    ok = True
    if emitted.startswith('(') and emitted.endswith(')'):
        print(f"  PASS: emitted expression is parenthesized: {emitted!r}")
    else:
        print(f"  FAIL: emitted expression is not parenthesized: {emitted!r}")
        ok = False

    # Python's +, -, * precedence matches C++'s, so eval() gives the width C++ would.
    DEBAYER_DIMENSION, PIXELS_PER_CLOCK = 5, 4
    substituted = f"8*{emitted}".replace('Config::', '')
    width = eval(substituted)  # noqa: S307 (fixed test expression, not user input)
    correctWidth = 8 * (DEBAYER_DIMENSION + PIXELS_PER_CLOCK - 1)
    if width == correctWidth:
        print(f"  PASS: 8*{emitted} evaluates to the correct width {width}")
    else:
        print(f"  FAIL: 8*{emitted} evaluates to {width}, expected {correctWidth}")
        ok = False
    return ok


def test_const_reference_cpp_parenthesizes_nested_derived_reference():
    print(f"\n{'='*70}\nTest: constReference_cpp parenthesizes a derived "
          f"constant's own referent when that referent is itself derived"
          f"\n{'='*70}")
    # Nests the sum above; the inner substitution needs its own parens or the
    # trailing `- 1` binds to the outer `* 2`.
    constants = {
        'DEBAYER_DIMENSION/d': {
            'isParameterizable': True, 'evalCanonical': '',
            'constant': 'DEBAYER_DIMENSION'},
        'PIXELS_PER_CLOCK/d': {
            'isParameterizable': True, 'evalCanonical': '',
            'constant': 'PIXELS_PER_CLOCK'},
        'PREPROCESS_GRID_WIDTH/d': {
            'isParameterizable': True,
            'evalCanonical': '${DEBAYER_DIMENSION/d} + ${PIXELS_PER_CLOCK/d} - 1',
            'constant': 'PREPROCESS_GRID_WIDTH'},
        'PREPROCESS_GRID_WIDTH_X2/d': {
            'isParameterizable': True,
            'evalCanonical': '${PREPROCESS_GRID_WIDTH/d} * 2',
            'constant': 'PREPROCESS_GRID_WIDTH_X2'},
    }
    prj = SimpleNamespace(data={'constants': constants})

    emitted = includes.constReference_cpp('PREPROCESS_GRID_WIDTH_X2/d', prj, useConfig=True)
    DEBAYER_DIMENSION, PIXELS_PER_CLOCK = 5, 4
    correctWidth = (DEBAYER_DIMENSION + PIXELS_PER_CLOCK - 1) * 2
    width = eval(emitted.replace('Config::', ''))  # noqa: S307 (fixed test expression, not user input)
    if width == correctWidth:
        print(f"  PASS: {emitted} evaluates to the correct width {width}")
        return True
    print(f"  FAIL: {emitted} evaluates to {width}, expected {correctWidth}")
    return False


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
        # Foreign Config structs are emitted `export struct ...` inside a module
        # interface unit; same-context Config structs stay bare `struct ...`.
        if (stripped.startswith(f"struct {structName} ") or
                stripped.startswith(f"export struct {structName} ")):
            inStruct = True
            continue
        if inStruct:
            if stripped.startswith("};"):
                return None
            marker = f" {constName} = "
            if marker in line:
                return line.split(marker, 1)[1].rstrip(';').strip()
    return None


def test_config_struct_derived_members_move_to_base():
    print(f"\n{'='*70}\nTest: derived Config members leave the struct and are "
          f"computed in the Base class\n{'='*70}")
    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)
        # A reusable IP that instantiates nothing is its own --parent
        # (calcConfigModules), so ip's default and variant0 live there.
        ownData = prj.getBlockData(prj.getQualBlock('ip'))
        ownData['parent'] = 'ip'
        out = config.configModule(None, prj, ownData)
        # ipBridge declares ip@variant1, so its struct is ipBridge_ipVariant1Config in the bridge's domain.
        foreignData = prj.getBlockData(prj.getQualBlock('ip'))
        foreignData['parent'] = 'ipBridge'
        foreignOut = config.configModule(None, prj, foreignData)

        ok = True
        derived = ('IP_DATA_WIDTH_X2', 'IP_DATA_WIDTH_X4', 'IP_MEM_DEPTH_X2', 'IP_MEM_DEPTH_X4')
        for structName in ('ip_ipDefaultConfig', 'ip_ipVariant0Config'):
            for constName in derived:
                if _config_member(out, structName, constName) is not None:
                    print(f"  FAIL: {structName} still carries derived member {constName}")
                    ok = False
        if _config_member(foreignOut, 'ipBridge_ipVariant1Config', 'IP_DATA_WIDTH') is None:
            print(f"  FAIL: ipBridge_ipVariant1Config struct is absent from the "
                  f"rendered output")
            ok = False
        else:
            for constName in derived:
                if _config_member(foreignOut, 'ipBridge_ipVariant1Config', constName) is not None:
                    print(f"  FAIL: ipBridge_ipVariant1Config still carries derived member {constName}")
                    ok = False
        if ok:
            print(f"  PASS: no Config struct carries a derived member")

        # ip declares only these three params; its Config carries exactly them.
        ownParams = ('IP_DATA_WIDTH', 'IP_MEM_DEPTH', 'IP_NONCONST_DEPTH')
        for constName in ownParams:
            if _config_member(out, 'ip_ipDefaultConfig', constName) is None:
                print(f"  FAIL: ip_ipDefaultConfig is missing its own param {constName}")
                ok = False
        if ok:
            print(f"  PASS: ip_ipDefaultConfig carries exactly its own declared params")

        # Second-level derived constants chain through the first by bare name, not re-expanded.
        block_data = prj.getBlockData(prj.getQualBlock('ip'))
        baseOut = baseClassDecl.render(
            SimpleNamespace(mode='module', noExternalComments=False), prj, block_data)
        expectations = [
            ('IP_DATA_WIDTH_X2', 'Config::IP_DATA_WIDTH * 2'),
            ('IP_DATA_WIDTH_X4', 'IP_DATA_WIDTH_X2 * 2'),
            ('IP_MEM_DEPTH_X2', 'Config::IP_MEM_DEPTH * 2'),
            ('IP_MEM_DEPTH_X4', 'IP_MEM_DEPTH_X2 * 2'),
        ]
        for constName, expectedRhs in expectations:
            marker = f"static constexpr auto {constName} = {expectedRhs};"
            if marker not in baseOut:
                print(f"  FAIL: ipBase missing {marker!r}")
                ok = False
            else:
                print(f"  PASS: ipBase.{constName} = {expectedRhs}")

        # C++ constexpr needs a prior declaration, so X2 must precede X4.
        if baseOut.index('IP_DATA_WIDTH_X2 =') > baseOut.index('IP_DATA_WIDTH_X4 ='):
            print(f"  FAIL: ipBase declares IP_DATA_WIDTH_X2 after IP_DATA_WIDTH_X4")
            ok = False
        if baseOut.index('IP_MEM_DEPTH_X2 =') > baseOut.index('IP_MEM_DEPTH_X4 ='):
            print(f"  FAIL: ipBase declares IP_MEM_DEPTH_X2 after IP_MEM_DEPTH_X4")
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


def _fw_constant(out, constName):
    """Return the RHS text of a flat `inline constexpr <type> constName = ...;`
    line in the FW constants section, or None if absent. Walks the rendered text
    structurally. The FW emitter spells flat constants `inline constexpr` (an
    ODR-safe module-linkage form), not the older `const <type>`."""
    marker = f" {constName} = "
    for line in out.splitlines():
        if marker in line and line.strip().startswith("inline constexpr "):
            return line.split(marker, 1)[1].split(';', 1)[0].strip()
    return None


def test_fw_constants_symbolic():
    print(f"\n{'='*70}\nTest: eval-derived parameterizable constants emit symbolic "
          f"into the FW header\n{'='*70}")
    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)
        ipCtx = prj.data['blocks'][prj.getQualBlock('ip')]['_context']
        data = prj.getContextData([ipCtx], genSystemC.dataTypeMappings)
        out = includes.includeConstants(SimpleNamespace(mode='fw'), prj, data)

        ok = True
        # FW has no per-variant Config. A first-level eval-derived parameterizable
        # constant re-spells its block-param referent from the persisted (default)
        # value (IP_DATA_WIDTH=70), keeping the operator structure; a second-level
        # one chains symbolically through the sibling FW constant.
        expectations = [
            ('IP_DATA_WIDTH_X2', '70 * 2'),
            ('IP_DATA_WIDTH_X4', 'IP_DATA_WIDTH_X2 * 2'),
            ('IP_MEM_DEPTH_X2', '16 * 2'),
            ('IP_MEM_DEPTH_X4', 'IP_MEM_DEPTH_X2 * 2'),
            # Non-parameterizable eval-derived constant keeps its resolved value.
            ('IP_FIXED_WORD_COUNT', '6'),
        ]
        for constName, expectedRhs in expectations:
            rhs = _fw_constant(out, constName)
            if rhs != expectedRhs:
                print(f"  FAIL: {constName} RHS {rhs!r}, expected {expectedRhs!r}")
                ok = False
            else:
                print(f"  PASS: {constName} = {rhs}")

        # Dependency ordering: a chained member must be declared after the
        # sibling it references (C requires the prior const definition).
        if out.index(" IP_DATA_WIDTH_X2 = ") > out.index(" IP_DATA_WIDTH_X4 = "):
            print("  FAIL: IP_DATA_WIDTH_X2 declared after IP_DATA_WIDTH_X4")
            ok = False
        if out.index(" IP_MEM_DEPTH_X2 = ") > out.index(" IP_MEM_DEPTH_X4 = "):
            print("  FAIL: IP_MEM_DEPTH_X2 declared after IP_MEM_DEPTH_X4")
            ok = False

        # The block param itself (non-eval parameterizable) is NOT emitted as a
        # flat FW constant; it has no single firmware value.
        if _fw_constant(out, 'IP_DATA_WIDTH') is not None:
            print("  FAIL: block param IP_DATA_WIDTH emitted as a flat FW constant")
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


def _config_member_lines(out, structName):
    """Return the in-order `constName = rhs` member pairs declared in the named
    struct block of a rendered text blob. Walks structurally, no C++ re-parse."""
    members = []
    inStruct = False
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"struct {structName} "):
            inStruct = True
            continue
        if inStruct:
            if stripped.startswith("};"):
                break
            if " = " in stripped and stripped.startswith("static constexpr"):
                lhs, rhs = stripped.split(" = ", 1)
                members.append((lhs.split()[-1], rhs.rstrip(';').strip()))
    return members


def test_teststructs_parameterizable_sample_points():
    print(f"\n{'='*70}\nTest: parameterizable struct tests emit Default/Mid/Max "
          f"sample-point Configs (Option C)\n{'='*70}")
    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)
        ipCtx = prj.data['blocks'][prj.getQualBlock('ip')]['_context']
        data = prj.getContextData([ipCtx], genSystemC.dataTypeMappings)

        hdr = structures.render(
            SimpleNamespace(mode='module', section='testStructsHeader',
                            template='structures', namespace=''),
            prj, data)
        cpp = structures.render(
            SimpleNamespace(mode='module', section='testStructsCPP',
                            template='structures', namespace=''),
            prj, data)

        ok = True

        # Header: a single generic round-trip helper templated over the struct
        # type, and a NON-templated test class (Option C pushes the Config choice
        # into test(), not onto the caller).
        if hdr.count('static void roundTrip(') != 1:
            print(f"  FAIL: expected exactly one roundTrip helper in header")
            ok = False
        else:
            print(f"  PASS: single roundTrip<T> helper emitted")
        if 'template<typename Config>\nclass test_ip_structs' in hdr or \
           'template<typename Config> class test_ip_structs' in hdr:
            print(f"  FAIL: test_ip_structs class is still templated")
            ok = False
        elif 'class test_ip_structs {' in hdr:
            print(f"  PASS: test_ip_structs class is non-templated")
        else:
            print(f"  FAIL: test_ip_structs class declaration not found")
            ok = False

        # CPP: three de-duplicated sample-point Config structs at the fixed names,
        # carrying the Default/Mid/Max base-param values. Sample points are
        # variant-independent (declared value/maxValue only): Default = value,
        # Max = maxValue, Mid = maxValue // 2. IP_DATA_WIDTH 70/64/128,
        # IP_MEM_DEPTH 16/16/32, IP_NONCONST_DEPTH 24/12/24.
        expectedBase = {
            'ipTestConfigDefault': {'IP_DATA_WIDTH': '70', 'IP_MEM_DEPTH': '16', 'IP_NONCONST_DEPTH': '24'},
            'ipTestConfigMid':     {'IP_DATA_WIDTH': '64', 'IP_MEM_DEPTH': '16', 'IP_NONCONST_DEPTH': '12'},
            'ipTestConfigMax':     {'IP_DATA_WIDTH': '128', 'IP_MEM_DEPTH': '32', 'IP_NONCONST_DEPTH': '24'},
        }
        for structName, baseExpect in expectedBase.items():
            members = dict(_config_member_lines(cpp, structName))
            if not members:
                print(f"  FAIL: {structName} not emitted")
                ok = False
                continue
            for constName, expVal in baseExpect.items():
                if members.get(constName) != expVal:
                    print(f"  FAIL: {structName}.{constName} = {members.get(constName)!r}, "
                          f"expected {expVal!r}")
                    ok = False
            # Eval-derived members stay symbolic in the struct's own members so
            # the C++ constexpr recomputes them from this sample point.
            if members.get('IP_DATA_WIDTH_X2') != 'IP_DATA_WIDTH * 2':
                print(f"  FAIL: {structName}.IP_DATA_WIDTH_X2 not symbolic: "
                      f"{members.get('IP_DATA_WIDTH_X2')!r}")
                ok = False
            if ok:
                print(f"  PASS: {structName} base values + symbolic derived members")

        # Call list: a parameterizable struct is exercised once per sample point;
        # a concrete struct exactly once (no Config).
        for role in ('ipTestConfigDefault', 'ipTestConfigMid', 'ipTestConfigMax'):
            if f'roundTrip<ipDataSt<{role}>>("ipDataSt"' not in cpp:
                print(f"  FAIL: missing ipDataSt call at {role}")
                ok = False
        if cpp.count('roundTrip<ipFixedSt>("ipFixedSt"') != 1:
            print(f"  FAIL: concrete ipFixedSt not called exactly once")
            ok = False
        else:
            print(f"  PASS: param struct at 3 sample points, concrete struct once")

        # Signed-pattern selection survives the helper-call form.
        if 'roundTrip<ipFixedSignedSt>("ipFixedSignedSt", signedPatterns)' not in cpp:
            print(f"  FAIL: signed struct does not select signedPatterns")
            ok = False
        else:
            print(f"  PASS: signed struct selects signedPatterns")

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
    print("TESTING: eval-derived constants leave the Config, computed in the Base class")
    print("="*70)
    tests = [
        test_emit_c_style_canonical_translation,
        test_const_reference_cpp_parenthesizes_compound_derived,
        test_const_reference_cpp_parenthesizes_nested_derived_reference,
        test_config_struct_derived_members_move_to_base,
        test_fw_constants_symbolic,
        test_teststructs_parameterizable_sample_points,
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
