#!/usr/bin/env python3
"""Router block (addressBlock:) also owns registers.

Diagnostic emitted by Check 4 in `config/postParseRegisterPorts.py`.

Control case: the same register declared on the served leaf instead of
the router must build cleanly.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# cfgR on apbDecode, rejected; leaf case below substitutes it.
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

registers:
    - { register: cfgR, regType: rw, block: apbDecode, structure: apbDataSt, desc: "router-owned register" }
"""
)


# The same register, declared on the served leaf instead - control case,
# must build cleanly.
ARCH_YAML_LEAF_OWNED = ARCH_YAML_ROUTER_OWNED.replace('block: apbDecode,', 'block: leaf,')


REQUIRED_SUBSTRINGS = [
    "block 'apbDecode' is a register-decode router (addressBlock:) but also "
    "owns register 'cfgR'. A router owns no firmware-accessible registers; "
    "declare them on a leaf the router serves.",
]

# The router-with-children rejection would otherwise name the synthesised
# handler instance, which the author never wrote.
ABSENT_SUBSTRING = "u_apbDecode_regs"


def _run_router_owned_rejected():
    print("router owning a register is rejected")
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
        if ABSENT_SUBSTRING in combined:
            print(
                f"FAIL: diagnostic names '{ABSENT_SUBSTRING}', an instance the "
                f"author never wrote.\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _run_leaf_owned_passes():
    print("the same register declared on the served leaf builds cleanly")
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
