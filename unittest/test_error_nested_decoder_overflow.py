#!/usr/bin/env python3
"""A nested router's routed footprint escapes its parent's per-child window.

Diagnostic emitted by the nested-decoder containment check in
`calcAddresses` (`pysrc/processYaml.py`). The primary router allocates a
1 MiB (0x100000) window per slot; the nested router in the `uSub` slot
routes a 16 MiB (0x1000000) footprint (addressIncrement 0x100000 x
maxAddressSpaces 16), which does not fit. Asserts the build fails and the
diagnostic names the nested router block plus both spans.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary router container"
        hasMdl: true
    sub:
        desc: "Nested router container"
        hasMdl: true
"""
    # Parent per-child window = addressIncrement 0x100000 x addressMultiples 1
    # = 1 MiB. Nested footprint = 0x100000 x 16 = 16 MiB > 1 MiB -> overflow.
    + render_router('apbDecode', 'top', address_increment='0x00100000')
    + render_router('subDecode', 'sub', address_increment='0x00100000',
                    max_address_spaces=16)
    + render_leaf('topLeaf')
    + render_leaf('subLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub, addressGroup: top }
    uSubDecode:  { container: sub, instanceType: subDecode }
    uTopLeaf:    { container: top, instanceType: topLeaf, addressGroup: top }
    uSubLeaf:    { container: sub, instanceType: subLeaf, addressGroup: sub }

registers:
    - { register: cfgT, regType: rw, block: topLeaf, structure: cfgRegSt, desc: "" }
    - { register: cfgS, regType: rw, block: subLeaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "Nested register decoder 'subDecode'",
    "group 'addrctl_test::sub'",   # project-qualified AddressGroups key
    "0x1000000",   # routed footprint (16 MiB)
    "0x100000",    # parent per-child window (1 MiB)
    "apbDecode",   # parent decoder named
]


def _run():
    print("nested router footprint exceeds parent per-child window")
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
