#!/usr/bin/env python3
"""Eval-derived parameterizable constants emit as a module-local
SystemVerilog ``localparam`` whose RHS is translated from the persisted
``evalCanonical`` string, symbolic in the owning module's parameters.

Two functionality-executing checks, no committed database read-back:

1. The template-layer emitter ``emitSvCanonical`` translates canonical eval
   strings to SV RHS text for a stubbed per-symbol spelling. It exercises
   operator pass-through, precedence-driven parenthesization, ``$clog2``,
   authored-base literal re-spelling, and a non-parameter symbol spelled as a
   literal.
2. The real emission path on the ``ip_test`` parity vehicle: ``projectCreate``
   builds a fresh database (the only place evals are parsed/evaluated and the
   canonical string + the ``blockParameterizedDecls`` constant row are
   persisted), ``projectOpen`` + ``getBlockData`` surface the block-local
   declaration set, and ``parameterizedDeclLines`` renders the localparam. The
   RHS must reference the module's ``IP_DATA_WIDTH`` parameter (not a frozen
   literal), and the package must not carry the constant.
"""

import os
import shutil
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate, projectOpen
from templates.systemVerilog import package

IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'arch', 'yaml', 'project.yaml')

IP_BLOCK = 'ip/ip/ip.yaml'
EVAL_CONST_KEY = 'IP_DATA_WIDTH_X2/ip/ip.yaml'
EXPECTED_LOCALPARAM = 'localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;'


def test_emit_sv_canonical_translation():
    print(f"\n{'='*70}\nTest: emitSvCanonical translates canonical eval -> SV RHS"
          f"\n{'='*70}")
    # A stub spelling: A is the owning module's parameter (stays symbolic), C
    # is a non-parameter symbol (spelled from a persisted value as a literal).
    spell = {'A/f': 'IP_DATA_WIDTH', 'B/f': 'B', 'C/f': '5'}
    symSpelling = lambda key: spell[key]
    cases = [
        ('${A/f} * 2', 'IP_DATA_WIDTH * 2'),                  # operator pass-through, symbolic param
        ('(${A/f} + ${B/f}) * 2', '(IP_DATA_WIDTH + B) * 2'),  # precedence restores parens
        ('$clog2(${A/f} + 1)', '$clog2(IP_DATA_WIDTH + 1)'),   # $clog2 pass-through
        ("${A/f} + 8'hff", "IP_DATA_WIDTH + 'hff"),            # authored hex, unsized re-spell
        ("${A/f} & 'b1010", "IP_DATA_WIDTH & 'b1010"),         # authored binary
        ('${A/f} + ${C/f}', 'IP_DATA_WIDTH + 5'),              # non-param symbol -> literal
    ]
    ok = True
    for canonical, expected in cases:
        got = package.emitSvCanonical(canonical, symSpelling)
        if got != expected:
            print(f"  FAIL: {canonical!r} -> {got!r}, expected {expected!r}")
            ok = False
        else:
            print(f"  PASS: {canonical!r} -> {got!r}")
    return ok


def _build_fresh_db():
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    try:
        _reset_project_create_class_state()
        projectCreate(IP_TEST_PROJECT, db_path)
    except BaseException:
        # projectCreate failed (it may sys.exit on YAML errors); drop the
        # partial database so a failing run leaks nothing into the test dir.
        if os.path.exists(db_path):
            os.unlink(db_path)
        raise
    finally:
        os.chdir(original_cwd)
        g.db = None
        g.cur = None
    return db_path


def _build_temp_project(ip_yaml_edit):
    src_dir = os.path.join(base_dir, 'examples', 'ip_test', 'arch', 'yaml')
    temp_root = tempfile.mkdtemp(prefix='eval_sv_emit_', dir=test_dir)
    try:
        dst_dir = os.path.join(temp_root, 'arch', 'yaml')
        shutil.copytree(src_dir, dst_dir)
        ip_yaml = os.path.join(dst_dir, 'ip', 'ip.yaml')
        with open(ip_yaml, 'r', encoding='utf-8') as f:
            text = f.read()
        with open(ip_yaml, 'w', encoding='utf-8') as f:
            f.write(ip_yaml_edit(text))
        return temp_root, os.path.join(dst_dir, 'project.yaml')
    except BaseException:
        # Fixture build failed after mkdtemp; drop the copied tree so a failing
        # run cannot leak an eval_sv_emit_* directory into the unittest dir.
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def _build_fresh_db_from_project(project_yaml):
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    try:
        _reset_project_create_class_state()
        projectCreate(project_yaml, db_path)
    except BaseException:
        # projectCreate failed (it may sys.exit on YAML errors); drop the
        # partial database so a failing run leaks nothing into the test dir.
        if os.path.exists(db_path):
            os.unlink(db_path)
        raise
    finally:
        os.chdir(original_cwd)
        g.db = None
        g.cur = None
    return db_path


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


def test_localparam_emitted_symbolic_per_module():
    print(f"\n{'='*70}\nTest: eval-derived constant emits a module-local "
          f"localparam symbolic in the module parameter\n{'='*70}")
    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)

        # The eval-derived parameterizable constant is selected into the block's
        # module-local declaration set as a 'constant' decl.
        block_data = prj.getBlockData(IP_BLOCK)
        const_decls = [d for d in block_data['parameterizedDecls']
                       if d['declKind'] == 'constant']
        if EVAL_CONST_KEY not in [d['declKey'] for d in const_decls]:
            print(f"  FAIL: block {IP_BLOCK} constant decls "
                  f"{[d['declKey'] for d in const_decls]} did not include {EVAL_CONST_KEY!r}")
            return False

        # Render the module-local declaration lines exactly as the SV module
        # templates do, then locate the eval-derived localparam line.
        params = prj.data['blocks'][IP_BLOCK]['params']
        lines = package.parameterizedDeclLines(
            block_data['parameterizedDecls'], prj, params)
        lines = [ln['line'] for ln in lines]
        localparams = [ln for ln in lines if ln.startswith('localparam IP_DATA_WIDTH_X2')]
        if len(localparams) != 1:
            print(f"  FAIL: expected one IP_DATA_WIDTH_X2 localparam line, got {localparams}")
            return False
        # Ordering: a derived localparam may be referenced by a type width or a
        # struct array size, so it must be declared ahead of the types/structs.
        first_typedef = next((i for i, ln in enumerate(lines) if ln.startswith('typedef')), None)
        localparam_idx = lines.index(localparams[0])
        if first_typedef is not None and localparam_idx > first_typedef:
            print(f"  FAIL: localparam at index {localparam_idx} emitted after the "
                  f"first typedef at index {first_typedef}; localparams must come first")
            return False

        line = localparams[0]
        # RHS must be symbolic in the module parameter, not the frozen literal 140.
        if not line.startswith(EXPECTED_LOCALPARAM):
            print(f"  FAIL: localparam line {line!r} does not start with {EXPECTED_LOCALPARAM!r}")
            return False
        if '140' in line.split('//')[0]:
            print(f"  FAIL: localparam RHS froze the default value instead of staying symbolic: {line!r}")
            return False

        # The constant must NOT be emitted into the package localparams (SV
        # cannot parameterize a package); the package render filters on exactly
        # this isParameterizable flag, so locking it here locks the exclusion.
        if not prj.data['constants'][EVAL_CONST_KEY]['isParameterizable']:
            print(f"  FAIL: {EVAL_CONST_KEY} not isParameterizable, so the package "
                  f"would emit it instead of the module")
            return False

        print(f"  PASS: {line!r} (module-local, package-excluded)")
        return True
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


def test_dependency_closure_orders_derived_constant_chain():
    print(f"\n{'='*70}\nTest: derived constant chain is selected symbolically and ordered"
          f"\n{'='*70}")

    def edit_ip_yaml(text):
        return text.replace(
            "    IP_FIXED_NIBBLE_COUNT:",
            "    IP_DATA_WIDTH_X8:      { eval: \"$IP_DATA_WIDTH_X4 * 2\", desc: \"Derived width, 8x data\" }\n"
            "    IP_FIXED_NIBBLE_COUNT:",
            1)

    temp_root, project_yaml = _build_temp_project(edit_ip_yaml)
    db_path = _build_fresh_db_from_project(project_yaml)
    try:
        prj = projectOpen(db_path)
        block_data = prj.getBlockData(IP_BLOCK)
        lines = package.parameterizedDeclLines(
            block_data['parameterizedDecls'], prj, prj.data['blocks'][IP_BLOCK]['params'])
        lines = [ln['line'] for ln in lines]
        chain = [ln for ln in lines if ln.startswith('localparam IP_DATA_WIDTH_X')]
        expected = [
            'localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;',
            'localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;',
            'localparam IP_DATA_WIDTH_X8 = IP_DATA_WIDTH_X4 * 2;',
        ]
        if [ln.split('//')[0].rstrip() for ln in chain] != expected:
            print(f"  FAIL: localparam chain {chain}, expected prefixes {expected}")
            return False
        print(f"  PASS: {[ln.split('//')[0].rstrip() for ln in chain]}")
        return True
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
        shutil.rmtree(temp_root)


def test_type_using_eval_derived_constant_is_selected():
    print(f"\n{'='*70}\nTest: type using eval-derived constant is selected with closure"
          f"\n{'='*70}")

    db_path = _build_fresh_db()
    try:
        prj = projectOpen(db_path)
        block_data = prj.getBlockData(IP_BLOCK)
        decl_keys = [(d['declKind'], d['declKey']) for d in block_data['parameterizedDecls']]
        expected_type = ('type', 'ipDerivedWidthT/ip/ip.yaml')
        expected_const = ('constant', 'IP_DATA_WIDTH_X4/ip/ip.yaml')
        if expected_const not in decl_keys or expected_type not in decl_keys:
            print(f"  FAIL: missing closure declarations; got {decl_keys}")
            return False
        if decl_keys.index(expected_const) > decl_keys.index(expected_type):
            print(f"  FAIL: {expected_const} appears after {expected_type}: {decl_keys}")
            return False
        lines = package.parameterizedDeclLines(
            block_data['parameterizedDecls'], prj, prj.data['blocks'][IP_BLOCK]['params'])
        lines = [ln['line'] for ln in lines]
        typedef = next((ln for ln in lines if ' ipDerivedWidthT;' in ln), '')
        if "IP_DATA_WIDTH_X4-1:0" not in typedef:
            print(f"  FAIL: derived type line {typedef!r} did not use IP_DATA_WIDTH_X4")
            return False
        print(f"  PASS: {typedef!r}")
        return True
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


def test_struct_array_size_uses_eval_derived_localparam():
    print(f"\n{'='*70}\nTest: struct array size uses eval-derived localparam"
          f"\n{'='*70}")

    def edit_ip_yaml(text):
        return text.replace(
            "    ipRegAddrSt:\n",
            "    ipDerivedArraySt:\n"
            "        derivedSamples: { varType: ipDataT, arraySize: IP_DATA_WIDTH_X4, desc: \"Array sized by an eval-derived localparam\" }\n"
            "    ipRegAddrSt:\n",
            1)

    temp_root, project_yaml = _build_temp_project(edit_ip_yaml)
    db_path = _build_fresh_db_from_project(project_yaml)
    try:
        prj = projectOpen(db_path)
        block_data = prj.getBlockData(IP_BLOCK)
        lines = package.parameterizedDeclLines(
            block_data['parameterizedDecls'], prj, prj.data['blocks'][IP_BLOCK]['params'])
        lines = [ln['line'] for ln in lines]
        sample_line = next((ln for ln in lines if ' derivedSamples;' in ln), '')
        expected = 'ipDataT [IP_DATA_WIDTH_X4-1:0] derivedSamples;'
        if expected not in sample_line:
            print(f"  FAIL: array line {sample_line!r} did not use {expected!r}")
            return False
        if '[280-1:0]' in sample_line:
            print(f"  FAIL: array line froze the resolved value instead of staying symbolic: {sample_line!r}")
            return False
        print(f"  PASS: {sample_line!r}")
        return True
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
        shutil.rmtree(temp_root)


def test_foreign_param_closure_not_selected_for_block():
    print(f"\n{'='*70}\nTest: declarations depending on another block's param are not selected"
          f"\n{'='*70}")

    def edit_ip_yaml(text):
        text = text.replace(
            "        IP_NONCONST_DEPTH: { value: 24, maxValue: 24, desc: \"Per-instance block-param depth (worst-case variant binding = 24)\" }\n",
            "        IP_NONCONST_DEPTH: { value: 24, maxValue: 24, desc: \"Per-instance block-param depth (worst-case variant binding = 24)\" }\n"
            "        OTHER_WIDTH:       { value: 11, maxValue: 32, desc: \"Parameter owned by another block\" }\n",
            1)
        text = text.replace(
            "    IP_FIXED_NIBBLE_COUNT:",
            "    FOREIGN_WIDTH_X2:     { eval: \"$OTHER_WIDTH * 2\", desc: \"Derived from another block parameter\" }\n"
            "    IP_FIXED_NIBBLE_COUNT:",
            1)
        text = text.replace(
            "    ipModeT:\n",
            "    foreignWidthT:\n"
            "        width: FOREIGN_WIDTH_X2\n"
            "        desc: \"Type sized by another block's parameter\"\n"
            "    ipModeT:\n",
            1)
        return text.replace(
            "    ip:\n"
            "        desc: \"Parameterizable IP under test\"\n",
            "    otherParamOwner:\n"
            "        desc: \"Owns OTHER_WIDTH so it is a real module parameter elsewhere\"\n"
            "        params: [OTHER_WIDTH]\n"
            "        hasVl: false\n"
            "        hasMdl: false\n"
            "        hasTb: false\n"
            "        hasRtl: false\n"
            "    ip:\n"
            "        desc: \"Parameterizable IP under test\"\n",
            1)

    temp_root, project_yaml = _build_temp_project(edit_ip_yaml)
    db_path = _build_fresh_db_from_project(project_yaml)
    try:
        prj = projectOpen(db_path)
        block_data = prj.getBlockData(IP_BLOCK)
        decl_keys = {(d['declKind'], d['declKey']) for d in block_data['parameterizedDecls']}
        forbidden = {
            ('constant', 'FOREIGN_WIDTH_X2/ip/ip.yaml'),
            ('type', 'foreignWidthT/ip/ip.yaml'),
        }
        present = sorted(decl_keys & forbidden)
        if present:
            print(f"  FAIL: foreign-param declarations selected for {IP_BLOCK}: {present}")
            return False
        print("  PASS: foreign-param closure stayed out of ip's local declarations")
        return True
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
        shutil.rmtree(temp_root)


def run_all_tests():
    print("\n" + "="*70)
    print("TESTING: SV localparam emission from evalCanonical")
    print("="*70)
    tests = [
        test_emit_sv_canonical_translation,
        test_localparam_emitted_symbolic_per_module,
        test_dependency_closure_orders_derived_constant_chain,
        test_type_using_eval_derived_constant_is_selected,
        test_struct_array_size_uses_eval_derived_localparam,
        test_foreign_param_closure_not_selected_for_block,
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
