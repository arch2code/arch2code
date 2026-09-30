#!/usr/bin/env python3
"""One router, one routed leaf with one register.

Asserts the canonical post-parse outputs of
`config/postParseRegisterPorts.py` for the smallest new-schema
topology: router-side addressDecode view, leaf-side addressDecode view,
synthesised handler block / instance, router-to-leaf connection,
leaf-to-handler connectionMap, the INSTANCES_WITH_REGAPB list, and the
no-_global invariant.
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
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_leaf('leaf')
    + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Leaf config register" }
"""
)


def _run():
    print("single router, one routed leaf with one register")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # ---- Router view ----
        router_key, _ = find_block(prj, 'apbDecode')
        router_view = prj.getBlockData(router_key)
        ad = router_view['addressDecode']
        assert bool(ad.get('isApbRouter')), \
            f"router isApbRouter expected truthy, got {ad.get('isApbRouter')!r}"
        assert ad.get('registerBusInterface') == 'apbReg', \
            f"router registerBusInterface expected 'apbReg', got {ad.get('registerBusInterface')}"
        assert ad.get('registerBusPort') == 'apbReg', \
            f"router registerBusPort expected 'apbReg', got {ad.get('registerBusPort')}"
        assert ad.get('addressGroup') == 'top', \
            f"router addressGroup expected 'top', got {ad.get('addressGroup')}"

        # ---- Leaf view ----
        leaf_key, _ = find_block(prj, 'leaf')
        leaf_view = prj.getBlockData(leaf_key)
        lad = leaf_view['addressDecode']
        assert not bool(lad.get('isApbRouter')), \
            f"leaf isApbRouter expected falsy, got {lad.get('isApbRouter')!r}"
        assert bool(lad.get('hasDecoder')), \
            f"leaf hasDecoder expected truthy (one register), got {lad.get('hasDecoder')!r}"
        assert lad.get('registerBusInterface') == 'apbReg', \
            f"leaf registerBusInterface expected 'apbReg', got {lad.get('registerBusInterface')}"
        assert lad.get('registerBusPort') == 'regs', \
            f"leaf registerBusPort expected 'regs' (the authored registerPorts: key), got {lad.get('registerBusPort')}"

        # ---- Synthesised handler block / instance ----
        # regBlockNaming default is instancePrefix='u_', blockSuffix='_regs'
        handler_block_key, handler_block_row = find_block(prj, 'leaf_regs')
        assert bool(handler_block_row.get('isRegHandler')), \
            f"handler block expected isRegHandler truthy, got {handler_block_row.get('isRegHandler')!r}"

        handler_inst_key, handler_inst_row = find_instance(prj, 'u_leaf_regs')
        assert handler_inst_row.get('instanceTypeKey') == handler_block_key, \
            f"u_leaf instanceTypeKey expected '{handler_block_key}', got '{handler_inst_row.get('instanceTypeKey')}'"
        assert handler_inst_row.get('containerKey') == leaf_key, \
            f"u_leaf containerKey expected '{leaf_key}' (the routed leaf block), got '{handler_inst_row.get('containerKey')}'"

        # ---- Router-to-leaf connection ----
        router_conns = find_connections(prj, src='uAPBDecode', dst='uLeaf')
        assert len(router_conns) == 1, \
            f"expected exactly one router-to-leaf connection, got {len(router_conns)}"
        rc = router_conns[0]
        assert rc.get('interface') == 'apbReg', \
            f"router-to-leaf interface expected 'apbReg', got {rc.get('interface')}"
        assert rc.get('dstport') == 'regs', \
            f"router-to-leaf dstport expected 'regs' (the leaf's authored port), got {rc.get('dstport')}"
        assert rc.get('srcport') == 'apbReg_uLeaf', \
            f"router-to-leaf srcport expected 'apbReg_uLeaf', got {rc.get('srcport')}"

        # ---- Leaf-to-handler connectionMap ----
        leaf_maps = find_connection_maps(prj, instance='u_leaf_regs')
        assert len(leaf_maps) == 1, \
            f"expected exactly one leaf-to-handler connectionMap, got {len(leaf_maps)}"
        cm = leaf_maps[0]
        assert cm.get('interface') == 'apbReg', \
            f"connectionMap interface expected 'apbReg', got {cm.get('interface')}"
        assert cm.get('port') == 'regs', \
            f"connectionMap port (leaf-side) expected 'regs', got {cm.get('port')}"
        assert cm.get('instancePort') == 'apbReg', \
            f"connectionMap instancePort (handler-side) expected 'apbReg', got {cm.get('instancePort')}"

        # ---- INSTANCES_WITH_REGAPB ----
        instances_with_regapb = prj.config.getConfig('INSTANCES_WITH_REGAPB', failOk=True)
        assert instances_with_regapb is not None, \
            "INSTANCES_WITH_REGAPB config key missing"
        leaf_inst_key, _ = find_instance(prj, 'uLeaf')
        assert leaf_inst_key in instances_with_regapb, \
            f"INSTANCES_WITH_REGAPB expected to include '{leaf_inst_key}'; got {instances_with_regapb}"

        # ---- No-_global invariant ----
        assert_no_global_register_binds(prj)

        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
