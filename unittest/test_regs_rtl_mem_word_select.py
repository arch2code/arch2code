#!/usr/bin/env python3
"""A firmware access to a memory word picks the word by its offset from the
memory's base.

With a numeric memory `alignment:` of 4, calcAddresses places a memory on any
4-byte boundary. leafA's first memory, odd, has three 4-byte rows, so the
memories after it start off their 8-byte row footprint: wide at 0x0c,
wideParam (depth from the block parameter WIDE_PDEPTH) at 0x2c, and the memory
register memReg at 0x6c. Each row is 40 bits, two bus words. Taking the word
from the absolute address's low bits swaps the two words of every row.

The RTL fixture is generated outside the repository working tree, and a small
bench drives the generated leafA over APB under Verilator `--binary --timing`.
It checks the stored row after two word writes and the words read from a
preloaded row, and ends with TB_PASS on stdout.
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

PACKED_PROJECT = (PROJECT.replace('fwAccess', 'memWordSelect')
                  .replace('memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }',
                           'memories:  { alignment: 4 }')
                  .replace('registers: { alignment: 8, sortDescending: true }',
                           'registers: { alignment: 4 }'))

DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        WIDE_PDEPTH: {{ value: 4, maxValue: 8, desc: "per-instance memory depth" }}

constants:
    ODD_DEPTH: {{ value: 3, desc: "rows that leave the next base off an 8-byte boundary" }}
    WIDE_DEPTH: {{ value: 4, desc: "fixed memory depth" }}

types:
    rowAddrT: {{ width: 8, desc: "row index" }}
    wideT: {{ width: 40, desc: "two-word payload" }}

structures:
    rowAddrSt:
        address: {{ varType: rowAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: cfgT, generator: memory, desc: "one-word payload" }}
    wideSt:
        data: {{ varType: wideT, generator: memory, desc: "two-word payload" }}

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
    - {{ memory: odd, block: leafA, structure: memSt, addressStruct: rowAddrSt, wordLines: ODD_DEPTH, regAccess: true, desc: "three one-word rows" }}
    - {{ memory: wide, block: leafA, structure: wideSt, addressStruct: rowAddrSt, wordLines: WIDE_DEPTH, regAccess: true, desc: "fixed depth" }}
    - {{ memory: wideParam, block: leafA, structure: wideSt, addressStruct: rowAddrSt, wordLines: WIDE_PDEPTH, regAccess: true, desc: "parameterizable depth" }}

registers:
    - {{ register: memReg, block: leafA, regType: memory, structure: wideSt, addressStruct: rowAddrSt, wordLines: WIDE_DEPTH, desc: "memory register" }}

parameters:
    leafA:
        small:
            WIDE_PDEPTH: 4
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=2)
          + render_leaf('leafA', extra_block_lines='        params: [WIDE_PDEPTH]\n'))

BENCH = """\
module word_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();

    leafA #(.WIDE_PDEPTH(4)) uLeafA (.regs(bus), .clk(clk), .rst_n(rst_n));

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
        @(negedge clk);
        bus.penable = 0;
        bus.psel = 0;
        repeat (3) @(negedge clk);
    endtask

    task automatic check(input logic [39:0] got, input logic [39:0] want, input string what);
        if (got !== want) begin
            $display("TB_FAIL: %s: got 0x%0h, expected 0x%0h", what, got, want);
            errors++;
        end else begin
            $display("TB_OK: %s", what);
        end
    endtask

    task automatic write_word(input logic [31:0] addr, input logic [31:0] wdata, input string what);
        logic [31:0] unused;
        access(1, addr, wdata, what, unused);
    endtask

    task automatic read_word(input logic [31:0] addr, input logic [31:0] want, input string what);
        logic [31:0] got;
        access(0, addr, 0, what, got);
        check(40'(got), 40'(want), what);
    endtask

    initial begin
        bus.psel = 0; bus.penable = 0; bus.pwrite = 0; bus.paddr = 0; bus.pwdata = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        // Row 1 of each memory is loaded directly and read over the bus.
        uLeafA.uWide.mem[1] = 40'hab_cdef0123;
        uLeafA.uWideParam.mem[1] = 40'hab_cdef0123;
        uLeafA.uMemReg.mem[1] = 40'hab_cdef0123;
        write_word(32'h0c, 32'h11111111, "write wide row 0 word 0");
        write_word(32'h10, 32'h00000022, "write wide row 0 word 1");
        write_word(32'h2c, 32'h11111111, "write wideParam row 0 word 0");
        write_word(32'h30, 32'h00000022, "write wideParam row 0 word 1");
        write_word(32'h6c, 32'h11111111, "write memReg row 0 word 0");
        write_word(32'h70, 32'h00000022, "write memReg row 0 word 1");
        check(uLeafA.uWide.mem[0], 40'h22_11111111, "wide row 0 holds both words in place");
        check(uLeafA.uWideParam.mem[0], 40'h22_11111111, "wideParam row 0 holds both words in place");
        check(uLeafA.uMemReg.mem[0], 40'h22_11111111, "memReg row 0 holds both words in place");
        read_word(32'h14, 32'hcdef0123, "read wide row 1 word 0");
        read_word(32'h18, 32'h000000ab, "read wide row 1 word 1");
        read_word(32'h34, 32'hcdef0123, "read wideParam row 1 word 0");
        read_word(32'h38, 32'h000000ab, "read wideParam row 1 word 1");
        read_word(32'h74, 32'hcdef0123, "read memReg row 1 word 0");
        read_word(32'h78, 32'h000000ab, "read memReg row 1 word 1");
        if (errors == 0) $display("TB_PASS");
        $finish;
    end
endmodule
"""

# A memory register's storage is the block's own RTL.
MEMREG_RAM = """\
memory_sp #(.DEPTH(WIDE_DEPTH), .data_t(wideSt)) uMemReg (.mem_port(memReg), .clk(clk));

endmodule: leafA"""

# The offsets the bench assumes, as calcAddresses lays them out.
OFFSETS = {'REG_LEAFA_ODD': 0x00, 'REG_LEAFA_WIDE': 0x0c,
           'REG_LEAFA_WIDEPARAM': 0x2c, 'REG_LEAFA_MEMREG': 0x6c}


def generate(fixture):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PACKED_PROJECT)
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'memWordSelect.db')
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
    bench = os.path.join(fixture, 'word_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH)
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'leafA_regs.sv', 'leafA.sv')]
    # The 8-bit index is wider than a 4-row RAM needs, by design; memory_sp.sv truncates it.
    waiver = os.path.join(fixture, 'waiver.vlt')
    with open(waiver, 'w') as f:
        f.write('`verilator_config\nlint_off -rule WIDTHTRUNC -file "*/memory_sp.sv"\n')
    cmd = (['verilator', '--binary', '--timing', '-j', '4', waiver, '--top-module', 'word_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vword_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_mem_word_')
    try:
        generate(fixture)
        check_offsets(fixture)
        simulate(fixture)
    except Exception as exc:
        print(f"FAIL: a firmware access picks the memory word by its offset from the base: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: a firmware access picks the memory word by its offset from the base")
    return 0


if __name__ == '__main__':
    sys.exit(main())
