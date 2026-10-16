#!/usr/bin/env python3
"""A firmware access to a memory drives the row's index inside that memory.

leafA owns three memories whose address types are 8 bits, wider than their
16 rows need. pad fills offsets 0x000-0x1ff so the others sit at non-zero
bases: idxParam (depth from the block parameter IDX_PDEPTH) at 0x200,
idxFixed at 0x280, and the memory register memReg at 0x2c0. An index taken
from the absolute address carries the base's bits, so row 0 of idxParam
would drive 0x80 and row 15 0x8f.

The RTL fixture is generated outside the repository working tree, and a small
bench drives the generated leafA over APB under Verilator `--binary --timing`.
It records the index each memory port carries while enabled and ends with
TB_PASS on stdout.
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
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'memory', 'status')]

DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        IDX_PDEPTH: {{ value: 16, maxValue: 32, desc: "per-instance memory depth" }}

constants:
    IDX_DEPTH: {{ value: 16, desc: "fixed memory depth" }}
    PAD_DEPTH: {{ value: 128, desc: "rows that push the other memories off base 0" }}

types:
    wideAddrT: {{ width: 8, desc: "row index wider than the depth needs" }}

structures:
    wideAddrSt:
        address: {{ varType: wideAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: cfgT, generator: memory, desc: "memory payload" }}

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top, variant: small }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

memories:
    - {{ memory: pad, block: leafA, structure: memSt, addressStruct: wideAddrSt, wordLines: PAD_DEPTH, regAccess: true, desc: "fills the low offsets" }}
    - {{ memory: idxParam, block: leafA, structure: memSt, addressStruct: wideAddrSt, wordLines: IDX_PDEPTH, regAccess: true, desc: "parameterizable depth" }}
    - {{ memory: idxFixed, block: leafA, structure: memSt, addressStruct: wideAddrSt, wordLines: IDX_DEPTH, regAccess: true, desc: "fixed depth" }}

registers:
    - {{ register: memReg, block: leafA, regType: memory, structure: memSt, addressStruct: wideAddrSt, wordLines: IDX_DEPTH, desc: "memory register" }}

parameters:
    leafA:
        small:
            IDX_PDEPTH: 16
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=2)
          + render_leaf('leafA', extra_block_lines='        params: [IDX_PDEPTH]\n'))

BENCH = """\
module index_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();

    leafA #(.IDX_PDEPTH(16)) uLeafA (.regs(bus), .clk(clk), .rst_n(rst_n));

    int errors = 0;

    // The index the register handler's port of each memory last carried
    // while enabled.
    logic [7:0] idxParam_seen, idxFixed_seen, memReg_seen;
    always @(posedge clk) begin
        if (uLeafA.idxParam_reg.enable) idxParam_seen <= uLeafA.idxParam_reg.addr;
        if (uLeafA.idxFixed_reg.enable) idxFixed_seen <= uLeafA.idxFixed_reg.addr;
        if (uLeafA.memReg.enable)   memReg_seen   <= uLeafA.memReg.addr;
    end

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
        @(negedge clk);
        bus.penable = 0;
        bus.psel = 0;
        repeat (3) @(negedge clk);
    endtask

    task automatic check(input logic [31:0] got, input logic [31:0] want, input string what);
        if (got !== want) begin
            $display("TB_FAIL: %s: got 0x%0h, expected 0x%0h", what, got, want);
            errors++;
        end else begin
            $display("TB_OK: %s", what);
        end
    endtask

    task automatic write_row(input logic [31:0] addr, input logic [31:0] wdata, input string what,
                             ref logic [7:0] seen, input logic [7:0] want_idx);
        logic [31:0] unused;
        seen = 'x;
        access(1, addr, wdata, what, unused);
        check(32'(seen), 32'(want_idx), {what, ": index"});
    endtask

    task automatic read_row(input logic [31:0] addr, input logic [31:0] want, input string what,
                            ref logic [7:0] seen, input logic [7:0] want_idx);
        logic [31:0] got;
        seen = 'x;
        access(0, addr, 0, what, got);
        check(32'(seen), 32'(want_idx), {what, ": index"});
        check(got, want, {what, ": data"});
    endtask

    initial begin
        bus.psel = 0; bus.penable = 0; bus.pwrite = 0; bus.paddr = 0; bus.pwdata = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        write_row(32'h200, 32'h1111, "write idxParam row 0", idxParam_seen, 8'd0);
        write_row(32'h23c, 32'h2222, "write idxParam row 15", idxParam_seen, 8'd15);
        write_row(32'h280, 32'h3333, "write idxFixed row 0", idxFixed_seen, 8'd0);
        write_row(32'h2bc, 32'h4444, "write idxFixed row 15", idxFixed_seen, 8'd15);
        write_row(32'h2c0, 32'h5555, "write memReg row 0", memReg_seen, 8'd0);
        write_row(32'h2fc, 32'h6666, "write memReg row 15", memReg_seen, 8'd15);
        read_row(32'h200, 32'h1111, "read idxParam row 0", idxParam_seen, 8'd0);
        read_row(32'h23c, 32'h2222, "read idxParam row 15", idxParam_seen, 8'd15);
        read_row(32'h280, 32'h3333, "read idxFixed row 0", idxFixed_seen, 8'd0);
        read_row(32'h2bc, 32'h4444, "read idxFixed row 15", idxFixed_seen, 8'd15);
        read_row(32'h2c0, 32'h5555, "read memReg row 0", memReg_seen, 8'd0);
        read_row(32'h2fc, 32'h6666, "read memReg row 15", memReg_seen, 8'd15);
        if (errors == 0) $display("TB_PASS");
        $finish;
    end
endmodule
"""

# A memory register's storage is the block's own RTL.
MEMREG_RAM = """\
memory_sp #(.DEPTH(IDX_DEPTH), .data_t(memSt)) uMemReg (.mem_port(memReg), .clk(clk));

endmodule: leafA"""

# The offsets the bench assumes, as calcAddresses lays them out.
OFFSETS = {'REG_LEAFA_PAD': 0x000, 'REG_LEAFA_IDXPARAM': 0x200,
           'REG_LEAFA_IDXFIXED': 0x280, 'REG_LEAFA_MEMREG': 0x2c0}


def generate(fixture):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'memIndex'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'memIndex.db')
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


def check_offsets(fixture):
    with open(os.path.join(fixture, 'rtl', 'leafA_regs.sv')) as f:
        text = f.read()
    for name, offset in OFFSETS.items():
        want = f"localparam int unsigned {name} = 32'h{offset:08x};"
        if want not in text:
            raise AssertionError(f"rtl/leafA_regs.sv does not place {name} at 0x{offset:x}: {want}")


def simulate(fixture):
    leaf = os.path.join(fixture, 'rtl', 'leafA.sv')
    with open(leaf) as f:
        text = f.read()
    if 'endmodule: leafA' not in text:
        raise AssertionError(
            f"{leaf} has no 'endmodule: leafA' line to insert the memory RAM before")
    with open(leaf, 'w') as f:
        f.write(text.replace('endmodule: leafA', MEMREG_RAM))
    bench = os.path.join(fixture, 'index_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH)
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'leafA_regs.sv', 'leafA.sv')]
    # The 8-bit index is wider than a 16-row RAM needs, by design; memory_sp.sv truncates it.
    waiver = os.path.join(fixture, 'waiver.vlt')
    with open(waiver, 'w') as f:
        f.write('`verilator_config\nlint_off -rule WIDTHTRUNC -file "*/memory_sp.sv"\n')
    cmd = (['verilator', '--binary', '--timing', '-j', '4', waiver, '--top-module', 'index_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vindex_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_mem_index_')
    try:
        generate(fixture)
        check_offsets(fixture)
        simulate(fixture)
    except Exception as exc:
        print(f"FAIL: a firmware access drives the row index inside the memory: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: a firmware access drives the row index inside the memory")
    return 0


if __name__ == '__main__':
    sys.exit(main())
