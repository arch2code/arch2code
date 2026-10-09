#!/usr/bin/env python3
"""A router whose addressGroup: holds no register-bus consumer is rejected.

An instance that carries the router's addressGroup: but has no registers,
regAccess memories or registerPorts: takes an address slot the router never
connects to. When every instance in the group is like that, the decoder has
nothing to dispatch to, and make db rejects it.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_plain_block,
    render_router,
)


GROUP_WITHOUT_CONSUMER = (
    APB_PREAMBLE
    + """
blocks:
"""
    + render_plain_block('top')
    + render_plain_block('cpu')
    + render_plain_block('plain')
    + render_router('apbDecode', 'top')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uPlain:     { container: top, instanceType: plain, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }
"""
)


def run_group_without_consumer():
    print("a router whose group holds only register-less instances is rejected")
    try:
        db_path, project_path, arch_paths, completed = build_database(
            GROUP_WITHOUT_CONSUMER, expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        for needle in [
            "Router 'uAPBDecode' (block 'apbDecode') serves addressGroup 'top'",
            "uPlain (block 'plain')",
            "registerPorts:",
            "remove the addressBlock: from block 'apbDecode'",
        ]:
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
    return 0 if run_group_without_consumer() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
