#!/usr/bin/env python3
"""Routed leaf instance sits in a container no router serves.

Diagnostic emitted by `postProcess` in
`config/postParseRegisterPorts.py`. Asserts the diagnostic names the
orphaned leaf instance, its container, and points at a router-style
recovery path.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# Two instances of `leaf`: `uLeafServed` lives in the router's
# container; `uLeafLost` lives in `unservedContainer`, which no router
# serves. Handler synthesis succeeds via the served instance, so the
# per-instance check (line 330 in postParseRegisterPorts.py) is the
# diagnostic under test.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
    unservedContainer:
        desc: "Container with no router under any ancestor"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uIsolated:    { container: top, instanceType: unservedContainer }
    uLeafServed:  { container: top, instanceType: leaf, addressGroup: top }
    uLeafLost:    { container: unservedContainer, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "'uLeafLost'",
    "unservedContainer",
    "not served by any router",
]


def _run():
    print("routed leaf in a container no router serves")
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
