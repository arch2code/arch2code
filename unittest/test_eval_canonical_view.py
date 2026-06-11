#!/usr/bin/env python3
"""Stage E3 - persisted canonical eval string reaches generators through
``projectOpen`` views with no parse or numeric evaluation at open/template
time.

This executes the real pipeline on the ``ip_test`` parity vehicle rather than
reading a committed database:

1. ``projectCreate`` builds a fresh database from the ``ip_test`` project YAML.
   This is the only place eval expressions are parsed and evaluated; it
   persists ``unparse(node)`` into ``constants.evalCanonical``.
2. ``projectOpen`` loads that database and ``getContextData`` assembles the
   context view the cppConfig / svConfig / docConfig generators consume.

The test asserts the canonical string is surfaced verbatim for an eval
constant and is the empty string for a non-eval constant, and locks the
"no open-time evaluation" contract by replacing ``evalExpr.parse`` and
``evalExpr.evaluate`` with traps before opening: if either fires during
``projectOpen`` or ``getContextData`` the test fails.
"""

import os
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
import pysrc.evalExpr as evalExpr
from pysrc.processYaml import projectCreate, projectOpen
from pysrc.systemcGen import genSystemC

IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'arch', 'yaml', 'project.yaml')

# An eval constant and a non-eval constant from ip.yaml. The canonical form
# carries fully qualified ${name/context} symbols, so it is context
# independent and needs no re-scoping on reload.
EVAL_CONST = 'IP_DATA_WIDTH_X2/ip.yaml'
EVAL_CANONICAL = '${IP_DATA_WIDTH/ip.yaml} * 2'
EVAL_VALUE = 140
NON_EVAL_CONST = 'IP_FIXED_NIBBLE_COUNT/ip.yaml'


def _build_fresh_db():
    """Run projectCreate on the ip_test project into a throwaway database.

    projectCreate chdirs to the project directory and closes its own write
    connection, so restore cwd and drop the global handles afterwards.
    """
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    original_cwd = os.getcwd()
    try:
        projectCreate(IP_TEST_PROJECT, db_path)
    finally:
        os.chdir(original_cwd)
    g.db = None
    g.cur = None
    return db_path


def test_canonical_reaches_context_view_without_evaluation():
    print(f"\n{'='*70}\nTest: evalCanonical reaches getContextData with no "
          f"open-time parse/evaluate\n{'='*70}")
    db_path = _build_fresh_db()

    # Trap the create-time facilities: neither may run during open/view.
    saved_parse = evalExpr.parse
    saved_evaluate = evalExpr.evaluate

    def _trap_parse(*args, **kwargs):
        raise AssertionError("evalExpr.parse called at open/view time")

    def _trap_evaluate(*args, **kwargs):
        raise AssertionError("evalExpr.evaluate called at open/view time")

    evalExpr.parse = _trap_parse
    evalExpr.evaluate = _trap_evaluate
    try:
        prj = projectOpen(db_path)
        data = prj.getContextData(['ip'], genSystemC.dataTypeMappings)
        constants = data['constants']

        eval_row = constants[EVAL_CONST]
        if eval_row['evalCanonical'] != EVAL_CANONICAL:
            print(f"  FAIL: {EVAL_CONST} canonical {eval_row['evalCanonical']!r}, "
                  f"expected {EVAL_CANONICAL!r}")
            return False
        # The numeric result is already persisted; the view exposes it
        # without re-evaluating the expression.
        if eval_row['value'] != EVAL_VALUE:
            print(f"  FAIL: {EVAL_CONST} value {eval_row['value']}, "
                  f"expected {EVAL_VALUE}")
            return False

        non_eval_row = constants[NON_EVAL_CONST]
        if non_eval_row['evalCanonical'] != '':
            print(f"  FAIL: non-eval {NON_EVAL_CONST} canonical "
                  f"{non_eval_row['evalCanonical']!r}, expected ''")
            return False

        print(f"  PASS: {EVAL_CONST} canonical={EVAL_CANONICAL!r} value={EVAL_VALUE}, "
              f"non-eval canonical='' , no parse/evaluate at open")
        return True
    except AssertionError as exc:
        print(f"  FAIL: {exc}")
        return False
    finally:
        evalExpr.parse = saved_parse
        evalExpr.evaluate = saved_evaluate
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
    print("TESTING: Stage E3 - canonical eval string surfaced via projectOpen")
    print("="*70)
    tests = [
        test_canonical_reaches_context_view_without_evaluation,
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
