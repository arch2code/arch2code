#!/usr/bin/env python3
"""Router block (addressBlock:) also owns a regAccess memory.

Diagnostic emitted by Check 3 in `config/postParseRegisterPorts.py`.

Control case: the same regAccess memory declared on the served leaf
instead of the router must build cleanly.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# regAccessMem on apbDecode, rejected; leaf case below substitutes it.
ARCH_YAML_ROUTER_OWNED = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uLeaf:       { container: top, instanceType: leaf, addressGroup: top }

memories:
    - { memory: regAccessMem, block: apbDecode, structure: apbDataSt, addressStruct: apbAddrSt, wordLines: 16, regAccess: true, desc: "regAccess memory" }
"""
)


# The same memory, declared on the served leaf instead - control case,
# must build cleanly.
ARCH_YAML_LEAF_OWNED = ARCH_YAML_ROUTER_OWNED.replace('block: apbDecode,', 'block: leaf,')


REQUIRED_SUBSTRINGS = [
    "block 'apbDecode'",
    "register-decode router",
    "regAccess memory",
    "regAccessMem",
]


def _run_router_owned_rejected():
    print("router owning a regAccess memory is rejected")
    db_path, project_path, arch_paths, completed = build_database(
        ARCH_YAML_ROUTER_OWNED, expect_success=False)
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


def _run_leaf_owned_passes():
    print("the same memory declared on the served leaf builds cleanly")
    db_path, project_path, arch_paths = build_database(ARCH_YAML_LEAF_OWNED)
    try:
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    ok = _run_router_owned_rejected()
    ok = _run_leaf_owned_passes() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
