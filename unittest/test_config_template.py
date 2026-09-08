#!/usr/bin/env python3
"""Config struct emission through `configModule`, one module per declaring
project and block, driven through a minimal stand-in for the `prj` view it
calls back into. The context-mode `includeConfig` path must emit nothing."""

import importlib.util
import os
import sys
from types import SimpleNamespace


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)


def load_config_template():
    path = os.path.join(base_dir, 'templates', 'systemc', 'config.py')
    spec = importlib.util.spec_from_file_location('systemc_config_template', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render_config_module(config, constants, descriptors):
    """Render one Config module for a fixed descriptor set, mirroring the real
    (args, prj, data) call shape: `prj.getConfigModuleData` supplies the
    descriptors, `prj.data['constants']` backs each member's type/value."""
    args = SimpleNamespace(template='config')
    prj = SimpleNamespace(
        data={'constants': constants},
        getConfigModuleData=lambda qualBlock, parent: {'descriptors': descriptors})
    data = {'qualBlock': 'blk/blk.yaml', 'parent': 'blk'}
    return config.render(args, prj, data)


def test_config_uses_maxvalue_for_type_width():
    constants = {
        'WIDE_PARAM/wide.yaml': {
            'constant': 'WIDE_PARAM', 'value': 8, 'maxValue': 0x100000000,
            'valueType': 'uint', 'isParameterizable': True, 'evalCanonical': '',
        },
        'NARROW_PARAM/wide.yaml': {
            'constant': 'NARROW_PARAM', 'value': 4, 'maxValue': 16,
            'valueType': 'uint', 'isParameterizable': True, 'evalCanonical': '',
        },
    }
    descriptor = {
        'declaringProject': 'proj', 'block': 'blk', 'variant': '',
        'structName': 'projBlkTestConfig', 'containerSourced': {},
        'values': {'WIDE_PARAM': 8, 'NARROW_PARAM': 4},
        'paramSourceKeys': {'WIDE_PARAM': 'WIDE_PARAM/wide.yaml',
                            'NARROW_PARAM': 'NARROW_PARAM/wide.yaml'},
    }
    config = load_config_template()
    rendered = _render_config_module(config, constants, [descriptor])

    if 'static constexpr uint64_t WIDE_PARAM = 8;' not in rendered:
        print('FAIL: WIDE_PARAM was not emitted as uint64_t')
        print(rendered)
        return False
    if 'static constexpr uint32_t NARROW_PARAM = 4;' not in rendered:
        print('FAIL: NARROW_PARAM was not emitted as uint32_t')
        print(rendered)
        return False
    print('PASS: Config field types use maxValue for width selection')
    return True


def test_config_includes_clog2_unconditionally():
    constants = {
        'WIDE_PARAM/wide.yaml': {
            'constant': 'WIDE_PARAM', 'value': 8, 'maxValue': 16,
            'valueType': 'uint', 'isParameterizable': True, 'evalCanonical': '',
        },
    }
    descriptor = {
        'declaringProject': 'proj', 'block': 'blk', 'variant': '',
        'structName': 'projBlkTestConfig', 'containerSourced': {},
        'values': {'WIDE_PARAM': 8},
        'paramSourceKeys': {'WIDE_PARAM': 'WIDE_PARAM/wide.yaml'},
    }
    config = load_config_template()
    rendered = _render_config_module(config, constants, [descriptor])
    if '#include "clog2.h"' not in rendered:
        print('FAIL: Config did not include clog2.h when Config structs are emitted')
        print(rendered)
        return False
    print('PASS: Config includes clog2.h unconditionally when Config structs are emitted')
    return True


def test_context_header_emits_nothing():
    """The context-mode path (no `parent` in data) emits nothing; Configs live
    in the registrar-domain module."""
    config = load_config_template()
    args = SimpleNamespace(template='config')
    data = {'context': 'wide.yaml'}
    rendered = config.render(args, None, data)
    if rendered != '':
        print(f'FAIL: context-mode Config header rendered {rendered!r}, expected empty')
        return False
    print('PASS: context-mode Config header renders empty')
    return True


def run_all_tests():
    tests = [
        test_config_uses_maxvalue_for_type_width,
        test_config_includes_clog2_unconditionally,
        test_context_header_emits_nothing,
    ]
    ok = True
    for test in tests:
        ok = test() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
