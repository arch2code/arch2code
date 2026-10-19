#!/usr/bin/env python3
"""A hasUvm block the UVM testbench cannot drive is rejected at db.

The testbench instantiates the block's HDL verification wrapper, gives every
boundary port an agent of its interface type, and drives every clock and reset
of the block. `validateUvmBlocks` (`pysrc/processYaml.py`) rejects a block
that breaks one of those assumptions, naming the block and, where one is at
fault, the port and its interface type. The boundary covers more than ports:.
A connectionMaps boundary port, a memoryConnections port and a
registerConnections port need no ports: row, and the wrapper still has a pin
group for each. A memoryConnections port has type memory, and a
registerConnections port the type its regType maps to, so each passes the
agent check exactly when that type has an agent. An rw register's status
port, an ext register's external_reg port and a memory port all do, and each
must reach the generated testbench: make gen gives it an agent typedef over
the row's structures, an agent in the env with the role opposite the port,
the testbench module its interface, and the wrapper its X/Z checker. A
one-bit payload pin is a scalar bit, as the simulator shell binds a bool. The
testbench module also declares names of its own: the DUT instance `dut`, the
completion pins, the report server `srv` and one `<clock>_if` per clock,
beside one `<port>_<signal>` pin per port signal and, for a block with a
model, the model DUT's `<port>_model` interface per port, so a port, clock or
reset named like one of them is rejected. A block without a model may name a
port `<port>_model`. A UVM register or memory row holds at most
64 bits, so a register, or a memory whose rows the register model pads to its
decoder stride, over 64 bits at any standalone variant is rejected, and the
padded case names the parameter maxValue that sets the stride. A field is a
member of its uvm_reg subclass and a register or memory a member of the
uvm_reg_block subclass, so a name that would hide a member of that class or of
uvm_object is rejected, once per block whatever the number of variants. A
register's class is `<block>_reg_<register>`, so a register named `block`
would take the register block's class name and is rejected. A memory's
structure members become no fields, so their names are not checked, and a name
is checked only against its own class.

The uvm-blocks fixture holds ubDut, an accepted hasUvm block with two rdy_vld
ports and an apb register bus, and declares ub_no_agent, an interface type of
its own with no agent, for the agent check. Each negative arm edits one rule's violation
into a copy. A block with params whose only variants another project declares
has no standalone variant, so the testbench would have no top for it.
"""

import os
import shutil
import sys
import subprocess
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'uvm-blocks')
ARCH = os.path.join('yaml', 'uvmBlocks.yaml')
CHILD_ARCH = os.path.join('child', 'yaml', 'ubChild.yaml')
CHILD_ROOT_ARCH = os.path.join('yaml', 'uvmBlocksChild.yaml')
ROOT_PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksProject.yaml')
CHILD_ROOT_PROJECT = os.path.join('prj', 'yaml', 'uvmBlocksChildProject.yaml')

WHERE = "Block 'ubDut' (file ../../yaml/uvmBlocks.yaml) declares hasUvm: true"
CHILD_WHERE = "Block 'ubChildDut' (file ../../child/yaml/ubChild.yaml) declares hasUvm: true"

# (name, project file, [(yaml file, edits)], required substrings)
REJECTED = [
    ('hasUvm without hasVl', ROOT_PROJECT,
     [(ARCH, [('        hasVl: true\n        hasUvm: true\n',
       '        hasVl: false\n        hasUvm: true\n')])],
     [WHERE, "has hasVl: false", "Set hasVl: true on 'ubDut'"]),
    ('no declared boundary', ROOT_PROJECT,
     [(ARCH, [('        ports:\n'
       '            in:  { interface: ubStream, direction: dst }\n'
       '            out: { interface: ubStream, direction: src }\n', '')])],
     [WHERE, "declares no ports:"]),
    ('port type without an agent', ROOT_PROJECT,
     [(ARCH, [('interfaceType: rdy_vld', 'interfaceType: ub_no_agent'),
              ('{ structure: ubSt, structureType: data_t }', '{ structure: ubSt, structureType: rdata_t }')])],
     [WHERE, "its port 'in' has interface 'ubStream' of type 'ub_no_agent'",
      "does not declare uvmAgent: true"]),
    ('output clock', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
       '        hasUvm: true\n'
       '        clocks:\n'
       '            clk: { default: true }\n'
       '            clkOut: { direction: output }\n'),
      ('addressGroup: top }', 'addressGroup: top, clocks: { clkOut: ~ } }')])],
     [WHERE, "has output clock 'clkOut'"]),
    ('output reset', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
       '        hasUvm: true\n'
       '        clocks:\n'
       '            clk: { default: true }\n'
       '        resets:\n'
       '            rst_n: { clock: clk, default: true }\n'
       '            rstOut_n: { clock: clk, direction: output }\n'),
      ('addressGroup: top }', 'addressGroup: top, resets: { rstOut_n: ~ } }')])],
     [WHERE, "has output reset 'rstOut_n'"]),
    ('an undeclared connectionMaps port of a type without an agent', ROOT_PROJECT,
     [(ARCH, [('blocks:\n',
               '    ubSide:\n'
               '        desc: "Side channel"\n'
               '        interfaceType: ub_no_agent\n'
               '        structures:\n'
               '            - { structure: ubSt, structureType: rdata_t }\n\n'
               'blocks:\n'),
              ('    ubDut:\n',
               '    ubSideSrc:\n'
               '        desc: "Side source"\n'
               '        hasMdl: true\n'
               '        hasRtl: false\n'
               '    ubCore:\n'
               '        desc: "Core"\n'
               '        hasMdl: true\n'
               '        hasRtl: true\n'
               '    ubDut:\n'),
              ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n'
               '    uSide:   { container: ubTb, instanceType: ubSideSrc, instGroup: top }\n'
               '    uCore:   { container: ubDut, instanceType: ubCore,  instGroup: top }\n'),
              ('    - { interface: ubRegs, src: uCpu, dst: uRouter }\n',
               '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
               '    - { interface: ubSide, src: uSide, srcport: side, dst: uDut, dstport: side, name: sideLink }\n\n'
               'connectionMaps:\n'
               '    - { interface: ubStream, block: ubDut, port: in, direction: dst, instance: uCore, instancePort: in }\n'
               '    - { interface: ubStream, block: ubDut, port: out, direction: src, instance: uCore, instancePort: out }\n'
               '    - { interface: ubSide, block: ubDut, port: side, direction: dst, instance: uCore, instancePort: side }\n')])],
     [WHERE, "its port 'side' has interface 'ubSide' of type 'ub_no_agent'",
      "does not declare uvmAgent: true"]),
    ('a block module named like the UVM testbench', ROOT_PROJECT,
     [(ARCH, [('    ubDut:\n',
               '    ubDut_uvm_tb:\n'
               '        desc: "Block named like the UVM testbench of ubDut"\n'
               '        hasMdl: true\n'
               '        hasRtl: true\n'
               '    ubDut:\n')])],
     ["ubDut_uvm_tb", "the default UVM testbench of block 'ubDut'",
      "block 'ubDut_uvm_tb'"]),
    ('a port named like the DUT instance', ROOT_PROJECT,
     [(ARCH, [('            in:  {', '            dut: {'), ('dstport: in,', 'dstport: dut,')])],
     [WHERE, "its port 'dut' has the name of the DUT instance 'dut' in its UVM testbench module"]),
    ('a port named like a completion pin', ROOT_PROJECT,
     [(ARCH, [('            out: {', '            uvm_done: {'), ('srcport: out,', 'srcport: uvm_done,')])],
     [WHERE, "its port 'uvm_done' has the name of the completion pin 'uvm_done'"]),
    ('a clock named like a completion pin', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
               '        hasUvm: true\n'
               '        clocks:\n'
               '            clk: { default: true }\n'
               '            uvm_errors: {}\n'),
              ('addressGroup: top }', 'addressGroup: top, clocks: { uvm_errors: clk } }')])],
     [WHERE, "its clock 'uvm_errors' has the name of the completion pin 'uvm_errors'"]),
    ('a reset named like a completion pin', ROOT_PROJECT,
     [(ARCH, [('        hasUvm: true\n',
               '        hasUvm: true\n'
               '        clocks:\n'
               '            clk: { default: true }\n'
               '        resets:\n'
               '            rst_n: { clock: clk, default: true }\n'
               '            rtl_dut: { clock: clk }\n'),
              ('addressGroup: top }', 'addressGroup: top, resets: { rtl_dut: rst_n } }')])],
     [WHERE, "its reset 'rtl_dut' has the name of the completion pin 'rtl_dut'"]),
    ('a register connection port named like a completion pin', ROOT_PROJECT,
     [(ARCH, [('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top, addressGroup: top }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: uvm_done, regType: rw, block: ubSink, structure: ubSt, desc: "Sink config" }\n\n'
               'registerConnections:\n'
               '    - { register: uvm_done, block: ubSink, instance: uDut }\n')])],
     [WHERE, "its port 'uvm_done' has the name of the completion pin 'uvm_done'"]),
    ('a port named like the report server variable', ROOT_PROJECT,
     [(ARCH, [('            in:  {', '            srv: {'), ('dstport: in,', 'dstport: srv,')])],
     [WHERE, "its port 'srv' has the name of the report server variable 'srv'"]),
    ('a port named like a clock interface instance', ROOT_PROJECT,
     [(ARCH, [('            out: {', '            clk_if: {'), ('srcport: out,', 'srcport: clk_if,')])],
     [WHERE, "its port 'clk_if' has the name of the a2c_clk_if instance 'clk_if' of clock 'clk'"]),
    ('a port named like another port\'s pin', ROOT_PROJECT,
     [(ARCH, [('            out: {', '            in_vld: {'), ('srcport: out,', 'srcport: in_vld,')])],
     [WHERE, "its port 'in_vld' has the name of the pin 'in_vld' of port 'in'"]),
    ('a port named like the model completion pin', ROOT_PROJECT,
     [(ARCH, [('            out: {', '            model_dut: {'), ('srcport: out,', 'srcport: model_dut,')])],
     [WHERE, "its port 'model_dut' has the name of the completion pin 'model_dut'"]),
    ('a port named like another port\'s model interface', ROOT_PROJECT,
     [(ARCH, [('            out: {', '            in_model: {'), ('srcport: out,', 'srcport: in_model,')])],
     [WHERE, "its port 'in_model' has the name of the model DUT's interface instance 'in_model' of port 'in'"]),
    ('a register wider than 64 bits at one variant', ROOT_PROJECT,
     [(ARCH, [('\ntypes:\n',
               '\nipParameters:\n'
               '    constants:\n'
               '        UB_W: { value: 8, maxValue: 64, desc: "Width knob" }\n\n'
               'types:\n'
               '    ubPT: { width: UB_W, desc: "Parameter-width field" }\n'),
              ('\nstructures:\n',
               '\nstructures:\n'
               '    ubBigSt:\n'
               '        word: { varType: ubWordT, desc: "Low word" }\n'
               '        ext: { varType: ubPT, desc: "Parameter-width extension" }\n'),
              ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n'),
              ('instGroup: top, addressGroup: top }', 'instGroup: top, addressGroup: top, variant: v0 }'),
              ('\nconnections:\n',
               '\nparameters:\n    ubDut:\n        v0: { UB_W: 8 }\n        v1: { UB_W: 40 }\n\n'
               'connections:\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: big, regType: rw, block: ubDut, structure: ubBigSt, desc: "Wide config" }\n')])],
     [WHERE, "its register 'big' is 72 bits wide at variant 'v1'", "UVM_REG_DATA_WIDTH"]),
    ('a memory padded past 64 bits by its row stride', ROOT_PROJECT,
     [(ARCH, [('\ntypes:\n',
               '\nipParameters:\n'
               '    constants:\n'
               '        UB_W: { value: 8, maxValue: 64, desc: "Width knob" }\n\n'
               'types:\n'
               '    ubPT: { width: UB_W, desc: "Parameter-width field" }\n'
               '    ubIdxT: { width: 4, desc: "Table index" }\n'),
              ('\nstructures:\n',
               '\nstructures:\n'
               '    ubBigSt:\n'
               '        word: { varType: ubWordT, desc: "Low word" }\n'
               '        ext: { varType: ubPT, desc: "Parameter-width extension" }\n'
               '    ubIdxSt:\n'
               '        idx: { varType: ubIdxT, desc: "Table index" }\n'),
              ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n'),
              ('instGroup: top, addressGroup: top }', 'instGroup: top, addressGroup: top, variant: v0 }'),
              ('\nconnections:\n',
               '\nparameters:\n    ubDut:\n        v0: { UB_W: 8 }\n\n'
               'connections:\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n\n'
               'memories:\n'
               '    - { memory: tbl, block: ubDut, structure: ubBigSt, wordLines: 4, addressStruct: ubIdxSt, '
               'regAccess: rw, desc: "Table" }\n')])],
     [WHERE, "its memory 'tbl' has 40-bit rows at variant 'v0', which the register model pads to 97 bits",
      "by the decoder's row stride", "the widest row of any variant, 96 bits with UB_W at its maxValue 64",
      "Lower the maxValue of UB_W, narrow its structure", "UVM_REG_DATA_WIDTH"]),
    ('a fixed memory row over 64 bits', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubIdxT: { width: 4, desc: "Table index" }\n    ubWordT:'),
              ('\nstructures:\n',
               '\nstructures:\n'
               '    ubIdxSt:\n'
               '        idx: { varType: ubIdxT, desc: "Table index" }\n'
               '    ubRowSt:\n'
               '        lo: { varType: ubWordT, desc: "Low word" }\n'
               '        hi: { varType: ubWordT, desc: "High word" }\n'
               '        tag: { varType: ubDataT, desc: "Tag" }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n\n'
               'memories:\n'
               '    - { memory: rows, block: ubDut, structure: ubRowSt, wordLines: 4, addressStruct: ubIdxSt, '
               'regAccess: rw, desc: "Table" }\n')])],
     [WHERE, "its memory 'rows' is 72 bits wide.", "Narrow its structure, or clear hasUvm."]),
    ('a register named like a uvm_reg_block member', ROOT_PROJECT,
     [(ARCH, [('{ register: ctrl,', '{ register: mirror,')])],
     [WHERE, "its register 'mirror' has the name of a member of uvm_reg_block"]),
    ('a register whose class is the register block class', ROOT_PROJECT,
     [(ARCH, [('{ register: ctrl,', '{ register: block,')])],
     [WHERE, "has a register named 'block', whose generated class would be 'ubDut_reg_block'",
      "Rename the register, or clear hasUvm."]),
    ('a memory named like a uvm_reg_block member', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubIdxT: { width: 4, desc: "Table index" }\n    ubWordT:'),
              ('\nstructures:\n',
               '\nstructures:\n'
               '    ubIdxSt:\n'
               '        idx: { varType: ubIdxT, desc: "Table index" }\n'
               '    ubMemSt:\n'
               '        predict: { varType: ubDataT, desc: "Row named like a uvm_reg member" }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n\n'
               'memories:\n'
               '    - { memory: get_registers, block: ubDut, structure: ubMemSt, wordLines: 4, addressStruct: ubIdxSt, '
               'regAccess: rw, desc: "Table" }\n')])],
     [WHERE, "its memory 'get_registers' has the name of a member of uvm_reg_block"]),
    ('a field named like a uvm_reg member', ROOT_PROJECT,
     [(ARCH, [('    ubSt:\n        data: {', '    ubSt:\n        predict: {')])],
     [WHERE, "its register 'ctrl' field 'predict' has the name of a member of uvm_reg"]),
    ('a field named like a uvm_object method', ROOT_PROJECT,
     [(ARCH, [('    ubSt:\n        data: {', '    ubSt:\n        print: {')])],
     [WHERE, "its register 'ctrl' field 'print' has the name of a member of uvm_reg"]),
    ('only variants another project declares', CHILD_ROOT_PROJECT,
     [(CHILD_ARCH,
       [('types:\n',
         'ipParameters:\n'
         '    constants:\n'
         '        UB_W: { value: 8, maxValue: 16, desc: "Width knob" }\n\n'
         'types:\n'),
        ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n')]),
      (CHILD_ROOT_ARCH,
       [('instanceType: ubChildDut,  instGroup: top }',
         'instanceType: ubChildDut,  instGroup: top, variant: v0 }'),
        ('connections:\n',
         'parameters:\n    ubChildDut:\n        v0: { UB_W: 8 }\n\nconnections:\n')])],
     [CHILD_WHERE, "has no standalone variant, so it would get no UVM testbench top",
      "Declare a variant of 'ubChildDut' under parameters: in its own project"]),
]

# (name, project file, [(yaml file, edits)])
ACCEPTED = [
    ('rdy_vld ports and an apb register bus', ROOT_PROJECT, []),
    ('a child-owned block with rdy_vld ports', CHILD_ROOT_PROJECT, []),
    ('a block without a model with a port named like another port\'s model interface', ROOT_PROJECT,
     [(ARCH, [('        desc: "DUT under the UVM testbench"\n        hasMdl: true\n',
               '        desc: "DUT under the UVM testbench"\n        hasMdl: false\n'),
              ('            in:  { interface: ubStream, direction: dst }\n'
               '            out: { interface: ubStream, direction: src }\n        registerPorts:',
               '            pix: { interface: ubStream, direction: dst }\n'
               '            pix_model: { interface: ubStream, direction: src }\n        registerPorts:'),
              ('dst: uDut, dstport: in,', 'dst: uDut, dstport: pix,'),
              ('src: uDut, srcport: out,', 'src: uDut, srcport: pix_model,')])]),
    ('a field named like a uvm_reg_block-only member', ROOT_PROJECT,
     [(ARCH, [('    ubSt:\n        data: {', '    ubSt:\n        get_registers: {')])]),
    ('a register named like a uvm_reg-only member', ROOT_PROJECT,
     [(ARCH, [('{ register: ctrl,', '{ register: get_offset,')])]),
    ('a memory structure member named like a uvm_reg member', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubIdxT: { width: 4, desc: "Table index" }\n    ubWordT:'),
              ('\nstructures:\n',
               '\nstructures:\n'
               '    ubIdxSt:\n'
               '        idx: { varType: ubIdxT, desc: "Table index" }\n'
               '    ubMemSt:\n'
               '        predict: { varType: ubDataT, desc: "Row named like a uvm_reg member" }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n\n'
               'memories:\n'
               '    - { memory: tbl, block: ubDut, structure: ubMemSt, wordLines: 4, addressStruct: ubIdxSt, '
               'regAccess: rw, desc: "Table" }\n')])]),
]

# Accepted, and the generated files must hold each line, stripped:
# (name, project file, [(yaml file, edits)], {generated file: [lines]})
GENERATED = [
    ('a status register connection port', ROOT_PROJECT,
     [(ARCH, [('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top, addressGroup: top }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: sinkCfg, regType: rw, block: ubSink, structure: ubSt, desc: "Sink config" }\n\n'
               'registerConnections:\n'
               '    - { register: sinkCfg, block: ubSink, instance: uDut }\n')])],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): [
         'typedef status_agent #(.data_t(ubSt)) sinkCfg_agent_t;',
         'typedef virtual status_if #(.data_t(ubSt)) sinkCfg_vif_t;',
         'sinkCfg_agent_t sinkCfg_agent;',
         'if (!uvm_config_db#(sinkCfg_vif_t)::get(this, "", "sinkCfg", sinkCfg_cfg.vif)) begin',
         'sinkCfg_cfg.role = a2c_uvm_pkg::A2C_SRC;',
         'uvm_config_db#(sinkCfg_config_t)::set(this, "sinkCfg_agent", "cfg", sinkCfg_cfg);',
         'sinkCfg_agent = sinkCfg_agent_t::type_id::create("sinkCfg_agent", this);'],
      os.path.join('uvm', 'ubDut_uvm_tb.sv'): [
         'output bit [$bits(uvmBlocks_package::ubSt)-1:0] sinkCfg_data,',
         'status_if #(.data_t(uvmBlocks_package::ubSt)) sinkCfg();',
         '.sinkCfg_data(sinkCfg.data),',
         'uvm_config_db#(ubDut_uvm_pkg::sinkCfg_vif_t)::set(null, "uvm_test_top.*", "sinkCfg", sinkCfg);']}),
    ('a one-bit status register connection port', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubFlagT: { width: 1, desc: "Flag" }\n    ubWordT:'),
              ('    ubAddrSt:', '    ubFlagSt:\n        flag: { varType: ubFlagT, desc: "Flag" }\n    ubAddrSt:'),
              ('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top, addressGroup: top }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: sinkFlag, regType: rw, block: ubSink, structure: ubFlagSt, desc: "Sink flag" }\n\n'
               'registerConnections:\n'
               '    - { register: sinkFlag, block: ubSink, instance: uDut }\n')])],
     {os.path.join('uvm', 'ubDut_uvm_tb.sv'): [
         'output bit sinkFlag_data,']}),
    ('a memoryConnections port', ROOT_PROJECT,
     [(ARCH, [('    ubWordT:', '    ubIdxT: { width: 4, desc: "Table index" }\n    ubWordT:'),
              ('    ubAddrSt:', '    ubIdxSt:\n        idx: { varType: ubIdxT, desc: "Table index" }\n    ubAddrSt:'),
              ('registers:\n',
               'memories:\n'
               '    - { memory: tbl, block: ubTb, structure: ubSt, wordLines: 16, '
               'addressStruct: ubIdxSt, ports: [port1], desc: "Table" }\n\n'
               'memoryConnections:\n'
               '    - { memory: tbl, block: ubTb, instance: uDut, port: port1 }\n\n'
               'registers:\n')])],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): [
         'typedef memory_agent #(.addr_t(ubIdxSt), .data_t(ubSt)) tbl_agent_t;',
         'typedef virtual memory_if #(.addr_t(ubIdxSt), .data_t(ubSt)) tbl_vif_t;',
         'tbl_cfg.role = a2c_uvm_pkg::A2C_DST;'],
      os.path.join('uvm', 'ubDut_uvm_tb.sv'): [
         'memory_if #(.addr_t(uvmBlocks_package::ubIdxSt), .data_t(uvmBlocks_package::ubSt)) tbl();'],
      os.path.join('verif', 'ubDut_hdl_sv_wrapper.sv'): [
         'memory_xcheck tbl_xcheck (.clk(clk), .rst_n(rst_n), .intf(tbl));']}),
    ('an external register connection port', ROOT_PROJECT,
     [(ARCH, [('    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top }\n',
               '    uSink:   { container: ubTb, instanceType: ubSink,   instGroup: top, addressGroup: top }\n'),
              ('    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n',
               '    - { register: ctrl, regType: rw, block: ubDut, structure: ubSt, desc: "Control" }\n'
               '    - { register: sinkExt, regType: ext, block: ubSink, structure: ubSt, desc: "Sink external" }\n\n'
               'registerConnections:\n'
               '    - { register: sinkExt, block: ubSink, instance: uDut }\n')])],
     {os.path.join('uvm', 'ubDut_uvm_pkg.sv'): [
         'typedef external_reg_agent #(.data_t(ubSt)) sinkExt_agent_t;',
         'typedef virtual external_reg_if #(.data_t(ubSt)) sinkExt_vif_t;',
         'sinkExt_cfg.role = a2c_uvm_pkg::A2C_SRC;'],
      os.path.join('uvm', 'ubDut_uvm_tb.sv'): [
         'external_reg_if #(.data_t(uvmBlocks_package::ubSt)) sinkExt();'],
      os.path.join('verif', 'ubDut_hdl_sv_wrapper.sv'): [
         'external_reg_xcheck sinkExt_xcheck (.clk(clk), .rst_n(rst_n), .intf(sinkExt));']}),
]

# A name that breaks the rule at every variant is reported once:
# (name, project file, [(yaml file, edits)], substring)
REPORTED_ONCE = [
    ('a field named like a uvm_reg member at two variants', ROOT_PROJECT,
     [(ARCH, [('\ntypes:\n',
               '\nipParameters:\n'
               '    constants:\n'
               '        UB_W: { value: 8, maxValue: 16, desc: "Width knob" }\n\n'
               'types:\n'),
              ('    ubSt:\n        data: {', '    ubSt:\n        copy: {'),
              ('        hasUvm: true\n', '        hasUvm: true\n        params: [UB_W]\n'),
              ('instGroup: top, addressGroup: top }', 'instGroup: top, addressGroup: top, variant: v0 }'),
              ('\nconnections:\n',
               '\nparameters:\n    ubDut:\n        v0: { UB_W: 8 }\n        v1: { UB_W: 12 }\n\n'
               'connections:\n')])],
     "its register 'ctrl' field 'copy' has the name of a member of uvm_reg"),
]


def make(project, projectYaml, target):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-j8', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, projectYaml)}', target]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_yaml(project, relative, edits):
    path = os.path.join(project, relative)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            raise RuntimeError(f"fixture no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def check_rejected(project, name, projectYaml, fileEdits, required):
    shutil.copytree(FIXTURE, project)
    for yamlFile, edits in fileEdits:
        edit_yaml(project, yamlFile, edits)
    rc, output = make(project, projectYaml, 'db')
    if rc == 0:
        print(f"  FAIL: {name}: make db accepted the block")
        return False
    if 'Traceback (most recent call last)' in output:
        print(f"  FAIL: {name}: got a Python stack trace instead of a clean rejection")
        print(output)
        return False
    missing = [s for s in required if s not in output]
    if missing:
        print(f"  FAIL: {name}: diagnostic missing substrings: {missing}")
        print(output)
        return False
    print(f"  PASS: {name} is rejected")
    return True


def check_accepted(project, name, projectYaml, fileEdits):
    shutil.copytree(FIXTURE, project)
    for yamlFile, edits in fileEdits:
        edit_yaml(project, yamlFile, edits)
    rc, output = make(project, projectYaml, 'db')
    if rc != 0:
        print(f"  FAIL: {name}: make db rejected the block (rc={rc})")
        print(output)
        return False
    print(f"  PASS: {name} is accepted")
    return True


def check_generated(project, name, projectYaml, fileEdits, expected):
    shutil.copytree(FIXTURE, project)
    for yamlFile, edits in fileEdits:
        edit_yaml(project, yamlFile, edits)
    for target in ('db', 'newmodule', 'gen'):
        rc, output = make(project, projectYaml, target)
        if rc != 0:
            print(f"  FAIL: {name}: make {target} failed (rc={rc})")
            print(output)
            return False
    missing = list()
    for relative, lines in expected.items():
        with open(os.path.join(project, relative)) as f:
            generated = {line.strip() for line in f}
        missing += [f"{relative}: {line}" for line in lines if line not in generated]
    if missing:
        print(f"  FAIL: {name}: generated lines missing:")
        for line in missing:
            print(f"    {line}")
        return False
    print(f"  PASS: {name} is accepted and generated")
    return True


def check_reported_once(project, name, projectYaml, fileEdits, message):
    shutil.copytree(FIXTURE, project)
    for yamlFile, edits in fileEdits:
        edit_yaml(project, yamlFile, edits)
    rc, output = make(project, projectYaml, 'db')
    if rc == 0 or output.count(message) != 1:
        print(f"  FAIL: {name}: make db exited {rc} and reported {message!r} "
              f"{output.count(message)} times, expected a rejection reporting it once")
        print(output)
        return False
    print(f"  PASS: {name} is reported once")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='uvm_blocks_', dir=test_dir)
    ok = True
    try:
        for index, (name, projectYaml, fileEdits) in enumerate(ACCEPTED):
            ok = check_accepted(os.path.join(tmp, f'accept{index}'), name, projectYaml, fileEdits) and ok
        for index, (name, projectYaml, fileEdits, expected) in enumerate(GENERATED):
            ok = check_generated(os.path.join(tmp, f'gen{index}'), name, projectYaml, fileEdits, expected) and ok
        for index, (name, projectYaml, fileEdits, message) in enumerate(REPORTED_ONCE):
            ok = check_reported_once(os.path.join(tmp, f'once{index}'), name, projectYaml,
                                     fileEdits, message) and ok
        for index, (name, projectYaml, fileEdits, required) in enumerate(REJECTED):
            ok = check_rejected(os.path.join(tmp, f'reject{index}'), name, projectYaml,
                                fileEdits, required) and ok
    finally:
        remove_tree(tmp)
    if ok:
        print("\nPASS: hasUvm blocks the UVM testbench cannot drive are rejected at db")
        return 0
    print("\nFAIL: a hasUvm validation rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
