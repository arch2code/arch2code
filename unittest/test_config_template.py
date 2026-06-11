#!/usr/bin/env python3
"""Tests for generated Config struct emission."""

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


def test_config_uses_maxvalue_for_type_width():
    config = load_config_template()
    args = SimpleNamespace(mode='header')
    data = {
        'context': 'wide.yaml',
        'constants': {
            'WIDE_PARAM': {
                'constant': 'WIDE_PARAM',
                'value': 8,
                'maxValue': 0x100000000,
                'valueType': 'uint',
                'isParameterizable': True,
                'evalCanonical': '',
            },
            'NARROW_PARAM': {
                'constant': 'NARROW_PARAM',
                'value': 4,
                'maxValue': 16,
                'valueType': 'uint',
                'isParameterizable': True,
                'evalCanonical': '',
            },
        },
        'contextBlockParamSynthetic': {},
        'contextVariantConfigs': [],
    }

    rendered = config.includeConfig(args, None, data)

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
    config = load_config_template()
    args = SimpleNamespace(mode='header')
    data = {
        'context': 'wide.yaml',
        'constants': {
            'WIDE_PARAM': {
                'constant': 'WIDE_PARAM',
                'value': 8,
                'maxValue': 16,
                'valueType': 'uint',
                'isParameterizable': True,
                'evalCanonical': '',
            },
        },
        'contextBlockParamSynthetic': {},
        'contextVariantConfigs': [],
    }

    rendered = config.includeConfig(args, None, data)
    if '#include "clog2.h"' not in rendered:
        print('FAIL: Config did not include clog2.h when Config structs are emitted')
        print(rendered)
        return False
    print('PASS: Config includes clog2.h unconditionally when Config structs are emitted')
    return True


def run_all_tests():
    tests = [
        test_config_uses_maxvalue_for_type_width,
        test_config_includes_clog2_unconditionally,
    ]
    ok = True
    for test in tests:
        ok = test() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
