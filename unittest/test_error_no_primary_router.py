#!/usr/bin/env python3
"""A cyclic router placement is rejected as a containment cycle.

Every router being contained by another router's served scope (zero
primary-router candidates for `_findPrimaryRouter` in
`config/postParseRegisterPorts.py`) needs the router containers to
contain each other, which is a containment cycle. projectCreate rejects
the cycle before post-parse router inference runs, naming the cycle as
a path at the instance row that closes it.

Topology (must be rejected - cyclic placement)::

    uTop (instanceType=tb)
    +-- uScopeA (instanceType=scopeA)
        +-- uRouterA (routerA, served scope = scopeA)
        +-- uScopeBInA (instanceType=scopeB)
            +-- uRouterB (routerB, served scope = scopeB)
            +-- uScopeAInB (instanceType=scopeA)
                +-- (scopeA holds routerA + a scopeB ... cycle)

    scopeA contains scopeB; scopeB contains scopeA.
"""

import os
import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    tb:
        desc: "Top block - holds the scopeA instance the cycle hangs from"
        hasMdl: true
    scopeA:
        desc: "Container A - holds routerA plus a scopeB instance"
        hasMdl: true
    scopeB:
        desc: "Container B - holds routerB plus a scopeA instance"
        hasMdl: true
"""
    + render_router('routerA', 'groupA')
    + render_router('routerB', 'groupB')
    + """
instances:
    uTop:        { container: tb,     instanceType: tb }
    uScopeA:     { container: tb,     instanceType: scopeA }
    uRouterA:    { container: scopeA, instanceType: routerA }
    uRouterB:    { container: scopeB, instanceType: routerB }
    uScopeBInA:  { container: scopeA, instanceType: scopeB }
    uScopeAInB:  { container: scopeB, instanceType: scopeA }
"""
)


# The line of the instance row that closes the cycle.
CLOSING_LINE = next(
    n for n, line in enumerate(ARCH_YAML.splitlines(), 1) if 'uScopeAInB:' in line)

REQUIRED_SUBSTRINGS = [
    "block 'scopeA' contains 'uScopeBInA' (scopeB), which contains "
    "'uScopeAInB' (scopeA). A block cannot contain itself, directly or "
    "through the blocks it contains.",
    "Found 1 Error.",
]

FORBIDDEN_SUBSTRINGS = [
    "Traceback",
    "No primary router could be inferred",
]


def _run():
    print("cyclic router placement rejected as a containment cycle")
    db_path, project_path, arch_paths, completed = build_database(
        ARCH_YAML, expect_success=False)
    try:
        combined = completed.stdout + completed.stderr
        # The diagnostic location of the closing row: its file, then the line.
        location = f"{os.path.basename(arch_paths[0])}:{CLOSING_LINE},"
        for needle in [location] + REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle in combined:
                print(
                    f"FAIL: output contains '{needle}'.\n"
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
