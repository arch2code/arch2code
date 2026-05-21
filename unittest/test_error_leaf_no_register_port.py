#!/usr/bin/env python3
"""E2.6: Routed leaf block has registers / memories but no registerPorts: row.

Diagnostic emitted by `_selectLeafRegisterPort` in
`config/postParseRegisterPorts.py`. Asserts the diagnostic names the
offending leaf block and points at the missing registerPorts:
declaration.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_router,
)


# `regsButNoPort` owns a register but declares no registerPorts: row.
# In a new-schema project this is fatal at handler-synthesis time.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + """    regsButNoPort:
        desc: "Block owning a register but missing registerPorts:"
        hasMdl: true

instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uOrphan:     { container: top, instanceType: regsButNoPort, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: regsButNoPort, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "Routed leaf block 'regsButNoPort'",
    "registerPorts:",
    "no registerPorts: entry",
]


def _run():
    print("E2.6: leaf has registers but no registerPorts: declaration")
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
        print("PASS: E2.6")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
