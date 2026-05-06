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


def load_includes_template():
    path = os.path.join(base_dir, 'templates', 'systemc', 'includes.py')
    spec = importlib.util.spec_from_file_location('systemc_includes_template', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_config_uses_maxvalue_for_type_width():
    includes = load_includes_template()
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
            },
            'NARROW_PARAM': {
                'constant': 'NARROW_PARAM',
                'value': 4,
                'maxValue': 16,
                'valueType': 'uint',
                'isParameterizable': True,
            },
        },
    }

    rendered = includes.includeConfig(args, None, data)

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


def run_all_tests():
    return 0 if test_config_uses_maxvalue_for_type_width() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
