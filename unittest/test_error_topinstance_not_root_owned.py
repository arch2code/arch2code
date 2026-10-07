#!/usr/bin/env python3
"""A root project's topInstance must be declared in the root project's own yaml.

Only the root project's own declaration of its topInstance is rewritten to the
`_topInstance` sentinel (`projectCreate._auto_container` in
`pysrc/processYaml.py`), and every design pass descends from that row. A root
project naming an instance that only a composed child's files declare would
otherwise build with no root row, an empty design.
`projectCreate._validateTopInstanceDeclared` rejects that, and any other build
left with no `_topInstance` row.

Cases:

* the root names its child's own root instance, declared only in the child's
  file: rejected, naming that file;
* the root names an instance nobody declares: rejected;
* the root declares its own testbench block holding the child's design:
  accepted;
* the root declares its own topInstance row of the child's testbench block:
  accepted. The child's own root row of that block stays a declaration, not a
  second instance of the top block;
* a child testbench block with an output clock, composed by a root with its
  own testbench block and by a root reusing the child's: accepted. The child's
  own root row binds no output, since the testbench observes it;
* a root reusing the child's testbench block that also places a copy of it
  inside another block: rejected, since that copy is a real containment;
* a definitions-only project with no topInstance: accepted.
"""

import os
import shutil
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

CHILD_PROJECT = """yamlFormat: 2
projectName: childProj

topInstance: childTop_tb

projectFiles:
    - childArch.yaml

dirs:
    root: ..

fileGeneration:
    template: none
"""

CHILD_ARCH = """blocks:
    childTop_tb: { desc: "The child's own testbench container" }
    childDut:    { desc: "The child's design", hasMdl: true }

instances:
    childTop_tb: { container: childTop_tb, instanceType: childTop_tb }
    uChildDut:   { container: childTop_tb, instanceType: childDut }
"""

CHILD_ARCH_OUTPUT_CLOCK = """blocks:
    childTop_tb:
        desc: "The child's own testbench container, supplying a clock"
        clocks:
            clk:  { default: true }
            oclk: { direction: output }
    childDut:    { desc: "The child's design", hasMdl: true }

instances:
    childTop_tb: { container: childTop_tb, instanceType: childTop_tb }
    uChildDut:   { container: childTop_tb, instanceType: childDut }
"""

ROOT_PROJECT = """yamlFormat: 2
projectName: rootProj
{topInstance}
projectFiles:
    - ../../child/yaml/childProject.yaml
    - rootArch.yaml

dirs:
    root: ..

fileGeneration:
    template: none
"""

# Declares nothing of its own beyond the file itself.
ROOT_ARCH_EMPTY = """include:
    - ../../child/yaml/childArch.yaml
"""

ROOT_ARCH_OWN_TB = """include:
    - ../../child/yaml/childArch.yaml

blocks:
    root_tb: { desc: "The root project's own testbench container" }

instances:
    root_tb:   { container: root_tb, instanceType: root_tb }
    uRootDut:  { container: root_tb, instanceType: childDut }
"""

ROOT_ARCH_CHILD_TB_ROW = """include:
    - ../../child/yaml/childArch.yaml

instances:
    root_tb: { container: childTop_tb, instanceType: childTop_tb }
"""

ROOT_ARCH_CHILD_TB_CONTAINED = """include:
    - ../../child/yaml/childArch.yaml

blocks:
    holder: { desc: "Holds a second copy of the top block" }

instances:
    root_tb: { container: childTop_tb, instanceType: childTop_tb }
    uAgain:  { container: holder,      instanceType: childTop_tb }
"""

DEFS_ONLY_ARCH = """constants:
    ROOT_ONLY_CONST: { value: 4, desc: "A shared definition" }
"""

COMMON_REQUIRED = [
    "Project 'rootProj' names topInstance",
    "which must be declared in the root project's own yaml files",
    "Declare the topInstance row",
    "in the yaml of project 'rootProj' (container: its own block). Its block "
    "may be a testbench block from a composed child project.",
    "Found 1 Error.",
]


def _build(root_arch, top_instance, compose_child=True, child_arch=CHILD_ARCH):
    """Build the root project from a temp tree. Returns (returncode, output)."""
    work = tempfile.mkdtemp(prefix='topinst_owned_', dir=test_dir)
    try:
        os.makedirs(os.path.join(work, 'child', 'yaml'))
        os.makedirs(os.path.join(work, 'root', 'yaml'))
        with open(os.path.join(work, 'child', 'yaml', 'childProject.yaml'), 'w') as f:
            f.write(CHILD_PROJECT)
        with open(os.path.join(work, 'child', 'yaml', 'childArch.yaml'), 'w') as f:
            f.write(child_arch)
        project = ROOT_PROJECT.format(
            topInstance=f"\ntopInstance: {top_instance}\n" if top_instance else "")
        if not compose_child:
            project = project.replace("    - ../../child/yaml/childProject.yaml\n", "")
        with open(os.path.join(work, 'root', 'yaml', 'rootProject.yaml'), 'w') as f:
            f.write(project)
        with open(os.path.join(work, 'root', 'yaml', 'rootArch.yaml'), 'w') as f:
            f.write(root_arch)
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        completed = subprocess.run(
            [sys.executable, ARCH2CODE,
             '--yaml', os.path.join(work, 'root', 'yaml', 'rootProject.yaml'),
             '--db', os.path.join(work, 'root.db')],
            capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
        return completed.returncode, completed.stdout + completed.stderr
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _check_rejected(label, root_arch, top_instance, required, common=COMMON_REQUIRED):
    print(label)
    returncode, combined = _build(root_arch, top_instance)
    if returncode == 0:
        print(f"FAIL: the build was accepted.\n{combined}")
        return False
    missing = [s for s in common + required if s not in combined]
    if missing or 'Traceback' in combined:
        print(f"FAIL: diagnostic missing {missing} or crashed.\n{combined}")
        return False
    print("PASS")
    return True


def _check_accepted(label, root_arch, top_instance, compose_child=True,
                    child_arch=CHILD_ARCH):
    print(label)
    returncode, combined = _build(root_arch, top_instance, compose_child, child_arch)
    if returncode != 0:
        print(f"FAIL: the build was rejected.\n{combined}")
        return False
    print("PASS")
    return True


def run_all_tests():
    results = [
        _check_rejected(
            "the root names its child's own root instance, declared only in "
            "the child's file", ROOT_ARCH_EMPTY, 'childTop_tb',
            ["'childTop_tb'",
             "is declared only in ",
             "childArch.yaml:",
             "a file of project 'childProj'"]),
        _check_rejected(
            "the root names an instance nobody declares", ROOT_ARCH_EMPTY,
            'noSuchTop', ["'noSuchTop'", "is declared in none of them"]),
        _check_accepted(
            "the root declares its own testbench block holding the child's "
            "design", ROOT_ARCH_OWN_TB, 'root_tb'),
        _check_accepted(
            "the root declares its own topInstance row of the child's testbench "
            "block", ROOT_ARCH_CHILD_TB_ROW, 'root_tb'),
        _check_accepted(
            "a child testbench block with an output clock, under the root's "
            "own testbench block", ROOT_ARCH_OWN_TB, 'root_tb',
            child_arch=CHILD_ARCH_OUTPUT_CLOCK),
        _check_accepted(
            "a child testbench block with an output clock, reused as the "
            "root's topInstance block", ROOT_ARCH_CHILD_TB_ROW, 'root_tb',
            child_arch=CHILD_ARCH_OUTPUT_CLOCK),
        _check_rejected(
            "a root reusing the child's testbench block that places another "
            "copy of it inside a block", ROOT_ARCH_CHILD_TB_CONTAINED, 'root_tb',
            ["instance 'uAgain' in container 'holder' has instanceType "
             "'childTop_tb', the block of topInstance 'root_tb'",
             "Found 1 Error."], common=[]),
        _check_accepted(
            "a definitions-only project with no topInstance", DEFS_ONLY_ARCH,
            None, compose_child=False),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
