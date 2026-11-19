#!/usr/bin/env python3
"""A testbench External re-creates a register array's channel as a vector.

When the excluded DUT is a child that takes a whole register array, the
External keeps the array's other ends, so it builds the array's channel. That
channel is an sc_vector, so the initializer passes the count and a creator
that builds each element with the source block.

An ro array split by index rows has a different source for each element,
and the creator names each element's own source. When the excluded DUT is
one of those sources, the External still names it as its element's source.
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

SPLIT_RO_ARCH = APB_PREAMBLE.rstrip() + """

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('owner') \
    + render_plain_block('childA') + render_plain_block('childB') + render_plain_block('childC') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uA:         { container: owner, instanceType: childA }
    uB:         { container: owner, instanceType: childB }
    uC:         { container: owner, instanceType: childC }

registers:
    - { register: arr, regType: ro, block: owner, structure: cfgRegSt, count: 2, desc: "array" }
    - { register: other, regType: rw, block: owner, structure: cfgRegSt, desc: "register of the DUT" }

registerConnections:
    - { register: arr, block: owner, instance: uA, index: 0 }
    - { register: arr, block: owner, instance: uB, index: 1 }
    - { register: other, block: owner, instance: uC }
"""


def check_external(label, arch, excluded, expected):
    db_path, project_path, arch_paths = build_database(arch)
    try:
        prj = projectOpen(db_path)
        blockKey, _ = find_block(prj, 'owner')
        external = prj.getBlockData(blockKey, trimRegLeafInstance=True, excludeInstances={excluded})
        testbench.refactor_tbExternal(None, prj, external)
        try:
            init = testbench.ext_sec_init(types.SimpleNamespace(variant=None), prj, external)
        except SystemExit:
            print(f"FAIL: {label}\n  the External init stopped with an error")
            return False
        lines = [line.strip() for line in init.splitlines() if line.strip().startswith(',arr(')]
        if lines != expected:
            print(f"FAIL: {label}\n  expected {expected}\n  got      {lines}\n{init}")
            return False
        print(f"PASS: {label}")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    results = [
        check_external("the External without uB builds arr as a channel vector", ARCH, 'uB',
                       [',arr("arr", 2, [&](const char * nm, size_t) { return new '
                        'status_channel<cfgRegSt>(nm, "u_owner_regs"); })']),
        check_external("the External without uC builds a split ro arr with each element's source",
                       SPLIT_RO_ARCH, 'uC',
                       [',arr("arr", 2, [&](const char * nm, size_t i) { const char * srcNames[] = '
                        '{"uA", "uB"}; return new status_channel<cfgRegSt>(nm, srcNames[i]); })']),
        check_external("the External without uA, a source of a split ro arr, still names uA as its element's source",
                       SPLIT_RO_ARCH, 'uA',
                       [',arr("arr", 2, [&](const char * nm, size_t i) { const char * srcNames[] = '
                        '{"uA", "uB"}; return new status_channel<cfgRegSt>(nm, srcNames[i]); })']),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
