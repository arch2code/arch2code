#!/usr/bin/env python3
"""T5.5: A register-owning top-down leaf with NO registerPorts: infers
its register bus from the serving router.

`registerPorts:` is the boundary marker for a bottom-up reusable IP: only
such a block must declare it (so its `<block>Base.h` stays self-contained).
A top-down leaf authors no register port; the post-parse pass resolves its
register-bus interface and canonical port from the serving router, mirroring
the way the legacy `postParseRegister.py` sourced the interface from the
project-wide RegisterBusInterface.

This is the inference counterpart to T1.1, which covers the authored
bottom-up boundary leaf (one that DOES declare registerPorts:). The fixture
here declares a register but no registerPorts:; the assertions confirm the
generator succeeds and produces the inferred register-bus surface on the
router-to-leaf connection, the leaf-to-handler connectionMap, and both the
leaf and synthesised-handler block views.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connection_maps,
    find_connections,
    find_instance,
    projectOpen,
    render_router,
)


# `inferLeaf` owns a register but declares no registerPorts: row. The
# router's registerDecoderPort defaults to 'apbReg', so the inferred
# register-bus interface and canonical leaf port are both 'apbReg'.
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + """    inferLeaf:
        desc: "Top-down leaf owning a register, no registerPorts:"
        hasMdl: true

instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uInfer:     { container: top, instanceType: inferLeaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: inferLeaf, structure: cfgRegSt, desc: "Leaf config register" }
"""
)


def _run():
    print("T5.5: top-down leaf with no registerPorts: infers register bus")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # ---- Synthesised handler block / instance ----
        handler_block_key, handler_block_row = find_block(prj, 'inferLeaf_regs')
        assert bool(handler_block_row.get('isRegHandler')), \
            f"handler block expected isRegHandler truthy, got {handler_block_row.get('isRegHandler')!r}"
        leaf_key, _ = find_block(prj, 'inferLeaf')
        handler_inst_key, handler_inst_row = find_instance(prj, 'u_inferLeaf_regs')
        assert handler_inst_row.get('containerKey') == leaf_key, \
            f"u_inferLeaf_regs containerKey expected '{leaf_key}', got '{handler_inst_row.get('containerKey')}'"

        # ---- Router-to-leaf connection: interface and ports inferred ----
        # from the router (registerDecoderPort default 'apbReg').
        router_conns = find_connections(prj, src='uAPBDecode', dst='uInfer')
        assert len(router_conns) == 1, \
            f"expected exactly one router-to-leaf connection, got {len(router_conns)}"
        rc = router_conns[0]
        assert rc.get('interface') == 'apbReg', \
            f"router-to-leaf interface expected inferred 'apbReg', got {rc.get('interface')}"
        assert rc.get('dstport') == 'apbReg', \
            f"router-to-leaf dstport expected inferred 'apbReg' (registerDecoderPort), got {rc.get('dstport')}"
        assert rc.get('srcport') == 'apbReg_uInfer', \
            f"router-to-leaf srcport expected 'apbReg_uInfer', got {rc.get('srcport')}"

        # ---- Leaf-to-handler connectionMap ----
        leaf_maps = find_connection_maps(prj, instance='u_inferLeaf_regs')
        assert len(leaf_maps) == 1, \
            f"expected exactly one leaf-to-handler connectionMap, got {len(leaf_maps)}"
        cm = leaf_maps[0]
        assert cm.get('interface') == 'apbReg', \
            f"connectionMap interface expected inferred 'apbReg', got {cm.get('interface')}"
        assert cm.get('port') == 'apbReg', \
            f"connectionMap port (leaf-side, inferred canonical) expected 'apbReg', got {cm.get('port')}"
        assert cm.get('instancePort') == 'apbReg', \
            f"connectionMap instancePort (handler-side) expected 'apbReg', got {cm.get('instancePort')}"

        # ---- Leaf view: register bus resolved by inference ----
        leaf_view = prj.getBlockData(leaf_key)
        lad = leaf_view['addressDecode']
        assert not bool(lad.get('isApbRouter')), \
            f"leaf isApbRouter expected falsy, got {lad.get('isApbRouter')!r}"
        assert bool(lad.get('hasDecoder')), \
            f"leaf hasDecoder expected truthy (one register), got {lad.get('hasDecoder')!r}"
        assert lad.get('registerBusInterface') == 'apbReg', \
            f"leaf registerBusInterface expected inferred 'apbReg', got {lad.get('registerBusInterface')}"
        assert lad.get('registerBusPort') == 'apbReg', \
            f"leaf registerBusPort expected inferred 'apbReg', got {lad.get('registerBusPort')}"

        # ---- Handler view: same inferred interface ----
        handler_view = prj.getBlockData(handler_block_key)
        had = handler_view['addressDecode']
        assert had.get('registerBusInterface') == 'apbReg', \
            f"handler registerBusInterface expected 'apbReg', got {had.get('registerBusInterface')}"

        # ---- INSTANCES_WITH_REGAPB ----
        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        assert instances_with_regapb is not None, \
            "INSTANCES_WITH_REGAPB config key missing"
        leaf_inst_key, _ = find_instance(prj, 'uInfer')
        assert leaf_inst_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB expected to include '{leaf_inst_key}'; got {instances_with_regapb}"

        # ---- No-_global invariant ----
        assert_no_global_register_binds(prj)

        print("PASS: T5.5")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
