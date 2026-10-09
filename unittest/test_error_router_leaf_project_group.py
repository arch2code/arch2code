#!/usr/bin/env python3
"""A leaf's addressGroup: must name the group of the project owning its router.

A group reference resolves in the project owning the file that declares the
instance. A root-owned file that places a leaf inside childA's container, where
childA's router dispatches to it, names the root's group 'top', not childA's,
even though both groups are spelled 'top'. childA's router allocates the leaf
no decode slot, and make db rejects it. The same leaf with no addressGroup:
gets the same advice, since no group it could carry resolves in childA.
Following either half of the advice makes make db pass.
"""

import sys

from _addrgroup_qual_helpers import (
    CHILD_A_PROJECT_NAME,
    CHILD_A_TOP,
    ROOT_PROJECT_NAME,
    ROOT_TOP,
    build_db,
    cleanup,
    copy_fixture,
    edit_fixture_yaml,
)


ANCHOR = ("    uChildB:      { container: rootTop, instanceType: childBTop,  "
          "instGroup: top, addressGroup: top }\n")
EXTRA_LEAF = ("    uRootLeaf:    { container: childATop, instanceType: childALeafX, "
              "instGroup: top, addressGroup: top }\n")
EXTRA_ROOT_LEAF = ("    uRootLeaf:    { container: rootTop, "
                   "instanceType: childALeafX, instGroup: top, "
                   "addressGroup: top }\n")
CHILD_A_ANCHOR = ("    uChildALeafY:  { container: childATop, "
                  "instanceType: childALeafY,  instGroup: top, "
                  "addressGroup: top }\n")
EXTRA_LEAF_WITHOUT_GROUP = ("    uRootLeaf:    { container: childATop, "
                            "instanceType: childALeafX, instGroup: top }\n")


def run_leaf_with_group_of_another_project():
    print("a leaf declared in the root's file inside childA's container is "
          "rejected")
    work = copy_fixture('addrgroup_leafproj_')
    try:
        edit_fixture_yaml(work, ROOT_TOP, ANCHOR, ANCHOR + EXTRA_LEAF)
        _db, built = build_db(work)
        if built.returncode == 0:
            print("FAIL: expected the leaf addressGroup project error, build "
                  f"succeeded:\n{built.stdout}\n{built.stderr}")
            return False
        combined = built.stdout + built.stderr
        for needle in [
            "Instance 'uRootLeaf' (block 'childALeafX') has a register bus, "
            "and router 'uChildADecode' (block 'childADecode') in container "
            "'childATop' dispatches to it",
            f"Its addressGroup: top resolves in project "
            f"'{ROOT_PROJECT_NAME}', but the router serves group top of "
            f"project '{CHILD_A_PROJECT_NAME}'. Declare instance 'uRootLeaf', "
            f"with addressGroup: top, in a file project "
            f"'{CHILD_A_PROJECT_NAME}' owns, or move it into a container that "
            f"a router of project '{ROOT_PROJECT_NAME}' serves and set "
            f"addressGroup: to that router's group.",
        ]:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
                return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_leaf_without_group_from_another_project():
    print("a leaf with no addressGroup: declared in the root's file inside "
          "childA's container gets the cross-project advice")
    work = copy_fixture('addrgroup_leafproj_nogroup_')
    try:
        edit_fixture_yaml(work, ROOT_TOP, ANCHOR,
                          ANCHOR + EXTRA_LEAF_WITHOUT_GROUP)
        _db, built = build_db(work)
        if built.returncode == 0:
            print("FAIL: expected the leaf addressGroup project error, build "
                  f"succeeded:\n{built.stdout}\n{built.stderr}")
            return False
        combined = built.stdout + built.stderr
        for needle in [
            "Instance 'uRootLeaf' (block 'childALeafX') has a register bus, "
            "and router 'uChildADecode' (block 'childADecode') in container "
            "'childATop' dispatches to it. Any addressGroup: set on it "
            f"resolves in project '{ROOT_PROJECT_NAME}', but the router "
            f"serves group top of project '{CHILD_A_PROJECT_NAME}'. Declare "
            f"instance 'uRootLeaf', with addressGroup: top, in a file project "
            f"'{CHILD_A_PROJECT_NAME}' owns, or move it into a container that "
            f"a router of project '{ROOT_PROJECT_NAME}' serves and set "
            f"addressGroup: to that router's group.",
        ]:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
                return False
        if "Set addressGroup:" in combined:
            print("FAIL: diagnostic advises setting addressGroup:.\n"
                  f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_advice_moves_leaf_into_router_project():
    print("the leaf declared with addressGroup: top in childA's file, as the "
          "diagnostic advises, builds")
    work = copy_fixture('addrgroup_leafproj_fixed_')
    try:
        edit_fixture_yaml(work, CHILD_A_TOP, CHILD_A_ANCHOR,
                          CHILD_A_ANCHOR + EXTRA_LEAF)
        _db, built = build_db(work)
        if built.returncode != 0:
            print("FAIL: following the advice still fails make db:\n"
                  f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_advice_moves_leaf_into_root_container():
    print("the leaf moved into a container the root's router serves, as the "
          "diagnostic advises, builds")
    work = copy_fixture('addrgroup_leafproj_rootctr_')
    try:
        edit_fixture_yaml(work, ROOT_TOP, ANCHOR, ANCHOR + EXTRA_ROOT_LEAF)
        _db, built = build_db(work)
        if built.returncode != 0:
            print("FAIL: following the advice still fails make db:\n"
                  f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    results = [
        run_leaf_with_group_of_another_project(),
        run_leaf_without_group_from_another_project(),
        run_advice_moves_leaf_into_router_project(),
        run_advice_moves_leaf_into_root_container(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
