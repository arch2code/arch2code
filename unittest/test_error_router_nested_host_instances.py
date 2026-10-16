#!/usr/bin/env python3
"""A block that hosts a nested router may have one instance.

Each instance of the host block carries its own copy of the nested router, but
a router has one instance. A second host instance gets no dispatch from the
parent router, or a decode slot with no connection behind it, so its nested
decoder is never fed. make db rejects it, with or without an addressGroup: on
the second instance.

A composed child project whose top block hosts a nested router keeps its own
topInstance row in the database. That row declares the child's root, so the
parent's single instance of the block is still one instance.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)
import _addrgroup_qual_helpers as composed


def mid_twice(second_group_field):
    return (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    mid:
        desc: "Container of the nested router"
        hasMdl: true
"""
        + render_router('apbDecode', 'top')
        + render_router('midDecode', 'mid', address_increment='0x00100000')
        + render_leaf('leafB')
        + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uMid:       {{ container: top, instanceType: mid, addressGroup: top }}
    uMidDecode: {{ container: mid, instanceType: midDecode }}
    uLeafB:     {{ container: mid, instanceType: leafB, addressGroup: mid }}
    uMid2:      {{ container: top, instanceType: mid{second_group_field} }}
"""
    )


NEEDLE = ("Block 'mid' hosts nested router 'uMidDecode' (block 'midDecode') "
          "and has 2 instances: 'uMid', 'uMid2'.")


def _expect_diagnostic(label, arch_yaml):
    print(label)
    try:
        db_path, project_path, arch_paths, completed = build_database(
            arch_yaml, expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        if NEEDLE not in combined:
            print(f"FAIL: diagnostic missing substring '{NEEDLE}'.\n"
                  f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_second_host_with_group():
    return _expect_diagnostic(
        "a second instance of a nested router's host block, carrying the "
        "parent group, is rejected",
        mid_twice(', addressGroup: top'))


def run_second_host_without_group():
    return _expect_diagnostic(
        "a second instance of a nested router's host block, with no "
        "addressGroup:, is rejected",
        mid_twice(''))


CHILD_A_PROJECT = 'childA/yaml/childAProject.yaml'
CHILD_A_PROJECT_ANCHOR = "projectName: childAProj\n"
CHILD_A_LEAF_ANCHOR = ("    uChildALeafY:  { container: childATop, "
                       "instanceType: childALeafY,  instGroup: top, "
                       "addressGroup: top }\n")
CHILD_A_ROOT_ROW = ("    uChildARoot:   { container: childATop, "
                    "instanceType: childATop, instGroup: top }\n")
ROOT_ANCHOR = ("    uChildB:      { container: rootTop, instanceType: childBTop,  "
               "instGroup: top, addressGroup: top }\n")
SECOND_CHILD_A = ("    uChildA2:     { container: rootTop, instanceType: childATop,  "
                  "instGroup: top, addressGroup: top }\n")


def _composed_child_with_root(prefix):
    """Copy the composed fixture and give childA a topInstance on its
    router-hosting top block."""
    work = composed.copy_fixture(prefix)
    composed.edit_fixture_yaml(work, CHILD_A_PROJECT, CHILD_A_PROJECT_ANCHOR,
                               CHILD_A_PROJECT_ANCHOR + "topInstance: uChildARoot\n")
    composed.edit_fixture_yaml(work, composed.CHILD_A_TOP, CHILD_A_LEAF_ANCHOR,
                               CHILD_A_LEAF_ANCHOR + CHILD_A_ROOT_ROW)
    return work


def run_composed_child_root_host_once():
    print("a composed child's router-hosting top block, instanced once under "
          "the parent router, is accepted")
    work = _composed_child_with_root('nested_host_child_root_')
    try:
        _db, built = composed.build_db(work)
        if built.returncode != 0:
            print(f"FAIL: make db failed:\n{built.stdout}\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        composed.cleanup(work)


def run_composed_child_root_host_twice():
    print("a second instance of a composed child's router-hosting top block "
          "is rejected")
    work = _composed_child_with_root('nested_host_child_root_twice_')
    try:
        composed.edit_fixture_yaml(work, composed.ROOT_TOP, ROOT_ANCHOR,
                                   ROOT_ANCHOR + SECOND_CHILD_A)
        _db, built = composed.build_db(work)
        needle = ("Block 'childATop' hosts nested router 'uChildADecode' "
                  "(block 'childADecode') and has 2 instances: 'uChildA', "
                  "'uChildA2'.")
        combined = built.stdout + built.stderr
        if built.returncode == 0 or needle not in combined:
            print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                  f"STDOUT:\n{built.stdout}\nSTDERR:\n{built.stderr}")
            return False
        print("PASS")
        return True
    finally:
        composed.cleanup(work)


def run_all_tests():
    results = [
        run_second_host_with_group(),
        run_second_host_without_group(),
        run_composed_child_root_host_once(),
        run_composed_child_root_host_twice(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
