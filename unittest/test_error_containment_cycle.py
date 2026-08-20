#!/usr/bin/env python3
"""A block that contains itself, at three depths of the same rule.

Containment must be a tree. A block placed inside itself gives the design no
bottom, and every pass that descends the hierarchy - parameter inheritance,
register decode, port validation - either runs forever or resolves nothing.
`projectCreate.validateBlockNotSelfContaining` in `pysrc/processYaml.py` walks
the containment adjacency and must reject the design.

The rule is one rule at any depth, so the cases here are depths of it rather
than separate features:

* depth one, `selfie` holding an instance of its own type;
* depth three, `cycA` holding `cycB` holding `cycC` holding `cycA`, which a
  check written as a self-containment or immediate-pair test does not see;
* depth three again, but in an island no `topInstance` reaches, because a
  block inside itself is malformed wherever it was authored.

One row is not a containment at all: a composed child project's own root
declaration, which stays literal because only the root project's top row is
rewritten to the `_topInstance` sentinel. A child spells that row either way
round, `uTop:` beside a `top` block or `X: { container: X, instanceType: X }`,
and both compose. Neither spelling is exempt in the ROOT project, whose own root
row has already been rewritten away.

Composing takes more than one project, so those cases run against
`fixtures/self-containment` rather than a single assembled YAML.

None of these blocks parameterizes anything and nothing connects to anything.
The defect is the placement alone, so nothing else has to be present for it to
be reported.

Which member of a loop gets named is deliberately not pinned: the walk enters
from whichever block the adjacency yields first, so every rotation of the loop
is an equally correct report. The assertions compare the set of blocks named
and check the path closes on itself.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import build_database, cleanup


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')
FIXTURE = os.path.join(test_dir, 'fixtures', 'self-containment')


SELF_YAML = """
blocks:
    top:    { desc: "Top container", hasMdl: true }
    selfie: { desc: "Holds an instance of its own type", hasMdl: true }

instances:
    uTop:      { container: top,    instanceType: top }
    uSelfie:   { container: top,    instanceType: selfie }
    uSelfInMe: { container: selfie, instanceType: selfie }
"""

THREE_YAML = """
blocks:
    top:  { desc: "Top container", hasMdl: true }
    cycA: { desc: "Holds cycB", hasMdl: true }
    cycB: { desc: "Holds cycC", hasMdl: true }
    cycC: { desc: "Holds cycA", hasMdl: true }

instances:
    uTop:  { container: top,  instanceType: top }
    uAinT: { container: top,  instanceType: cycA }
    uBinA: { container: cycA, instanceType: cycB }
    uCinB: { container: cycB, instanceType: cycC }
    uAinC: { container: cycC, instanceType: cycA }
"""

# Same loop, but nothing places cycA under the top instance, so the whole
# island sits outside this build's design tree.
ISLAND_YAML = """
blocks:
    top:  { desc: "Top container, reaches none of the loop", hasMdl: true }
    cycA: { desc: "Holds cycB", hasMdl: true }
    cycB: { desc: "Holds cycC", hasMdl: true }
    cycC: { desc: "Holds cycA", hasMdl: true }

instances:
    uTop:  { container: top,  instanceType: top }
    uBinA: { container: cycA, instanceType: cycB }
    uCinB: { container: cycB, instanceType: cycC }
    uAinC: { container: cycC, instanceType: cycA }
"""

# A root declaration's shape, in the root project, where the project's real root
# row is the rewritten `uTop` one. Nothing composes childTop, so this is a block
# authored inside itself.
ROOT_SELF_YAML = """
blocks:
    top:      { desc: "Top container", hasMdl: true }
    childTop: { desc: "Holds an instance of its own type", hasMdl: true }

instances:
    uTop:     { container: top,      instanceType: top }
    childTop: { container: childTop, instanceType: childTop }
"""

CYCLE_STEM = "contains itself"

# Block keys are context-qualified and the context is a temp filename, so only
# the simple name ahead of the separator is stable.
PATH_TEXT = re.compile(r"contains itself: (.+?)\. A block")
SIMPLE_NAME = re.compile(r"([^/\s]+)/\S*")


def _reported_path(combined):
    """The loop the diagnostic printed, as simple block names."""
    match = PATH_TEXT.search(combined)
    if match is None:
        return None
    return SIMPLE_NAME.findall(match.group(1))


def _rotations(loop):
    """Every place the walk could have entered `loop`, as closed paths.

    The reported path always reads container-to-contained, so only the entry
    point is free; the order is not. Reversing it would name a containment
    that does not exist, and that is what tells an author which instance to
    delete.
    """
    return [[loop[(start + step) % len(loop)] for step in range(len(loop))]
            + [loop[start]]
            for start in range(len(loop))]


def _loop_complaint(combined, expected_loop):
    """Why the output failed to name `expected_loop`, or None if it named it."""
    if CYCLE_STEM not in combined:
        return "no self-containment diagnostic"
    path = _reported_path(combined)
    # An author cannot act on "a block contains itself": the message has to
    # say which blocks, and in what order, so the loop can be broken.
    accepted = _rotations(expected_loop)
    if path not in accepted:
        return (f"reported path {path} is not the expected loop "
                f"(any of {accepted})")
    return None


def _check(label, arch_yaml, expected_loop):
    print(label)
    db_path, project_path, arch_paths, completed = build_database(
        arch_yaml, expect_success=False)
    try:
        # build_database already refuses a zero exit status here.
        combined = completed.stdout + completed.stderr
        complaint = _loop_complaint(combined, expected_loop)
        if complaint:
            print(f"FAIL: {complaint}.\nSTDOUT:\n{completed.stdout}\n"
                  f"STDERR:\n{completed.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _build_composition(assembler_project):
    """Build one composition of the multi-project fixture from a temp copy.

    Returns (returncode, stdout + stderr). The copy keeps the generated database
    out of the committed fixture.
    """
    work = tempfile.mkdtemp(prefix='selfcontain_', dir=test_dir)
    try:
        shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        completed = subprocess.run(
            [sys.executable, ARCH2CODE,
             '--yaml', os.path.join(work, 'top', 'yaml', assembler_project),
             '--db', os.path.join(work, 'self-containment.db')],
            capture_output=True, text=True, timeout=180, cwd=base_dir, env=env)
        return completed.returncode, completed.stdout + completed.stderr
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _check_composed_accepted(label, assembler_project):
    print(label)
    returncode, combined = _build_composition(assembler_project)
    if returncode != 0:
        print(f"FAIL: the composition was rejected.\n{combined}")
        return False
    print("PASS")
    return True


def _check_composed(label, assembler_project, expected_loop):
    print(label)
    returncode, combined = _build_composition(assembler_project)
    if returncode == 0:
        print(f"FAIL: the composition was accepted.\n{combined}")
        return False
    complaint = _loop_complaint(combined, expected_loop)
    if complaint:
        print(f"FAIL: {complaint}.\n{combined}")
        return False
    print("PASS")
    return True


def run_all_tests():
    results = [
        _check("depth one: a block holding an instance of its own type",
               SELF_YAML, ['selfie']),
        _check("depth three: cycA holds cycB holds cycC holds cycA",
               THREE_YAML, ['cycA', 'cycB', 'cycC']),
        _check("depth three in an island no topInstance reaches",
               ISLAND_YAML, ['cycA', 'cycB', 'cycC']),
        _check("a root declaration's shape in the root project, whose own root "
               "row is already the rewritten one", ROOT_SELF_YAML,
               ['childTop']),
        _check_composed_accepted(
            "two composed children's own root declarations, one named 'uTop' "
            "beside its block and one named for it", 'acceptProject.yaml'),
        _check_composed(
            "a self-edge in the assembler's own yaml, alongside two accepted "
            "composed root declarations", 'rootSelfProject.yaml', ['rogue']),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
