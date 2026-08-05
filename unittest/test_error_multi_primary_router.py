#!/usr/bin/env python3
"""More than one primary-router candidate.

Diagnostic emitted by `_findPrimaryRouter` in
`config/postParseRegisterPorts.py`. Asserts the diagnostic names every
candidate router instance.

Topology (must be rejected)::

    uTop (top)
    +-- uSubA (subA)
    |   +-- uRouterA (routerA, addressGroup=groupA) <- primary candidate
    |   +-- uLeafA   (leafA,   addressGroup=groupA)
    +-- uSubB (subB)
        +-- uRouterB (routerB, addressGroup=groupB) <- primary candidate
        +-- uLeafB   (leafB,   addressGroup=groupB)

    Two routers sit at sibling subtrees and neither is nested inside
    the other's served scope, so both qualify as primary. The
    diagnostic must list every candidate router instance plus its
    block name.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# Two routers sit at the same hierarchy level under `top`. Neither is
# nested inside the other's served scope, so both qualify as primary.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container hosting two sibling subtrees"
        hasMdl: true
    subA:
        desc: "First subtree container"
        hasMdl: true
    subB:
        desc: "Second subtree container"
        hasMdl: true
"""
    + render_router('routerA', 'groupA')
    + render_router('routerB', 'groupB')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:      { container: top, instanceType: top }
    uSubA:     { container: top, instanceType: subA }
    uSubB:     { container: top, instanceType: subB }
    uRouterA:  { container: subA, instanceType: routerA }
    uRouterB:  { container: subB, instanceType: routerB }
    uLeafA:    { container: subA, instanceType: leafA, addressGroup: groupA }
    uLeafB:    { container: subB, instanceType: leafB, addressGroup: groupB }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "Multiple candidate primary routers",
    "uRouterA",
    "uRouterB",
    "routerA",
    "routerB",
]


def _run():
    print("more than one primary-router candidate")
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
