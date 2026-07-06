#!/usr/bin/env python3
"""Router declares non-default upstreamPort / registerDecoderPort.

Asserts the router-side addressBlock view echoes the authored values
and that the router-to-leaf srcport is built from the custom
registerDecoderPort name.
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
    render_router,
)


# Inject two extra APB-shaped interfaces (customUpstream, customDecoder)
# into APB_PREAMBLE's existing `interfaces:` map. They must live under
# the same top-level key, so splice them in textually.
EXTRA_INTERFACES = """    customUpstream:
        desc: "Custom non-default upstream APB interface"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    customDecoder:
        desc: "Custom non-default decoder-side APB interface"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
"""


PREAMBLE_WITH_EXTRA = APB_PREAMBLE.rstrip() + "\n" + EXTRA_INTERFACES


ARCH_YAML = (
    PREAMBLE_WITH_EXTRA
    + """
blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top',
                    upstream_port='customUpstream',
                    register_decoder_port='customDecoder')
    + render_leaf('leaf', port_name='leafCustom', interface='customDecoder')
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
    print("router with explicit non-default port names")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        router_key, router_row = find_block(prj, 'apbDecode')
        ab = router_row.get('addressBlock') or {}
        assert ab.get('upstreamPort') == 'customUpstream', \
            f"authored upstreamPort expected 'customUpstream', got {ab.get('upstreamPort')!r}"
        assert ab.get('registerDecoderPort') == 'customDecoder', \
            f"authored registerDecoderPort expected 'customDecoder', got {ab.get('registerDecoderPort')!r}"

        # Router-to-leaf srcport reflects the custom decoder port name.
        conns = find_connections(prj, src='uAPBDecode', dst='uLeaf')
        assert conns and conns[0].get('srcport') == 'customDecoder_uLeaf', \
            f"srcport expected 'customDecoder_uLeaf', got {conns}"
        # Router view's registerBusInterface and registerBusPort reflect
        # the authored upstream-side interface.
        view = prj.getBlockData(router_key)
        assert view['addressDecode'].get('registerBusInterface') == 'customUpstream', \
            f"router registerBusInterface expected 'customUpstream', got " \
            f"{view['addressDecode'].get('registerBusInterface')!r}"
        assert view['addressDecode'].get('registerBusPort') == 'customUpstream', \
            f"router registerBusPort expected 'customUpstream', got " \
            f"{view['addressDecode'].get('registerBusPort')!r}"

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
