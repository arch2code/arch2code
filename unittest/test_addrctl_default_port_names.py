#!/usr/bin/env python3
"""Router omits upstreamPort: and registerDecoderPort:.

Defaults resolve to `apbReg`. Asserts the router-side view exposes
`apbReg` for both fields and that the emitted router-to-leaf bind names
the default decoder port.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_block,
    find_connections,
    projectOpen,
    render_leaf,
)


# Router declaration is hand-written so upstreamPort: and
# registerDecoderPort: are omitted (the helper always emits them).
ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    apbDecode:
        desc: "Primary router with default port names"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
"""
    + render_leaf('leaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uLeaf:       { container: top, instanceType: leaf, addressGroup: top }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("router with default upstream/register port names")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        router_key, router_row = find_block(prj, 'apbDecode')
        ab = router_row.get('addressBlock') or {}
        assert ab.get('upstreamPort') == 'apbReg', \
            f"upstreamPort default expected 'apbReg', got {ab.get('upstreamPort')!r}"
        assert ab.get('registerDecoderPort') == 'apbReg', \
            f"registerDecoderPort default expected 'apbReg', got {ab.get('registerDecoderPort')!r}"

        # Router-to-leaf bind srcport is built from registerDecoderPort.
        conns = find_connections(prj, src='uAPBDecode', dst='uLeaf')
        assert conns and conns[0].get('srcport') == 'apbReg_uLeaf', \
            f"srcport expected 'apbReg_uLeaf' (default decoder port + instance), got {conns}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
