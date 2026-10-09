#!/usr/bin/env python3
"""Write-only LUT memories on a leaf whose register port runs on another clock.

The leaf lsc runs on clk and takes its register bus on cfg_clk. It owns three
18-bit LUTs, mem_r, mem_g and mem_b, each portRportW with regAccess: wo and a
block-side port core. Firmware loads each LUT through port B on cfg_clk and
the block reads it through port A on clk. The check compares each generated
memory_dp_2clk instance with the instance text written by hand for this design,
and checks that the register handler instance binds only the cfg_clk domain.

Fixtures are written outside the repository working tree.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from _tmp_helpers import remove_tree

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

PROJECT = """yamlFormat: 2
projectName: lscLuts
topInstance: uTop

projectFiles:
    - ../../yaml/shared.yaml
    - ../../yaml/top.yaml

clocks:
    clk:     { desc: "the datapath clock", default: true, period: 1, timeUnit: ns }
    cfg_clk: { desc: "the register bus clock", period: 3, timeUnit: ns }

resets:
    rst_n:     { desc: "the datapath reset", default: true, clock: clk }
    cfg_rst_n: { desc: "the register bus reset", clock: cfg_clk }

dirs:
    root: ../..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""

DEPTH = 'LSC_MEM_DEPTH'

DESIGN = """include:
    - shared.yaml

constants:
    LSC_MEM_DEPTH: { value: 8, desc: "LUT depth" }

types:
    lscMemDataT: { width: 18, desc: "LUT entry" }
    lscMemAddrT: { width: 3, desc: "LUT address" }

structures:
    lsc_mem_data_t:
        data: { varType: lscMemDataT, generator: memory, desc: "LUT entry" }
    lsc_mem_addr_t:
        address: { varType: lscMemAddrT, generator: address, desc: "LUT address" }

blocks:
""" + (render_plain_block('top', extra_block_lines=(
           '        clocks:\n'
           '            clk:     { default: true }\n'
           '            cfg_clk: { }\n'
           '        resets:\n'
           '            rst_n:     { default: true }\n'
           '            cfg_rst_n: { clock: cfg_clk }\n'))
       + render_plain_block('cpu')
       + render_router('apbDecode', 'top')
       + render_leaf('lsc', port_extra=', clock: cfg_clk, reset: cfg_rst_n', extra_block_lines=(
           '        clocks:\n'
           '            clk:     { default: true }\n'
           '            cfg_clk: { }\n'
           '        resets:\n'
           '            rst_n:     { clock: clk }\n'
           '            cfg_rst_n: { clock: cfg_clk }\n'))) + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu, clocks: { clk: cfg_clk }, resets: { rst_n: cfg_rst_n } }
    uAPBDecode: { container: top, instanceType: apbDecode, clocks: { clk: cfg_clk }, resets: { rst_n: cfg_rst_n } }
    uLsc:       { container: top, instanceType: lsc, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

memories:
""" + ''.join(
    f"    - {{ memory: mem_{c}, block: lsc, structure: lsc_mem_data_t, addressStruct: lsc_mem_addr_t, "
    f"wordLines: {DEPTH}, memoryType: portRportW, regAccess: wo, ports: [core], desc: \"{c} LUT\" }}\n"
    for c in 'rgb')

# The expected instance text, verbatim; only the depth and memory name vary.
EXPECTED_INSTANCE = """memory_dp_2clk #(.DEPTH({depth}), .data_t(lsc_mem_data_t), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uMem_{c} (
    .mem_portA (mem_{c}_core),
    .mem_portB (mem_{c}_reg),
    .clkA (clk),
    .clkB (cfg_clk)
);"""

LEAF = 'rtl/lsc.sv'


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=300, cwd=cwd, env=env)


def _generate():
    """Build the fixture and render the leaf. Returns (fixture_dir, leaf text)."""
    fixture = tempfile.mkdtemp(prefix='lscluts_')
    try:
        os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'yaml'))
        with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
            f.write(PROJECT)
        with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
            f.write(APB_PREAMBLE)
        with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
            f.write(DESIGN)
        db = os.path.join(fixture, 'lscLuts.db')
        for args in (('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db),
                     ('--db', db, '-r', '--newmodule'),
                     ('--db', db, '-r', '--systemVerilog', '--file', os.path.join(fixture, LEAF))):
            done = _arch2code(*args, cwd=fixture)
            if done.returncode != 0:
                raise AssertionError(f"arch2code {' '.join(args[:2])} failed:\n{done.stdout}\n{done.stderr}")
        with open(os.path.join(fixture, LEAF)) as f:
            return fixture, f.read()
    except BaseException:
        remove_tree(fixture)
        raise


def _run_case(label, fn):
    try:
        fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"PASS: {label}")
    return True


def check_lut_instance(text, c):
    expected = EXPECTED_INSTANCE.format(depth=DEPTH, c=c)
    if expected not in text:
        start = text.find(f"uMem_{c} (")
        got = text[text.rfind('\n', 0, start) + 1:text.find(');', start) + 2] if start >= 0 else '(none)'
        raise AssertionError(f"mem_{c} instance differs.\n--- expected\n{expected}\n--- generated\n{got}")


def check_handler_on_cfg_clk(text):
    """The handler instance's clock and reset binds are exactly cfg_clk and
    cfg_rst_n."""
    match = re.search(r'^\s*lsc_regs\s.*?\(\n(.*?)\n\s*\);', text, re.M | re.S)
    if not match:
        raise AssertionError(f"{LEAF} has no lsc_regs instance:\n{text}")
    binds = re.findall(r'\.(\w+)\s*\((\w+)\)', match.group(1))
    domain = [bind for bind in binds if bind[0] in ('clk', 'cfg_clk', 'rst_n', 'cfg_rst_n')]
    if domain != [('cfg_clk', 'cfg_clk'), ('cfg_rst_n', 'cfg_rst_n')]:
        raise AssertionError(f"lsc_regs binds {binds}; its clock and reset binds are {domain}, "
                             f"expected [('cfg_clk', 'cfg_clk'), ('cfg_rst_n', 'cfg_rst_n')]")


def main():
    print("=" * 72)
    print("lsc write-only LUT memories on the register clock")
    print("=" * 72)
    fixture, text = _generate()
    try:
        ok = [_run_case(f"mem_{c} matches the hand-edited memory_dp_2clk instance", lambda c=c: check_lut_instance(text, c))
              for c in 'rgb']
        ok.append(_run_case("the lsc_regs handler instance is clocked on cfg_clk only",
                            lambda: check_handler_on_cfg_clk(text)))
    finally:
        remove_tree(fixture)
    print()
    if all(ok):
        print("RESULT: all lsc LUT checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} lsc LUT checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
