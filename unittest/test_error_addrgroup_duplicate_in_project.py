#!/usr/bin/env python3
"""One project declaring the same addressGroup twice still errors.

Qualification narrows the duplicate-declaration check from build-wide to
within-project: two projects may each declare `top`, but one project declaring it
on two router blocks is still an authoring error, because `generateAddressEnums`
would fold both routers' slots into one ID counter and one enum.

Spliced into the composed fixture so the check is exercised where it now has to
discriminate: the build also contains two OTHER projects declaring `top`, which
must not be mistaken for the duplicate.
"""

import sys

from _addrgroup_qual_helpers import (
    CHILD_A_PROJECT_NAME,
    CHILD_A_TOP,
    build_db,
    cleanup,
    copy_fixture,
    edit_fixture_yaml,
)


# A second childA router declaring the same group. Its varType is distinct, so
# the duplicate-group error is unambiguously the one under test.
SECOND_ROUTER = """    childADecode2:
        desc: "second childA router declaring the same address group"
        hasMdl: true
        hasRtl: false
        addressBlock:
            addressGroup: top
            addressIncrement: 0x00001000
            maxAddressSpaces: 8
            varType: addr_id_child_a2
            enumPrefix: ADDR_ID_CHILD_A2_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
"""

REQUIRED_SUBSTRINGS = [
    "addressGroup 'top'",
    "block 'childADecode2'",
    "block 'childADecode'",
    "duplicates a prior addressBlock:",
    f"project '{CHILD_A_PROJECT_NAME}'",
    "within a project",
]


def _run():
    print("within-project duplicate addressGroup in a composed build")
    work = copy_fixture('addrgroup_dup_')
    try:
        edit_fixture_yaml(work, CHILD_A_TOP,
                          "\ninstances:", SECOND_ROUTER + "\ninstances:")
        _db, built = build_db(work)
        if built.returncode == 0:
            print("FAIL: expected the duplicate-declaration error, build "
                  f"succeeded:\n{built.stdout}\n{built.stderr}")
            return False
        combined = built.stdout + built.stderr
        for needle in REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
                return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
