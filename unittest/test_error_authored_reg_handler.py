#!/usr/bin/env python3
"""A block authors `isRegHandler: true`.

Diagnostic emitted by `postProcess` in `config/postParseRegisterPorts.py`
before it synthesises any register handler. Asserts the diagnostic names
the block and the field.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


# `leaf` owns a register and is served by `apbDecode`, so the pass would
# synthesise `leaf_regs`; `handWritten` authors isRegHandler itself.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    handWritten:
        desc: "Block that authors isRegHandler"
        hasMdl: true
        isRegHandler: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uLeaf:        { container: top, instanceType: leaf, addressGroup: top }
    uHandWritten: { container: top, instanceType: handWritten }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


# No addressBlock: router, so the check runs before postProcess() returns
# for a project with nothing to route.
ROUTERLESS_ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    handWritten:
        desc: "Block that authors isRegHandler"
        hasMdl: true
        isRegHandler: true

instances:
    uTop:         { container: top, instanceType: top }
    uHandWritten: { container: top, instanceType: handWritten }
"""
)


REQUIRED_SUBSTRINGS = [
    "block 'handWritten' sets isRegHandler: true",
    "remove isRegHandler from block 'handWritten'",
]


def _run(label, arch_yaml):
    print(label)
    db_path, project_path, arch_paths, completed = build_database(
        arch_yaml, expect_success=False)
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
    results = [
        _run("block that authors isRegHandler is rejected", ARCH_YAML),
        _run("block that authors isRegHandler is rejected in a project with "
             "no router", ROUTERLESS_ARCH_YAML),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
