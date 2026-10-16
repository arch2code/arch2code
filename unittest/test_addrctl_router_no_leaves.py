#!/usr/bin/env python3
"""Router declared but no leaves under it.

A router with `addressBlock:` declared and no instance carrying its
addressGroup: has no channel to dispatch to. make db rejects it.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_plain_block,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_plain_block('inert')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uInert:      { container: top, instanceType: inert }
"""
)


def _run():
    print("router with no leaves to dispatch to")
    try:
        db_path, project_path, arch_paths, completed = build_database(
            ARCH_YAML, expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        needle = (
            "Router 'uAPBDecode' (block 'apbDecode') serves addressGroup "
            "'top', but no instance in this build's design tree carries "
            "addressGroup: top, so the router has nothing to dispatch to. "
            "Set addressGroup: top on an instance in container 'top' that "
            "has registers, a regAccess memory or a registerPorts: entry, or "
            "remove the addressBlock: from block 'apbDecode'."
        )
        if needle not in combined:
            print(f"FAIL: diagnostic missing substring '{needle}'.\n"
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
