#!/usr/bin/env python3
"""projectOpen._sampleConfigConstants returns only root parameters: the
context's own parameterizable base constants plus any a structure reaches
through an included file. Eval-derived constants are excluded, so a sample
Config struct has literal members only."""

import os
import sys
from types import SimpleNamespace

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


ROOT = 'DATA_WIDTH/../shared/yaml/types.yaml'
LOCAL_ROOT = 'MAX_GAIN/blk.yaml'
DERIVED = 'MAX_DATA_VALUE/blk.yaml'
PLAIN = 'FIXED_WIDTH/blk.yaml'


def _constants():
    return {
        ROOT: {'constant': 'DATA_WIDTH', 'value': 8, 'maxValue': 16,
               'isParameterizable': True, 'evalCanonical': ''},
        LOCAL_ROOT: {'constant': 'MAX_GAIN', 'value': 4, 'maxValue': 8,
                     'isParameterizable': True, 'evalCanonical': ''},
        DERIVED: {'constant': 'MAX_DATA_VALUE', 'value': 255, 'maxValue': 65535,
                  'isParameterizable': True,
                  'evalCanonical': '(1 << ${' + ROOT + '}) - 1'},
        PLAIN: {'constant': 'FIXED_WIDTH', 'value': 3, 'maxValue': 3,
                'isParameterizable': False, 'evalCanonical': ''},
    }


def test_members_are_root_parameters_only():
    constants = _constants()
    prj = SimpleNamespace(data={'constants': constants},
                          structureParamDeps={'data_st/blk.yaml': [ROOT]})
    # Declaring-file order: derived first, then the local root, then a plain
    # constant. The shared root arrives only through the structure deps.
    own = {DERIVED: constants[DERIVED], LOCAL_ROOT: constants[LOCAL_ROOT], PLAIN: constants[PLAIN]}
    got = list(projectOpen._sampleConfigConstants(prj, own, ['data_st/blk.yaml']))
    expected = [LOCAL_ROOT, ROOT]
    if got != expected:
        print(f'FAIL: members {got} != {expected}')
        return False
    print('PASS: derived and non-parameterizable constants are excluded, struct-dep roots included')
    return True


def test_struct_dep_already_own_is_not_duplicated():
    constants = _constants()
    prj = SimpleNamespace(data={'constants': constants},
                          structureParamDeps={'data_st/blk.yaml': [ROOT]})
    own = {ROOT: constants[ROOT], LOCAL_ROOT: constants[LOCAL_ROOT]}
    got = list(projectOpen._sampleConfigConstants(prj, own, ['data_st/blk.yaml']))
    expected = [ROOT, LOCAL_ROOT]
    if got != expected:
        print(f'FAIL: members {got} != {expected}')
        return False
    print('PASS: own-file order is kept and a struct dep already present is not repeated')
    return True


def run_all_tests():
    ok = True
    for test in (test_members_are_root_parameters_only,
                 test_struct_dep_already_own_is_not_duplicated):
        ok = test() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
