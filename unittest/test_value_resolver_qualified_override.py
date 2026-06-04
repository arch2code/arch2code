#!/usr/bin/env python3
"""ValueResolver keeps variant overrides scoped to their qualified key."""

import sys
import os


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.valueResolver import ValueResolver


class FakeProject:
    def __init__(self):
        self.data = {
            'constants': {
                'owner.yaml': {
                    'WIDTH': {
                        'value': 16,
                        'isParameterizable': False,
                        'maxValue': 0,
                        '_context': 'owner.yaml',
                    },
                    'DEPTH': {
                        'value': 2,
                        'isParameterizable': True,
                        'maxValue': 4,
                        '_context': 'owner.yaml',
                    },
                },
                'foreign.yaml': {
                    'WIDTH': {
                        'value': 8,
                        'isParameterizable': False,
                        'maxValue': 0,
                        '_context': 'foreign.yaml',
                    },
                    'DEPTH': {
                        'value': 5,
                        'isParameterizable': True,
                        'maxValue': 8,
                        '_context': 'foreign.yaml',
                    },
                },
            },
            'structures': {
                'owner.yaml': {
                    'inner_st': {
                        '_context': 'owner.yaml',
                        'vars': {
                            'low': {
                                '_context': 'owner.yaml',
                                'entryType': 'NamedVar',
                                'arraySizeKey': '',
                                'arraySize': 0,
                                'varTypeKey': '',
                                'bitwidth': 8,
                            },
                            'high': {
                                '_context': 'owner.yaml',
                                'entryType': 'NamedVar',
                                'arraySizeKey': '',
                                'arraySize': 0,
                                'varTypeKey': '',
                                'bitwidth': 8,
                            },
                        },
                    },
                    'array_st': {
                        '_context': 'owner.yaml',
                        'vars': {
                            'payload': {
                                '_context': 'owner.yaml',
                                'entryType': 'NamedVar',
                                'arraySizeKey': 'DEPTH/owner.yaml',
                                'arraySize': 'DEPTH',
                                'varTypeKey': '',
                                'bitwidth': 4,
                            },
                        },
                    },
                    'outer_st': {
                        '_context': 'owner.yaml',
                        'vars': {
                            'payload': {
                                '_context': 'owner.yaml',
                                'entryType': 'NamedStruct',
                                'arraySizeKey': '',
                                'arraySize': 0,
                                'subStructKey': 'inner_st/owner.yaml',
                            },
                        },
                    },
                },
            },
        }
        self.enums = {
            'owner.yaml': {
                'OWNER_MODE': {'value': 2, 'type': 'mode_t'},
            },
        }
        self.qualEnums = {
            'OWNER_MODE/owner.yaml': {'value': 2, 'type': 'mode_t'},
        }
        self.flatData = {
            'constants': {
                'WIDTH/owner.yaml': self.data['constants']['owner.yaml']['WIDTH'],
                'DEPTH/owner.yaml': self.data['constants']['owner.yaml']['DEPTH'],
                'WIDTH/foreign.yaml': self.data['constants']['foreign.yaml']['WIDTH'],
                'DEPTH/foreign.yaml': self.data['constants']['foreign.yaml']['DEPTH'],
            },
            'structures': {
                'inner_st/owner.yaml': self.data['structures']['owner.yaml']['inner_st'],
                'array_st/owner.yaml': self.data['structures']['owner.yaml']['array_st'],
                'outer_st/owner.yaml': self.data['structures']['owner.yaml']['outer_st'],
            },
        }
        self.yamlContext = {
            'owner.yaml': {
                'owner.yaml': None,
                'foreign.yaml': None,
            },
            'foreign.yaml': {
                'foreign.yaml': None,
            },
        }


def _run():
    print("ValueResolver: qualified override scope")
    resolver = ValueResolver(
        FakeProject(),
        values={
            'WIDTH': 32,
            'WIDTH/owner.yaml': 32,
            'DEPTH/owner.yaml': 3,
        },
        context='owner.yaml',
    )
    checks = [
        ("bare override", resolver.value('WIDTH'), 32),
        ("owner qualified override", resolver.value('WIDTH/owner.yaml'), 32),
        ("foreign qualified constant", resolver.value('WIDTH/foreign.yaml'), 8),
        ("owner qualified enum", resolver.value('OWNER_MODE/owner.yaml'), 2),
        (
            "qualified arraySize max ignores active override",
            resolver.arraySize(
                resolver.project.data['structures']['owner.yaml']
                ['array_st']['vars']['payload'],
                use_max=True),
            4,
        ),
        (
            "nested packed fields",
            resolver.structPackedFields('outer_st/owner.yaml'),
            [('payload.low', 8, 0), ('payload.high', 8, 8)],
        ),
        (
            "qualified arraySize override in packed fields",
            resolver.structPackedFields('array_st/owner.yaml'),
            [('payload', 12, 0)],
        ),
    ]
    for label, actual, expected in checks:
        if actual != expected:
            print(f"FAIL: {label}: expected {expected}, got {actual}")
            return False
    print("PASS: ValueResolver qualified override scope")
    return True


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
