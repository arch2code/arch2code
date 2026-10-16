#!/usr/bin/env python3
"""The generated model declares a read-only register as read-only.

hwRegister ignores CPU writes only when its third template argument is true, so
the SystemC class declaration must spell an `ro` register as
`hwRegister< st, 4, true >` and leave the argument off a read-write register.
Without it the model takes firmware writes to an RO register that the RTL
discards.

The fixture puts one `ro` and one `rw` register on the same routed leaf and
renders the leaf's class declaration from the view the SystemC generator uses,
in which the leaf owns the register objects.
"""

import sys
from types import SimpleNamespace

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
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
    - { register: status, regType: ro, block: leaf, structure: cfgRegSt, desc: "" }
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "" }
"""
)


def _run():
    print("ro and rw registers on one leaf render with and without the read-only flag")
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    paths = [project_path, db_path] + arch_paths
    try:
        prj = projectOpen(db_path)
        leaf_key, _ = find_block(prj, 'leaf')
        data = prj.getBlockData(leaf_key, trimRegLeafInstance=True)
        from templates.systemc.classDecl import render_default
        args = SimpleNamespace(mode='module', section=None, noDestructor=False)
        rendered = render_default(args, prj, data)
        assert 'hwRegister< cfgRegSt, 4, true > status;' in rendered, \
            f"expected the ro register declared read-only:\n{rendered}"
        assert 'hwRegister< cfgRegSt, 4 > cfg;' in rendered, \
            f"expected the rw register declared without the read-only flag:\n{rendered}"
        print("PASS")
        return True
    finally:
        cleanup(paths)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
