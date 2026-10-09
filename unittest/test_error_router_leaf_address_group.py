#!/usr/bin/env python3
"""An instance a router dispatches to must carry the router's addressGroup:.

The router connects to every register-bus consumer in its container, and to
every container hosting a nested router, but only an instance carrying its
addressGroup: gets a decode slot. An instance with no group, or with another
router's group, would get a port on the router that the decoder never drives.
Both are rejected at make db.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


LEAF_WITHOUT_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('fullLeaf')
    + render_leaf('emptyLeaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uFullLeaf:  { container: top, instanceType: fullLeaf, addressGroup: top }
    uEmptyLeaf: { container: top, instanceType: emptyLeaf }
"""
)

# uEmptyLeaf names group 'sub', which the nested router subDecode serves,
# but it sits in top, where apbDecode dispatches to it.
LEAF_WITH_OTHER_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    sub:
        desc: "Container of the nested router"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subDecode', 'sub', address_increment='0x1000')
    + render_leaf('fullLeaf')
    + render_leaf('emptyLeaf')
    + render_leaf('subLeaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uFullLeaf:  { container: top, instanceType: fullLeaf, addressGroup: top }
    uSub:       { container: top, instanceType: sub, addressGroup: top }
    uSubDecode: { container: sub, instanceType: subDecode }
    uSubLeaf:   { container: sub, instanceType: subLeaf, addressGroup: sub }
    uEmptyLeaf: { container: top, instanceType: emptyLeaf, addressGroup: sub }
"""
)


# uSub hosts the nested router subDecode; apbDecode dispatches to uSub.
def nested_container(sub_group_field):
    return (
        APB_PREAMBLE
        + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    sub:
        desc: "Container of the nested router"
        hasMdl: true
"""
        + render_router('apbDecode', 'top')
        + render_router('subDecode', 'sub', address_increment='0x1000')
        + render_leaf('fullLeaf')
        + render_leaf('subLeaf')
        + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uFullLeaf:  {{ container: top, instanceType: fullLeaf, addressGroup: top }}
    uSub:       {{ container: top, instanceType: sub{sub_group_field} }}
    uSubDecode: {{ container: sub, instanceType: subDecode }}
    uSubLeaf:   {{ container: sub, instanceType: subLeaf, addressGroup: sub }}
"""
    )


# uMid hosts midDecode, and leafDecode sits one level further down, inside
# uLeafLevel. uMid carries leafDecode's group.
MID_WITH_GRANDCHILD_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    mid:
        desc: "Container of the nested router"
        hasMdl: true
    leafLevel:
        desc: "Container of the second nested router"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('midDecode', 'mid', address_increment='0x00100000')
    + render_router('leafDecode', 'leafLevel', address_increment='0x00010000')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uMid:        { container: top, instanceType: mid, addressGroup: leafLevel }
    uMidDecode:  { container: mid, instanceType: midDecode }
    uLeafLevel:  { container: mid, instanceType: leafLevel, addressGroup: mid }
    uLeafDecode: { container: leafLevel, instanceType: leafDecode }
    uLeafA:      { container: leafLevel, instanceType: leafA, addressGroup: leafLevel }
    uLeafB:      { container: mid, instanceType: leafB, addressGroup: mid }
"""
)


def _expect_diagnostic(label, arch_yaml, required_substrings,
                       forbidden_substrings=()):
    print(label)
    try:
        db_path, project_path, arch_paths, completed = build_database(
            arch_yaml, expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        for needle in required_substrings:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        for needle in forbidden_substrings:
            if needle in combined:
                print(
                    f"FAIL: diagnostic contains '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_leaf_without_group():
    return _expect_diagnostic(
        "a registerPorts: leaf next to the router with no addressGroup: is rejected",
        LEAF_WITHOUT_GROUP,
        [
            "Instance 'uEmptyLeaf' (block 'emptyLeaf') has a register bus, and "
            "router 'uAPBDecode' (block 'apbDecode') in container 'top' "
            "dispatches to it, but it carries no addressGroup:. Set "
            "addressGroup: top on instance 'uEmptyLeaf'; without it the router "
            "allocates it no decode slot.",
        ],
    )


def run_leaf_with_other_group():
    return _expect_diagnostic(
        "a leaf next to the router carrying another router's addressGroup: is rejected",
        LEAF_WITH_OTHER_GROUP,
        [
            "Instance 'uEmptyLeaf' (block 'emptyLeaf') has a register bus, and "
            "router 'uAPBDecode' (block 'apbDecode') in container 'top' "
            "dispatches to it, but it carries addressGroup: sub.",
            "Change addressGroup: sub to top on instance 'uEmptyLeaf'",
            "move it into container 'sub', which router 'uSubDecode' serves",
        ],
    )


def run_nested_container_without_group():
    return _expect_diagnostic(
        "a container hosting a nested router with no addressGroup: is rejected",
        nested_container(''),
        [
            "Instance 'uSub' (block 'sub') hosts nested router 'uSubDecode', "
            "and router 'uAPBDecode' (block 'apbDecode') in container 'top' "
            "dispatches to it, but it carries no addressGroup:. Set "
            "addressGroup: top on instance 'uSub'",
        ],
    )


def run_nested_container_with_nested_group():
    return _expect_diagnostic(
        "a container hosting a nested router that carries the nested "
        "router's own addressGroup: is rejected",
        nested_container(', addressGroup: sub'),
        [
            "Instance 'uSub' (block 'sub') hosts nested router 'uSubDecode', "
            "and router 'uAPBDecode' (block 'apbDecode') in container 'top' "
            "dispatches to it, but it carries addressGroup: sub.",
            "Change addressGroup: sub to top on instance 'uSub'",
            "Group sub belongs to router 'uSubDecode' inside it",
        ],
    )


def run_nested_container_with_deeper_group():
    return _expect_diagnostic(
        "a container hosting a nested router that carries the group of a "
        "router further down is told the group belongs inside it",
        MID_WITH_GRANDCHILD_GROUP,
        [
            "Instance 'uMid' (block 'mid') hosts nested router 'uMidDecode', "
            "and router 'uAPBDecode' (block 'apbDecode') in container 'top' "
            "dispatches to it, but it carries addressGroup: leafLevel.",
            "Change addressGroup: leafLevel to top on instance 'uMid'",
            "Group leafLevel belongs to router 'uLeafDecode' inside it",
        ],
        forbidden_substrings=["move it into container"],
    )


def run_all_tests():
    results = [
        run_leaf_without_group(),
        run_leaf_with_other_group(),
        run_nested_container_without_group(),
        run_nested_container_with_nested_group(),
        run_nested_container_with_deeper_group(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
