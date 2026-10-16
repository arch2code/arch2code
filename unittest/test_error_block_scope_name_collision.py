#!/usr/bin/env python3
"""A child instance or a connection channel named like another name of its
container block.

A block's generated SystemVerilog module and SystemC class declare its ports,
register channels, memories, child instances and the channels of connections
between its children in one scope, so two of them sharing a name is a
duplicate declaration in both languages. `clockTree.build` rejects it at
`make db` with the block, both kinds and the shared name.

The generator also checks a block's connection channels, register channels,
connectionMaps: ports and memory channels (<memory>_<port> for a memory port
wired to a child, <memory>_reg for a regAccess memory) against each other by
name. A name two of those supply is rejected, even when the connection channel
is shared with other connections.

The same names in different blocks are accepted. Connections of one interface
that share one channel name are declared numbered, so a shared name matching a
child instance or a memory is accepted too. Every accepted cell also builds each block's
generator view.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    projectOpen,
    render_leaf,
    render_plain_block,
    render_router,
)


def arch_yaml(leaf_instances, leaf_connections='', top_instances='', connection_maps='',
              table_fields='', extra_registers='', memory_connections=''):
    return (
        APB_PREAMBLE
        + """
    stIf:
        desc: "Status interface"
        interfaceType: status
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
"""
        + render_router('apbDecode', 'top')
        + render_leaf('leaf')
        + render_plain_block('child')
        + render_plain_block('child2')
        + render_plain_block('sink')
        + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeaf:      {{ container: top, instanceType: leaf, addressGroup: top }}
    uSink:      {{ container: top, instanceType: sink }}
{top_instances}{leaf_instances}
connections:
    - {{ interface: stIf, src: uLeaf, dst: uSink }}
{leaf_connections}
{'connectionMaps:' + chr(10) + connection_maps if connection_maps else ''}
registers:
    - {{ register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Leaf config register" }}
{extra_registers}
memories:
    - {{ memory: tbl, block: leaf, structure: apbDataSt, addressStruct: apbAddrSt, wordLines: 4, desc: "Leaf table"{table_fields} }}
{'memoryConnections:' + chr(10) + memory_connections if memory_connections else ''}
"""
    )


CHILD_PAIR = """    uC1:        { container: leaf, instanceType: child }
    uC2:        { container: leaf, instanceType: child }
"""


# Wires port rd of memory tbl to uC1, so leaf declares channel tbl_rd.
TABLE_RD = dict(table_fields=", ports: [rd]",
                memory_connections="    - { memory: tbl, block: leaf, instance: uC1, port: rd }\n")

# Binds leaf's connectionMaps: port tbl_reg to uC5 inside and to uSink outside.
TABLE_REG_MAP = dict(
    connection_maps="    - { interface: stIf, block: leaf, port: tbl_reg, direction: src, instance: uC5, instancePort: p }\n",
    table_fields=", regAccess: rw")

CHILD_QUAD = CHILD_PAIR + """    uC3:        { container: leaf, instanceType: child }
    uC4:        { container: leaf, instanceType: child }
"""


def channel(name):
    return f"    - {{ interface: stIf, src: uC1, srcport: o, dst: uC2, dstport: i, interfaceName: {name} }}\n"


def shared_channel(srcport):
    # Two connections whose channel name comes from the same srcport: are
    # declared numbered, so the bare name is never declared.
    return (f"    - {{ interface: stIf, src: uC1, srcport: {srcport}, dst: uC2, dstport: i }}\n"
            f"    - {{ interface: stIf, src: uC3, srcport: {srcport}, dst: uC4, dstport: i }}\n")


REJECTED = [
    ("a register and a child instance share a name",
     arch_yaml("    cfg:        { container: leaf, instanceType: child }\n"),
     ["Block 'leaf'", "'cfg'", "register", "child instance"]),
    ("a memory and a child instance share a name",
     arch_yaml("    tbl:        { container: leaf, instanceType: child }\n"),
     ["Block 'leaf'", "'tbl'", "memory", "child instance"]),
    ("a port and a child instance share a name",
     arch_yaml("    stIf:       { container: leaf, instanceType: child }\n"),
     ["Block 'leaf'", "'stIf'", "port", "child instance", "srcport:/dstport:"]),
    ("a register and a connection channel share a name",
     arch_yaml(CHILD_PAIR, channel('cfg')),
     ["Block 'leaf'", "'cfg'", "register", "channel of a connection"]),
    ("a memory and a connection channel share a name",
     arch_yaml(CHILD_PAIR, channel('tbl')),
     ["Block 'leaf'", "'tbl'", "memory", "channel of a connection"]),
    ("a child instance and a connection channel share a name",
     arch_yaml(CHILD_PAIR, channel('uC1')),
     ["Block 'leaf'", "'uC1'", "child instance", "channel of a connection"]),
    ("a shared channel name equal to a register name",
     arch_yaml(CHILD_QUAD, shared_channel('cfg')),
     ["Block 'leaf'", "'cfg'", "register", "channel of a connection"]),
    ("a shared channel name equal to a connectionMaps: port",
     arch_yaml(CHILD_QUAD + "    uC5:        { container: leaf, instanceType: child }\n",
               shared_channel('o')
               + "    - { interface: stIf, src: uLeaf, srcport: o, dst: uSink, dstport: fromO }\n",
               connection_maps="    - { interface: stIf, block: leaf, port: o, direction: src, instance: uC5, instancePort: p }\n"),
     ["Block 'leaf'", "'o'", "connectionMaps: port", "channel of a connection"]),
    ("a connection channel named like a regAccess memory's register channel",
     arch_yaml(CHILD_PAIR, channel('tbl_reg'), table_fields=", regAccess: rw"),
     ["Block 'leaf'", "'tbl_reg'", "memory 'tbl' register channel", "channel of a connection"]),
    ("a connection channel named like a memory port's channel",
     arch_yaml(CHILD_PAIR, channel('tbl_rd'), **TABLE_RD),
     ["Block 'leaf'", "'tbl_rd'", "memory 'tbl' channel", "channel of a connection"]),
    ("a register named like a regAccess memory's register channel",
     arch_yaml('', table_fields=", regAccess: rw",
               extra_registers='    - { register: tbl_reg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Clashing register" }\n'),
     ["Block 'leaf'", "'tbl_reg'", "register", "memory 'tbl' register channel"]),
    ("a connectionMaps: port named like a regAccess memory's register channel",
     arch_yaml("    uC5:        { container: leaf, instanceType: child }\n",
               "    - { interface: stIf, src: uLeaf, srcport: tbl_reg, dst: uSink, dstport: fromTbl }\n",
               **TABLE_REG_MAP),
     ["Block 'leaf'", "'tbl_reg'", "connectionMaps: port", "memory 'tbl' register channel"]),
    ("a memory port named reg on a regAccess memory, wired to a child",
     arch_yaml(CHILD_PAIR, table_fields=", regAccess: rw, ports: [reg]",
               memory_connections="    - { memory: tbl, block: leaf, instance: uC1, port: reg }\n"),
     ["memory 'tbl'", "lists port 'reg'", "Rename the port"]),
    ("a memory port named reg on a regAccess memory, unwired",
     arch_yaml('', table_fields=", regAccess: rw, ports: [reg]"),
     ["memory 'tbl'", "lists port 'reg'", "Rename the port"]),
    ("one memory port wired to two children",
     arch_yaml(CHILD_PAIR, table_fields=", ports: [rd]",
               memory_connections="    - { memory: tbl, block: leaf, instance: uC1, port: rd }\n"
                                  "    - { memory: tbl, block: leaf, instance: uC2, port: rd }\n"),
     ["Memory port 'rd' of 'tbl'", "more than one instance", "'uC1'", "'uC2'"]),
    ("connections of two interfaces sharing one channel name",
     arch_yaml(CHILD_PAIR + """    uC3:        { container: leaf, instanceType: child2 }
    uC4:        { container: leaf, instanceType: child2 }
""",
               "    - { interface: stIf, src: uC1, srcport: o, dst: uC2, dstport: i }\n"
               "    - { interface: apbReg, src: uC3, srcport: o, dst: uC4, dstport: i }\n"),
     ["Block 'leaf'", "'stIf'", "'apbReg'", "channel name 'o'", "one interface"]),
]


ACCEPTED = [
    ("the register's name on an instance of another block",
     arch_yaml('', top_instances="    cfg:        { container: top, instanceType: child }\n")),
    ("two connections sharing one channel name",
     arch_yaml(CHILD_QUAD, shared_channel('o'))),
    ("a shared channel name equal to a child instance name",
     arch_yaml(CHILD_QUAD + "    o:          { container: leaf, instanceType: child }\n",
               shared_channel('o'))),
    ("a shared channel name equal to a memory name",
     arch_yaml(CHILD_QUAD, shared_channel('tbl'))),
    ("a memory port's channel name on a connection in another block",
     arch_yaml(CHILD_PAIR,
               "    - { interface: stIf, src: uT1, srcport: o, dst: uT2, dstport: i, interfaceName: tbl_rd }\n",
               top_instances="    uT1:        { container: top, instanceType: child }\n"
                             "    uT2:        { container: top, instanceType: child }\n",
               **TABLE_RD)),
]


def _rejected(label, yaml, needles):
    print(f"{label}: rejected")
    try:
        db_path, project_path, arch_paths, completed = build_database(
            yaml, expect_success=False)
    except RuntimeError as e:
        print(f"  FAIL: {e}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        if 'Traceback (most recent call last):' in combined:
            print(f"  FAIL: Python stack trace instead of a diagnostic:\n{combined}")
            return False
        missing = [needle for needle in needles if needle not in combined]
        if missing:
            print(f"  FAIL: diagnostic missing {missing}:\n{combined}")
            return False
        print("  PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _accepted(label, yaml):
    print(f"{label}: accepted")
    try:
        db_path, project_path, arch_paths = build_database(yaml)
    except RuntimeError as e:
        print(f"  FAIL: {e}")
        return False
    try:
        prj = projectOpen(db_path)
        for blockKey in prj.data['blocks']:
            prj.getBlockData(blockKey)
    except SystemExit as e:
        # A generator diagnostic exits through SystemExit.
        print(f"  FAIL: the generator view of an accepted design failed: {e!r}")
        return False
    finally:
        cleanup([project_path, db_path] + arch_paths)
    print("  PASS")
    return True


def run_all_tests():
    ok = True
    for label, yaml, needles in REJECTED:
        ok = _rejected(label, yaml, needles) and ok
    for label, yaml in ACCEPTED:
        ok = _accepted(label, yaml) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
