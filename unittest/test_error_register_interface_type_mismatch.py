#!/usr/bin/env python3
"""Synthesized register-bus bind crosses interfaceType values."""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


ALT_APB_DEF = """interface_defs:
    alt_apb:
        addressBus: true
        parameters:
            addr_t: { datatype: struct, default: 'bit' }
            data_t: { datatype: struct, default: 'bit' }
        signals:
            paddr: addr_t
            pwdata: data_t
            pready: bool
            prdata: data_t
        modports:
            src:
                inputs: ['pready', 'prdata']
                outputs: ['paddr', 'pwdata']
            dst:
                inputs: ['paddr', 'pwdata']
                outputs: ['pready', 'prdata']
        sc_channel:
            type: 'apb'
            multicycle_types: []

"""


ARCH_YAML = (
    ALT_APB_DEF
    + APB_PREAMBLE
    + """
    altBus:
        desc: "Router-side address bus with a different meta-protocol"
        interfaceType: alt_apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top', upstream_port='altBus')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }
"""
)


REQUIRED_SUBSTRINGS = [
    "cross-interface bind",
    "same interface meta-protocol",
    "alt_apb",
    "apb",
    "protocol changer",
    "uAPBDecode",
    "uLeaf",
]


def _run():
    print("register-bus interfaceType mismatch")
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
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
