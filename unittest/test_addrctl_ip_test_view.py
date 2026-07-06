#!/usr/bin/env python3
"""Migrated `examples/ip_test/` view assertions.

Reads the post-migration `ip_test` database rather than a synthetic
topology fixture, covering:

- Leaf interface scoping — the routed leaf `ip` declares its register-bus
  interface (`ipReg`) in its own scope, distinct from the routers'
  upstream interface (`apbReg`); the divergence is reconciled in the
  leaf-to-handler connectionMap, and the packed form matches so the
  build succeeds.
- The primary router `apbDecode` serves direct leaves
  (`uIp0`, `uIp1`) *and* a nested router (the `uBridge` subtree) from
  the same address group.
- The nested `bridgeApbDecode` router dispatches to the leaves
  inside the cross-config `ipBridge` thunker container.

Unlike the synthetic `test_addrctl_*.py` fixtures, this test opens the
real migrated example database, so a regression in the example's YAML
or in the post-parse pass that touches `ip_test` surfaces here as a
view-assertion failure. It does not run the generator templates; the
`examples/ip_test/` build sweep owns template coverage.
"""

import os
import sys
import tempfile

from _addrctl_helpers import (
    assert_no_global_register_binds,
    base_dir,
    cleanup,
    find_block,
    find_connection_maps,
    find_connections,
    find_instance,
    projectOpen,
    run_arch2code,
)


IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'arch', 'yaml', 'project.yaml')


def _build_ip_test_db():
    db_path = tempfile.mktemp(suffix='.db', dir=os.path.dirname(__file__))
    result = run_arch2code(IP_TEST_PROJECT, db_path, timeout=180)
    if result.returncode != 0:
        cleanup([db_path])
        raise RuntimeError(
            f"arch2code.py failed on migrated ip_test:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return db_path


def _assert_leaf_interface_scoping(prj):
    """Leaf-scoped `ipReg` distinct from router `apbReg`."""
    # Routers resolve their own upstream APB interface.
    for router, group in (('apbDecode', 'top'), ('bridgeApbDecode', 'bridge')):
        key, _ = find_block(prj, router)
        ad = prj.getBlockData(key)['addressDecode']
        assert bool(ad.get('isApbRouter')), \
            f"{router} expected isApbRouter truthy, got {ad.get('isApbRouter')!r}"
        assert ad.get('registerBusInterface') == 'apbReg', \
            f"{router} registerBusInterface expected 'apbReg', got {ad.get('registerBusInterface')}"
        assert ad.get('registerBusPort') == 'apbReg', \
            f"{router} registerBusPort expected 'apbReg', got {ad.get('registerBusPort')}"
        assert ad.get('addressGroup') == group, \
            f"{router} addressGroup expected '{group}', got {ad.get('addressGroup')}"

    # The leaf resolves its own scoped interface and authored port name.
    ip_key, _ = find_block(prj, 'ip')
    lad = prj.getBlockData(ip_key)['addressDecode']
    assert not bool(lad.get('isApbRouter')), \
        f"ip leaf expected isApbRouter falsy, got {lad.get('isApbRouter')!r}"
    assert bool(lad.get('hasDecoder')), \
        f"ip leaf expected hasDecoder truthy, got {lad.get('hasDecoder')!r}"
    assert lad.get('registerBusInterface') == 'ipReg', \
        f"ip leaf registerBusInterface expected 'ipReg', got {lad.get('registerBusInterface')}"
    assert lad.get('registerBusPort') == 'regs', \
        f"ip leaf registerBusPort expected 'regs', got {lad.get('registerBusPort')}"

    # The leaf-to-handler connectionMap is where the leaf-scoped `ipReg`
    # and the router-side `apbReg` port meet: the leaf side carries
    # `ipReg` on port `regs`, the handler side carries the router's
    # `apbReg` port name.
    handler_maps = find_connection_maps(prj, instance='uIpRegs')
    assert len(handler_maps) == 1, \
        f"expected one uIpRegs leaf-to-handler connectionMap, got {len(handler_maps)}"
    cm = handler_maps[0]
    assert cm.get('interface') == 'ipReg', \
        f"uIpRegs connectionMap interface expected 'ipReg', got {cm.get('interface')}"
    assert cm.get('port') == 'regs', \
        f"uIpRegs connectionMap port expected 'regs', got {cm.get('port')}"
    assert cm.get('instancePort') == 'apbReg', \
        f"uIpRegs connectionMap instancePort expected 'apbReg', got {cm.get('instancePort')}"

    # Handler block / instance synthesised once for the reused `ip` block.
    handler_block_key, handler_block_row = find_block(prj, 'ipRegs')
    assert bool(handler_block_row.get('isRegHandler')), \
        f"ipRegs expected isRegHandler truthy, got {handler_block_row.get('isRegHandler')!r}"
    handler_inst_key, handler_inst_row = find_instance(prj, 'uIpRegs')
    assert handler_inst_row.get('instanceTypeKey') == handler_block_key, \
        f"uIpRegs instanceTypeKey expected '{handler_block_key}', got '{handler_inst_row.get('instanceTypeKey')}'"
    assert handler_inst_row.get('containerKey') == ip_key, \
        f"uIpRegs containerKey expected '{ip_key}' (block ip), got '{handler_inst_row.get('containerKey')}'"


def _assert_primary_serves_leaves_and_nested_router(prj):
    """Primary router has direct leaves AND a nested router."""
    for leaf in ('uIp0', 'uIp1'):
        conns = find_connections(prj, src='uAPBDecode', dst=leaf)
        assert len(conns) == 1, \
            f"expected one uAPBDecode->{leaf} register bind, got {len(conns)}"
        assert conns[0].get('dstport') == 'regs', \
            f"uAPBDecode->{leaf} dstport expected 'regs', got {conns[0].get('dstport')}"
        assert conns[0].get('interface') == 'apbReg', \
            f"uAPBDecode->{leaf} interface expected 'apbReg', got {conns[0].get('interface')}"

    # Router-to-router bind into the nested-router container. The child
    # router's upstreamPort ('apbReg') is the destination port.
    nested = find_connections(prj, src='uAPBDecode', dst='uBridge',
                              interface='apbReg')
    assert len(nested) == 1, \
        f"expected one uAPBDecode->uBridge router-to-router bind, got {len(nested)}"
    assert nested[0].get('dstport') == 'apbReg', \
        f"uAPBDecode->uBridge dstport expected 'apbReg', got {nested[0].get('dstport')}"


def _assert_nested_router_subtree(prj):
    """The bridge nested router dispatches to its own leaves."""
    for leaf in ('uBridgeIp0', 'uBridgeIp1'):
        conns = find_connections(prj, src='uBridgeAPBDecode', dst=leaf)
        assert len(conns) == 1, \
            f"expected one uBridgeAPBDecode->{leaf} register bind, got {len(conns)}"
        assert conns[0].get('dstport') == 'regs', \
            f"uBridgeAPBDecode->{leaf} dstport expected 'regs', got {conns[0].get('dstport')}"
        # These binds are authored in the bridge block's own context,
        # never _global.
        assert conns[0].get('_context') != '_global', \
            f"uBridgeAPBDecode->{leaf} must not carry _context '_global'"


def _run():
    print("migrated ip_test view assertions")
    db_path = _build_ip_test_db()
    try:
        prj = projectOpen(db_path)
        _assert_leaf_interface_scoping(prj)
        _assert_primary_serves_leaves_and_nested_router(prj)
        _assert_nested_router_subtree(prj)
        assert_no_global_register_binds(prj)
        print("PASS: ip_test view assertions")
        return True
    finally:
        cleanup([db_path])


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
