#!/usr/bin/env python3
"""Coverage for a block declaring `clocks: {}`, a combinational block with no
clock and no reset.

Fixture A is built and generated once. Container `dut` holds a clocked
producer and consumer, which declare no clocks: and so keep the implicit
`clk`/`rst_n`, and the clockless `pass` between them. `pass` has hasVl, so
its co-simulation wrappers are generated too. The checks read the emitted
text:
  - `pass`'s module has no clock or reset port and no clk/rst_n alias;
  - `dut` binds no clock or reset to `uPass` and still binds both to the
    clocked children;
  - a block with no clocks: key still gets `input clk, rst_n`;
  - `pass`'s verilated SV wrapper has no clock or reset pin;
  - `pass`'s SC wrapper generates the project's default testbench clock and
    reset and binds every BFM to them, and binds neither to the RTL.

The remaining cases each build a design that gives a clockless block
something needing a clock, and read the build diagnostic.

Fixtures are written outside the repository working tree, as in
test_clock_local_nets.py.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

from pysrc.intf_gen_utils import sc_hdl_member_names
from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from _tmp_helpers import remove_tree

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=120,
                          cwd=cwd, env=env)


PROJECT = """yamlFormat: 2
projectName: {name}
topInstance: {top}

projectFiles:
{files}
clocks:
    clkRef: {{ desc: "reference clock", default: true, period: 10, timeUnit: ns }}

resets:
    rstRef_n: {{ desc: "reference reset", default: true, clock: clkRef, releaseCycles: 4 }}

dirs:
    root: ../..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  {{ alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }}
    registers: {{ alignment: 8, sortDescending: true }}

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""

# `pass` forwards a status and a rdy_vld stream unchanged. {passExtra} adds
# lines to its block, {extraBlocks}, {extraInstances} and {extraSections}
# extend the design for a rejection case.
DESIGN = """types:
    dataT: {{ width: 8, desc: "payload word" }}
    addrT: {{ width: 4, desc: "table address" }}

structures:
    dataSt:
        data: {{ varType: dataT, desc: "payload word" }}
    addrSt:
        addr: {{ varType: addrT, desc: "table address" }}

interfaces:
    levelIf:
        desc: "level"
        interfaceType: status
        structures:
            - {{ structure: dataSt, structureType: data_t }}
    streamIf:
        desc: "stream"
        interfaceType: rdy_vld
        structures:
            - {{ structure: dataSt, structureType: data_t }}

blocks:
    top_tb:
        desc: "testbench container"
        hasRtl: false
        clocks:
            clkRef: {{ default: true }}
        resets:
            rstRef_n: {{ clock: clkRef }}
    dut:
        desc: "clocked container"
        clocks:
            clkRef: {{ default: true }}
        resets:
            rstRef_n: {{ clock: clkRef }}
    producer:
        desc: "clocked producer, no clocks: key"
    consumer:
        desc: "clocked consumer, no clocks: key"
    pass:
        desc: "combinational pass-through"
        hasVl: true
        clocks: {{}}
        ports:
            in:   {{ interface: levelIf, direction: dst }}
            out:  {{ interface: levelIf, direction: src }}
            sIn:  {{ interface: streamIf, direction: dst }}
            sOut: {{ interface: streamIf, direction: src }}
{passExtra}{extraBlocks}
instances:
    top_tb:    {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    u_dut:     {{ container: top_tb, instanceType: dut, instGroup: top }}
    uProducer: {{ container: dut, instanceType: producer, instGroup: top,
                 clocks: {{ clk: clkRef }}, resets: {{ rst_n: rstRef_n }} }}
    uPass:     {{ container: dut, instanceType: pass, instGroup: top }}
    uConsumer: {{ container: dut, instanceType: consumer, instGroup: top,
                 clocks: {{ clk: clkRef }}, resets: {{ rst_n: rstRef_n }} }}
{extraInstances}
connections:
    - {{ interface: levelIf, src: uProducer, srcport: out, dst: uPass, dstport: in }}
    - {{ interface: levelIf, src: uPass, srcport: out, dst: uConsumer, dstport: in }}
    - {{ interface: streamIf, src: uProducer, srcport: sOut, dst: uPass, dstport: sIn }}
    - {{ interface: streamIf, src: uPass, srcport: sOut, dst: uConsumer, dstport: sIn }}
{extraSections}"""


def _build(name, design, top='top_tb', shared=None, expect_success=True):
    """Write and build one fixture. Returns (fixture_dir, db_path, result)."""
    fixture = tempfile.mkdtemp(prefix='clockless_')
    try:
        os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'yaml'))
        files = ''
        if shared is not None:
            with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
                f.write(shared)
            files += '    - ../../yaml/shared.yaml\n'
        files += '    - ../../yaml/top.yaml\n'
        with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
            f.write(PROJECT.format(name=name, top=top, files=files))
        with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
            f.write(design)
        db = os.path.join(fixture, f"{name}.db")
        built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                           '--db', db, cwd=fixture)
        if expect_success and built.returncode != 0:
            raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
        return fixture, db, built
    except BaseException:
        remove_tree(fixture)
        raise


def _design(passExtra='', extraBlocks='', extraInstances='', extraSections=''):
    return DESIGN.format(passExtra=passExtra, extraBlocks=extraBlocks,
                         extraInstances=extraInstances, extraSections=extraSections)


# ------------------------------------------------------ Fixture A: emission --

GENERATED = {
    'pass': ('rtl/pass.sv', '--systemVerilog'),
    'dut': ('rtl/dut.sv', '--systemVerilog'),
    'producer': ('rtl/producer.sv', '--systemVerilog'),
    'svWrapper': ('verif/pass_hdl_sv_wrapper.sv', '--systemVerilog'),
    'scWrapper': ('verif/pass_hdl_sc_wrapper.h', '--systemc'),
}


def _generate_fixture_a():
    fixture, db, built = _build('clocklessEmit', _design())
    try:
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
        texts = dict()
        for key, (rel, mode) in GENERATED.items():
            gen = _arch2code('--db', db, '-r', mode, '--file', os.path.join(fixture, rel),
                             cwd=fixture)
            if gen.returncode != 0:
                raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
            with open(os.path.join(fixture, rel)) as f:
                texts[key] = f.read()
        return fixture, texts
    except BaseException:
        remove_tree(fixture)
        raise


def _instantiation(text, instance):
    start = text.index(f" {instance} (")
    return text[start:text.index(');', start)]


def check_module_has_no_clock_or_reset(texts):
    """The clockless module's port list ends at its last interface port, and
    it declares no clk/rst_n alias."""
    text = texts['pass']
    if 'rdy_vld_if.src sOut\n);' not in text:
        raise AssertionError(f"pass.sv's port list does not end at sOut:\n{text}")
    for word in ('clk', 'rst_n', 'input'):
        if word in text:
            raise AssertionError(f"pass.sv mentions '{word}':\n{text}")
    return True


def check_container_binds_nothing_to_clockless_child(texts):
    text = texts['dut']
    inst = _instantiation(text, 'uPass')
    if '.sOut (sOut_1)\n' not in inst or 'clk' in inst or 'rst' in inst:
        raise AssertionError(f"dut.sv's uPass instantiation binds a clock or reset, "
                             f"or does not end at sOut:\n{inst}")
    inst = _instantiation(text, 'uProducer')
    if '.clk (clkRef),\n    .rst_n (rstRef_n)\n' not in inst:
        raise AssertionError(f"dut.sv's uProducer instantiation lost its clock/reset binds:\n{inst}")
    return True


def check_missing_clocks_key_keeps_implicit_clk(texts):
    if '    input clk, rst_n\n);' not in texts['producer']:
        raise AssertionError(f"producer.sv does not declare 'input clk, rst_n':\n{texts['producer']}")
    return True


def check_sv_wrapper_has_no_clock_pins(texts):
    text = texts['svWrapper']
    if 'input bit sOut_rdy\n);' not in text:
        raise AssertionError(f"the SV wrapper's port list does not end at sOut_rdy:\n{text}")
    if '.sOut(sOut) // rdy_vld_if.src\n    );' not in text:
        raise AssertionError(f"the SV wrapper's DUT instantiation does not end at sOut:\n{text}")
    for word in ('clk', 'rst_n'):
        if word in text:
            raise AssertionError(f"the SV wrapper mentions '{word}':\n{text}")
    return True


def check_sc_wrapper_drives_bfms_from_testbench_clock(texts):
    """The testbench default clock (10 ns) and reset (4 release cycles) are
    generated in the wrapper and bound to every BFM, and not to the RTL."""
    text = texts['scWrapper']
    expected = ['sc_signal<bool> clkRef;', 'sc_signal<bool> rstRef_n;',
                'clkRef_half_(sc_time(10, SC_NS) / 2)', 'SC_THREAD(clock_gen_clkRef);',
                'reset_driver(rstRef_n, clkRef, 4);']
    for port in ('in', 'out', 'sIn', 'sOut'):
        bfm = sc_hdl_member_names(port)[1]
        expected += [f'{bfm}.clk(clkRef);', f'{bfm}.rst_n(rstRef_n);']
    missing = [line for line in expected if line not in text]
    if missing:
        raise AssertionError(f"the SC wrapper lacks {missing}:\n{text}")
    if 'dut_hdl->clkRef' in text or 'dut_hdl->rstRef_n' in text:
        raise AssertionError(f"the SC wrapper binds a clock or reset to the RTL:\n{text}")
    return True


FIXTURE_A_CHECKS = [
    ("a clockless module has no clock or reset port and no alias",
     check_module_has_no_clock_or_reset),
    ("a container binds no clock or reset to a clockless child",
     check_container_binds_nothing_to_clockless_child),
    ("a block with no clocks: key keeps the implicit clk and rst_n",
     check_missing_clocks_key_keeps_implicit_clk),
    ("a clockless block's verilated SV wrapper has no clock or reset pin",
     check_sv_wrapper_has_no_clock_pins),
    ("a clockless block's SC wrapper drives its BFMs from the testbench clock and reset",
     check_sc_wrapper_drives_bfms_from_testbench_clock),
]


# ------------------------------------------------------- rejection cases --

def _expect_error(name, design, expected, **kwargs):
    fixture, db, built = _build(name, design, expect_success=False, **kwargs)
    try:
        output = built.stdout + built.stderr
        if built.returncode == 0:
            raise AssertionError(f"the build succeeded; expected an error containing "
                                 f"{expected!r}:\n{output}")
        if expected not in output:
            raise AssertionError(f"the build failed without {expected!r}:\n{output}")
    finally:
        remove_tree(fixture)
    return True


def check_rejects_reset():
    return _expect_error(
        'clocklessReset', _design(passExtra="        resets:\n            rst_n: { }\n"),
        "Block 'pass' declares clocks: {}, so it has no clock, but it declares "
        "resets (rst_n), and a reset belongs to a clock.")


def check_rejects_memory():
    memories = ("memories:\n"
                "    - { memory: table, block: pass, structure: dataSt, addressStruct: addrSt, "
                "wordLines: 16, desc: \"table\" }\n")
    return _expect_error(
        'clocklessMemory', _design(extraSections=memories),
        "Block 'pass' declares clocks: {}, so it has no clock, but it declares "
        "memories (table), and a memory is clocked.")


def check_rejects_memory_accessor():
    memories = ("memories:\n"
                "    - { memory: table, block: dut, structure: dataSt, addressStruct: addrSt, "
                "wordLines: 16, desc: \"table\", ports: [tbl] }\n"
                "memoryConnections:\n"
                "    - { memory: table, block: dut, instance: uPass, port: tbl }\n")
    return _expect_error(
        'clocklessMemoryAccess', _design(extraSections=memories),
        "Instance 'uPass' of block 'pass' accesses memory 'table' of block 'dut', but "
        "'pass' declares clocks: {}, so it has no clock")


def check_rejects_clocked_child_of_clockless_container():
    """The existing binding error reports the clocked child, naming the
    container's empty clock list."""
    return _expect_error(
        'clocklessContainer',
        _design(extraBlocks="    inner:\n        desc: \"clocked child\"\n",
                extraInstances="    uInner:    { container: pass, instanceType: inner, instGroup: top }\n"),
        "Instance 'uInner' of block 'inner' in container 'pass' has no binding for its "
        "clock 'clk'")


# Register-bus cases: a router serves `leafA`, and {leafExtra}/{sections}
# make it or its instance need a clock.
def _register_design(leafBlock, sections='', instances=''):
    return f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{render_router('apbDecode', 'top')}{leafBlock}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
{instances}
connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{sections}"""


CLOCKLESS = "        clocks: {}\n"


def check_rejects_register():
    design = _register_design(
        render_plain_block('leafA', CLOCKLESS),
        sections=("registers:\n"
                  "    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, "
                  "desc: \"leafA configuration\" }\n"))
    return _expect_error(
        'clocklessRegister', design,
        "Block 'leafA' declares clocks: {}, so it has no clock, but it owns register 'cfgA'",
        top='uTop', shared=APB_PREAMBLE)


def check_rejects_register_port():
    return _expect_error(
        'clocklessRegisterPort', _register_design(render_leaf('leafA', extra_block_lines=CLOCKLESS)),
        "Block 'leafA' declares clocks: {}, so it has no clock, but it declares "
        "registerPorts: (regs), and a register port runs on a clock.",
        top='uTop', shared=APB_PREAMBLE)


def check_rejects_router():
    design = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{render_router('apbDecode', 'top', extra_block_lines=CLOCKLESS)}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}
"""
    return _expect_error(
        'clocklessRouter', design,
        "Block 'apbDecode' declares clocks: {}, so it has no clock, but it declares "
        "an addressBlock:, and a router runs on its bus clock.",
        top='uTop', shared=APB_PREAMBLE)


def check_rejects_register_accessor():
    design = _register_design(
        render_plain_block('leafA'),
        sections=("registers:\n"
                  "    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, "
                  "desc: \"leafA configuration\" }\n"
                  "registerConnections:\n"
                  "    - { register: cfgA, block: leafA, instance: uComb }\n"),
        instances="    uComb:      { container: leafA, instanceType: comb }\n")
    design = design.replace("\ninstances:", f"{render_plain_block('comb', CLOCKLESS)}\ninstances:", 1)
    return _expect_error(
        'clocklessRegisterAccess', design,
        "Instance 'uComb' of block 'comb' accesses register 'cfgA' of block 'leafA', but "
        "'comb' declares clocks: {}, so it has no clock",
        top='uTop', shared=APB_PREAMBLE)


# ------------------------------------------------------------- harness --

def _run_case(label, fn):
    try:
        ok = fn()
    except AssertionError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    if not ok:
        print(f"FAIL: {label}: returned falsy")
        return False
    print(f"PASS: {label}")
    return True


def main():
    print("=" * 72)
    print("Clockless blocks: clocks: {}")
    print("=" * 72)
    ok = []
    fixture, texts = _generate_fixture_a()
    try:
        ok += [_run_case(label, lambda fn=fn: fn(texts)) for label, fn in FIXTURE_A_CHECKS]
    finally:
        remove_tree(fixture)

    cases = [
        ("a clockless block declaring a reset is rejected", check_rejects_reset),
        ("a clockless block owning a memory is rejected", check_rejects_memory),
        ("a clockless memory accessor is rejected", check_rejects_memory_accessor),
        ("a clocked child of a clockless container is rejected",
         check_rejects_clocked_child_of_clockless_container),
        ("a clockless block owning a register is rejected", check_rejects_register),
        ("a clockless block with registerPorts: is rejected", check_rejects_register_port),
        ("a clockless router is rejected", check_rejects_router),
        ("a clockless register accessor is rejected", check_rejects_register_accessor),
    ]
    ok += [_run_case(label, fn) for label, fn in cases]

    print()
    print("=" * 72)
    if all(ok):
        print(f"RESULT: all {len(ok)} clockless-block checks passed")
    else:
        print(f"RESULT: {ok.count(False)} of {len(ok)} clockless-block checks FAILED")
    print("=" * 72)
    return 0 if all(ok) else 1


if __name__ == '__main__':
    sys.exit(main())
