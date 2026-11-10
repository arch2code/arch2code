#!/usr/bin/env python3
"""A testbench External re-creates a register array's channel as a vector.

When the excluded DUT is a child that takes a whole register array, the
External keeps the array's other ends, so it builds the array's channel. That
channel is an sc_vector, so the initializer passes the count and a creator
that builds each element with the source block.
"""

import sys
import types

from _addrctl_helpers import (
    APB_PREAMBLE,
    base_dir,
    build_database,
    cleanup,
    find_block,
    render_leaf,
    render_plain_block,
    render_router,
)

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
from templates.systemc import testbench


ARCH = APB_PREAMBLE.rstrip() + """

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('owner') \
    + render_plain_block('childA') + render_plain_block('childB') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uA:         { container: owner, instanceType: childA }
    uB:         { container: owner, instanceType: childB }

registers:
    - { register: arr, regType: rw, block: owner, structure: cfgRegSt, count: 2, desc: "array" }

registerConnections:
    - { register: arr, block: owner, instance: uA }
    - { register: arr, block: owner, instance: uB }
"""


def run_all_tests():
    db_path, project_path, arch_paths = build_database(ARCH)
    try:
        prj = projectOpen(db_path)
        blockKey, _ = find_block(prj, 'owner')
        external = prj.getBlockData(blockKey, trimRegLeafInstance=True, excludeInstances={'uB'})
        testbench.refactor_tbExternal(None, prj, external)
        init = testbench.ext_sec_init(types.SimpleNamespace(variant=None), prj, external)
        lines = [line.strip() for line in init.splitlines() if line.strip().startswith(',arr(')]
        expected = [',arr("arr", 2, [&](const char * nm, size_t) { return new '
                    'status_channel<cfgRegSt>(nm, "u_owner_regs"); })']
        if lines != expected:
            print(f"FAIL: the External without uB builds arr as a channel vector\n"
                  f"  expected {expected}\n  got      {lines}\n{init}")
            return 1
        print("PASS: the External without uB builds arr as a channel vector")
        return 0
    finally:
        cleanup([project_path, db_path] + arch_paths)


if __name__ == '__main__':
    sys.exit(run_all_tests())
