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

A leaf's register-bus port name, authored or inferred, must not already
name one of its registers or ports, and each passthrough boundary's
interface, authored or inferred, must share the inner consumer's packed form.
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

# A plain leaf behind an authored boundary takes the boundary's
# registerPorts: key as its register-bus port name; here that key is also
# the name of one of the leaf's own registers.
INFERRED_PORT_NAME_COLLIDES_WITH_REGISTER = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_plain_block('cpu')
    + render_router('apbDecode', 'top')
    + render_leaf('wrap', port_name='cfgA')
    + render_plain_block('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgA, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# A reusable IP's authored registerPorts: key is also the name of one of
# its own registers.
AUTHORED_PORT_NAME_COLLIDES_WITH_REGISTER = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_plain_block('cpu')
    + render_router('apbDecode', 'top')
    + render_leaf('leaf', port_name='cfgA')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgA, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# The router and the passthrough boundary carry a 32-bit data bus; the
# inner reusable IP declares a 64-bit one.
WIDE_REG_PREAMBLE = """constants:
    ADDR_WIDTH:      { value: 32, desc: "Register bus address width" }
    DATA_WIDTH:      { value: 32, desc: "Register bus data width" }
    WIDE_DATA_WIDTH: { value: 64, desc: "Wide register bus data width" }
    REG_WIDTH:       { value: 16, desc: "Register payload width" }

types:
    apbAddrT:  { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT:  { width: DATA_WIDTH, desc: "APB data" }
    wideDataT: { width: WIDE_DATA_WIDTH, desc: "Wide APB data" }
    cfgT:      { width: REG_WIDTH,  desc: "Register payload" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    wideDataSt:
        data: { varType: wideDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    wideReg:
        desc: "APB register bus with 64-bit data"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: wideDataSt, structureType: data_t }
"""

PASSTHROUGH_BOUNDARY_WIDTH_MISMATCH = (
    WIDE_REG_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_plain_block('cpu')
    + render_router('apbDecode', 'top')
    + render_leaf('wrap')
    + render_leaf('leaf', interface='wideReg')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeaf:      { container: wrap, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)

# The same 32/64 mismatch through a container that authors no
# registerPorts: and infers the router's interface.
INFERRING_PASSTHROUGH_WIDTH_MISMATCH = PASSTHROUGH_BOUNDARY_WIDTH_MISMATCH.replace(
    "    wrap:\n        desc: \"Routed leaf block 'wrap'\"\n        hasMdl: true\n"
    "        registerPorts:\n            regs: { interface: apbReg }\n",
    "    wrap:\n        desc: \"Router-less container\"\n        hasMdl: true\n")

# A plain leaf takes the boundary key 'cfgA' as its bus port name while an
# authored data connection already gives it a port named 'cfgA'.
INFERRED_PORT_NAME_COLLIDES_WITH_CONNECTION_PORT = (
    APB_PREAMBLE
    + """    dataIf:
        desc: "Data stream"
        interfaceType: rdy_vld
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
"""
    + render_plain_block('cpu')
    + render_plain_block('src')
    + render_router('apbDecode', 'top')
    + render_leaf('wrap', port_name='cfgA')
    + render_plain_block('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uSrc:       { container: wrap, instanceType: src }
    uLeaf:      { container: wrap, instanceType: leaf }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }
    - { interface: dataIf, src: uSrc, dst: uLeaf, dstport: cfgA }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


# A router-less container holding two register consumers: a passthrough
# forwards the bus to exactly one.
CONTAINER_WITH_TWO_CONSUMERS = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container (carries the primary router)"
        hasMdl: true
    wrap:
        desc: "Router-less container holding two consumers"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leafA')
    + render_leaf('leafB')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uWrap:      { container: top, instanceType: wrap, addressGroup: top }
    uLeafA:     { container: wrap, instanceType: leafA }
    uLeafB:     { container: wrap, instanceType: leafB }

registers:
    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "" }
    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "" }
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
            "'uIsolated' (block 'unservedContainer')",
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


def run_wrap_not_reached_by_any_router_is_unserved():
    return _expect_diagnostic(
        "a passthrough container no router ever reaches reports its inner "
        "leaf as unserved",
        WRAP_NOT_REACHED_BY_ANY_ROUTER,
        [
            "'leaf'",
            "no router was found serving any of its instances, directly "
            "or through single-consumer containers",
        ],
    )


def run_inferred_port_name_colliding_with_register_rejected():
    return _expect_diagnostic(
        "a plain leaf whose inferred register-bus port name is also one of "
        "its register names is rejected",
        INFERRED_PORT_NAME_COLLIDES_WITH_REGISTER,
        [
            "Block 'leaf' declares no registerPorts: and takes its "
            "register-bus port name 'cfgA' from registerPorts: key 'cfgA' of "
            "block 'wrap', but block 'leaf' already uses 'cfgA' as a register.",
            "Rename the register 'cfgA' of block 'leaf', rename the "
            "registerPorts: key 'cfgA' of block 'wrap', or give block 'leaf' "
            "its own registerPorts: entry.",
        ],
    )


def run_authored_port_name_colliding_with_register_rejected():
    return _expect_diagnostic(
        "a reusable IP whose registerPorts: key is also one of its register "
        "names is rejected",
        AUTHORED_PORT_NAME_COLLIDES_WITH_REGISTER,
        [
            "Block 'leaf' uses the name 'cfgA' for both a registerPort and a "
            "register;",
            "must be pairwise distinct within a block. Rename one of them.",
        ],
    )


def run_passthrough_boundary_width_mismatch_rejected():
    return _expect_diagnostic(
        "a passthrough boundary whose authored interface differs in packed "
        "width from the inner consumer's interface is rejected",
        PASSTHROUGH_BOUNDARY_WIDTH_MISMATCH,
        [
            "Router-less container 'wrap' (instance 'uWrap') passes the "
            "register bus on interface 'apbReg' (its registerPorts: "
            "interface) to instance 'uLeaf' of block 'leaf', whose "
            "registerPorts: interface is 'wideReg'. Both interfaces carry the "
            "one bus, so they must have the same packed form; give the "
            "registerPorts: interfaces of blocks 'wrap' and 'leaf' the same "
            "packed form",
            "parent field 'data' has _bitWidth 32 at bit offset 0 in "
            "structure 'apbDataSt'",
            "child field 'data' has _bitWidth 64 at bit offset 0 in "
            "structure 'wideDataSt'",
        ],
    )


def run_inferring_passthrough_width_mismatch_rejected():
    return _expect_diagnostic(
        "a passthrough container with no registerPorts: whose inferred "
        "interface differs in packed width from the inner consumer's is "
        "rejected",
        INFERRING_PASSTHROUGH_WIDTH_MISMATCH,
        [
            "Router-less container 'wrap' (instance 'uWrap') passes the "
            "register bus on interface 'apbReg' (the interface it infers) to "
            "instance 'uLeaf' of block 'leaf', whose registerPorts: interface "
            "is 'wideReg'. Both interfaces carry the one bus, so they must have "
            "the same packed form; give the registerPorts: interface of block "
            "'leaf' the same packed form as 'apbReg'",
            "parent field 'data' has _bitWidth 32 at bit offset 0 in "
            "structure 'apbDataSt'",
        ],
    )


def run_inferred_port_name_colliding_with_connection_port_rejected():
    return _expect_diagnostic(
        "a plain leaf whose inferred register-bus port name is also a port "
        "an authored connection gives it is rejected",
        INFERRED_PORT_NAME_COLLIDES_WITH_CONNECTION_PORT,
        [
            "Block 'leaf' declares no registerPorts: and takes its "
            "register-bus port name 'cfgA' from registerPorts: key 'cfgA' of "
            "block 'wrap', but block 'leaf' already uses 'cfgA' as a "
            "connection port.",
            "Rename the connection port 'cfgA' of block 'leaf', rename the "
            "registerPorts: key 'cfgA' of block 'wrap', or give block 'leaf' "
            "its own registerPorts: entry.",
        ],
    )



def run_container_with_two_consumers_rejected():
    return _expect_diagnostic(
        "a router-less container holding two register consumers is rejected",
        CONTAINER_WITH_TWO_CONSUMERS,
        [
            "Container block 'wrap' hosts 2 instances that need a register "
            "bus (uLeafA (block leafA), uLeafB (block leafB))",
            "can pass the bus through to exactly one such instance",
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
        run_wrap_not_reached_by_any_router_is_unserved(),
        run_inferred_port_name_colliding_with_register_rejected(),
        run_authored_port_name_colliding_with_register_rejected(),
        run_passthrough_boundary_width_mismatch_rejected(),
        run_inferring_passthrough_width_mismatch_rejected(),
        run_inferred_port_name_colliding_with_connection_port_rejected(),
        run_container_with_two_consumers_rejected(),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
