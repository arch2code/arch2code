#!/usr/bin/env python3
"""Generated decoder channel map is scoped to the router's own project.

Companion to `test_addrgroup_composed_sibling_groups.py`, which proves the
firmware enum side. This suite covers the *generated decoder*: the SystemC
constructor emits one channel slot per instance the router dispatches to, and the
instance set comes from the router's address group.

Three projects in the composed fixture each declare a group named `top`, so a
router selecting its channels by the bare group name folds every project's routed
instances into one decoder - emitting channel pointers for ports that do not
exist on that router, and duplicating slot indices because each project allocates
`addressID` from 0. The assertion here is that childAProj's router receives
exactly childAProj's two leaves, childBProj's exactly childBProj's two, each in
its own contiguous slot order.

The proof is a generator run: the router's block module is scaffolded and
generated, and the emitted channel list is read back out of the file.
"""

import os
import sys

from _addrgroup_qual_helpers import (
    CHILD_A_PROJECT_NAME,
    CHILD_B_PROJECT_NAME,
    build_db,
    cleanup,
    copy_fixture,
    db_for_project,
    generate,
    newmodule,
)


# Per project: the router block module it owns, and the channel entries the
# decoder must hold, in address-slot order. The root router is excluded: its
# container declares no registerPorts and no parent dispatches to it, so the
# dispatch-tree root has no upstream feed to name in the decoder construction.
PROJECT_DECODERS = [
    (CHILD_A_PROJECT_NAME,
     os.path.join('childA', 'model', 'childADecode.cppm'),
     ['&apbReg_uChildALeafX', '&apbReg_uChildALeafY']),
    (CHILD_B_PROJECT_NAME,
     os.path.join('childB', 'model', 'childBDecode.cppm'),
     ['&apbReg_uChildBLeafX', '&apbReg_uChildBLeafY']),
]


def _fail(msg):
    print(f"FAIL: {msg}")
    return False


def _decoder_channels(text):
    """Return the channel entries of the emitted `,decoder(...)` initialiser, in
    the order emitted, or None when no decoder was emitted."""
    lines = text.splitlines()
    start = None
    for (index, line) in enumerate(lines):
        if ',decoder(' in line:
            start = index
            break
    if start is None:
        return None
    channels = list()
    for line in lines[start + 1:]:
        entry = line.strip()
        last = entry.endswith('})')
        entry = entry.rstrip('})').rstrip(',').strip()
        if entry:
            channels.append(entry)
        if last:
            return channels
    return None


def _run():
    print("composed build: per-project decoder channel maps")
    work = copy_fixture('addrgroup_chan_')
    try:
        db, built = build_db(work)
        if built.returncode != 0:
            return _fail("composed database build failed:\n"
                         f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")

        for (projectName, relPath, expected) in PROJECT_DECODERS:
            projectDb = db_for_project(work, db, projectName)
            made = newmodule(projectDb)
            if made.returncode != 0:
                return _fail(f"--newmodule under {projectName} failed:\n"
                             f"{made.stdout}\n{made.stderr}")
            path = os.path.join(work, relPath)
            if not os.path.exists(path):
                return _fail(f"{projectName} did not scaffold {relPath}")
            gen = generate(projectDb, path)
            if gen.returncode != 0:
                return _fail(f"generating {relPath} under {projectName} "
                             f"failed:\n{gen.stdout}\n{gen.stderr}")
            with open(path) as f:
                text = f.read()
            channels = _decoder_channels(text)
            if channels is None:
                return _fail(f"{relPath} emitted no decoder initialiser:\n{text}")
            if channels != expected:
                return _fail(
                    f"{relPath} decoder channels expected {expected}, got "
                    f"{channels}; a router must dispatch only the instances in "
                    f"the address group its own project declares, so channels "
                    f"naming another project's instances mean the group name was "
                    f"matched unqualified")

        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
