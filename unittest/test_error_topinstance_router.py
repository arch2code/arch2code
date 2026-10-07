#!/usr/bin/env python3
"""A decode router cannot be the topInstance's block.

The topInstance's block is the testbench. Nothing contains it, so a router
there has no container to decode for.
`projectCreate._validateTopInstanceBlockNotRouter` in `pysrc/processYaml.py`
rejects it at the topInstance row, before post-parse register decode runs.

The rule holds for every project's top block, including a composed child's
own root row. Cases:

* a router top block holding a leaf, and a bare router top block with no
  leaf (the shape that used to crash in post-parse): rejected;
* the same router, leaf and register inside a plain testbench block:
  accepted;
* a root reusing a composed child's router block as its topInstance:
  rejected;
* a composed child whose own topInstance is a router, under a root with no
  router and under a root with its own router: rejected by this check, not by
  the router-children or primary-router diagnostics a later pass would print.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
    base_dir,
    build_database,
    cleanup,
    render_leaf,
    render_plain_block,
    render_router,
    test_dir,
)


REGISTERS = """
registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Leaf config register" }
"""

REJECT_YAML = (
    APB_PREAMBLE
    + "\nblocks:\n"
    + render_router('tbDec', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:  { container: tbDec, instanceType: tbDec }
    uLeaf: { container: tbDec, instanceType: leaf, addressGroup: top }
"""
    + REGISTERS
)

BARE_ROUTER_YAML = (
    APB_PREAMBLE
    + "\nblocks:\n"
    + render_router('tbDec', 'top')
    + """
instances:
    uTop: { container: tbDec, instanceType: tbDec }
"""
)

ACCEPT_YAML = (
    APB_PREAMBLE
    + "\nblocks:\n"
    + render_plain_block('tb')
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: tb, instanceType: tb }
    uAPBDecode: { container: tb, instanceType: apbDecode }
    uLeaf:      { container: tb, instanceType: leaf, addressGroup: top }
"""
    + REGISTERS
)

def _row_line(yaml_text, row_start):
    """The 1-based line of the instance row the diagnostic points at."""
    return next(n for n, line in enumerate(yaml_text.splitlines(), 1)
                if line.strip().startswith(row_start))

COMMON_REQUIRED = [
    "which declares addressBlock:.",
    "A project's topInstance block is its testbench",
    "Instantiate the router inside the testbench block instead.",
    "Found 1 Error.",
]

REQUIRED_SUBSTRINGS = COMMON_REQUIRED + [
    "topInstance 'uTop' of project 'addrctl_test' has instanceType 'tbDec'",
]

FORBIDDEN_SUBSTRINGS = [
    "Traceback",
    "KeyError",
    "Register-decode router block",
    "No primary router",
]

# Two-project trees. The child's own topInstance may be a router; the root
# composes it with one of the root arch files below.
CHILD_ROUTER_ARCH = (
    APB_PREAMBLE
    + "\nblocks:\n"
    + render_router('childDec', 'top')
    + render_leaf('leaf')
    + """
instances:
    childDec: { container: childDec, instanceType: childDec }
    uLeaf:    { container: childDec, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Leaf config register" }
"""
)

CHILD_ROUTER_ROW_LINE = _row_line(CHILD_ROUTER_ARCH, 'childDec: { container')

PROJECT_TAIL = """
instanceGroups:
    top: { varType: inst_top, enumPrefix: INST_TOP_ }
addressObjects:
    memories: { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }
dirs:
    root: ..
fileGeneration:
    template: none
"""

CHILD_PROJECT = ("yamlFormat: 2\nprojectName: childProj\ntopInstance: childDec\n"
                 "projectFiles:\n    - childArch.yaml\n" + PROJECT_TAIL)

ROOT_PROJECT = ("yamlFormat: 2\nprojectName: rootProj\ntopInstance: root_tb\n"
                "projectFiles:\n    - ../../child/yaml/childProject.yaml\n"
                "    - rootArch.yaml\n" + PROJECT_TAIL)

ROOT_INCLUDE = "include:\n    - ../../child/yaml/childArch.yaml\n"

ROOT_REUSES_CHILD_ROUTER = ROOT_INCLUDE + """
instances:
    root_tb: { container: childDec, instanceType: childDec }
"""

ROOT_NO_ROUTER = ROOT_INCLUDE + "\nblocks:\n" + render_plain_block('root_tb') + """
instances:
    root_tb: { container: root_tb, instanceType: root_tb }
"""

ROOT_OWN_ROUTER = (
    ROOT_INCLUDE + "\nblocks:\n" + render_plain_block('root_tb')
    + render_router('rootDec', 'rtop') + render_leaf('rootLeaf')
    + """
instances:
    root_tb:   { container: root_tb, instanceType: root_tb }
    uRootDec:  { container: root_tb, instanceType: rootDec }
    uRootLeaf: { container: root_tb, instanceType: rootLeaf, addressGroup: rtop }

registers:
    - { register: rootCfg, regType: rw, block: rootLeaf, structure: cfgRegSt, desc: "Root leaf config register" }
"""
)


def _diagnostic_ok(combined, required):
    for needle in required:
        if needle not in combined:
            print(f"FAIL: diagnostic missing substring '{needle}'.\n{combined}")
            return False
    for needle in FORBIDDEN_SUBSTRINGS:
        if needle in combined:
            print(f"FAIL: output contains '{needle}'.\n{combined}")
            return False
    print("PASS")
    return True


def _check_rejected(label, arch_yaml):
    print(label)
    db_path, project_path, arch_paths, completed = build_database(
        arch_yaml, expect_success=False)
    try:
        location = f"{os.path.basename(arch_paths[0])}:{_row_line(arch_yaml, 'uTop:')},"
        return _diagnostic_ok(completed.stdout + completed.stderr,
                              [location] + REQUIRED_SUBSTRINGS)
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _build_composed(root_arch):
    """Build the root of a two-project tree. Returns (returncode, output)."""
    work = tempfile.mkdtemp(prefix='topinst_router_', dir=test_dir)
    try:
        files = {
            ('child', 'childProject.yaml'): CHILD_PROJECT,
            ('child', 'childArch.yaml'): CHILD_ROUTER_ARCH,
            ('root', 'rootProject.yaml'): ROOT_PROJECT,
            ('root', 'rootArch.yaml'): root_arch,
        }
        for (project, name), text in files.items():
            os.makedirs(os.path.join(work, project, 'yaml'), exist_ok=True)
            with open(os.path.join(work, project, 'yaml', name), 'w') as f:
                f.write(text)
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        completed = subprocess.run(
            [sys.executable, os.path.join(base_dir, 'arch2code.py'),
             '--yaml', os.path.join(work, 'root', 'yaml', 'rootProject.yaml'),
             '--db', os.path.join(work, 'root.db')],
            capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
        return completed.returncode, completed.stdout + completed.stderr
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _check_composed_rejected(label, root_arch, required):
    print(label)
    returncode, combined = _build_composed(root_arch)
    if returncode == 0:
        print(f"FAIL: the build was accepted.\n{combined}")
        return False
    return _diagnostic_ok(combined, COMMON_REQUIRED + required)


def _check_accepted():
    print("the same router inside a plain testbench block builds")
    try:
        db_path, project_path, arch_paths = build_database(ACCEPT_YAML)
    except RuntimeError as e:
        print(f"FAIL: {e}")
        return False
    cleanup([project_path, db_path] + arch_paths)
    print("PASS")
    return True


def run_all_tests():
    child_root = [f"childArch.yaml:{CHILD_ROUTER_ROW_LINE},",
                  "topInstance 'childDec' of project 'childProj' has instanceType 'childDec'"]
    results = [
        _check_rejected("a topInstance whose block is a decode router is rejected",
                        REJECT_YAML),
        _check_rejected("a bare router as the top block, with no leaf, is rejected",
                        BARE_ROUTER_YAML),
        _check_accepted(),
        _check_composed_rejected(
            "a root reusing a composed child's router block as its topInstance",
            ROOT_REUSES_CHILD_ROUTER,
            [f"rootArch.yaml:{_row_line(ROOT_REUSES_CHILD_ROUTER, 'root_tb:')},",
             "topInstance 'root_tb' of project 'rootProj' has instanceType 'childDec'"]),
        _check_composed_rejected(
            "a composed child whose topInstance is a router, under a root with "
            "no router", ROOT_NO_ROUTER, child_root),
        _check_composed_rejected(
            "a composed child whose topInstance is a router, under a root with "
            "its own router", ROOT_OWN_ROUTER, child_root),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
