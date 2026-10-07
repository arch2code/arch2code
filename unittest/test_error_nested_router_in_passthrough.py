#!/usr/bin/env python3
"""Nested router hosted by a router-less container one level too deep.

`_findRouterParent` walks exactly one level: it takes the nested
router's container block instance and checks whether *that* instance's
immediate container hosts a router. When the nested router's container
instance instead sits inside a router-less container (which itself
sits under the primary router's container), the walk finds no parent
and `_findPrimaryRouter` sees two dispatch-tree roots. Passing the
register bus through a router-less container to reach a nested router
is unsupported (passthrough synthesis covers only a single
register-owning leaf or a `registerPorts:` IP), so this must raise a
specific diagnostic naming the nested router, its container, and the
router-less wrapper, rather than the generic "multiple candidate
primary routers" message.

Topology (must be rejected)::

    uTop (top)
    +-- uAPBDecode ........... primary router, directly in top
    +-- uWrap (wrap) ......... router-less container
        +-- uBridge (bridge)
            +-- uInnerDecode . nested router
            +-- uLeafA (leafA, addressGroup=bridge)
            +-- uLeafB (leafB, addressGroup=bridge)

Control case: the same design with `uBridge` moved directly into `top`
(bridge's container instantiated in the primary router's own
container, the shape `_findRouterParent` supports) still builds.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_router,
)


NESTED_ROUTER_THROUGH_WRAP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary-level container"
        hasMdl: true
    wrap:
        desc: "Router-less container, wraps bridge"
        hasMdl: true
    bridge:
        desc: "Container hosting the nested router, no registerPorts"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('innerDecode', 'bridge')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uWrap:        { container: top, instanceType: wrap, addressGroup: top }
    uBridge:      { container: wrap, instanceType: bridge }
    uInnerDecode: { container: bridge, instanceType: innerDecode }
    uLeafA:       { container: bridge, instanceType: leafA, addressGroup: bridge }
    uLeafB:       { container: bridge, instanceType: leafB, addressGroup: bridge }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)

# Control: bridge instantiated directly in top (the primary router's own
# container), no router-less wrapper in between. This is the supported
# nested-router shape and must still build.
NESTED_ROUTER_DIRECT_CONTROL = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary-level container"
        hasMdl: true
    bridge:
        desc: "Container hosting the nested router, no registerPorts"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('innerDecode', 'bridge')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:         { container: top, instanceType: top }
    uAPBDecode:   { container: top, instanceType: apbDecode }
    uBridge:      { container: top, instanceType: bridge }
    uInnerDecode: { container: bridge, instanceType: innerDecode }
    uLeafA:       { container: bridge, instanceType: leafA, addressGroup: bridge }
    uLeafB:       { container: bridge, instanceType: leafB, addressGroup: bridge }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
"""
)


REQUIRED_SUBSTRINGS = [
    "uInnerDecode",
    "uBridge",
    "wrap",
    "not supported",
    "Move 'uBridge' into 'top'",
]


def run_nested_router_through_router_less_wrap_rejected():
    print("nested router hosted through a router-less container is rejected "
          "with a specific diagnostic")
    db_path, project_path, arch_paths, completed = build_database(
        NESTED_ROUTER_THROUGH_WRAP, expect_success=False)
    try:
        combined = completed.stdout + completed.stderr
        for needle in REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        if "Multiple candidate primary routers" in combined:
            print(
                f"FAIL: the generic ambiguous-router message fired instead "
                f"of the specific one.\nSTDOUT:\n{completed.stdout}"
            )
            return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_nested_router_direct_in_top_still_builds():
    print("control: nested router's container instantiated directly in "
          "the primary router's container still builds")
    db_path, project_path, arch_paths = build_database(
        NESTED_ROUTER_DIRECT_CONTROL)
    try:
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    results = [
        run_nested_router_through_router_less_wrap_rejected(),
        run_nested_router_direct_in_top_still_builds(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
