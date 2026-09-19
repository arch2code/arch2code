#!/usr/bin/env python3
"""A router-less container hosts two register consumers at once.

Diagnostic emitted by `postProcess` in `config/postParseRegisterPorts.py`.
A router-less container may pass the register bus through to exactly one
consumer; holding two makes the passthrough ambiguous and is rejected
regardless of whether the container itself is ever reached by a router.
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
        desc: "Top container (carries the primary router)"
        hasMdl: true
    unservedContainer:
        desc: "Router-less container holding two register consumers"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uIsolated:    { container: top, instanceType: unservedContainer }
    uLeafLost1:   { container: unservedContainer, instanceType: leaf }
    uLeafLost2:   { container: unservedContainer, instanceType: leaf }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "'unservedContainer'",
    "uLeafLost1",
    "uLeafLost2",
    "exactly one such",
]


def _run():
    print("router-less container hosts two register consumers")
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
