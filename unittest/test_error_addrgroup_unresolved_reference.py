#!/usr/bin/env python3
"""An addressGroup: reference its own project does not declare must error.

Resolution does not fall outward to ancestor projects: a group reference resolves
only within the project owning the referring file. An IP naming a group it does
not declare has hard-coded a name owned by someone else, which is exactly the
reuse property qualification exists to establish.

The fixture renames the ROOT's own group declaration while leaving the root's
routed slots referencing `top`. The two child projects (parsed earlier, since
files are processed in include-dependency order) do declare `top`, so the
diagnostic must name them - that list is what makes the error actionable in a
composed build.

That list is an observation, not a census: reference resolution is parse-time and
the group registry fills as each file is parsed, so a project whose declaration
lives in a later-processed file is not registered yet. The second case drives the
name that exists nowhere and asserts the diagnostic offers NO list at all rather
than claiming a build-wide absence it cannot know.
"""

import sys

from _addrgroup_qual_helpers import (
    ROOT_PROJECT_NAME,
    ROOT_TOP,
    build_db,
    cleanup,
    copy_fixture,
    edit_fixture_yaml,
)


REQUIRED_SUBSTRINGS = [
    "uChildA",                        # the referring row
    "address group 'top'",            # the unresolved reference
    "rootTop.yaml",                   # the referring file
    f"project '{ROOT_PROJECT_NAME}'",  # its owning project
    "childAProj",                     # projects that DO declare 'top'
    "childBProj",
]

NOWHERE_REQUIRED_SUBSTRINGS = [
    "uChildA",
    "address group 'nowhereBus'",
    "rootTop.yaml",
    f"project '{ROOT_PROJECT_NAME}'",
]

# The declared-projects clause is only offered when the registry actually holds a
# declaration of that name; with none seen the diagnostic must stay silent about
# which projects declare it.
NOWHERE_FORBIDDEN_SUBSTRING = "parsed so far in this build"


def _declared_by_later_parsed_project():
    print("addressGroup: reference not declared by the referring file's project")
    work = copy_fixture('addrgroup_unres_')
    try:
        # Rename the root router's own declaration (anchored on the
        # addressBlock: key so the edit cannot land on a prose mention of the
        # field); the routed slots below keep referencing 'top'.
        edit_fixture_yaml(work, ROOT_TOP,
                          "        addressBlock:\n            addressGroup: top",
                          "        addressBlock:\n            addressGroup: rootBus")
        _db, built = build_db(work)
        if built.returncode == 0:
            print("FAIL: expected the unresolved-reference error, build "
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


def _declared_nowhere():
    print("addressGroup: reference to a group name no project declares")
    work = copy_fixture('addrgroup_nowhere_')
    try:
        edit_fixture_yaml(
            work, ROOT_TOP,
            "instanceType: childATop,  instGroup: top, addressGroup: top }",
            "instanceType: childATop,  instGroup: top, addressGroup: nowhereBus }")
        _db, built = build_db(work)
        if built.returncode == 0:
            print("FAIL: expected the unresolved-reference error, build "
                  f"succeeded:\n{built.stdout}\n{built.stderr}")
            return False
        combined = built.stdout + built.stderr
        for needle in NOWHERE_REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
                return False
        if NOWHERE_FORBIDDEN_SUBSTRING in combined:
            print(f"FAIL: diagnostic offered a declared-projects clause for a "
                  f"name no project declares.\n"
                  f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    results = [_declared_by_later_parsed_project(), _declared_nowhere()]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
