#!/usr/bin/env python3
"""Two-level hierarchy with non-parameterized leaves only.

Same shape as the primary + nested router case (leaves under each) but
confirms the post-parse pass does not require any ipParameters: /
variants and that the resulting connections carry no per-variant
ConfigType.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    assert_no_global_register_binds,
    build_database,
    cleanup,
    find_connections,
    projectOpen,
    render_leaf,
    render_router,
)


ARCH_YAML = (
    APB_PREAMBLE
    + """
blocks:
    top:
        desc: "Primary container"
        hasMdl: true
    sub:
        desc: "Nested container"
        hasMdl: true
"""
    + render_router('apbDecode', 'top')
    + render_router('subDecode', 'sub')
    + render_leaf('topLeaf')
    + render_leaf('subLeaf')
    + """
instances:
    uTop:        { container: top, instanceType: top }
    uAPBDecode:  { container: top, instanceType: apbDecode }
    uSub:        { container: top, instanceType: sub }
    uSubDecode:  { container: sub, instanceType: subDecode }
    uTopLeaf:    { container: top, instanceType: topLeaf, addressGroup: top }
    uSubLeaf:    { container: sub, instanceType: subLeaf, addressGroup: sub }

registers:
    - { register: cfgT, regType: rw, block: topLeaf, structure: cfgRegSt, desc: "" }
    - { register: cfgS, regType: rw, block: subLeaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("two-level hierarchy, no IP parameterization")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)

        # Connection / bind shape matches the primary + nested router case.
        assert len(find_connections(prj, src='uAPBDecode', dst='uTopLeaf')) == 1
        assert len(find_connections(prj, src='uSubDecode', dst='uSubLeaf')) == 1
        assert len(find_connections(prj, src='uAPBDecode', dst='uSub')) == 1

        # No leaf carries ipParameters: every block's isParameterizable
        # field is falsy. Routed leaves whose downstream is purely
        # non-parameterized must still produce the binds above.
        for blockKey, row in prj.data['blocks'].items():
            if row.get('block') in ('topLeaf', 'subLeaf', 'apbDecode', 'subDecode'):
                assert not bool(row.get('isParameterizable')), (
                    f"block '{row.get('block')}' should not be parameterizable "
                    f"in a no-IP fixture; got {row.get('isParameterizable')!r}"
                )

        assert_no_global_register_binds(prj)
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
