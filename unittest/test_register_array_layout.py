#!/usr/bin/env python3
"""A register array takes one block of address space, and the views and the
firmware header describe it.

An array of count elements is one allocation unit of count * stride bytes. The
stride is the element's decoded footprint, whole 4-byte bus words, rounded up
to the addressObjects.registers alignment, a multiple of 4, so elements never
overlap. sortDescending orders by unit size, so a large array goes
below a scalar that would precede it in declaration order. The registers row
persists offset (element 0) and stride; a scalar's stride is 0.

projectOpen views carry countValue on register rows, None for a scalar. A
register port row and a container's register connection row stand for every
instance they reach, so they carry no index: a consuming block's port row
carries isElementPort, true when its instances take one element each, and each
end of the container's connection carries indexValue, None for an end with no
index. The derived channel index of a duplicated channel name is channelIndex.

regAddresses.h gets REG_<BLOCK>_<REG>, then _STRIDE and _COUNT for an array,
count 1 included. A scalar keeps its single define.
"""

import os
import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    make_project,
    projectOpen,
    render_leaf,
    render_plain_block,
    render_router,
    run_arch2code,
    test_dir,
)
from pysrc.intf_gen_utils import get_channel_name
from templates.systemc import includes


def _arch(registers, connections=''):
    preamble = APB_PREAMBLE.replace(
        'constants:\n', 'constants:\n    N_ARR: { value: 3, desc: "array size" }\n', 1).replace(
        'structures:\n', 'structures:\n    wideRegSt:\n        a: { varType: cfgT }\n'
                         '        b: { varType: cfgT }\n        c: { varType: cfgT }\n', 1)
    return preamble + """
blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('owner') \
        + render_plain_block('childA') + render_plain_block('childB') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uA0:        { container: owner, instanceType: childA }
    uA1:        { container: owner, instanceType: childA }
    uB:         { container: owner, instanceType: childB }

registers:
""" + registers + ("\nregisterConnections:\n" + connections if connections else "")


ARCH = _arch("""    - { register: wide,  regType: rw, block: owner, structure: wideRegSt, desc: "48-bit scalar, 8 bytes" }
    - { register: rwArr, regType: rw, block: owner, structure: cfgRegSt, count: N_ARR, desc: "3 x 8 bytes" }
    - { register: roArr, regType: ro, block: owner, structure: wideRegSt, count: 2, desc: "2 x 8 bytes" }
""", """    - { register: rwArr, block: owner, instance: uA0, index: 0 }
    - { register: rwArr, block: owner, instance: uA1, index: 2 }
    - { register: rwArr, block: owner, instance: uB }
    - { register: roArr, block: owner, instance: uA0, index: 1 }
    - { register: roArr, block: owner, instance: uA1, index: 0 }
""")

# With alignment 4, the smallest make db accepts, a 48-bit element is 6 bytes
# and decodes two 4-byte words.
SMALL_ALIGNMENT_ARCH = _arch("""    - { register: small, regType: rw, block: owner, structure: cfgRegSt, desc: "16-bit scalar, 2 bytes" }
    - { register: one,   regType: rw, block: owner, structure: cfgRegSt, count: 1, desc: "1 x 4 bytes" }
    - { register: wArr,  regType: rw, block: owner, structure: wideRegSt, count: 2, desc: "2 x 8 bytes" }
""")


def _check(failures, label, got, want):
    if got != want:
        failures.append(f"{label}: got {got!r}, want {want!r}")


def _without_index(failures, label, rows):
    _check(failures, f"{label} without index or indexKey",
           [name for name, row in rows.items() if 'index' in row or 'indexKey' in row], [])


def check_layout_and_views(failures):
    db_path, project_path, arch_paths = build_database(ARCH)
    try:
        prj = projectOpen(db_path)
        regs = {row['register']: row for row in prj.data['registers'].values()}
        # sortDescending by unit size: rwArr 24, roArr 16, wide 8
        for name, offset, stride in (('rwArr', 0, 8), ('roArr', 24, 8), ('wide', 40, 0)):
            _check(failures, f"{name} offset", regs[name]['offset'], offset)
            _check(failures, f"{name} stride", regs[name]['stride'], stride)

        handlerKey, _ = find_block(prj, 'owner_regs')
        handler = prj.getBlockData(handlerKey)
        countValues = {row['register']: row['countValue'] for row in handler['registers'].values()}
        _check(failures, "handler countValue", countValues, {'wide': None, 'rwArr': 3, 'roArr': 2})
        portCounts = {name: port['connection']['countValue'] for name, port in handler['ports']['registers'].items()}
        _check(failures, "handler port countValue", portCounts, {'wide': None, 'rwArr': 3, 'roArr': 2})

        ownerKey, _ = find_block(prj, 'owner')
        conns = prj.getBlockData(ownerKey)['connectDouble']['registerConnections']
        _check(failures, "container rwArr countValue", conns['rwArr']['countValue'], 3)
        ends = {end['instance']: end['indexValue'] for end in conns['rwArr']['ends'].values()}
        _check(failures, "container rwArr end indexValue",
               {k: v for k, v in ends.items() if k in ('uA0', 'uA1', 'uB')}, {'uA0': 0, 'uA1': 2, 'uB': None})
        _without_index(failures, "container registerConnections rows", conns)

        for block, want in (('childA', {'rwArr': (3, True), 'roArr': (2, True)}),
                            ('childB', {'rwArr': (3, False)})):
            blockKey, _ = find_block(prj, block)
            view = prj.getBlockData(blockKey)
            ports = view['ports']['registers']
            got = {name: (port['connection']['countValue'], port['connection']['isElementPort'])
                   for name, port in ports.items()}
            _check(failures, f"{block} port countValue/isElementPort", got, want)
            _check(failures, f"{block} port rows without indexValue",
                   [name for name, port in ports.items() if 'indexValue' in port['connection']], [])
            _without_index(failures, f"{block} registerPorts rows", view['registerPorts'])

        header = includes.includeRegAddresses({}, prj, {}).splitlines()
        _check(failures, "regAddresses defines", header[1:8], [
            "#define REG_OWNER_WIDE                      0x28",
            "#define REG_OWNER_RWARR                     0x0",
            "#define REG_OWNER_RWARR_STRIDE              0x8",
            "#define REG_OWNER_RWARR_COUNT               3",
            "#define REG_OWNER_ROARR                     0x18",
            "#define REG_OWNER_ROARR_STRIDE              0x8",
            "#define REG_OWNER_ROARR_COUNT               2",
        ])

        # Two connection rows naming one channel get channelIndex 0 and 1.
        interfaceKey = next(iter(prj.data['interfaces']))
        ret = {'connectDouble': {}, 'connectSingle': {}, 'registerConnections': {},
               'connectionMaps': {}, 'memoryConnections': {},
               'connections': {name: {'interfaceName': 'shared', 'interfaceKey': interfaceKey, 'ends': {}}
                               for name in ('c0', 'c1')}}
        prj.getBDConnectionsFinal(ret)
        rows = ret['connectDouble']['connections']
        _check(failures, "duplicated channel channelIndex",
               {name: row['channelIndex'] for name, row in rows.items()}, {'c0': 0, 'c1': 1})
        _check(failures, "duplicated channel names",
               {name: get_channel_name(row) for name, row in rows.items()}, {'c0': 'shared_0', 'c1': 'shared_1'})
    finally:
        cleanup([project_path, db_path] + arch_paths)


def check_small_alignment(failures):
    project_path, arch_paths = make_project([('arch', SMALL_ALIGNMENT_ARCH)])
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        with open(project_path) as f:
            text = f.read()
        aligned8 = "    registers:\n        alignment: 8\n"
        assert aligned8 in text, "make_project no longer sets the register alignment this test edits"
        with open(project_path, 'w') as f:
            f.write(text.replace(aligned8, "    registers:\n        alignment: 4\n"))
        result = run_arch2code(project_path, db_path)
        if result.returncode != 0:
            failures.append(f"alignment 4 build failed:\n{result.stdout}{result.stderr}")
            return
        prj = projectOpen(db_path)
        regs = {row['register']: row for row in prj.data['registers'].values()}
        # sortDescending by unit size: wArr 2 x 8, then small and one, 4 each, in
        # declaration order
        for name, offset, stride in (('wArr', 0, 8), ('small', 16, 0), ('one', 20, 4)):
            _check(failures, f"alignment 4 {name} offset", regs[name]['offset'], offset)
            _check(failures, f"alignment 4 {name} stride", regs[name]['stride'], stride)
        header = includes.includeRegAddresses({}, prj, {}).splitlines()
        _check(failures, "alignment 4 regAddresses defines", header[1:8], [
            "#define REG_OWNER_SMALL                     0x10",
            "#define REG_OWNER_ONE                       0x14",
            "#define REG_OWNER_ONE_STRIDE                0x4",
            "#define REG_OWNER_ONE_COUNT                 1",
            "#define REG_OWNER_WARR                      0x0",
            "#define REG_OWNER_WARR_STRIDE               0x8",
            "#define REG_OWNER_WARR_COUNT                2",
        ])
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    failures = []
    check_layout_and_views(failures)
    check_small_alignment(failures)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print("PASS: an array is one allocation unit with persisted offset and a stride no element "
          "overlaps, the views carry countValue, isElementPort and per-end indexValue and no "
          "index, channelIndex numbers duplicated channels, and regAddresses.h has _STRIDE and _COUNT")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
