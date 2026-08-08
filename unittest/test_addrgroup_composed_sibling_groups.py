#!/usr/bin/env python3
"""Acceptance proof for `addressGroup` project qualification.

Three independently authored projects in ONE composed build - the root plus two
sibling child IPs - each declare an address group named `top`. Before the
registry was keyed on (owning projectName, group name) this composition could not
reach a database at all: the duplicate-declaration error fired on the second
project to declare `top`.

The proof is a generator run, not a column read. For each project it builds the
composed database, scaffolds and generates that project's firmware header, and
asserts the header carries that project's own address enum with its own address
IDs restarting at 0. Independent ID counters are what a shared registry could not
produce: one counter would have numbered the six routed slots 0..5 across the
three projects.
"""

import os
import sys

from _addrgroup_qual_helpers import (
    CHILD_A_PROJECT_NAME,
    CHILD_B_PROJECT_NAME,
    ROOT_PROJECT_NAME,
    build_db,
    cleanup,
    copy_fixture,
    db_for_project,
    generate,
    instance_address_rows,
    newmodule,
)


# Per project: the firmware header its router's context owns, the enum type it
# declares, and the routed-slot enum members in address-ID order.
PROJECT_ENUMS = [
    (ROOT_PROJECT_NAME,
     os.path.join('root', 'fw', 'include', 'rootTopIncludesFW.h'),
     'addr_id_root',
     ['ADDR_ID_ROOT_UCHILDA=0', 'ADDR_ID_ROOT_UCHILDB=1']),
    (CHILD_A_PROJECT_NAME,
     os.path.join('childA', 'fw', 'include', 'childATopIncludesFW.h'),
     'addr_id_child_a',
     ['ADDR_ID_CHILD_A_UCHILDALEAFX=0', 'ADDR_ID_CHILD_A_UCHILDALEAFY=1']),
    (CHILD_B_PROJECT_NAME,
     os.path.join('childB', 'fw', 'include', 'childBTopIncludesFW.h'),
     'addr_id_child_b',
     ['ADDR_ID_CHILD_B_UCHILDBLEAFX=0', 'ADDR_ID_CHILD_B_UCHILDBLEAFY=1']),
]

# Every routed slot in the build, with the address ID its own project's counter
# must allocate. Two slots per project, so a shared counter shows up immediately.
EXPECTED_IDS = {
    ('rootTop.yaml', 'uChildA'): 0,
    ('rootTop.yaml', 'uChildB'): 1,
    ('../../childA/yaml/childATop.yaml', 'uChildALeafX'): 0,
    ('../../childA/yaml/childATop.yaml', 'uChildALeafY'): 1,
    ('../../childB/yaml/childBTop.yaml', 'uChildBLeafX'): 0,
    ('../../childB/yaml/childBTop.yaml', 'uChildBLeafY'): 1,
}


def _fail(msg):
    print(f"FAIL: {msg}")
    return False


def _run():
    print("composed build: three projects each declaring addressGroup 'top'")
    work = copy_fixture('addrgroup_qual_')
    try:
        db, built = build_db(work)
        if built.returncode != 0:
            return _fail("composed database build failed; two projects naming "
                         f"one address group must compose:\n"
                         f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")

        # Independent per-project ID counters.
        rows = instance_address_rows(db)
        if set(rows) != set(EXPECTED_IDS):
            return _fail(f"routed-slot set mismatch: {sorted(rows)}")
        for key, expectedID in EXPECTED_IDS.items():
            (group, addressID) = rows[key]
            if group != 'top':
                return _fail(f"{key} expected group 'top', got {group!r}")
            if addressID != expectedID:
                return _fail(
                    f"{key} expected addressID {expectedID}, got {addressID!r}; "
                    f"a shared counter would number all six slots 0..5")

        # Each project emits its own enum, with its own IDs, into its own header.
        headers = dict()
        for (projectName, relPath, enumType, members) in PROJECT_ENUMS:
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
            if f"enum  {enumType} " not in text:
                return _fail(f"{relPath} is missing 'enum {enumType}':\n{text}")
            for member in members:
                if member not in text:
                    return _fail(
                        f"{relPath} is missing enum member '{member}'; the "
                        f"project's address IDs must restart at 0:\n{text}")
            headers[enumType] = text

        # The three enum identities stay distinct: group names are qualified, the
        # emitted firmware enum names are not.
        for (_projectName, relPath, enumType, _members) in PROJECT_ENUMS:
            for (otherType, otherText) in headers.items():
                if otherType == enumType:
                    continue
                if f"enum  {enumType} " in otherText:
                    return _fail(f"enum {enumType} also emitted into the "
                                 f"{otherType} header ({relPath})")

        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
