#!/usr/bin/env python3
"""E2.3: Zero primary-router candidates.

Diagnostic emitted by `_findPrimaryRouter` in
`config/postParseRegisterPorts.py`. Asserts the diagnostic lists every
router instance and identifies the missing-root condition.

The fixture constructs a deliberately cyclic placement: container block
`scopeA` holds `uRouterA` plus an instance of `scopeB`, while
`scopeB` holds `uRouterB` plus an instance of `scopeA`. Each router's
upward walk lands in the other router's served container, so neither
qualifies as the dispatch-tree root and the post-parse pass must
diagnose the missing primary.

Topology (must be rejected — cyclic placement)::

    uTop (instanceType=scopeA)
    +-- uRouterA (routerA, served scope = scopeA)
    +-- uScopeBInA (instanceType=scopeB)
        +-- uRouterB (routerB, served scope = scopeB)
        +-- uScopeAInB (instanceType=scopeA)
            +-- (scopeA holds routerA + a scopeB ... cycle)

    scopeA contains scopeB; scopeB contains scopeA. Walking up from
    uRouterA lands inside uRouterB's served scope, and walking up
    from uRouterB lands inside uRouterA's served scope. Neither
    router can be the dispatch-tree root, so the diagnostic must
    list every router instance + block name.
"""

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
    scopeA:
        desc: "Container A — holds routerA plus a scopeB instance"
        hasMdl: true
    scopeB:
        desc: "Container B — holds routerB plus a scopeA instance"
        hasMdl: true
"""
    + render_router('routerA', 'groupA')
    + render_router('routerB', 'groupB')
    + """
instances:
    uTop:        { container: scopeA, instanceType: scopeA }
    uRouterA:    { container: scopeA, instanceType: routerA }
    uRouterB:    { container: scopeB, instanceType: routerB }
    uScopeBInA:  { container: scopeA, instanceType: scopeB }
    uScopeAInB:  { container: scopeB, instanceType: scopeA }
"""
)


REQUIRED_SUBSTRINGS = [
    "No primary router could be inferred",
    "uRouterA",
    "uRouterB",
    "routerA",
    "routerB",
]


def _run():
    print("E2.3: zero primary-router candidates")
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
        print("PASS: E2.3")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
