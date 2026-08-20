#!/usr/bin/env python3
"""A self-containing block is rejected before register decode runs.

`projectCreate.validateBlockNotSelfContaining` in `pysrc/processYaml.py` runs
ahead of the post-parse register-decode pass, so a design whose blocks contain
themselves is turned away while the hierarchy is still the only thing wrong
with it. Everything downstream descends that hierarchy, and this suite pins
the ordering: the register-decode pass must never be the one to report a
malformed containment.

The fixture is the placement `_findPrimaryRouter` in
`config/postParseRegisterPorts.py` used to be exercised with. Container block
`scopeA` holds `uRouterA` plus an instance of `scopeB`, while `scopeB` holds
`uRouterB` plus an instance of `scopeA`, so each block sits inside itself one
level down::

    scopeA holds scopeB holds scopeA

Routers are present because they are what would drag the register-decode pass
in: without the containment check it walks up from each router looking for the
one that serves it, finds every router enclosed by another router's scope, and
reports that it cannot infer a dispatch-tree root. That report is the later,
less useful description of the same defect, so this suite also asserts it is
not what comes out.

Which block of the loop is named is not pinned; the walk may enter at either.
"""

import re
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
    uTop:        { container: scopeA, instanceType: scopeA }
    uRouterA:    { container: scopeA, instanceType: routerA }
    uRouterB:    { container: scopeB, instanceType: routerB }
    uScopeBInA:  { container: scopeA, instanceType: scopeB }
    uScopeAInB:  { container: scopeB, instanceType: scopeA }
"""
)

CYCLE_STEM = "contains itself"

# The later diagnostic this one must pre-empt.
DECODE_STEM = "No primary router could be inferred"

# Block keys are context-qualified and the context is a temp filename, so only
# the simple name ahead of the separator is stable.
PATH_TEXT = re.compile(r"contains itself: (.+?)\. A block")
SIMPLE_NAME = re.compile(r"([^/\s]+)/\S*")


def _run():
    print("self-containing blocks rejected ahead of register decode")
    db_path, project_path, arch_paths, completed = build_database(
        ARCH_YAML, expect_success=False)
    try:
        # build_database already refuses a zero exit status here.
        combined = completed.stdout + completed.stderr
        if CYCLE_STEM not in combined:
            print(f"FAIL: no self-containment diagnostic.\n"
                  f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
            return False
        if DECODE_STEM in combined:
            print(f"FAIL: register decode reported the malformed hierarchy "
                  f"instead of the containment check.\n"
                  f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
            return False
        match = PATH_TEXT.search(combined)
        path = SIMPLE_NAME.findall(match.group(1)) if match else None
        if path != ['scopeA', 'scopeB', 'scopeA'] and \
                path != ['scopeB', 'scopeA', 'scopeB']:
            print(f"FAIL: diagnostic does not name the scopeA/scopeB loop "
                  f"(got {path}).\n"
                  f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
