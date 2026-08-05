#!/usr/bin/env python3
"""Regression: implied register-status connections stay in-container scope.

`getBDRegisterConnections` builds an *implied* register-status connection
for a register owned by the block being generated (qualBlock) that has no
explicit `registerConnections` row. The register is routed to the block's
in-container reg handler (`<block>_regs`), and the non-handler end is the
block's own register boundary.

The historical defect (processYaml.py around the implied-connection
branch) selected that non-handler end with
`next(iter(qualBlockInstances))`, where `qualBlockInstances` is EVERY
instance of the block type project-wide. When the block type is reused in
more than one container, this names an *out-of-scope* sibling-container
instance and emits it into the wrong module (e.g. SystemC
`sibling->reg(chan);`), producing "use of undeclared identifier".

This fixture reuses a register-owning reusable-IP leaf (`ip`, declared via
`registerPorts:`) in TWO containers and gives `ip` a contained non-reg
child so the SC view does not trim the reg handler (the implied connection
is actually built). The sibling-container instance is ordered so it would
be `next(iter)`'s first pick. The assertions require every implied
register-connection end to be in-scope: either the in-container reg
handler (`containerKey == ip`) or the qualBlock register boundary (keyed by
the block itself) — and specifically NOT a sibling-container instance.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    projectOpen,
    render_router,
)


# `ip` is a reusable IP leaf (authors registerPorts:) that ALSO contains a
# plain non-reg child (uChild*), so the reg handler is not the only contained
# instance and trimRegLeafInstance does not collapse it -> the implied
# register connection is built for the SC view too. `ip` is instantiated in
# contA (uIpA + uChildA) and contB (uIpB). The instances are authored so a
# project-wide next(iter) over ip's instances would land on a sibling
# container's instance rather than the in-scope boundary.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    contA:
        desc: "Container A"
        hasMdl: true
    contB:
        desc: "Container B"
        hasMdl: true
    ipChild:
        desc: "Plain non-reg child contained inside ip"
        hasMdl: true
    ip:
        desc: "Reusable IP leaf reused across two containers"
        hasMdl: true
        registerPorts:
            regs: { interface: apbReg }
"""
    + render_router('apbDecode', 'top')
    + render_router('aDecode', 'contA')
    + render_router('bDecode', 'contB')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uContA:     { container: top, instanceType: contA }
    uContB:     { container: top, instanceType: contB }
    uADecode:   { container: contA, instanceType: aDecode }
    uIpA:       { container: contA, instanceType: ip, addressGroup: contA }
    uChildA:    { container: ip,    instanceType: ipChild }
    uBDecode:   { container: contB, instanceType: bDecode }
    uIpB:       { container: contB, instanceType: ip, addressGroup: contB }

registers:
    - { register: cfg, regType: rw, block: ip, structure: cfgRegSt, desc: "Implied (no explicit registerConnections) register on ip" }
"""
)


def _implied_register_ends(prj, ip_key):
    """Return the implied registerConnection ends for block `ip`.

    The implied connection carries the qualBlock-owned register `cfg`; it is
    sourced from getBDRegisterConnections' implied branch (no explicit
    registerConnections row authored for it).
    """
    view = prj.getBlockData(ip_key, trimRegLeafInstance=True)
    assert view['enableRegConnections'], (
        "fixture must keep enableRegConnections True (ip needs a contained "
        "non-reg child so the reg handler is not trimmed)"
    )
    reg_conns = view['connectDouble'].get('registerConnections', {})
    assert 'cfg' in reg_conns, (
        f"expected an implied register connection 'cfg'; got {list(reg_conns)}"
    )
    return view, reg_conns['cfg']['ends']


def _run():
    print("Regression: implied register connection stays in-container scope")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        ip_key, _ = find_block(prj, 'ip')

        # The set of out-of-scope sibling-container instances of `ip`: any
        # instance of block `ip` whose container is NOT `ip` itself.
        sibling_instance_names = {
            row['instance']
            for row in prj.data['instances'].values()
            if isinstance(row, dict)
            and row.get('instanceTypeKey') == ip_key
        }
        assert {'uIpA', 'uIpB'} <= sibling_instance_names, (
            f"fixture should reuse ip across containers; got {sibling_instance_names}"
        )

        view, ends = _implied_register_ends(prj, ip_key)

        contained = view['subBlockInstances']
        contained_names = {row['instance'] for row in contained.values()}
        block_name = view['blockName']

        # Every end must be in-scope for the `ip` module: either a contained
        # instance (the in-container reg handler) or the qualBlock register
        # boundary, which is keyed by the block itself and named by the block.
        for end_key, end in ends.items():
            in_container_instance = end_key in contained
            is_block_boundary = (end_key == ip_key) and (end['instance'] == block_name)
            assert in_container_instance or is_block_boundary, (
                f"implied register end {end_key!r} -> instance "
                f"{end['instance']!r} is out of scope for module {block_name!r}; "
                f"expected an in-container instance ({sorted(contained_names)}) "
                f"or the block boundary {block_name!r}"
            )
            # Specifically: no end may name a sibling-container instance.
            assert end['instance'] not in sibling_instance_names, (
                f"implied register end names sibling-container instance "
                f"{end['instance']!r}; this leaks an out-of-scope instance "
                f"into module {block_name!r} (the :1798 cross-container bug)"
            )

        # The in-container reg handler must be one of the ends (the register is
        # actually routed up to the handler).
        handler_key = view['regHandler']
        assert handler_key in ends, (
            f"implied register connection must include the in-container reg "
            f"handler end {handler_key!r}; got {list(ends)}"
        )
        assert prj.data['instances'][handler_key]['containerKey'] == ip_key, (
            "reg handler end must be contained in the block being generated"
        )

        print("PASS: implied register connection in-container scope")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
