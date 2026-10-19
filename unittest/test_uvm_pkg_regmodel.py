#!/usr/bin/env python3
"""Each variant package holds a register model that reads and writes the bits
the RTL decoder serves, and an env that wires every port's agent.

A register class that disagrees with the decoder on its width, a field's
position or its access fails every register test against the RTL, and a
uvm_mem that steps by a different stride from the decoder reads the wrong row.
UVM steps a memory by ceil(n_bits / 32) bus words, so a row whose stride is 8
bytes needs n_bits over 32 even when the row is narrower. The decoder flops
padding like any field, so padding fields are modelled with the register's
access and reset. The design drives ro and ext registers, so both are volatile.

uvm_mem accepts only RW or RO, so a write-only memory is RW with WO map
rights. With one map UVM reports its access as RW, and the built-in memory
sequences would read it back, so the register block must set NO_MEM_TESTS on
it. A padded row holds bits the decoder does not store, so a padded memory
that is not write-only must get NO_MEM_WALK_TEST.

The fixture is the two-variant register fixture of test_uvm_register_view.py,
plus a default value on the padded register, an ext register with a default
value, and two memories whose worst-case row is 40 bits, so their stride is 8
bytes while both variants' rows are at most 32 bits: wtbl is write-only and
ptbl is rw. ubDut also masters a second APB bus through port mst. Offsets
come from the view, which test_uvm_register_view.py checks against the
firmware header. Everything else is worked out here from the YAML.

The env must create one agent per port with its config, one transaction
counter for the DUT stream output and none for the input or either APB port,
and an explicit predictor on the register bus agent's monitor with
auto-predict off. Its register model starts at its reset values. Every
agent's config carries the role opposite its port's direction, so the agent
on mst, where the DUT is the master, is A2C_DST and the register bus agent
A2C_SRC, and the env sets no agent passive. The AXI port rdM binds no id_t,
so its config sets id_unbound. rdS binds one, and no other port's config sets
it.

In Mode B, which the env reads from the testbench's a2c_dual_dut, the env
also fetches every port's <port>_model interface into its config's model_vif,
gives each counter the model monitor's stream, lists every agent's model_cmp
that is set, marks the counted ports' comparators as counted, and creates the
midstream guard over the counters and comparators. The guard hears every
write on the DUT lane's register bus through a2c_reg_write_subscriber, which
resolves it against the register map. None of this happens outside Mode B:
the vif fetches, the guard and everything connect_phase adds sit under
dual_dut, so a Mode A or rtl run builds and connects what it did before. The
env's model_stable_point() calls stable_point() on each listed comparator
with auto_stable set.

An agent whose port binds no parameter is spelled with no #(), which no port
of the fixture exercises, so the typedef lines are also checked on a port
built here.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from _tmp_helpers import remove_tree
from pysrc.processYaml import projectOpen
import test_uvm_register_view as regView
from templates.systemVerilog import uvmPkg


EXTRA_EDITS = [
    ('    ubAlignBaseSt:\n',
     '    ubMemSt:\n'
     '        x: { varType: ubPT, desc: "First parameter-width member" }\n'
     '        y: { varType: ubPT, desc: "Second parameter-width member" }\n'
     '        z: { varType: ubDataT, desc: "Fixed member" }\n'
     '    ubAlignBaseSt:\n'),
    ('register: aligned, regType: rw, block: ubDut, structure: ubAlignSt,',
     'register: aligned, regType: rw, block: ubDut, structure: ubAlignSt, defaultValue: 0x030201,'),
    ('\nmemories:\n',
     '    - { register: ext, regType: ext, block: ubDut, structure: ubSt, defaultValue: 3, desc: "External" }\n'
     '\nmemories:\n'
     '    - { memory: wtbl, block: ubDut, structure: ubMemSt, wordLines: 4, addressStruct: ubIdxSt, '
     'regAccess: wo, desc: "Write-only table on an 8-byte stride" }\n'
     '    - { memory: ptbl, block: ubDut, structure: ubMemSt, wordLines: 4, addressStruct: ubIdxSt, '
     'regAccess: rw, desc: "Padded table on an 8-byte stride" }\n'),
]

# ubDut masters a second APB bus, port mst, served by uSlave.
MASTER_EDITS = [
    ('            out: { interface: ubStream, direction: src }\n',
     '            out: { interface: ubStream, direction: src }\n'
     '            mst: { interface: ubRegs, direction: src }\n'),
    ('    ubRouter:\n        desc: "APB register decoder"',
     '    ubSlave:\n'
     '        desc: "APB slave the DUT masters"\n'
     '        hasMdl: true\n'
     '        hasTb: false\n'
     '        hasRtl: false\n'
     '        hasVl: false\n'
     '    ubRouter:\n        desc: "APB register decoder"'),
    ('    uRouter: { container: ubTb',
     '    uSlave:  { container: ubTb, instanceType: ubSlave,  instGroup: top }\n'
     '    uRouter: { container: ubTb'),
    ('    - { interface: ubRegs, src: uCpu, dst: uRouter }',
     '    - { interface: ubRegs, src: uCpu, dst: uRouter }\n'
     '    - { interface: ubRegs, src: uDut, srcport: mst, dst: uSlave, name: mstLink }'),
]

EXTRA_EDITS = EXTRA_EDITS + MASTER_EDITS

UB_W = regView.UB_W
UB_D = regView.UB_D


def edit_fixture(project):
    regView.edit_fixture(project)
    path = os.path.join(project, regView.ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in EXTRA_EDITS:
        if text.count(old) != 1:
            raise RuntimeError(f"fixture no longer carries the single anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def make(project, target):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-j8', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           f'A2C_PRJ_YAML={os.path.join(project, regView.PROJECT)}', target]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)


def configure(field, width, lsb, access, volatile, reset, isRand):
    return (f'{field}.configure(this, {width}, {lsb}, "{access}", {volatile}, '
            f"{width}'h{reset:x}, 1, {isRand}, 0);")


def expected_regmodel(variant, offsets):
    w = UB_W[variant]
    lines = [
        'class ubDut_reg_ctrl extends uvm_reg;',
        'super.new(name, 8, UVM_NO_COVERAGE);',
        configure('data', 8, 0, 'RW', 0, 0, 1),
        'class ubDut_reg_cfg extends uvm_reg;',
        f'super.new(name, {8 + w}, UVM_NO_COVERAGE);',
        configure('hi', 8, w, 'RW', 0, 0, 1),
        configure('lo', w, 0, 'RW', 0, 5, 1),
        'class ubDut_reg_wide extends uvm_reg;',
        'super.new(name, 40, UVM_NO_COVERAGE);',
        configure('word', 32, 8, 'RO', 1, 0, 0),
        configure('tag', 8, 0, 'RO', 1, 0, 0),
        'class ubDut_reg_aligned extends uvm_reg;',
        'super.new(name, 24, UVM_NO_COVERAGE);',
        configure('a', 8, 16, 'RW', 0, 3, 1),
        configure('reserved0', 8, 8, 'RW', 0, 2, 1),
        configure('b', 8, 0, 'RW', 0, 1, 1),
        'class ubDut_reg_ext extends uvm_reg;',
        'super.new(name, 8, UVM_NO_COVERAGE);',
        configure('data', 8, 0, 'RW', 1, 3, 1),
        'class ubDut_reg_block extends uvm_reg_block;',
        'lut = new("lut", 8, 8, "RW", UVM_NO_COVERAGE);',
        f'tbl = new("tbl", {UB_D[variant]}, {8 + w}, "RO", UVM_NO_COVERAGE);',
        # Rows of 2 * UB_W + 8 bits, at most 32, on an 8-byte stride. uvm_mem
        # takes no WO, so the map rights say write-only and NO_MEM_TESTS keeps
        # the memory sequences off it. ptbl's padding keeps the walk off it.
        'wtbl = new("wtbl", 4, 33, "RW", UVM_NO_COVERAGE);',
        'uvm_resource_db#(bit)::set({"REG::", wtbl.get_full_name()}, "NO_MEM_TESTS", 1, this);',
        'ptbl = new("ptbl", 4, 33, "RW", UVM_NO_COVERAGE);',
        'uvm_resource_db#(bit)::set({"REG::", ptbl.get_full_name()}, "NO_MEM_WALK_TEST", 1, this);',
        "default_map = create_map(\"default_map\", 'h0, 4, UVM_LITTLE_ENDIAN, 1);",
    ]
    for name, rights in (('ctrl', 'RW'), ('cfg', 'RW'), ('wide', 'RO'), ('aligned', 'RW'), ('ext', 'RW')):
        lines.append(f"default_map.add_reg({name}, 'h{offsets[name]:x}, \"{rights}\");")
    for name, rights in (('lut', 'RW'), ('tbl', 'RO'), ('wtbl', 'WO'), ('ptbl', 'RW')):
        lines.append(f"default_map.add_mem({name}, 'h{offsets[name]:x}, \"{rights}\");")
    return lines


ENV_LINES = [
    'class ubDut_env extends uvm_env;',
    'in_agent_t in_agent;',
    'out_agent_t out_agent;',
    'ubRegs_agent_t ubRegs_agent;',
    'a2c_uvm_pkg::a2c_txn_counter #(out_item_t) out_counter;',
    'virtual a2c_clk_if clk_vif;',
    'mst_agent_t mst_agent;',
    'ubDut_reg_block regmodel;',
    'apb_reg_adapter adapter;',
    'uvm_reg_predictor #(ubRegs_item_t) predictor;',
    'if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin',
    'if (!uvm_config_db#(in_vif_t)::get(this, "", "in", in_cfg.vif)) begin',
    'in_cfg.clk_vif = clk_vif;',
    'in_cfg.role = a2c_uvm_pkg::A2C_SRC;',
    'in_cfg.no_backpressure = 0;',
    'uvm_config_db#(in_config_t)::set(this, "in_agent", "cfg", in_cfg);',
    'in_agent = in_agent_t::type_id::create("in_agent", this);',
    'out_cfg.role = a2c_uvm_pkg::A2C_DST;',
    'out_counter = a2c_uvm_pkg::a2c_txn_counter#(out_item_t)::type_id::create("out_counter", this);',
    'out_counter.port_name = "out";',
    'ubRegs_cfg.role = a2c_uvm_pkg::A2C_SRC;',
    'ubRegs_cfg.port_name = "ubRegs";',
    'mst_cfg.role = a2c_uvm_pkg::A2C_DST;',
    'rdM_cfg.id_unbound = 1;',
    'regmodel = ubDut_reg_block::type_id::create("regmodel");',
    'regmodel.build();',
    'regmodel.reset();',
    'predictor = uvm_reg_predictor#(ubRegs_item_t)::type_id::create("predictor", this);',
    'out_agent.mon.ap.connect(out_counter.analysis_export);',
    'regmodel.default_map.set_sequencer(ubRegs_agent.sqr, adapter);',
    'regmodel.default_map.set_auto_predict(0);',
    'ubRegs_agent.mon.ap.connect(predictor.bus_in);',
]


# connect_phase's Mode B branch, whole and in order.
MODE_B_CONNECT = [
    'out_agent.model_mon.ap.connect(out_counter.model_export);',
    'rdM_agent.model_mon.ap.connect(rdM_counter.model_export);',
] + [line for agent in ('in', 'out', 'rdM', 'rdS', 'mst', 'ubRegs')
     for line in (f'if ({agent}_agent.model_cmp != null) begin', f'comparators.push_back({agent}_agent.model_cmp);', 'end')] + [
    'out_agent.model_cmp.counted = 1;',
    'rdM_agent.model_cmp.counted = 1;',
    'reg_writes.map     = regmodel.default_map;',
    'reg_writes.adapter = adapter;',
    'ubRegs_agent.mon.ap.connect(reg_writes.analysis_export);',
    'reg_writes.ap.connect(guard.analysis_export);',
    'guard.counters.push_back(out_counter);',
    'guard.counters.push_back(rdM_counter);',
    'guard.comparators = comparators;',
]

MODE_B_MEMBERS = [
    'bit dual_dut;',
    'a2c_uvm_pkg::a2c_comparator_base comparators[$];',
    'a2c_uvm_pkg::a2c_midstream_guard guard;',
    'a2c_uvm_pkg::a2c_reg_write_subscriber #(ubRegs_item_t) reg_writes;',
    'if (!uvm_config_db#(bit)::get(this, "", "a2c_dual_dut", dual_dut)) begin',
    'out_counter.dual = dual_dut;',
    'rdM_counter.dual = dual_dut;',
]

STABLE_POINT = [
    'function void model_stable_point();',
    'foreach (comparators[i]) begin',
    'if (comparators[i].auto_stable) begin',
    'comparators[i].stable_point();',
    'end',
    'end',
    'endfunction',
]


def block_after(lines, start, opener):
    """The lines of the begin/end block that opens at the first opener at or
    after start, without the opener and its closing end."""
    i = lines.index(opener, start)
    depth = 1
    for j in range(i + 1, len(lines)):
        if lines[j].endswith(' begin') or lines[j] == 'begin' or lines[j] == 'fork':
            depth += 1
        elif lines[j] in ('end', 'join') or lines[j].startswith('end else'):
            depth -= 1
            if depth == 0:
                return lines[i + 1:j]
    raise ValueError(f"no end for {opener!r} at line {i}")


def check_mode_b(pkg, lines):
    problems = [f"{pkg}.sv lacks the line {line!r}" for line in MODE_B_MEMBERS if line not in lines]
    connect = lines.index('virtual function void connect_phase(uvm_phase phase);')
    branch = block_after(lines, connect, 'if (dual_dut) begin')
    if branch != MODE_B_CONNECT:
        problems.append(f"{pkg}.sv connect_phase's dual_dut branch is\n    {branch}\n  expected\n    {MODE_B_CONNECT}")
    # Each model vif fetch, and the guard and its feeder, exist only under dual_dut.
    build = lines.index('virtual function void build_phase(uvm_phase phase);')
    for port, intf in (('in', 'rdy_vld'), ('out', 'rdy_vld'), ('rdM', 'axi_read'), ('rdS', 'axi_read'),
                       ('mst', 'apb'), ('ubRegs', 'apb')):
        fetch = f'if (!uvm_config_db#({port}_vif_t)::get(this, "", "{port}_model", {port}_cfg.model_vif)) begin'
        if fetch not in lines or lines[lines.index(fetch) - 1] != 'if (dual_dut) begin':
            problems.append(f"{pkg}.sv does not fetch {port}_model under dual_dut")
        elif lines[lines.index(fetch) + 1] != f'`uvm_fatal("A2C_CFG", "no virtual {intf}_if \'{port}_model\'")':
            problems.append(f"{pkg}.sv does not stop with A2C_CFG when {port}_model is missing")
    guardBranch = block_after(lines, lines.index('predictor = uvm_reg_predictor#(ubRegs_item_t)::type_id::create("predictor", this);', build),
                              'if (dual_dut) begin')
    wantGuard = ['guard = a2c_uvm_pkg::a2c_midstream_guard::type_id::create("guard", this);',
                 'reg_writes = a2c_uvm_pkg::a2c_reg_write_subscriber#(ubRegs_item_t)::type_id::create("reg_writes", this);']
    if guardBranch != wantGuard:
        problems.append(f"{pkg}.sv creates under dual_dut\n    {guardBranch}\n  expected\n    {wantGuard}")
    if not in_order(lines, STABLE_POINT):
        problems.append(f"{pkg}.sv has no model_stable_point() over the auto_stable comparators")
    return problems


def in_order(lines, expected):
    position = 0
    for line in expected:
        if line not in lines[position:]:
            return False
        position = lines.index(line, position) + 1
    return True


def check(project):
    prj = projectOpen(os.path.join(project, regView.DB))
    (qualBlock,) = [key for key, row in prj.data['blocks'].items() if row['block'] == 'ubDut']
    uvm = prj.getBlockData(qualBlock)['uvm']
    offsets = {row['name']: row['offset'] for row in uvm['registers'] + uvm['memories']}
    (wtbl,) = [row for row in uvm['memories'] if row['name'] == 'wtbl']
    problems = []
    if wtbl['rowBytes'] != 8:
        problems.append(f"wtbl's decoder stride is {wtbl['rowBytes']} bytes, the fixture means it to be 8")
    for variant, pkg in regView.PKG.items():
        path = os.path.join(project, 'uvm', f'{pkg}.sv')
        with open(path) as f:
            lines = [line.strip() for line in f]
        expected = expected_regmodel(variant, offsets) + ENV_LINES
        problems += [f"{pkg}.sv lacks the line {line!r}" for line in expected if line not in lines]
        unexpected = [line for line in lines
                      if re.match(r'(in|ubRegs|mst)_counter\b|.*_cfg\.ready_pct\b|(ubRegs|mst)_cfg\.no_backpressure\b'
                                  r'|.*_cfg\.is_active\b|(in|out|rdS|ubRegs|mst)_cfg\.id_unbound\b', line)]
        problems += [f"{pkg}.sv has the line {line!r}" for line in unexpected]
        problems += check_mode_b(pkg, lines)
        # The resources come after their memory's configure() call, which
        # gives the memory the full name they are keyed by.
        for mem in ('wtbl', 'ptbl'):
            configured = lines.index(f'{mem}.configure(this);')
            resource = [i for i, line in enumerate(lines) if line.startswith('uvm_resource_db') and f' {mem}.' in line]
            if resource != [configured + 1]:
                problems.append(f"{pkg}.sv sets {mem}'s resource at lines {resource}, expected just after "
                                f"its configure() at line {configured}")
        resources = [line for line in lines if line.startswith('uvm_resource_db')]
        if len(resources) != 2:
            problems.append(f"{pkg}.sv sets {len(resources)} resources, expected 2: {resources}")
        # The fields' configure calls sit in their own register's build(), in
        # declaration order.
        configures = [line for line in lines if '.configure(this, ' in line]
        wantConfigures = [line for line in expected if '.configure(this, ' in line]
        if configures != wantConfigures:
            problems.append(f"{pkg}.sv configures fields\n    {configures}\n  expected\n    {wantConfigures}")
    return problems


def check_typedefs():
    bound = {'structureType': 'data_t', 'structure': 'ubSt', 'isNull': False}
    unbound = {'structureType': 'user_t', 'structure': None, 'isNull': True}
    cases = [
        ({'name': 'p', 'interfaceType': 'rdy_vld', 'paramBindings': [bound, unbound]},
         ['typedef rdy_vld_agent #(.data_t(ubSt)) p_agent_t;',
          'typedef p_agent_t::item_t p_item_t;',
          'typedef p_agent_t::config_t p_config_t;',
          'typedef virtual rdy_vld_if #(.data_t(ubSt)) p_vif_t;']),
        ({'name': 'q', 'interfaceType': 'notify_ack', 'paramBindings': [unbound]},
         ['typedef notify_ack_agent q_agent_t;',
          'typedef q_agent_t::item_t q_item_t;',
          'typedef q_agent_t::config_t q_config_t;',
          'typedef virtual notify_ack_if q_vif_t;']),
    ]
    return [f"port {port['name']} typedefs\n    {uvmPkg.agent_typedefs(port)}\n  expected\n    {want}"
            for port, want in cases if uvmPkg.agent_typedefs(port) != want]


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM VARIANT PACKAGE REGISTER MODEL AND ENV")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix='uvm_pkg_regmodel_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'prj')
        shutil.copytree(regView.FIXTURE, project)
        edit_fixture(project)
        for target in ('db', 'newmodule', 'gen'):
            result = make(project, target)
            if result.returncode != 0:
                print(f"FAIL: make {target} rejected the fixture (rc={result.returncode})")
                print(result.stdout + result.stderr)
                return 1
        problems = check(project) + check_typedefs()
    finally:
        remove_tree(tmp)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        print("\nFAIL: a variant package's register model or env disagrees with the block")
        return 1
    print("  PASS: register classes, fields, memories and map offsets at v0 and v1")
    print("  PASS: NO_MEM_TESTS on the write-only memory, NO_MEM_WALK_TEST on the padded one")
    print("  PASS: agent typedefs with and without bound parameters")
    print("  PASS: env agents with their roles, the output transaction counter and the register predictor")
    print("  PASS: env Mode B wiring under dual_dut: model vifs, counter model streams, comparators, guard")
    print("\nPASS: the variant packages hold the register model and the env")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
