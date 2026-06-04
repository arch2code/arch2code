#!/usr/bin/env python3
"""E3.2: synthesized register-bus bind has incompatible packed fields."""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


NARROW_APB_PREAMBLE = (
    APB_PREAMBLE
    .replace(
        '    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }\n',
        '    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }\n'
        '    narrowDataT: { width: 16, desc: "Narrow leaf-side register data" }\n',
    )
    .replace(
        '    cfgRegSt:\n'
        '        value: { varType: cfgT, generator: register, desc: "Register payload" }\n',
        '    cfgRegSt:\n'
        '        value: { varType: cfgT, generator: register, desc: "Register payload" }\n'
        '    narrowDataSt:\n'
        '        data: { varType: narrowDataT, generator: data }\n',
    )
)


ARCH_YAML = (
    NARROW_APB_PREAMBLE.rstrip()
    + """
    narrowReg:
        desc: "Leaf-side APB register bus with narrower data"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: narrowDataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf', interface='narrowReg')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }
"""
)


REQUIRED_SUBSTRINGS = [
    "cross-interface bind",
    "per-field _bitWidth",
    "field 'data'",
    "_bitWidth 32",
    "_bitWidth 16",
    "uAPBDecode",
    "uLeaf",
]


def _run():
    print("E3.2: register-bus packed-form mismatch")
    db_path, project_path, arch_paths, completed = build_database(
        ARCH_YAML, expect_success=False)
    try:
        combined = completed.stdout + completed.stderr
        for needle in REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        print("PASS: E3.2")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
