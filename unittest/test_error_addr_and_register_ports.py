#!/usr/bin/env python3
"""Block declares both addressBlock: and registerPorts:.

Asserts that arch2code.py exits non-zero and that stderr names the
offending block and both field names. Diagnostic emitted by
`_post_validateBlockAddressDecl` in `pysrc/processYaml.py`.
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
    bothDecl:
        desc: "Block that illegally declares both addressBlock and registerPorts"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
        registerPorts:
            regs: { interface: apbReg }

instances:
    uTop:      { container: top, instanceType: top }
    uBoth:     { container: top, instanceType: bothDecl }
"""


REQUIRED_SUBSTRINGS = [
    "block 'bothDecl'",
    "declares both",
    "registerPorts:",
    "addressBlock:",
    "mutually exclusive",
]


def _run():
    print("block declares both addressBlock: and registerPorts:")
    result = build_database(ARCH_YAML, expect_success=False)
    db_path, project_path, arch_paths, completed = result
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
