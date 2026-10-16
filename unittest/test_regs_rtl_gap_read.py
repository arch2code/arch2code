#!/usr/bin/env python3
"""A generated register block answers an address gap with 32'hBADD_C0DE.

A gap is an address in a register block's decoded range that no register or
memory claims. A read there returns 32'hBADD_C0DE, the value an empty decoder
slot reads. An address past the decoded range aliases through the address mask
onto an address in the range, so it is no gap. A write to a gap
is dropped and changes no register. Both complete with PREADY and without
PSLVERR, as every access to the block does.

leafA serves two rw registers at 0x0 and 0x8 in a 16-byte range, so 0x4 is a
gap between them and 0xc a gap past the last one. The bench writes both registers, writes two gaps,
reads both registers back unchanged and reads both gaps.

The fixture is generated outside the repository working tree, and a small
bench drives the generated leafA over APB under Verilator `--binary --timing`.
The bench ends with TB_PASS on stdout.
"""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from test_memory_firmware_access import PROJECT, _arch2code, _generated_files

COMMON_SV = os.path.join(base_dir, 'common', 'systemVerilog')
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'status')]

DESIGN = """include:
    - shared.yaml

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA0, regType: rw, block: leafA, structure: cfgRegSt, desc: "first leafA register" }}
    - {{ register: cfgA1, regType: rw, block: leafA, structure: cfgRegSt, desc: "second leafA register" }}
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=2)
          + render_leaf('leafA'))

BENCH = """\
module gap_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();

    leafA uLeafA (.regs(bus), .clk(clk), .rst_n(rst_n));

    int errors = 0;

    // One transfer, starting at a negedge.
    task automatic access(input logic write, input logic [31:0] addr, input logic [31:0] wdata,
                          input string what, output logic [31:0] rdata);
        int cycles = 0;
        bus.psel = 1; bus.penable = 0; bus.pwrite = write; bus.paddr = addr; bus.pwdata = wdata;
        @(negedge clk);
        bus.penable = 1;
        while (!bus.pready) begin
            @(negedge clk);
            cycles++;
            if (cycles > 50) begin
                $display("TB_FAIL: %s: %s 0x%0h never completed", what, write ? "write" : "read", addr);
                $finish;
            end
        end
        rdata = bus.prdata;
        if (bus.pslverr) begin
            $display("TB_FAIL: %s: 0x%0h completed with PSLVERR", what, addr);
            errors++;
        end
        @(negedge clk);
        bus.penable = 0;
        bus.psel = 0;
        @(negedge clk);
    endtask

    task automatic write_reg(input logic [31:0] addr, input logic [31:0] wdata, input string what);
        logic [31:0] unused;
        access(1, addr, wdata, what, unused);
    endtask

    task automatic expect_read(input logic [31:0] addr, input logic [31:0] want, input string what);
        logic [31:0] got;
        access(0, addr, 0, what, got);
        if (got !== want) begin
            $display("TB_FAIL: %s: read 0x%0h returned 0x%0h, expected 0x%0h", what, addr, got, want);
            errors++;
        end else begin
            $display("TB_OK: %s", what);
        end
    endtask

    initial begin
        bus.psel = 0; bus.penable = 0; bus.pwrite = 0; bus.paddr = 0; bus.pwdata = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        write_reg(32'h000, 32'h1111, "write cfgA0");
        write_reg(32'h008, 32'h2222, "write cfgA1");
        write_reg(32'h004, 32'hFFFF, "write the gap between the registers");
        write_reg(32'h00c, 32'hFFFF, "write the gap past the registers");
        expect_read(32'h000, 32'h1111, "gap writes leave cfgA0 unchanged");
        expect_read(32'h008, 32'h2222, "gap writes leave cfgA1 unchanged");
        expect_read(32'h004, 32'hBADD_C0DE, "the gap between the registers reads 32'hBADD_C0DE");
        expect_read(32'h00c, 32'hBADD_C0DE, "the gap past the registers reads 32'hBADD_C0DE");
        if (errors == 0) $display("TB_PASS");
        $finish;
    end
endmodule
"""


def generate(fixture):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'regsGap'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'regsGap.db')
    steps = [('database build', ['--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db]),
             ('newmodule', ['--db', db, '-r', '--newmodule'])]
    for label, args in steps:
        run = _arch2code(*args, cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"{label} failed:\n{run.stdout}\n{run.stderr}")
    for rel in _generated_files(fixture):
        lang = '--systemVerilog' if rel.endswith('.sv') else '--systemc'
        run = _arch2code('--db', db, '-r', lang, '--file', os.path.join(fixture, rel), cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{run.stdout}\n{run.stderr}")


def simulate(fixture):
    bench = os.path.join(fixture, 'gap_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH)
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'leafA_regs.sv', 'leafA.sv')]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'gap_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vgap_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_regs_gap_')
    try:
        generate(fixture)
        simulate(fixture)
    except Exception as exc:
        print(f"FAIL: register block gap reads 32'hBADD_C0DE and drops writes: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: register block gap reads 32'hBADD_C0DE and drops writes")
    return 0


if __name__ == '__main__':
    sys.exit(main())
