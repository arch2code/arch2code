#!/usr/bin/env python3
"""E1.2: Leaf declares more than one registerPorts: row.

Diagnostic emitted by `_post_validateBlockAddressDecl` in
`pysrc/processYaml.py`. Asserts the diagnostic names the offending
block and both register-port names.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
)


ARCH_YAML = APB_PREAMBLE + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    multiReg:
        desc: "Block illegally declaring two registerPorts: rows"
        hasMdl: true
        registerPorts:
            regsA: { interface: apbReg }
            regsB: { interface: apbReg }

instances:
    uTop:    { container: top, instanceType: top }
    uMulti:  { container: top, instanceType: multiReg }
"""


REQUIRED_SUBSTRINGS = [
    "block 'multiReg'",
    "declares multiple",
    "registerPorts:",
    "regsA",
    "regsB",
    "exactly",
]


def _run():
    print("E1.2: leaf declares multiple registerPorts: rows")
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
        print("PASS: E1.2")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
