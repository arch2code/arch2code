#!/usr/bin/env python3
"""Register-owning leaf has no instance served by a router.

Diagnostic emitted by `postProcess` in
`config/postParseRegisterPorts.py` while synthesising register handlers.
This proves a register-owning leaf that lacks a resolved leaf-to-handler
connectionMap is rejected during projectCreate rather than reaching
`projectOpen._registerBusInterfacePort()`.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# The design has a valid router in `top`, so the new-schema post-parse
# pass is active. The only `leaf` instance is inside `unservedContainer`,
# whose container is not served by any router, so handler synthesis cannot
# resolve the leaf's register-bus source.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container carrying an unrelated router"
        hasMdl: true
    unservedContainer:
        desc: "Container with no local router"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uIsolated:  { container: top, instanceType: unservedContainer }
    uLeafLost:  { container: unservedContainer, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "Leaf block 'leaf' needs a register handler",
    "no router was found serving any of its instances",
    "Place the leaf in a router's container",
]


def _run():
    print("register-owning leaf has no serving router")
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
