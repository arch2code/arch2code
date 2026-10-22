#!/usr/bin/env python3
"""A connection's maxTransferSize sizes the ports of a testbench's DUT, one
size per port and variant.

A multi-cycle channel splits a burst at its maxTransferSize, and a UVM AXI
agent must not send a burst above the size the model's channel takes. A hasTb
block's testbench builds one channel per port in <block>Channels, and a hasUvm
block's env one agent per port, so each port of such a block takes one size
per variant. A block a fileMap entry with buildsChannels is made for, such as
Pro's tandem wrapper, builds <block>Channels too; a project under base never
merges Pro, so pro/unittest/test_tandem_port_transfer_size.py covers it. A
fileMap entry that sets a key make db does not know, such as buildChannels for
buildsChannels, is rejected rather than read as false. The override on a
connection applies to both ends, and through a connectionMaps entry to the
child port the block port hands down. An end bound
through an adapter keeps its declared interface's size.
`calcPortTransferSizes` (pysrc/processYaml.py) works the size out once per
port and variant; `<block>Channels` and the UVM env's max_transfer_bytes read
it. A port with no connection, or reached only without an override, takes the
interface's value.

`make db` rejects two connections that give one such port different sizes at
one variant, and names both, when the port uses its size: a multi-cycle port,
or a hasUvm block's port whose type sets uvmMaxTransferBytes. Other blocks get
a channel per connection, so one block type may sit on connections of
different sizes. `<block>Channels<Config>` is one class template, so a
parameterized block whose multi-cycle port an override would size differently
per variant is rejected too; an override equal to the interface's size is no
override. An override is a positive number of bytes, a project constant or an
enumerator, resolved as the interface's own field is, or a parameter of the
block that holds the connection, whose channel for it reads that block's
Config; the test compiles one such model. An end takes the holder's binding at
each variant the holder is built at; a parameter the holder does not take is
rejected.

The env sets max_transfer_bytes on the ports of a type whose definition
declares `uvmMaxTransferBytes: true`; a copy that adds a test-only flagged type
checks that the flag, not the type's name, chooses them. That flag and
`uvmIdParam` need `uvmAgent: true`, and `uvmIdParam` names a parameter.

A copy of `fixtures/uvm-blocks` gains an AXI read port rd on ubDut, fed by
uRdWrap, a container whose port hands down to its child uRdCore through a
connectionMaps entry. The connection sets maxTransferSize 64 against the
interface's 256.
"""

import os
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree
import test_error_uvm_blocks as uvmBlocks


ARCH = uvmBlocks.ARCH
PROJECT = uvmBlocks.ROOT_PROJECT

RD_EDITS = [
    ('\nblocks:\n',
     '    ubAxr:\n'
     '        desc: "AXI read into the DUT"\n'
     '        interfaceType: axi_read\n'
     '        multiCycleMode: api_list_size\n'
     '        maxTransferSize: 256\n'
     '        structures:\n'
     '            - { structure: ubAddrSt, structureType: addr_t }\n'
     '            - { structure: ubWordSt, structureType: data_t }\n'
     '\nblocks:\n'),
    ('    ubDut:\n',
     '    ubRdWrap:\n'
     '        desc: "AXI read master container"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '    ubRdCore:\n'
     '        desc: "AXI read master"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '    ubDut:\n'),
    ('            out: { interface: ubStream, direction: src }\n',
     '            out: { interface: ubStream, direction: src }\n'
     '            rd:  { interface: ubAxr, direction: dst }\n'),
    ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
     '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
     '    uRdWrap: { container: ubTb, instanceType: ubRdWrap, instGroup: top }\n'
     '    uRdCore: { container: ubRdWrap, instanceType: ubRdCore, instGroup: top }\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubAxr, src: uRdWrap, srcport: rd, dst: uDut, dstport: rd, name: rdLink, '
     'maxTransferSize: 64 }\n\n'
     'connectionMaps:\n'
     '    - { interface: ubAxr, block: ubRdWrap, port: rd, direction: src, instance: uRdCore, instancePort: rd }\n'),
]

PARAM_EDITS = [
    ('\ntypes:\n',
     '\nipParameters:\n'
     '    constants:\n'
     '        UB_W: { value: 4, maxValue: 16, desc: "Width knob" }\n\n'
     'types:\n'),
    ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n'),
    ('instanceType: ubDut,    instGroup: top, addressGroup: top }',
     'instanceType: ubDut,    instGroup: top, addressGroup: top, variant: v0 }'),
    ('\nconnections:\n',
     '\nparameters:\n'
     '    ubDut:\n'
     '        v0: { UB_W: 4 }\n'
     '        v1: { UB_W: 12 }\n\n'
     'connections:\n'),
]

# A second source and sink pair on its own link, so ubSrc's out and ubSink's
# in are each reached by two connections.
SIDE_EDITS = [
    ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
     '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
     '    uSrc2:   { container: ubTb, instanceType: ubSrc,    instGroup: top }\n'
     '    uSink2:  { container: ubTb, instanceType: ubSink,   instGroup: top }\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubStream, src: uSrc2, srcport: out, dst: uSink2, dstport: in, name: sideLink, '
     'maxTransferSize: 128 }\n'),
]


def override(link, size):
    return (f'name: {link} }}', f'name: {link}, maxTransferSize: {size} }}')


def has_tb(block, desc):
    return (f'    {block}:\n        desc: "{desc}"\n        hasMdl: true\n        hasTb: false\n',
            f'    {block}:\n        desc: "{desc}"\n        hasMdl: true\n        hasTb: true\n')


def constant(name, value):
    return ('\ninterfaces:\n', f'\nconstants:\n    {name}: {{ value: {value}, desc: "Burst size" }}\n\ninterfaces:\n')


SCOPED_SIDES = [has_tb('ubSrc', 'Stream source'), has_tb('ubSink', 'Stream sink')]
RD_CORE_TB = [('    ubRdCore:\n        desc: "AXI read master"\n        hasMdl: true\n        hasTb: false\n',
               '    ubRdCore:\n        desc: "AXI read master"\n        hasMdl: true\n        hasTb: true\n')]
RD_LINK2 = [
    ('instancePort: rd }\n',
     'instancePort: rd }\n'
     '    - { interface: ubAxr, block: ubRdWrap, port: rd2, direction: src, instance: uRdCore, '
     'instancePort: rd }\n'),
    ('maxTransferSize: 64 }\n',
     'maxTransferSize: 64 }\n'
     '    - { interface: ubAxr, src: uRdWrap, srcport: rd2, dst: uSink, dstport: rd2, name: rdLink2, '
     'maxTransferSize: 32 }\n')]
# ubAxr's limit is ubDut's parameter UB_W: 4 bytes at v0, 12 at v1.
PARAM_SIZE = [('        maxTransferSize: 256\n', '        maxTransferSize: UB_W\n')]
NOT_MULTI_CYCLE = [('        multiCycleMode: api_list_size\n', '')]
# ubStream as a multi-cycle interface, so its channels use their size.
MULTI_STREAM = [('        desc: "Stream through the DUT"\n        interfaceType: rdy_vld\n',
                 '        desc: "Stream through the DUT"\n        interfaceType: rdy_vld\n'
                 '        multiCycleMode: api_list_size\n        maxTransferSize: 256\n')]

ENUM = [('\nstructures:\n',
         '\nenums:\n'
         '    ubBurstE:\n'
         '        desc: "Burst sizes"\n'
         '        enum:\n'
         '            - { enumName: UB_BURST_SMALL, value: 16, desc: "Small" }\n'
         '            - { enumName: UB_BURST_BIG, value: 32, desc: "Big" }\n'
         '\nstructures:\n')]

# ubPair takes UB_W and holds prLink, whose override is UB_W, between
# ubPrSrc and ubPrDst, a hasTb block with no parameters. uPair is built at p0,
# where UB_W is 8.
PAIR_EDITS = [
    RD_EDITS[0],
    PARAM_EDITS[0],
    ('    ubDut:\n',
     '    ubPair:\n'
     '        desc: "Container holding a sized link"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '        params: [UB_W]\n'
     '    ubPrSrc:\n'
     '        desc: "Pair source"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '        ports:\n'
     '            rd: { interface: ubAxr, direction: src }\n'
     '    ubPrDst:\n'
     '        desc: "Pair sink"\n'
     '        hasMdl: true\n'
     '        hasTb: true\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '        ports:\n'
     '            rd: { interface: ubAxr, direction: dst }\n'
     '    ubDut:\n'),
    ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
     '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
     '    uPair:   { container: ubTb, instanceType: ubPair,   instGroup: top, variant: p0 }\n'
     '    uPrSrc:  { container: ubPair, instanceType: ubPrSrc, instGroup: top }\n'
     '    uPrDst:  { container: ubPair, instanceType: ubPrDst, instGroup: top }\n'),
    ('\nconnections:\n',
     '\nparameters:\n'
     '    ubPair:\n'
     '        p0: { UB_W: 8 }\n\n'
     'connections:\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubAxr, src: uPrSrc, srcport: rd, dst: uPrDst, dstport: rd, name: prLink, '
     'maxTransferSize: UB_W }\n'),
]
# A second ubDut, whose rd a second ubRdWrap feeds over a 32-byte link.
DUT_TWICE = [
    ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
     '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
     '    uDut2:   { container: ubTb, instanceType: ubDut,    instGroup: top, addressGroup: top }\n'
     '    uRdWrap2: { container: ubTb, instanceType: ubRdWrap, instGroup: top }\n'),
    ('maxTransferSize: 64 }\n',
     'maxTransferSize: 64 }\n'
     '    - { interface: ubAxr, src: uRdWrap2, srcport: rd, dst: uDut2, dstport: rd, name: rdLink2, '
     'maxTransferSize: 32 }\n'),
]
# A second ubPair, built at p1, where UB_W is 16.
PAIR_TWICE = [
    ('instanceType: ubPair,   instGroup: top, variant: p0 }\n',
     'instanceType: ubPair,   instGroup: top, variant: p0 }\n'
     '    uPair2:  { container: ubTb, instanceType: ubPair,   instGroup: top, variant: p1 }\n'),
    ('        p0: { UB_W: 8 }\n', '        p0: { UB_W: 8 }\n        p1: { UB_W: 16 }\n'),
]

# ubSrc drives ubDut's rd directly.
SRC_RD_EDITS = [
    RD_EDITS[0],
    RD_EDITS[2],
    ('    ubSrc:\n        desc: "Stream source"\n        hasMdl: true\n        hasTb: false\n',
     '    ubSrc:\n        desc: "Stream source"\n        hasMdl: true\n        hasTb: false\n'
     '        ports:\n'
     '            out:   { interface: ubStream, direction: src }\n'
     '            rdOut: { interface: ubAxr, direction: src }\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubAxr, src: uSrc, srcport: rdOut, dst: uDut, dstport: rd, name: rdLink, '
     'maxTransferSize: 64 }\n'),
]

# ubRdWrap and ubRdCore take UB_W too. uRdWrap is built at w1, and uRdCore,
# which inherits its container's Config, at w1 as well, so only w1 sees the
# override.
INHERIT_EDITS = [
    ('    ubRdWrap:\n        desc: "AXI read master container"\n',
     '    ubRdWrap:\n        desc: "AXI read master container"\n        params: [UB_W]\n'),
    ('    ubRdCore:\n        desc: "AXI read master"\n',
     '    ubRdCore:\n        desc: "AXI read master"\n        params: [UB_W]\n'),
    ('instanceType: ubRdWrap, instGroup: top }', 'instanceType: ubRdWrap, instGroup: top, variant: w1 }'),
    ('instanceType: ubRdCore, instGroup: top }',
     'instanceType: ubRdCore, instGroup: top, inheritContainerParam: true }'),
    ('        v1: { UB_W: 12 }\n',
     '        v1: { UB_W: 12 }\n'
     '    ubRdWrap:\n'
     '        w0: { UB_W: 4 }\n'
     '        w1: { UB_W: 8 }\n'
     '    ubRdCore:\n'
     '        c0: { UB_W: 4 }\n'),
]

# ubDut's rd port declares ubAxrB, a 128-byte copy of ubAxr, so the 64-byte
# connection reaches it through an adapter.
ADAPTED_EDITS = [
    ('\nblocks:\n',
     '    ubAxrB:\n'
     '        desc: "AXI read as the DUT declares it"\n'
     '        interfaceType: axi_read\n'
     '        multiCycleMode: api_list_size\n'
     '        maxTransferSize: 128\n'
     '        structures:\n'
     '            - { structure: ubAddrSt, structureType: addr_t }\n'
     '            - { structure: ubWordSt, structureType: data_t }\n'
     '\nblocks:\n'),
    ('            rd:  { interface: ubAxr, direction: dst }\n', '            rd:  { interface: ubAxrB, direction: dst }\n'),
]

# ubSpare is a library container no instance reaches. Its 128-byte link would
# give ubSrc's out a second size if it counted.
UNREACHED_EDITS = [
    ('    ubDut:\n',
     '    ubSpare:\n'
     '        desc: "Container nothing instantiates"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '    ubDut:\n'),
    ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
     '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
     '    uSpSrc:  { container: ubSpare, instanceType: ubSrc,  instGroup: top }\n'
     '    uSpSink: { container: ubSpare, instanceType: ubSink, instGroup: top }\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubStream, src: uSpSrc, srcport: out, dst: uSpSink, dstport: in, name: spareLink, '
     'maxTransferSize: 128 }\n'),
]


def flag_type(name, lines):
    return [('interface_defs:\n',
             'interface_defs:\n'
             f'  {name} :\n'
             '    timing: elastic\n'
             '    backpressure: { default: true, overridable: false }\n'
             + lines +
             '    parameters :\n'
             '      data_t : { datatype : struct }\n'
             '    signals:\n'
             '      vld : bool\n'
             '      rdy : bool\n'
             '      data : data_t\n'
             '    modports :\n'
             '      src :\n'
             '        inputs : [\'rdy\']\n'
             '        outputs: [\'vld\', \'data\']\n'
             '      dst :\n'
             '        inputs : [\'vld\', \'data\']\n'
             '        outputs: [\'rdy\']\n'
             '    sc_channel :\n'
             f'      type : \'{name}\'\n'
             '      multicycle_types : []\n')]


# A type with no parameters: section at all.
def unparameterized_type(name, lines):
    return [('interface_defs:\n',
             'interface_defs:\n'
             f'  {name} :\n'
             '    timing: elastic\n'
             '    backpressure: { default: true, overridable: false }\n'
             + lines +
             '    signals:\n'
             '      vld : bool\n'
             '      rdy : bool\n'
             '    modports :\n'
             '      src :\n'
             '        inputs : [\'rdy\']\n'
             '        outputs: [\'vld\']\n'
             '      dst :\n'
             '        inputs : [\'vld\']\n'
             '        outputs: [\'rdy\']\n'
             '    sc_channel :\n'
             f'      type : \'{name}\'\n'
             '      multicycle_types : []\n')]


IF_YAML = os.path.join('yaml', 'ubIf.yaml')

REJECTED = [
    ('two overrides on one multi-cycle port of a testbench block at one variant', PROJECT,
     [(ARCH, MULTI_STREAM + SIDE_EDITS + SCOPED_SIDES + [override('inLink', 64)])],
     ["Port 'out' of block 'ubSrc' is reached by connections that give it different transfer sizes",
      "64 bytes from connection 'inLink'", "128 bytes from connection 'sideLink'",
      "Port 'in' of block 'ubSink' is reached by connections",
      "connection 'outLink'", "the interface's maxTransferSize",
      "Block 'ubSrc' has hasTb, so its testbench builds one channel and one agent for the port",
      "give these connections the same maxTransferSize, or none"]),
    ('two overrides on a port that is not multi-cycle, whose UVM agent takes the size', PROJECT,
     [(ARCH, RD_EDITS + NOT_MULTI_CYCLE + DUT_TWICE)],
     ["Port 'rd' of block 'ubDut' is reached by connections that give it different transfer sizes",
      "32 bytes from connection 'rdLink2'", "64 bytes from connection 'rdLink'"]),
    ('two overrides meeting through a connectionMaps entry', PROJECT,
     [(ARCH, RD_EDITS + RD_CORE_TB + RD_LINK2)],
     ["Port 'rd' of block 'ubRdCore' is reached by connections",
      "64 bytes from connection 'rdLink'", "32 bytes from connection 'rdLink2'",
      "through connectionMaps entry for port 'rd' of block 'ubRdWrap'",
      "through connectionMaps entry for port 'rd2' of block 'ubRdWrap'"]),
    ('a multi-cycle port of a parameterized block sized differently per variant', PROJECT,
     [(ARCH, RD_EDITS + PARAM_EDITS)],
     ["Port 'rd' of parameterized block 'ubDut' has transfer size 64 bytes at variant 'v0', "
      "256 bytes at variant 'v1'",
      "The override comes from connection 'rdLink'", "at variant 'v0'",
      "ubDutChannels is one class template over Config",
      "Remove the override, or replace it by binding the interface's maxTransferSize to a parameter of 'ubDut'"]),
    ('an override against a parameter-bound multi-cycle size', PROJECT,
     [(ARCH, RD_EDITS + PARAM_EDITS + PARAM_SIZE)],
     ["Port 'rd' of parameterized block 'ubDut' has transfer size 64 bytes at variant 'v0', "
      "12 bytes at variant 'v1'"]),
    ('an override reaching an inheriting child at its container\'s variant', PROJECT,
     [(ARCH, RD_EDITS + PARAM_EDITS + RD_CORE_TB + INHERIT_EDITS + PARAM_SIZE)],
     ["Port 'rd' of parameterized block 'ubRdCore' has transfer size 4 bytes at variant 'w0', "
      "64 bytes at variant 'w1'",
      "through connectionMaps entry for port 'rd' of block 'ubRdWrap'"]),
    ('an undeclared constant as an override', PROJECT,
     [(ARCH, [override('inLink', 'UB_X')])],
     ["Constant or enum 'UB_X' is not declared"]),
    ('a parameter the block holding the connection does not take, as an override', PROJECT,
     [(ARCH, RD_EDITS + PARAM_EDITS + [('maxTransferSize: 64 }', 'maxTransferSize: UB_W }')])],
     ["The connection 'rdLink'",
      "sets maxTransferSize 'UB_W', which is a parameter that block 'ubTb', which holds the connection, does "
      "not take", "an override is a number of bytes, a project constant, or a parameter of 'ubTb'",
      "Binding the interface's maxTransferSize to a parameter instead sizes every port of interface 'ubAxr'",
      "Found 1 Error."]),
    ('a holder\'s parameter that gives a testbench port two sizes across the holder\'s variants', PROJECT,
     [(ARCH, PAIR_EDITS + PAIR_TWICE)],
     ["Port 'rd' of block 'ubPrDst' is reached by connections that give it different transfer sizes",
      "8 bytes from connection 'prLink'", "at variant 'p0' of block 'ubPair', its maxTransferSize",
      "16 bytes from connection 'prLink'", "at variant 'p1' of block 'ubPair', its maxTransferSize"]),
    ('a negative override', PROJECT,
     [(ARCH, [override('inLink', -8)])],
     ["connection 'inLink'", "sets maxTransferSize '-8', which is -8 bytes at port 'in' of block 'ubDut'",
      "An override is a positive number of bytes"]),
    ('a constant override of zero', PROJECT,
     [(ARCH, [constant('UB_NONE', 0), override('inLink', 'UB_NONE')])],
     ["connection 'inLink'", "sets maxTransferSize 'UB_NONE', which is 0 bytes at port 'in' of block 'ubDut'"]),
    ('uvmMaxTransferBytes on a type without an agent', PROJECT,
     [(IF_YAML, flag_type('ub_mtb', '    uvmMaxTransferBytes: true\n'))],
     ["Interface type 'ub_mtb'", "sets uvmMaxTransferBytes but not uvmAgent: true"]),
    ('uvmIdParam on a type without an agent', PROJECT,
     [(IF_YAML, flag_type('ub_idp', '    uvmIdParam: data_t\n'))],
     ["Interface type 'ub_idp'", "sets uvmIdParam but not uvmAgent: true"]),
    ('uvmIdParam naming no parameter', PROJECT,
     [(IF_YAML, flag_type('ub_idq', '    uvmAgent: true\n    uvmIdParam: id_t\n'))],
     ["Interface type 'ub_idq'", "sets uvmIdParam 'id_t', which is not one of its parameters"]),
    ('uvmIdParam on a type with no parameters', PROJECT,
     [(IF_YAML, unparameterized_type('ub_idn', '    uvmAgent: true\n    uvmIdParam: id_t\n'))],
     ["Interface type 'ub_idn'", "sets uvmIdParam 'id_t', which is not one of its parameters"]),
    ('a fileMap entry with a misspelled buildsChannels', PROJECT,
     [(PROJECT, [('    fileCopyrightStatement: ""\n',
                  '    fileCopyrightStatement: ""\n'
                  '    fileMap:\n'
                  '        ubWrap: { name: "Wrap", ext: {hdr: "h"}, cond: {hasTb: true}, mode: block, basePath: base, '
                  'langDomain: sc, buildChannels: true, desc: "a wrapper that builds <block>Channels" }\n')])],
     ["fileGeneration.fileMap entry 'ubWrap' in project", "sets 'buildChannels', which is not a fileMap key",
      "the keys are basePath, blockDir, buildsChannels,"]),
    ('an override that is not a whole number, reported once', PROJECT,
     [(ARCH, [override('inLink', 1.5)])],
     ["The connection 'inLink'", "sets maxTransferSize '1.5', which is not a whole number of bytes",
      "Found 1 Error."]),
]

ACCEPTED = [
    ('connections agreeing on the size of each port they reach', PROJECT,
     [(ARCH, SIDE_EDITS + SCOPED_SIDES + [override('inLink', 128), override('outLink', 128)])]),
    ('one block type, two instances, two connection sizes, no hasTb and no hasUvm', PROJECT,
     [(ARCH, SIDE_EDITS + [override('inLink', 64)])]),
    ('an override equal to the interface\'s parameter-bound size where it reaches the port', PROJECT,
     [(ARCH, RD_EDITS + PARAM_EDITS + PARAM_SIZE + [('maxTransferSize: 64 }\n', 'maxTransferSize: 4 }\n')])]),
    ('a connection in a container no instance reaches', PROJECT,
     [(ARCH, MULTI_STREAM + UNREACHED_EDITS + SCOPED_SIDES + [override('inLink', 64)])]),
    ('two overrides on one port of a testbench block whose interface is not multi-cycle', PROJECT,
     [(ARCH, SIDE_EDITS + SCOPED_SIDES + [override('inLink', 64)])]),
]

# ub_burst, a test-only type with no companion files, carries
# uvmMaxTransferBytes, so the env sets max_transfer_bytes on its port too, and
# uvmIdParam tag_t, which the port leaves unbound, so it sets id_unbound: the
# definition chooses the ports, not the type's name.
BURST_TYPE_EDITS = [
    ('interface_defs:\n',
     'interface_defs:\n'
     '  ub_burst :\n'
     '    timing: elastic\n'
     '    backpressure: { default: true, overridable: false }\n'
     '    uvmAgent: true\n'
     '    uvmMaxTransferBytes: true\n'
     '    uvmIdParam: tag_t\n'
     '    parameters :\n'
     '      data_t : { datatype : struct }\n'
     '      tag_t : { datatype : type, optional : true, defaultWidth : 4 }\n'
     '    signals:\n'
     '      vld : bool\n'
     '      rdy : bool\n'
     '      data : data_t\n'
     '    modports :\n'
     '      src :\n'
     '        inputs : [\'rdy\']\n'
     '        outputs: [\'vld\', \'data\']\n'
     '      dst :\n'
     '        inputs : [\'vld\', \'data\']\n'
     '        outputs: [\'rdy\']\n'
     '    sc_channel :\n'
     '      type : \'ub_burst\'\n'
     '      multicycle_types : []\n'),
]
BURST_EDITS = [
    ('\nblocks:\n',
     '    ubBurst:\n'
     '        desc: "Burst stream into the DUT"\n'
     '        interfaceType: ub_burst\n'
     '        maxTransferSize: 48\n'
     '        structures:\n'
     '            - { structure: ubSt, structureType: data_t }\n'
     '\nblocks:\n'),
    ('            out: { interface: ubStream, direction: src }\n',
     '            out: { interface: ubStream, direction: src }\n'
     '            bst: { interface: ubBurst, direction: dst }\n'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubBurst, src: uSrc, srcport: bst, dst: uDut, dstport: bst, name: bstLink }\n'),
]

GENERATED = [
    ('a flagged type that is not AXI gets max_transfer_bytes and id_unbound', PROJECT,
     [(os.path.join('yaml', 'ubIf.yaml'), BURST_TYPE_EDITS), (ARCH, BURST_EDITS)],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): ['bst_cfg.max_transfer_bytes = 48;',
                                                 'bst_cfg.id_unbound = 1;']}),
    ('the override sizes the agent and the channels of the DUT, and blocks without a testbench keep the '
     'interface\'s size', PROJECT,
     [(ARCH, RD_EDITS)],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 64;'],
      os.path.join('base', 'ubDutBase.cppm'): [
          ',rd(("rd"+name).c_str(), srcName, "api_list_size", 64, "")'],
      os.path.join('base', 'ubRdWrapBase.cppm'): [
          'rd(("rd"+name).c_str(), srcName, "api_list_size", 256, "")'],
      os.path.join('base', 'ubRdCoreBase.cppm'): [
          'rd(("rd"+name).c_str(), srcName, "api_list_size", 256, "")']}),
    ('the override reaches a testbench block through a connectionMaps entry', PROJECT,
     [(ARCH, RD_EDITS + RD_CORE_TB)],
     {os.path.join('base', 'ubRdCoreBase.cppm'): [
          'rd(("rd"+name).c_str(), srcName, "api_list_size", 64, "")']}),
    ('a constant override resolves as the interface\'s field does', PROJECT,
     [(ARCH, RD_EDITS + [constant('UB_RD_BURST', 32),
                         ('maxTransferSize: 64 }\n', 'maxTransferSize: UB_RD_BURST }\n')])],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 32;'],
      os.path.join('base', 'ubDutBase.cppm'): [
          ',rd(("rd"+name).c_str(), srcName, "api_list_size", 32, "")']}),
    ('an enumerator override resolves as a constant does', PROJECT,
     [(ARCH, RD_EDITS + ENUM + [('maxTransferSize: 64 }\n', 'maxTransferSize: UB_BURST_BIG }\n')])],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 32;'],
      os.path.join('base', 'ubDutBase.cppm'): [
          ',rd(("rd"+name).c_str(), srcName, "api_list_size", 32, "")']}),
    ('a parameter of the block holding the connection sizes the holder\'s channel and the testbench end alike',
     PROJECT,
     [(ARCH, PAIR_EDITS)],
     {os.path.join('model', 'ubPair.cppm'): [',rd("ubPrDst_rd", "ubPrSrc", "api_list_size", UB_W, "")'],
      os.path.join('base', 'ubPrDstBase.cppm'): [
          'rd(("rd"+name).c_str(), srcName, "api_list_size", 8, "")']}),
    ('an override and a parameter-bound size, per variant', PROJECT,
     [(ARCH, SRC_RD_EDITS + PARAM_EDITS + PARAM_SIZE + NOT_MULTI_CYCLE)],
     {os.path.join('uvm', 'ubDut_v0_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 64;'],
      os.path.join('uvm', 'ubDut_v1_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 12;']}),
    ('a container port the connectionMaps entry infers, on an interface with a size but no multiCycleMode',
     PROJECT,
     [(ARCH, RD_EDITS + NOT_MULTI_CYCLE)],
     {os.path.join('base', 'ubRdWrapBase.cppm'): ['rd(("rd"+name).c_str(), srcName)']}),
    ('an end bound through an adapter keeps its declared interface\'s size', PROJECT,
     [(ARCH, RD_EDITS + ADAPTED_EDITS)],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): ['rd_cfg.max_transfer_bytes = 128;'],
      os.path.join('base', 'ubDutBase.cppm'): [
          ',rd(("rd"+name).c_str(), srcName, "api_list_size", 128, "")']}),
]

# The holder's channel takes its size from the holder's Config, so the model
# must compile as well as generate.
COMPILED = [
    ('a parameter of the block holding the connection as the size of the holder\'s channel', PROJECT,
     [(ARCH, PAIR_EDITS)]),
]


def check_compiled(project, name, projectYaml, fileEdits):
    if not uvmBlocks.check_generated(project, name, projectYaml, fileEdits, {}):
        return False
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-j8', '-C', os.path.join(project, 'rundir'), f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, projectYaml)}', 'CCACHE_DISABLE=1', 'all']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=env)
    if result.returncode != 0 or not os.path.exists(os.path.join(project, 'rundir', 'build', 'run')):
        print(f"  FAIL: {name}: the model did not compile (rc={result.returncode})")
        print((result.stdout + result.stderr)[-4000:])
        return False
    print(f"  PASS: {name} compiles")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='port_transfer_size_', dir=test_dir)
    ok = True
    try:
        for index, (name, projectYaml, fileEdits) in enumerate(ACCEPTED):
            ok = uvmBlocks.check_accepted(os.path.join(tmp, f'accept{index}'), name, projectYaml,
                                          fileEdits) and ok
        for index, (name, projectYaml, fileEdits, expected) in enumerate(GENERATED):
            ok = uvmBlocks.check_generated(os.path.join(tmp, f'gen{index}'), name, projectYaml,
                                           fileEdits, expected) and ok
        for index, (name, projectYaml, fileEdits) in enumerate(COMPILED):
            ok = check_compiled(os.path.join(tmp, f'compile{index}'), name, projectYaml, fileEdits) and ok
        for index, (name, projectYaml, fileEdits, required) in enumerate(REJECTED):
            ok = uvmBlocks.check_rejected(os.path.join(tmp, f'reject{index}'), name, projectYaml,
                                          fileEdits, required) and ok
    finally:
        remove_tree(tmp)
    if ok:
        print("\nPASS: a connection's maxTransferSize sizes the ports of a testbench's DUT, one size per port and variant")
        return 0
    print("\nFAIL: a port transfer size rule is wrong")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
