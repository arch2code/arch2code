#!/usr/bin/env python3
"""A router whose slot count or slot spacing is not a power of two misroutes.

The RTL decoder masks the address with addressIncrement x maxAddressSpaces - 1,
and the model decoder shifts it right by addressIncrement.bit_length() - 1.
With 24 address spaces the RTL aliases slots 8-15 onto 0-7, and with a 0x3000
increment the model decodes slot 2 as slot 3. projectCreate rejects both,
naming the block, group, field and value and suggesting the next power of two.
A power-of-two router still builds.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


def _arch_yaml(address_increment, max_address_spaces):
    return (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
        + render_router('apbDecode', 'top',
                        address_increment=address_increment,
                        max_address_spaces=max_address_spaces)
        + render_leaf('leaf')
        + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
    )


def _expect_rejected(label, address_increment, max_address_spaces, needles):
    print(label)
    try:
        db_path, project_path, arch_paths, completed = build_database(
            _arch_yaml(address_increment, max_address_spaces),
            expect_success=False)
    except RuntimeError as err:
        print(f"FAIL: expected a power-of-two rejection.\n{err}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        for needle in needles:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
                return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _expect_accepted():
    print("power-of-two addressBlock accepted")
    db_path, project_path, arch_paths = build_database(
        _arch_yaml('0x1000', 32))
    cleanup([project_path, db_path] + arch_paths)
    print("PASS")
    return True


def run_all_tests():
    common = ["addressBlock: of block 'apbDecode'", "(addressGroup 'top')",
              "which is not a power of two"]
    results = [
        _expect_rejected("maxAddressSpaces 24 rejected", '0x1000', 24,
                         common + ["sets maxAddressSpaces 24", "Use 32."]),
        _expect_rejected("addressIncrement 0x3000 rejected", '0x3000', 16,
                         common + ["sets addressIncrement 0x3000", "Use 0x4000."]),
        _expect_accepted(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
