#!/usr/bin/env python3
"""A UVM testbench top's boundary files match the HDL top it instantiates.

The testbench top drives what the DUT samples and samples what it drives, takes
the DUT's clocks and resets as inputs, and adds four completion outputs:
uvm_done, uvm_errors, rtl_dut and model_dut. The VCS port map and the Xcelium shell
`--vlBoundary` writes for it must say so with the DUT's widths at each variant,
or the SystemC side binds mis-sized or mis-directed ports.

A copy of `fixtures/vl-boundary-widths` gains two hasUvm blocks. dutU has an
rdy_vld port each way over the parameterizable pst_a, and a third over the
fixed st_a timed by a second clock, clkB, with its own reset. It is
instantiated at two variants that size pst_a differently. dutV has no model.
The expected pins are computed from the fixture YAML, independently of the
generator, for each HDL top and UVM top. The build manifest must list every
UVM top with its files and the DUTs it can hold, model, rtl and both or, for
dutV, rtl only. dutV sits directly under the top instance, so its top is its
block's default; dutU, under vbwTop, has no default.

Each variant package must bind that variant's parameter values, declare pst_a
from them, and type every port's agent and virtual interface by its payload.
Its env must give each agent its port's clock handle and role, count every
output with a transaction counter, and hold no register model, because
neither block has registers.

Each block has one test package for all its variants, which every one of its
tops lists in the manifest. Its base test waits for every clock's reset
release, and waits for each output's transactions on that output's own clock,
all outputs at once.

Each testbench module must import the block's test package, so the factory
registers its tests, and declare exactly those pins, sizing each vector
payload by `$bits` of its type in the package that declares it, type its
interfaces by the same types, give each clock an a2c_clk_if released by that clock's reset,
bind the HDL top with the pins toward SystemC tied off, and publish every port
and clock in the config_db. A block with a model holds the RTL under
A2C_UVM_RTL_DUT, and with neither DUT define carries each signal across in
the direction the DUT sees it. Under A2C_UVM_BOTH_DUT it holds the RTL on
the port interfaces, carries each signal across through a second interface
per port, <port>_model, and publishes those too. Each branch is checked on
its own: it drives rtl_dut and model_dut to its DUT set and sets a2c_dual_dut
in the config_db. A block without a model always holds the RTL and sets
a2c_dual_dut to 0.

Each block's SystemC wrapper must include the BFM header that declares its
pin bridges, bind every testbench pin, check the shell's payload pin types,
drive each clock at its period and hold each reset low from time 0 until its
own clock releases it. It imports the block's base module only when the block
has a model, and with params its block module as well, because it names the
model class at the factory as a container does for a child typed by its
Config. With a model it carries each port through a BFM of the swapped role
on the port's clock domain, when the run's DUT set holds the model. Its config
must accept both only for a block with a model, set the run's rtlDut and
modelDut from --uvmDut, create the wrapper under the block's name at the
scaffolded variant, and its
registrar must register one wrapper per variant over that variant's shell and
Config.

Under VCS every top's shell is analyzed, whichever top is selected, and each
testbench module imports its block's test package. A dry run at each selected
top must analyze another block's test package once, before that block's
shells and after the variant package its A2C_UVM_PKG names, one of that
block's, and must leave the selected block's test package to the RTL
analysis. Those steps, and each other top's variant package step, carry the
RTL analysis's defines without the selected top's A2C_UVM_PKG.

At each UVM_DUT of dutU_v0, the VCS RTL analysis, the VCS shell of dutU_v0
and the Xcelium DUT library each carry A2C_UVM_RTL_DUT only for rtl and
A2C_UVM_BOTH_DUT only for both. The default UVM_TOPOLOGIES of dutU_v0
builds the model, rtl and both snapshots in that order, and make gen refuses
UVM_DUT=both for dutV, which has no model.

A builder layer's A2C_LAYER_UVM_F_FILES reaches the VCS RTL analysis and the
Xcelium DUT library, each list behind -F, after a2c_uvm.f and before the
top's variant package, test package and testbench module. Each list, and
each file it names relative to its own directory, is a prerequisite of both
steps.
"""

import glob
import os
import re
import shlex
import shutil
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree
from test_build_manifest import parse_manifest
from test_vl_boundary_widths_build import (
    FIXTURE, PORTMAP_TYPES, V0, V1, Design, compare, generate, make, pin_type, read_portmap,
    read_xcelium)


WORK_PREFIX = 'uvm_boundary_pins_'
TOP_YAML = os.path.join('top', 'yaml', 'vbwTop.yaml')
VARIANTS = {'v0': V0, 'v1': V1}

EDITS = [
    ('interfaces:\n',
     'interfaces:\n'
     '  iu:\n'
     '    interfaceType: rdy_vld\n'
     '    desc: "Stream over a parameterizable payload"\n'
     '    structures:\n'
     '      - {structureType: data_t, structure: pst_a}\n'
     '  iuf:\n'
     '    interfaceType: rdy_vld\n'
     '    desc: "Stream over a fixed payload"\n'
     '    structures:\n'
     '      - {structureType: data_t, structure: st_a}\n'),
    ('blocks:\n',
     'blocks:\n'
     '  dutU:\n'
     '    desc: "DUT under a UVM testbench"\n'
     '    params: [P_W, P_N]\n'
     '    hasVl: true\n'
     '    hasRtl: true\n'
     '    hasMdl: true\n'
     '    hasUvm: true\n'
     '    clocks:\n'
     '      clk: {default: true, period: 10}\n'
     '      clkB: {period: 20}\n'
     '    resets:\n'
     '      rst_n: {clock: clk}\n'
     '      rstB_n: {clock: clkB}\n'
     '    ports:\n'
     '      in: {interface: iu, direction: dst}\n'
     '      out: {interface: iu, direction: src}\n'
     '      side: {interface: iuf, direction: src, clock: clkB}\n'
     '  pU:\n'
     '    desc: "Peer of dutU"\n'
     '    params: [P_W, P_N]\n'
     '    hasRtl: false\n'
     '    hasMdl: true\n'
     '    clocks:\n'
     '      clk: {default: true, period: 10}\n'
     '      clkB: {period: 20}\n'
     '    resets:\n'
     '      rst_n: {clock: clk}\n'
     '      rstB_n: {clock: clkB}\n'
     '    ports:\n'
     '      out: {interface: iu, direction: src}\n'
     '      in: {interface: iu, direction: dst}\n'
     '      side: {interface: iuf, direction: dst, clock: clkB}\n'
     '  dutV:\n'
     '    desc: "UVM DUT with no model"\n'
     '    hasVl: true\n'
     '    hasRtl: true\n'
     '    hasMdl: false\n'
     '    hasUvm: true\n'
     '    ports:\n'
     '      vin: {interface: iuf, direction: dst}\n'
     '      vout: {interface: iuf, direction: src}\n'
     '  pV:\n'
     '    desc: "Peer of dutV"\n'
     '    hasRtl: false\n'
     '    hasMdl: true\n'
     '    ports:\n'
     '      vout: {interface: iuf, direction: src}\n'
     '      vin: {interface: iuf, direction: dst}\n'),
    ('instances:\n',
     'instances:\n'
     '  uDutU0: {container: vbwTop, instanceType: dutU, instGroup: top, variant: v0}\n'
     '  uPU0:   {container: vbwTop, instanceType: pU, instGroup: top, variant: v0}\n'
     '  uDutU1: {container: vbwTop, instanceType: dutU, instGroup: top, variant: v1}\n'
     '  uPU1:   {container: vbwTop, instanceType: pU, instGroup: top, variant: v1}\n'
     '  uDutV:  {container: topTb, instanceType: dutV, instGroup: top}\n'
     '  uPV:    {container: topTb, instanceType: pV, instGroup: top}\n'),
    ('connections:\n',
     'connections:\n'
     '  - {src: uPU0, srcport: out, dst: uDutU0, dstport: in, interface: iu, name: iuIn0}\n'
     '  - {src: uDutU0, srcport: out, dst: uPU0, dstport: in, interface: iu, name: iuOut0}\n'
     '  - {src: uDutU0, srcport: side, dst: uPU0, dstport: side, interface: iuf, name: iuSide0}\n'
     '  - {src: uPU1, srcport: out, dst: uDutU1, dstport: in, interface: iu, name: iuIn1}\n'
     '  - {src: uDutU1, srcport: out, dst: uPU1, dstport: in, interface: iu, name: iuOut1}\n'
     '  - {src: uDutU1, srcport: side, dst: uPU1, dstport: side, interface: iuf, name: iuSide1}\n'
     '  - {src: uPV, srcport: vout, dst: uDutV, dstport: vin, interface: iuf, name: ivIn}\n'
     '  - {src: uDutV, srcport: vout, dst: uPV, dstport: vin, interface: iuf, name: ivOut}\n'),
    ('parameters:\n',
     'parameters:\n'
     '  dutU:\n'
     '    v0: {P_W: 5, P_N: 16}\n'
     '    v1: {P_W: 12, P_N: 40}\n'
     '  pU:\n'
     '    v0: {P_W: 5, P_N: 16}\n'
     '    v1: {P_W: 12, P_N: 40}\n'),
]

INVERSE = {'input': 'output', 'output': 'input'}
# Each UVM top by its name stem, with its block and parameter values.
UVM_TOPS = {'dutU_v0': ('dutU', V0), 'dutU_v1': ('dutU', V1), 'dutV': ('dutV', {})}
# Each block's rdy_vld ports in boundary order, with the side the block takes
# and the payload.
UVM_PORTS = {'dutU': [('in', 'dst', 'pst_a'), ('out', 'src', 'pst_a'), ('side', 'src', 'st_a')],
             'dutV': [('vin', 'dst', 'st_a'), ('vout', 'src', 'st_a')]}
HAS_MDL = {'dutU': True, 'dutV': False}
# Each block's default UVM top. uDutV sits directly under the top instance,
# so dutV's wrapper is a DUT top; dutU sits under vbwTop and has none.
DEFAULT_TOPS = {'dutU': None, 'dutV': ['dutV']}
# The package of vbwTop.yaml, which declares st_a.
TOP_PKG = 'vbwTop_package'
# What a clock with no reset port releases its a2c_clk_if with.
NO_RESET = "1'b1"
RDY_VLD = (('vld', 'src'), ('data', 'src'), ('rdy', 'dst'))
PROJECT = 'vbwTop'
# Each block's variant labels and Config structs, in declaration order; '' is
# the variantless top of a block without params.
CONFIGS = {'dutU': {'v0': 'vbwTop_dutUV0Config', 'v1': 'vbwTop_dutUV1Config'}, 'dutV': {'': None}}
# A port timed by a clock other than the block default, with that clock's reset.
PORT_DOMAIN = {('dutU', 'side'): ('clkB', 'rstB_n')}
# A dry run needs the tool variables, not the tool.
VCS_DRY_RUN = ('-n', 'USE_UVM=1', 'USE_VCS=1', 'VCS_HOME=/placeholder/vcs')
XRUN_DRY_RUN = ('-n', 'USE_UVM=1', 'USE_XCELIUM=1', 'XCELIUM_TOOLS=/placeholder/xcelium', 'XRUN_GCC_VERS=placeholder')
COMPLETION_PINS = [('uvm_done', 'output', 1, False), ('uvm_errors', 'output', 32, True),
                   ('rtl_dut', 'output', 1, False), ('model_dut', 'output', 1, False)]


def edit_fixture(work):
    path = os.path.join(work, TOP_YAML)
    with open(path) as f:
        text = f.read()
    for anchor, replacement in EDITS:
        if text.count(anchor) != 1:
            raise RuntimeError(f"fixture no longer carries the single anchor {anchor!r}")
        text = text.replace(anchor, replacement)
    with open(path, 'w') as f:
        f.write(text)


def port_pins(design, block, values):
    """[(pin, direction, width, vector, port, signal, payload)] of a block's
    HDL top ports: per port vld, data and rdy, where the dst side drives only
    rdy."""
    pins = []
    for port, side, payload in UVM_PORTS[block]:
        for signal, driver in RDY_VLD:
            direction = 'output' if driver == side else 'input'
            width = design.width(payload, values) if signal == 'data' else 1
            pins.append((f'{port}_{signal}', direction, width, signal == 'data', port, signal, payload))
    return pins


def hdl_pins(design, block, values):
    return ([pin[:4] for pin in port_pins(design, block, values)]
            + design.clock_reset_pins(block))


def uvm_pins(design, block, values):
    return ([(pin, INVERSE[direction], width, vector)
             for pin, direction, width, vector, *_ in port_pins(design, block, values)]
            + design.clock_reset_pins(block) + COMPLETION_PINS)


def clock_domains(design, block):
    """[(clock, reset)] of a block, each reset the one declared on its clock.
    An omitted clocks: is the implicit clk with rst_n."""
    row = design.blocks[block]
    if 'clocks' not in row:
        return [('clk', 'rst_n')]
    resets = row.get('resets') or {}
    return [(clock, next((reset for reset, attrs in resets.items() if attrs['clock'] == clock), None))
            for clock in row['clocks']]


def check_top(vl, top, expected):
    problems = []
    portmap = os.path.join(vl, f'{top}.portmap')
    if not os.path.exists(portmap):
        return [f"{top}: no boundary files under {vl}"]
    problems += compare(top, 'portmap',
                        [(pin, str(width), *PORTMAP_TYPES[vector])
                         for pin, _, width, vector in expected],
                        read_portmap(portmap))
    problems += compare(top, 'Xcelium shell',
                        [(pin, direction, pin_type(vector, width))
                         for pin, direction, width, vector in expected],
                        read_xcelium(os.path.join(vl, f'{top}_xcelium.h')))
    return problems


def check_boundary_files(work, design):
    vl = os.path.join(work, 'top', '.gen', 'vl')
    problems = []
    for stem, (block, values) in UVM_TOPS.items():
        problems += check_top(vl, f'{stem}_hdl_sv_wrapper', hdl_pins(design, block, values))
        problems += check_top(vl, f'{stem}_uvm_tb', uvm_pins(design, block, values))
    return problems


def check_variant_packages(work, design):
    problems = []
    for stem, (block, values) in UVM_TOPS.items():
        pkg = f'{stem}_uvm_pkg'
        with open(os.path.join(work, 'top', 'uvm', f'{pkg}.sv')) as f:
            lines = [line.strip() for line in f]
        expected = [f'package {pkg};', f'endpackage : {pkg}', 'import rdy_vld_uvm_pkg::*;']
        for port, _, payload in UVM_PORTS[block]:
            expected += [f'typedef rdy_vld_agent #(.data_t({payload})) {port}_agent_t;',
                         f'typedef {port}_agent_t::item_t {port}_item_t;',
                         f'typedef {port}_agent_t::config_t {port}_config_t;',
                         f'typedef virtual rdy_vld_if #(.data_t({payload})) {port}_vif_t;']
        # The env: one agent per port on its own clock domain's handle, and a
        # transaction counter on every output. Neither block has registers, so
        # neither gets a register model.
        expected += [f'class {block}_env extends uvm_env;']
        for clock, _ in clock_domains(design, block):
            expected.append(f'if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "{clock}", {clock}_vif)) begin')
        for port, side, _ in UVM_PORTS[block]:
            clock = PORT_DOMAIN.get((block, port), ('clk',))[0]
            expected += [f'{port}_agent_t {port}_agent;',
                         f'{port}_cfg.clk_vif = {clock}_vif;',
                         f"{port}_cfg.role = a2c_uvm_pkg::{'A2C_SRC' if side == 'dst' else 'A2C_DST'};",
                         f'{port}_agent = {port}_agent_t::type_id::create("{port}_agent", this);']
            if side == 'src':
                expected += [f'a2c_uvm_pkg::a2c_txn_counter #({port}_item_t) {port}_counter;',
                             f'{port}_agent.mon.ap.connect({port}_counter.analysis_export);']
        problems += [f"{pkg}.sv lacks the line {line!r}" for line in expected if line not in lines]
        counters = [line for line in lines if re.match(r'a2c_uvm_pkg::a2c_txn_counter #', line)]
        outputs = [port for port, side, _ in UVM_PORTS[block] if side == 'src']
        if len(counters) != len(outputs):
            problems.append(f"{pkg}.sv declares {len(counters)} transaction counters, expected one per output {outputs}")
        regModel = [line for line in lines if re.search(r'\b(uvm_reg_block|uvm_reg_predictor|regmodel)\b', line)]
        if regModel:
            problems.append(f"{pkg}.sv has a register model for a block without registers: {regModel}")
        localparams = [line for line in lines if line.startswith('localparam ')]
        expectedParams = [f'localparam {param} = {value};' for param, value in values.items()]
        if localparams != expectedParams:
            problems.append(f"{pkg}.sv binds {localparams}, expected {expectedParams}")
        if values:
            if not any(re.match(r'typedef logic\s*\[P_W-1:0\] pty_w;', line) for line in lines):
                problems.append(f"{pkg}.sv does not declare pty_w from P_W")
            if 'pty_w x; //Parameter-width field' not in lines:
                problems.append(f"{pkg}.sv does not type pst_a's field x by pty_w")
            if not any(line.endswith('} pst_a;') for line in lines):
                problems.append(f"{pkg}.sv does not declare pst_a")
    return problems


def check_test_packages(work, design):
    problems = []
    for block in UVM_PORTS:
        name = f'{block}_uvm_test_pkg.sv'
        with open(os.path.join(work, 'top', 'uvm', name)) as f:
            lines = [line.strip() for line in f]
        waits = [line for line in lines if line.endswith('.wait_reset_release();')]
        expected = [f'env.{clock}_vif.wait_reset_release();' for clock, _ in clock_domains(design, block)]
        problems += match(name, 'reset waits', waits, expected)
        counts = [line for line in lines if '.wait_for_count(' in line]
        expected = [f'env.{port}_counter.wait_for_count(env.{PORT_DOMAIN.get((block, port), ("clk",))[0]}_vif, '
                    f'output_deadline_cycles, quiet_cycles);'
                    for port, side, _ in UVM_PORTS[block] if side == 'src']
        problems += match(name, 'output waits', counts, expected)
        # The waits run in one fork, so the outputs are waited on at once.
        if counts and lines[lines.index(counts[0]) - 1] != 'fork':
            problems.append(f"{name} does not fork its output waits")
    return problems


def match(fileName, what, actual, expected):
    if actual == expected:
        return []
    return [f"{fileName} {what} are {actual}, expected {expected}"]


def check_testbenches(work, design):
    problems = []
    for stem, (block, values) in UVM_TOPS.items():
        tb = f'{stem}_uvm_tb'
        pkg = f'{stem}_uvm_pkg'
        hdl = f'{stem}_hdl_sv_wrapper'
        with open(os.path.join(work, 'top', 'uvm', f'{tb}.sv')) as f:
            lines = [line.strip().rstrip(',') for line in f]
        payloadPkg = {payload: pkg if design.parameterizable(payload) else TOP_PKG
                      for *_, payload in UVM_PORTS[block]}
        portPins = port_pins(design, block, values)

        problems += match(f'{tb}.sv', 'imports', [line for line in lines if line.startswith('import ')],
                          ['import uvm_pkg::*;', f'import {block}_uvm_test_pkg::*;'])

        decls = []
        clockResets = {pin for pin, *_ in design.clock_reset_pins(block)}
        for pin, direction, width, vector in uvm_pins(design, block, values):
            if pin in clockResets:
                decls.append(f'{direction} {pin}')
                continue
            spelled = f' [{width - 1}:0]' if vector else ''
            decls.append(f'{direction.ljust(6)} bit{spelled} {pin}')
        for i, (pin, direction, _, vector, _, signal, payload) in enumerate(portPins):
            if signal == 'data' and vector:
                decls[i] = f'{INVERSE[direction].ljust(6)} bit [$bits({payloadPkg[payload]}::{payload})-1:0] {pin}'
        problems += match(f'{tb}.sv', 'port declarations',
                          [line for line in lines if re.match(r'(input|output)\b', line)], decls)

        binds = [f'.{pin}({port}.{signal})' for pin, _, _, _, port, signal, _ in portPins]
        binds += [f'.{pin}({pin})' for pin, *_ in design.clock_reset_pins(block)]

        def flags(rtl, model):
            return [f"assign rtl_dut = 1'b{int(rtl)};", f"assign model_dut = 1'b{int(model)};"]

        def carry(suffix):
            return [f'assign {pin} = {port}{suffix}.{signal};' if direction == 'input'
                    else f'assign {port}{suffix}.{signal} = {pin};'
                    for pin, direction, _, _, port, signal, _ in portPins]

        ties = [f'assign {pin} = ' + ("'0" if vector else "1'b0") + ';'
                for pin, direction, _, vector, *_ in portPins if direction == 'input']
        domains = clock_domains(design, block)
        intfs = [f'rdy_vld_if #(.data_t({payloadPkg[payload]}::{payload})) {port}();'
                 for port, _, payload in UVM_PORTS[block]]
        intfs += [f"a2c_clk_if {clock}_if(.clk({clock}), .rst_n({reset or NO_RESET}));"
                  for clock, reset in domains]
        modelIntfs = [f'rdy_vld_if #(.data_t({payloadPkg[payload]}::{payload})) {port}_model();'
                      for port, _, payload in UVM_PORTS[block]]
        sets = [f'uvm_config_db#({pkg}::{port}_vif_t)::set(null, "uvm_test_top.*", "{port}", {port});'
                for port, *_ in UVM_PORTS[block]]
        sets += [f'uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "{clock}", {clock}_if);'
                 for clock, _ in domains]
        modelSets = [f'uvm_config_db#({pkg}::{port}_vif_t)::set(null, "uvm_test_top.*", "{port}_model", {port}_model);'
                     for port, *_ in UVM_PORTS[block]]
        dual = 'uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_dual_dut", 1\'b{});'

        # Each section's lines: the module text outside any `ifdef, then each
        # branch of the body group and of the config_db group by its DUT.
        expected = {'common': {'assigns': [], 'binds': [], 'intfs': intfs, 'sets': sets}}
        if HAS_MDL[block]:
            expected.update({
                'body both': {'assigns': carry('_model') + flags(True, True), 'binds': binds,
                              'intfs': modelIntfs, 'sets': []},
                'body rtl': {'assigns': ties + flags(True, False), 'binds': binds, 'intfs': [], 'sets': []},
                'body model': {'assigns': carry('') + flags(False, True), 'binds': [], 'intfs': [], 'sets': []},
                'sets both': {'assigns': [], 'binds': [], 'intfs': [], 'sets': modelSets + [dual.format(1)]},
                'sets other': {'assigns': [], 'binds': [], 'intfs': [], 'sets': [dual.format(0)]}})
            groups = [['body both', 'body rtl', 'body model'], ['sets both', 'sets other']]
            expectedDirectives = ['`ifdef A2C_UVM_BOTH_DUT', '`elsif A2C_UVM_RTL_DUT', '`else', '`endif',
                                  '`ifdef A2C_UVM_BOTH_DUT', '`else', '`endif']
        else:
            expected['common'].update({'assigns': ties + flags(True, False), 'binds': binds,
                                       'sets': sets + [dual.format(0)]})
            groups = []
            expectedDirectives = []
        directives = [line for line in lines if line.startswith(('`if', '`el', '`endif'))]
        problems += match(f'{tb}.sv', 'preprocessor directives', directives, expectedDirectives)
        if directives == expectedDirectives:
            sections = {name: [] for name in expected}
            current = 'common'
            group = branch = 0
            for line in lines:
                if line.startswith(('`if', '`el')):
                    current = groups[group][branch]
                    branch += 1
                    continue
                if line.startswith('`endif'):
                    current = 'common'
                    group += 1
                    branch = 0
                    continue
                sections[current].append(line)
            for name, want in expected.items():
                got = {'assigns': [line for line in sections[name] if line.startswith('assign ')],
                       'binds': [line for line in sections[name] if line.startswith('.')],
                       'intfs': [line for line in sections[name] if line.startswith(('rdy_vld_if', 'a2c_clk_if'))],
                       'sets': [line for line in sections[name] if line.startswith('uvm_config_db#')]}
                for what in want:
                    problems += match(f'{tb}.sv', f'{name} {what}', got[what], want[what])
            if HAS_MDL[block]:
                for name in ('body both', 'body rtl'):
                    if f'{hdl} dut (' not in sections[name]:
                        problems.append(f"{tb}.sv {name} does not instantiate {hdl}")

        expected = [f'module {tb}', f'endmodule : {tb}', f'{hdl} dut (', 'run_test();',
                    'uvm_root::get().finish_on_completion = 0;']
        problems += [f"{tb}.sv lacks the line {line!r}" for line in expected if line not in lines]
    return problems


def check_sc_files(work, design):
    problems = []
    uvmDir = os.path.join(work, 'top', 'uvm')
    for block, configs in CONFIGS.items():
        values = VARIANTS.get(next(iter(configs)), {})
        hasParams = block in ('dutU',)
        domains = clock_domains(design, block)

        wrapperFile = f'{block}_uvm_sc_wrapper.h'
        with open(os.path.join(uvmDir, wrapperFile)) as f:
            text = f.read()
        lines = [line.strip() for line in text.splitlines()]
        templateHead = 'template <typename TB_T, typename Config>' if hasParams else 'template <typename TB_T>'
        expected = [templateHead, f'class {block}_uvm_sc_wrapper : public sc_module, public blockBase {{',
                    f'struct {block}_uvm_run {{', 'static inline bool rtlDut = false;',
                    'static inline bool modelDut = false;', '#include "rdy_vld_bfm.h"']
        problems += [f"{wrapperFile} lacks the line {line!r}" for line in expected if line not in lines]
        if bool(re.search(r'^import \S+\.base;$', text, re.M)) != HAS_MDL[block]:
            problems.append(f"{wrapperFile} imports the base module: {not HAS_MDL[block]}, "
                            f"but the block has a model: {HAS_MDL[block]}")
        if bool(re.search(r'^import \S+\.block;$', text, re.M)) != (HAS_MDL[block] and hasParams):
            problems.append(f"{wrapperFile} imports the block module: {not (HAS_MDL[block] and hasParams)}, "
                            f"but the block has a model with params: {HAS_MDL[block] and hasParams}")

        problems += match(wrapperFile, 'shell binds',
                          re.findall(r'^\s*tb_hdl\.(\w+)\(', text, re.M),
                          [pin for pin, *_ in uvm_pins(design, block, values)])

        asserts = re.findall(r'decltype\(TB_T::(\w+)\), (\S+)>,$', text, re.M)
        expectedAsserts = []
        for pin, direction, width, vector, _, signal, payload in port_pins(design, block, values):
            if signal != 'data':
                continue
            port = 'sc_in' if INVERSE[direction] == 'input' else 'sc_out'
            bridge = f'sc_bv<{payload}<Config>::_bitWidth>' if design.parameterizable(payload) \
                else pin_type(vector, width)
            expectedAsserts.append((pin, f'{port}<{bridge}>'))
        problems += match(wrapperFile, 'shell pin type checks', asserts, expectedAsserts)

        for clock, reset in domains:
            expected = [f'void clock_gen_{clock}() {{ clock_gen({clock}, {clock}_half_); }}',
                        f'SC_THREAD(clock_gen_{clock});']
            period = (design.blocks[block].get('clocks') or {}).get(clock, {}).get('period')
            if period is not None:
                expected.append(f'{clock}_half_(sc_time({period}, SC_NS) / 2),')
            if reset is not None:
                expected += [f'{reset}("{reset}", false),', f'SC_THREAD(reset_driver_{reset});']
                if not any(line.startswith(f'void reset_driver_{reset}() {{ reset_driver({reset}, {clock}, ')
                           for line in lines):
                    problems.append(f"{wrapperFile} does not release {reset} on {clock}")
            problems += [f"{wrapperFile} lacks the line {line!r}" for line in expected if line not in lines]
        if 'rst.write(false);' in lines or re.search(r'_n\("\w+", true\)', text):
            problems.append(f"{wrapperFile} releases a reset at time 0 or asserts it after construction")

        bfmRoles = re.findall(r'^\s*(\w+)_bfm_inst = std::make_unique<rdy_vld_(src|dst)_bfm<', text, re.M)
        bfmDomains = re.findall(r'^\s*(\w+)_bfm_inst->clk\((\w+)\);\s*\n\s*\1_bfm_inst->rst_n\((\w+)\);',
                                text, re.M)
        if HAS_MDL[block]:
            problems += match(wrapperFile, 'BFM roles', bfmRoles,
                              [(port, 'src' if side == 'dst' else 'dst') for port, side, _ in UVM_PORTS[block]])
            problems += match(wrapperFile, 'BFM clock domains', bfmDomains,
                              [(port, *PORT_DOMAIN.get((block, port), ('clk', 'rst_n')))
                               for port, *_ in UVM_PORTS[block]])
            impl = f'<{block}<Config>>' if hasParams else ''
            createModel = (f'instanceFactory::createInstance{impl}(name(), "{block}", "{block}", variant, "{PROJECT}"));')
            if createModel not in lines:
                problems.append(f"{wrapperFile} does not create the {block} model")
            if f'if ({block}_uvm_run::modelDut) {{' not in lines:
                problems.append(f"{wrapperFile} does not create the model only when the DUT set holds it")
        elif bfmRoles or 'createInstance' in text:
            problems.append(f"{wrapperFile} creates a model or BFMs for a block without a model")

        configFile = f'{block}UvmConfig.cpp'
        with open(os.path.join(uvmDir, configFile)) as f:
            lines = [line.strip() for line in f]
        expected = ['#if defined(XCELIUM) || defined(VCS)', f'#include "{block}_uvm_sc_wrapper.h"',
                    f'{block}_uvm_run::rtlDut = m_uvmDut == "rtl" || m_uvmDut == "both";',
                    f'{block}_uvm_run::modelDut = m_uvmDut == "model" || m_uvmDut == "both";',
                    'if (m_uvmDut != "model" && m_uvmDut != "rtl" && m_uvmDut != "both") {' if HAS_MDL[block]
                    else 'if (m_uvmDut != "rtl") {',
                    f'instanceFactory::registerInstance("{block}", "uvm");',
                    f'instanceFactory::createInstance("", "{block}", "{block}", m_variant.c_str(), "{PROJECT}");',
                    f'"{block}_uvm",',
                    f'std::string m_uvmDut = "{"model" if HAS_MDL[block] else "rtl"}";',
                    'inline static const std::map<std::string, std::string> s_topVariants = {'
                    + ', '.join('{"%s", "%s"}' % (f'{block}_{v}' if v else block, v) for v in configs) + '};']
        problems += [f"{configFile} lacks the line {line!r}" for line in expected if line not in lines]

        registrarFile = f'{block}UvmRegistrar.cpp'
        with open(os.path.join(uvmDir, registrarFile)) as f:
            text = f.read()
        lines = [line.strip() for line in text.splitlines()]
        stems = [f'{block}_{v}' if v else block for v in configs]
        expected = [f'#include "{stem}_uvm_tb_xcelium.h"' for stem in stems]
        expected += [f'#include "{stem}_uvm_tb.h"' for stem in stems]
        problems += [f"{registrarFile} lacks the line {line!r}" for line in expected if line not in lines]
        registrations = [(blockType, target, *key) for blockType, target, key in zip(
            re.findall(r'registerBlock\(\s*"(\w+)",', text),
            re.findall(r'std::make_shared<(.+)>\(blockName, variant, bbMode\)', text),
            re.findall(r'^\s*"(\w*)", "(\w+)"\);$', text, re.M))]
        problems += match(registrarFile, 'registrations', registrations,
                          [(f'{block}_uvm',
                            f'{block}_uvm_sc_wrapper<{stem}_uvm_tb, {config}>' if config
                            else f'{block}_uvm_sc_wrapper<{stem}_uvm_tb>',
                            variant, PROJECT)
                           for stem, (variant, config) in zip(stems, configs.items())])
    return problems


def check_vcs_shells(work):
    """The -sc_model recipe of a VCS dry run at each selected top: each
    vlogan as (sv files, A2C_UVM_PKG define, -sc_model top, +define+ words),
    in order."""
    problems = []
    uvmDir = os.path.join(work, 'top', 'uvm')
    testSv = {block: os.path.join(uvmDir, f'{block}_uvm_test_pkg.sv') for block in CONFIGS}
    pkgSv = {stem: os.path.join(uvmDir, f'{stem}_uvm_pkg.sv') for stem in UVM_TOPS}
    for selected, (selectedBlock, _) in UVM_TOPS.items():
        result = make(work, 'all', os.path.join('top', 'rundir'),
                      extra=(*VCS_DRY_RUN, f'UVM_TOP={selected}', 'EXTRA_HDL_DEFINES=A2C_PROBE'))
        if result.returncode != 0:
            problems.append(f"UVM_TOP={selected}: make -n failed (rc={result.returncode})\n{result.stderr}")
            continue
        recipes = [line for line in result.stdout.replace('\\\n', ' ').splitlines() if f' -sc_model {selected}_uvm_tb ' in line]
        if len(recipes) != 1:
            problems.append(f"UVM_TOP={selected}: {len(recipes)} -sc_model recipe lines, expected 1")
            continue
        steps = []
        for command in recipes[0].split('&&'):
            tokens = shlex.split(command)
            if not tokens or os.path.basename(tokens[0]) != 'vlogan':
                continue
            define = [t.split('=', 1)[1] for t in tokens if t.startswith('+define+A2C_UVM_PKG=')]
            model = tokens[tokens.index('-sc_model') + 1] if '-sc_model' in tokens else None
            steps.append(([t for t in tokens if t.endswith('.sv')], define, model,
                          [t for t in tokens if t.startswith('+define+')]))
        if any(testSv[selectedBlock] in svs for svs, _, _, _ in steps):
            problems.append(f"UVM_TOP={selected}: the shell step re-analyzes {selectedBlock}'s own test package")
        # The default UVM_DUT is rtl only for a block without a model.
        rtlDut = not HAS_MDL[selectedBlock]
        pkgSteps = [(i, f'{stem}_uvm_pkg') for stem in UVM_TOPS if stem != selected
                    for i, (svs, _, model, _) in enumerate(steps) if model is None and pkgSv[stem] in svs]
        testSteps = []
        for block in CONFIGS:
            if block == selectedBlock:
                continue
            stems = [stem for stem, (b, _) in UVM_TOPS.items() if b == block]
            shells = [i for i, (_, _, model, _) in enumerate(steps) if model in [f'{stem}_uvm_tb' for stem in stems]]
            analyses = [(i, define) for i, (svs, define, _, _) in enumerate(steps) if testSv[block] in svs]
            if len(shells) != len(stems):
                problems.append(f"UVM_TOP={selected}: {len(shells)} -sc_model shells for {block}'s tops {stems}")
            elif (len(analyses) != 1 or analyses[0][0] > min(shells)
                  or analyses[0][1] not in [[f'{stem}_uvm_pkg'] for stem in stems]):
                problems.append(f"UVM_TOP={selected}: {block}'s test package must be analyzed once, before its "
                                f"shells, with A2C_UVM_PKG naming one of {[f'{stem}_uvm_pkg' for stem in stems]}; "
                                f"analyses (step, A2C_UVM_PKG): {analyses}, shells at steps {shells}")
            else:
                i, [named] = analyses[0]
                if not any(j < i and pkg == named for j, pkg in pkgSteps):
                    problems.append(f"UVM_TOP={selected}: {block}'s test package at step {i} names {named}, "
                                    f"which no earlier step analyzes; variant package steps: {pkgSteps}")
                testSteps.append((i, f'{block}_uvm_test_pkg'))
        if len(pkgSteps) != len(UVM_TOPS) - 1:
            problems.append(f"UVM_TOP={selected}: variant package steps {pkgSteps}, expected one per other top")
        # These steps re-analyze the RTL analysis's library sources, so they
        # carry its defines, apart from the selected top's A2C_UVM_PKG.
        for i, what in pkgSteps + testSteps:
            defines = steps[i][3]
            if '+define+A2C_PROBE' not in defines:
                problems.append(f"UVM_TOP={selected}: the {what} step lacks EXTRA_HDL_DEFINES' +define+A2C_PROBE; "
                                f"defines {defines}")
            if f'+define+A2C_UVM_PKG={selected}_uvm_pkg' in defines:
                problems.append(f"UVM_TOP={selected}: the {what} step carries the selected top's "
                                f"+define+A2C_UVM_PKG={selected}_uvm_pkg")
            if '+define+A2C_UVM_BOTH_DUT' in defines:
                problems.append(f"UVM_TOP={selected}: the {what} step carries +define+A2C_UVM_BOTH_DUT, "
                                f"but UVM_DUT is {'rtl' if rtlDut else 'model'}")
            if ('+define+A2C_UVM_RTL_DUT' in defines) != rtlDut:
                problems.append(f"UVM_TOP={selected}: the {what} step {'lacks' if rtlDut else 'carries'} "
                                f"+define+A2C_UVM_RTL_DUT, but UVM_DUT is {'rtl' if rtlDut else 'model'}")
    return problems


def check_both_dut(work):
    """The DUT defines at each UVM_DUT on dutU_v0, on the VCS RTL analysis,
    the VCS shell of dutU_v0 and the Xcelium DUT library; the default
    UVM_TOPOLOGIES; and the refusal of both for dutV. The parse writes a stamp
    directory per top and DUT, so this runs after the checks that count them."""
    problems = []

    def shellOf(tokens):
        return '-sc_model' in tokens and tokens[tokens.index('-sc_model') + 1] == 'dutU_v0_uvm_tb'

    vendors = (('VCS', VCS_DRY_RUN, 'vlogan', {'RTL analysis': lambda t: 'vlogan_rtl.log' in t,
                                               'dutU_v0 shell': shellOf}),
               ('Xcelium', XRUN_DRY_RUN, 'xrun', {'DUT library': lambda t: '-makelib' in t}))
    for dut in ('model', 'rtl', 'both'):
        wanted = {'+define+A2C_UVM_RTL_DUT': dut == 'rtl', '+define+A2C_UVM_BOTH_DUT': dut == 'both'}
        for flow, dryRun, tool, named in vendors:
            result = make(work, 'all', os.path.join('top', 'rundir'), extra=(*dryRun, 'UVM_TOP=dutU_v0', f'UVM_DUT={dut}'))
            if result.returncode != 0:
                problems.append(f"{flow} UVM_DUT={dut}: make -n failed (rc={result.returncode})\n{result.stderr}")
                continue
            steps = [shlex.split(part) for command in result.stdout.replace('\\\n', ' ').splitlines()
                     for part in command.split('&&')
                     if part.split() and os.path.basename(part.split()[0]) == tool]
            for what, isStep in named.items():
                found = [tokens for tokens in steps if isStep(tokens)]
                if len(found) != 1:
                    problems.append(f"{flow} UVM_DUT={dut}: {len(found)} {tool} {what} steps, expected 1")
                    continue
                for define, present in wanted.items():
                    if (define in found[0]) != present:
                        problems.append(f"{flow} UVM_DUT={dut}: the {what} step {'lacks' if present else 'carries'} "
                                        f"{define}; defines {[t for t in found[0] if t.startswith('+define+')]}")
    result = make(work, 'uvm_snapshots', os.path.join('top', 'rundir'), extra=(*XRUN_DRY_RUN, 'UVM_TOP=dutU_v0'))
    duts = re.findall(r'UVM_TOP=dutU_v0 UVM_DUT=(\w+) all', result.stdout)
    if result.returncode != 0 or duts != ['model', 'rtl', 'both']:
        problems.append(f"uvm_snapshots at UVM_TOP=dutU_v0 builds {duts}, expected ['model', 'rtl', 'both'] "
                        f"(rc={result.returncode})\n{result.stderr}")
    result = make(work, 'gen', os.path.join('top', 'rundir'), extra=(*XRUN_DRY_RUN, 'UVM_TOP=dutV', 'UVM_DUT=both'))
    refusal = "UVM_DUT must be one of rtl for UVM_TOP dutV, not 'both'"
    if result.returncode == 0 or refusal not in result.stderr:
        problems.append(f"make gen with UVM_TOP=dutV UVM_DUT=both should stop with {refusal!r} "
                        f"(rc={result.returncode})\n{result.stderr}")
    return problems


def check_layer_uvm_lists(work):
    """Two layer lists on A2C_LAYER_UVM_F_FILES, at the top dutV: their place
    in the vlogan RTL analysis and the xrun DUT library, and their place, with
    the package each names, among the prerequisites of each step's stamp."""
    problems = []
    layerLists = []
    layerPkgs = []
    for layer in ('layerA', 'layerB'):
        listPath = os.path.join(work, f'{layer}_uvm.f')
        pkgPath = os.path.join(work, layer, f'{layer}_uvm_pkg.sv')
        os.makedirs(os.path.dirname(pkgPath), exist_ok=True)
        open(pkgPath, 'w').close()
        with open(listPath, 'w') as f:
            f.write(f'{layer}/{layer}_uvm_pkg.sv\n')
        layerLists.append(listPath)
        layerPkgs.append(pkgPath)
    a2cUvmF = os.path.join(base_dir, 'common', 'systemVerilog', 'uvm', 'a2c_uvm.f')
    uvmDir = os.path.join(work, 'top', 'uvm')
    generated = [os.path.join(uvmDir, name) for name in
                 ('dutV_uvm_pkg.sv', 'dutV_uvm_test_pkg.sv', 'dutV_uvm_tb.sv')]
    order = [a2cUvmF, *layerLists, *generated]
    hook = (f"A2C_LAYER_UVM_F_FILES={' '.join(layerLists)}", 'UVM_TOP=dutV')
    rundir = os.path.join(work, 'top', 'rundir')
    for flow, dryRun, tool, isStep in (
            ('VCS', VCS_DRY_RUN, 'vlogan', lambda t: 'vlogan_rtl.log' in t),
            ('Xcelium', XRUN_DRY_RUN, 'xrun', lambda t: '-makelib' in t)):
        result = make(work, 'all', os.path.join('top', 'rundir'), extra=(*dryRun, *hook))
        if result.returncode != 0:
            problems.append(f"{flow}: make -n failed (rc={result.returncode})\n{result.stderr}")
            continue
        steps = []
        for command in result.stdout.replace('\\\n', ' ').splitlines():
            for part in command.split('&&'):
                words = part.split()
                if not words or os.path.basename(words[0]) != tool:
                    continue
                tokens = shlex.split(part)
                if isStep(tokens):
                    steps.append(tokens)
        if len(steps) != 1:
            problems.append(f"{flow}: {len(steps)} {tool} RTL steps, expected 1")
            continue
        tokens = steps[0]
        found = [tokens.index(t) if tokens.count(t) == 1 else None for t in order]
        if None in found or found != sorted(found):
            problems.append(f"{flow}: {tool} should name {order} once each in this order, "
                            f"got {[t for t in tokens if t in order]}")
        problems += [f"{flow}: {tool} names {path} without -F before it" for path in layerLists
                     if path in tokens and tokens[tokens.index(path) - 1] != '-F']
        # The parse writes each step's options file beside its stamp.
        stamp = ([os.path.join(os.path.dirname(p), 'rtl.vlogan') for p in
                  glob.glob(os.path.join(rundir, 'build*', '**', 'vcs', 'vlogan_opts'), recursive=True)]
                 if flow == 'VCS' else
                 [os.path.join(os.path.dirname(p), 'snapshot') for p in
                  glob.glob(os.path.join(rundir, 'build*', '**', 'xrun', 'xcelium_uvm_dutV_*.d', 'opts'),
                            recursive=True)])
        if len(stamp) != 1:
            problems.append(f"{flow}: expected one {tool} stamp, found {stamp}")
            continue
        database = make(work, stamp[0], os.path.join('top', 'rundir'),
                        extra=('-pq', *dryRun[1:], *hook)).stdout
        rules = [line for line in database.splitlines() if line.startswith(f'{stamp[0]}:')
                 and not re.match(r'\s*[\w.]+\s*[:+?]?=', line[len(stamp[0]) + 1:])]
        if len(rules) != 1:
            problems.append(f"{flow}: expected one rule for {stamp[0]}, found {len(rules)}")
            continue
        problems += [f"{flow}: {stamp[0]} does not depend on {path}" for path in (*layerLists, *layerPkgs)
                     if path not in rules[0].split()]
    return problems


def check_manifest(work):
    root = os.path.join(work, 'top')
    man = parse_manifest(os.path.join(root, '.gen', 'build.mk'))
    uvmDir = os.path.join(root, 'uvm')
    tops = [f'{stem}_uvm_tb' for stem in UVM_TOPS]
    expected = {'A2C_UVM_TOPS': tops, 'A2C_UVM_SRC_DIRS': [uvmDir], 'A2C_UVM_TOP_STEMS': list(UVM_TOPS),
                'A2C_UVM_REGISTRAR_SRC': [os.path.join(uvmDir, f'{block}UvmRegistrar.cpp') for block in CONFIGS]}
    for stem, top in zip(UVM_TOPS, tops):
        expected[f'A2C_UVM_TB_TOP_{stem}'] = [top]
        expected[f'A2C_UVM_PKG_{top}'] = [f'{stem}_uvm_pkg']
        expected[f'A2C_UVM_TESTBENCH_{top}'] = [f'{UVM_TOPS[stem][0]}_uvm']
        expected[f'A2C_UVM_PKG_SV_{top}'] = [os.path.join(uvmDir, f'{stem}_uvm_pkg.sv')]
        expected[f'A2C_UVM_TEST_SV_{top}'] = [os.path.join(uvmDir, f'{UVM_TOPS[stem][0]}_uvm_test_pkg.sv')]
        expected[f'A2C_UVM_TB_SV_{top}'] = [os.path.join(uvmDir, f'{top}.sv')]
        expected[f'A2C_UVM_PORTMAP_{top}'] = [os.path.join(root, '.gen', 'vl', f'{top}.portmap')]
        expected[f'A2C_UVM_DUTS_{top}'] = ['model', 'rtl', 'both'] if HAS_MDL[UVM_TOPS[stem][0]] else ['rtl']
    for block, stems in DEFAULT_TOPS.items():
        expected[f'A2C_UVM_DEFAULT_TOP_{block}'] = stems
    problems = [f"{key} is {man.get(key)}, expected {value}"
                for key, value in expected.items() if man.get(key) != value]
    problems += [f"newmodule did not scaffold {paths[0]}" for key, paths in expected.items()
                 if key.startswith(('A2C_UVM_PKG_SV_', 'A2C_UVM_TEST_SV_', 'A2C_UVM_TB_SV_'))
                 and not os.path.isfile(paths[0])]
    return problems


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM TESTBENCH TOP BOUNDARY PINS")
    print("=" * 70)
    work = tempfile.mkdtemp(prefix=WORK_PREFIX, dir=test_dir)
    ok = True
    try:
        shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
        edit_fixture(work)
        failure = generate(work)
        if failure:
            print(f"  FAIL: {failure}")
            ok = False
        else:
            design = Design(work)
            for name, problems in (('boundary files', check_boundary_files(work, design)),
                                   ('build manifest', check_manifest(work)),
                                   ('variant packages', check_variant_packages(work, design)),
                                   ('test packages', check_test_packages(work, design)),
                                   ('testbench modules', check_testbenches(work, design)),
                                   ('SystemC wrapper, config and registrar', check_sc_files(work, design)),
                                   ('VCS shell analysis', check_vcs_shells(work)),
                                   ('layer agent lists', check_layer_uvm_lists(work)),
                                   ('both DUT', check_both_dut(work))):
                for problem in problems:
                    print(f"  FAIL: {name}: {problem}")
                if not problems:
                    print(f"  PASS: {name}")
                ok = ok and not problems
    finally:
        remove_tree(work)
    if ok:
        print("\nPASS: UVM testbench tops mirror their HDL tops at every variant")
        return 0
    print("\nFAIL")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
