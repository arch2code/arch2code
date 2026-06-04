#!/usr/bin/env python3
"""E2.2: Two instances exist for the same router block.

Diagnostic emitted by `_resolveRouterInstances` in
`config/postParseRegisterPorts.py`. Asserts the diagnostic names both
instance keys and the router block.

Topology (must be rejected)::

    uTop (top)
    +-- uAPBDecode  (instanceType=apbDecode) <--+
    +-- uSub (sub)                              |  Same router block
        +-- uAPBDecode2 (instanceType=apbDecode)<+  instantiated twice.

    Multi-instance routers are deferred; the post-parse pass must
    reject the project before any downstream emission and the
    diagnostic must name both instance keys plus the router block.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_router,
)


# `apbDecode` declares `addressBlock:` once but is instantiated twice
# (uAPBDecode in 'top', uAPBDecode2 in 'sub'). Multi-instance routers are
# deferred per the parent plan; the post-parse pass must reject the
# project before any downstream emission.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    sub:
        desc: "Sibling container holding the duplicate router instance"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uSub:         { container: top, instanceType: sub }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uAPBDecode2:  { container: sub, instanceType: apbDecode }
"""
)


REQUIRED_SUBSTRINGS = [
    "Router block 'apbDecode'",
    "multiple",
    "uAPBDecode",
    "uAPBDecode2",
    "Multi-instance",
]


def _run():
    print("E2.2: two instances of the same router block")
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
        print("PASS: E2.2")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
