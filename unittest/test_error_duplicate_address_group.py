#!/usr/bin/env python3
"""E1.4: Two router blocks declare the same addressBlock.addressGroup.

Diagnostic emitted by `_post_registerAddressBlock` in
`pysrc/processYaml.py`. Asserts the diagnostic names both router-block
names and the duplicated group name.
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
    top:
        desc: "Top container"
        hasMdl: true
    sub:
        desc: "Nested container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subDecode', 'top')  # duplicate group 'top'
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub }
    uSubDecode:  { container: sub, instanceType: subDecode }
"""
)


REQUIRED_SUBSTRINGS = [
    "addressGroup 'top'",
    "block 'subDecode'",
    "block 'apbDecode'",
    "duplicates a prior addressBlock:",
]


def _run():
    print("E1.4: duplicate addressGroup across two router blocks")
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
        print("PASS: E1.4")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
