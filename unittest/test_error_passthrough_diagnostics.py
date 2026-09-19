#!/usr/bin/env python3
"""Router-less passthrough container diagnostics.

A passthrough container's own instance is the routed slot: it carries the
router's `addressGroup:` and receives the synthesised dispatch, and the
inner consumer carries none. Two ways to violate that:

- the inner consumer itself carries `addressGroup:` (it is not the
  instance the router allocates a decode slot to); or
- the container's own instance does not carry the router's
  `addressGroup:` (the router allocates it no decode slot at all).

A container is also rejected as a passthrough when it owns firmware-
accessible registers or memories itself, since its own handler is already
the one consumer its boundary can serve, or when it is the design root,
which has no parent to be fed from.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_plain_block,
    render_router,
)


INNER_CONSUMER_ADDRESS_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
    unservedContainer:
        desc: "Router-less container, single consumer"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uIsolated:  { container: top, instanceType: unservedContainer, addressGroup: top }
    uLeafLost:  { container: unservedContainer, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

CONTAINER_MISSING_ADDRESS_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
    unservedContainer:
        desc: "Router-less container, single consumer"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uIsolated:  { container: top, instanceType: unservedContainer }
    uLeafLost:  { container: unservedContainer, instanceType: leaf }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# A top-down container owning registers directly, with no registerPorts:,
# hosting a single inner consumer and no router of its own.
CONTAINER_OWNS_REGISTERS_TOPDOWN = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
    wrap:
        desc: "Router-less container owning registers and hosting a consumer"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

registers:
    - { register: cfgW, regType: rw, block: wrap, structure: cfgRegSt, desc: "" }
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# The same shape, but the container is a reusable IP declaring its own
# registerPorts: boundary as well as owning registers directly.
CONTAINER_OWNS_REGISTERS_REUSABLE_IP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('wrap')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

registers:
    - { register: cfgW, regType: rw, block: wrap, structure: cfgRegSt, desc: "" }
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# The design root itself hosts a register-owning leaf directly, while the
# only router in the design is nested inside an unrelated sibling container.
# The root has no parent to pass the bus through to, so this is the ordinary
# "not served by any router" case, not a passthrough.
ROOT_HOSTS_UNSERVED_LEAF = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    bridge:
        desc: "Hosts the only router, unrelated to the unserved leaf"
        hasMdl: true
"""
    + render_plain_block('cpu')
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + render_leaf('inner')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uBridge:    { container: top, instanceType: bridge }
    uAPBDecode: { container: bridge, instanceType: apbDecode }
    uInner:     { container: bridge, instanceType: inner, addressGroup: top }
    uLeaf:      { container: top, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uBridge, dstport: apbReg }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
    - { register: cfgI, regType: rw, block: inner, structure: cfgRegSt, desc: "" }
"""
)


# An ordinary routed leaf, co-located with its router, with no
# addressGroup:. No post-parse check rejects it; `calcAddresses`'
# address-space check does.
DIRECT_LEAF_MISSING_ADDRESS_GROUP = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_plain_block('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# No router reaches 'wrap'; the only router is nested in the unrelated
# sibling 'bridge'. The inner consumer also carries addressGroup:. With no
# routed slot to name, the addressGroup check must stay silent and the
# unserved-leaf diagnostic must name the leaf.
WRAP_NOT_REACHED_BY_ANY_ROUTER = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    bridge:
        desc: "Hosts the only router, unrelated to wrap"
        hasMdl: true
    wrap:
        desc: "Router-less container, not reached by any router"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_plain_block('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uBridge:    { container: top, instanceType: bridge }
    uAPBDecode: { container: bridge, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap }
    uLeaf:      { container: wrap, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


def _expect_diagnostic(label, arch_yaml, required_substrings):
    print(label)
    db_path, project_path, arch_paths, completed = build_database(
        arch_yaml, expect_success=False)
    try:
        combined = completed.stdout + completed.stderr
        for needle in required_substrings:
            if needle not in combined:
                print(
                    f"FAIL: diagnostic missing substring '{needle}'.\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_inner_consumer_must_not_carry_address_group():
    return _expect_diagnostic(
        "inner consumer fed through a passthrough container must not "
        "carry addressGroup:",
        INNER_CONSUMER_ADDRESS_GROUP,
        [
            "'uLeafLost'",
            "fed through router-less container 'unservedContainer'",
            "must not carry addressGroup:",
        ],
    )


def run_container_slot_must_carry_router_address_group():
    return _expect_diagnostic(
        "the passthrough container's own instance must carry the "
        "router's addressGroup:",
        CONTAINER_MISSING_ADDRESS_GROUP,
        [
            "'uIsolated'",
            "must carry addressGroup: top",
        ],
    )


def run_container_owning_registers_is_not_a_passthrough_topdown():
    return _expect_diagnostic(
        "a top-down container owning registers itself cannot also pass "
        "the bus through to another consumer",
        CONTAINER_OWNS_REGISTERS_TOPDOWN,
        [
            "'wrap'",
            "uLeaf",
            "owns firmware-accessible registers/memories itself",
        ],
    )


def run_container_owning_registers_is_not_a_passthrough_reusable_ip():
    return _expect_diagnostic(
        "a reusable-IP container declaring registerPorts: and owning "
        "registers itself cannot also pass the bus through to another "
        "consumer",
        CONTAINER_OWNS_REGISTERS_REUSABLE_IP,
        [
            "'wrap'",
            "uLeaf",
            "owns firmware-accessible registers/memories itself",
        ],
    )


def run_root_hosting_unserved_leaf_is_not_a_passthrough():
    return _expect_diagnostic(
        "the design root hosting a register-owning leaf, while the only "
        "router is nested in an unrelated sibling, is an ordinary unserved "
        "leaf rather than a passthrough container",
        ROOT_HOSTS_UNSERVED_LEAF,
        [
            "'leaf'",
            "no router was found serving any of its instances, directly "
            "or through single-consumer containers",
        ],
    )


def run_direct_leaf_missing_address_group_rejected():
    return _expect_diagnostic(
        "a leaf directly served by its router but missing addressGroup: "
        "entirely is rejected",
        DIRECT_LEAF_MISSING_ADDRESS_GROUP,
        [
            "'uLeaf'",
            "'leaf'",
            "carries no addressGroup:",
            "not fed through a single-consumer container",
        ],
    )


def run_wrap_not_reached_by_any_router_is_unserved_not_d2():
    return _expect_diagnostic(
        "a passthrough container no router ever reaches reports its inner "
        "leaf as unserved rather than raising d2 on an empty slot list",
        WRAP_NOT_REACHED_BY_ANY_ROUTER,
        [
            "'leaf'",
            "no router was found serving any of its instances, directly "
            "or through single-consumer containers",
        ],
    )


def run_all_tests():
    results = [
        run_inner_consumer_must_not_carry_address_group(),
        run_container_slot_must_carry_router_address_group(),
        run_container_owning_registers_is_not_a_passthrough_topdown(),
        run_container_owning_registers_is_not_a_passthrough_reusable_ip(),
        run_root_hosting_unserved_leaf_is_not_a_passthrough(),
        run_direct_leaf_missing_address_group_rejected(),
        run_wrap_not_reached_by_any_router_is_unserved_not_d2(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
