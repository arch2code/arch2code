#!/usr/bin/env python3
"""registerPorts: row points at an interface whose interfaceType
is not addressBus: true.

Diagnostic emitted by `_post_validateRegisterPortInterface` in
`pysrc/processYaml.py`. Asserts the diagnostic names the offending
port, interface, and the not-addressBus interfaceType.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
)


# push_ack interface_def is not addressBus: true. A registerPorts: row
# pointing at it must be rejected.
ARCH_YAML = (
    APB_PREAMBLE.rstrip()
    + """
    badIf:
        desc: "Non-addressBus interface used illegally as a register-bus"
        interfaceType: push_ack
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    badLeaf:
        desc: "Routed leaf with a non-addressBus registerPorts: row"
        hasMdl: true
        registerPorts:
            regs: { interface: badIf }

instances:
    uTop:      { container: top, instanceType: top }
    uBadLeaf:  { container: top, instanceType: badLeaf }
"""
)


REQUIRED_SUBSTRINGS = [
    "registerPorts",
    "'regs'",
    "'badIf'",
    "push_ack",
    "addressBus: true",
]


def _run():
    print("registerPorts row references non-addressBus interface")
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
