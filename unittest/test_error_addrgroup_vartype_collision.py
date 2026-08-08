#!/usr/bin/env python3
"""Two address groups resolving one firmware enum identity must error.

Group NAMES are project-qualified; the emitted firmware enum is not. Firmware
lives in one flat namespace (`fw_ns`) shared by every context and firmware headers
include each other across project boundaries, so two groups sharing a `varType:`
either collide as a C++ redefinition or, in separate translation units, bind the
same enumerator to a different address ID - a wrong address, with no diagnostic
required. The same applies to a shared `enumPrefix:`.

Narrowing the duplicate-group check without this gate would trade a loud
database-time error for a possibly silent one, so both are asserted here.
"""

import sys

from _addrgroup_qual_helpers import (
    CHILD_B_TOP,
    build_db,
    cleanup,
    copy_fixture,
    edit_fixture_yaml,
)


CASES = [
    ("varType", "varType: addr_id_child_b", "varType: addr_id_child_a",
     ["varType: 'addr_id_child_a'"]),
    ("enumPrefix", "enumPrefix: ADDR_ID_CHILD_B_", "enumPrefix: ADDR_ID_CHILD_A_",
     ["enumPrefix: 'ADDR_ID_CHILD_A_'"]),
]

# Both colliding groups are named, in project::group spelling, with their
# declaring block and file.
COMMON_SUBSTRINGS = [
    "childAProj::top",
    "childBProj::top",
    "block 'childADecode'",
    "block 'childBDecode'",
]


def _case(label, old, new, extraSubstrings):
    print(f"two projects' address groups sharing one {label}")
    work = copy_fixture(f'addrgroup_{label}_')
    try:
        edit_fixture_yaml(work, CHILD_B_TOP, old, new)
        _db, built = build_db(work)
        if built.returncode == 0:
            print(f"FAIL: expected the {label} collision gate to fire, build "
                  f"succeeded:\n{built.stdout}\n{built.stderr}")
            return False
        combined = built.stdout + built.stderr
        for needle in COMMON_SUBSTRINGS + extraSubstrings:
            if needle not in combined:
                print(f"FAIL: {label} diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
                return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    ok = True
    for (label, old, new, extraSubstrings) in CASES:
        if not _case(label, old, new, extraSubstrings):
            ok = False
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
