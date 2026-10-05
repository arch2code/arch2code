#!/usr/bin/env python3
"""The generated RTL decoder answers an access to an unmapped address itself.

A router with eight 0x1000-byte address slots serves leafA in slot 1 and leafB,
with addressMultiples 2, in slots 3 and 4. Two register-less instances in the
address group hold slots 0 and 2, and slots 5 to 7 are free, so the window has
a gap at address 0, a gap between the two leaves and a gap above the top leaf.

An unmapped address is a fall-through of the decode. The select chain compares
each arm's start address only, highest first, and a gap is one more arm that
selects no child. With no child selected, the response mux completes the
transfer itself: a read returns 32'hBADD_C0DE and a write is dropped. The
generated decoder is checked for that shape, one compare per arm and no flop
of its own for the unmapped case.

Each access is checked for the child it selects, its read data and, for gap
writes, that the leaves' registers are unchanged afterwards. The bench also
runs a back-to-back sequence, with PSEL held high from one transfer's
completing edge into the next transfer's setup phase. On every edge it checks
that PREADY is high only in an access phase and never for two clocks in a row,
so each transfer sees exactly one PREADY clock.

The fixture is generated outside the repository working tree, and a small
bench drives the generated decoder and both generated leaves over APB under
Verilator `--binary --timing`. The bench ends with TB_PASS on stdout.
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
    uPad0:      {{ container: top, instanceType: pad, addressGroup: top }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
    uPad2:      {{ container: top, instanceType: pad, addressGroup: top }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top, addressMultiples: 2 }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA configuration" }}
    - {{ register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "leafB configuration" }}
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=8)
          + render_leaf('leafA') + render_leaf('leafB') + render_plain_block('pad'))

# Start address of each select arm, highest first; the lowest arm, the gap at
# address 0, is the bare else.
ARM_STARTS = [0x5000, 0x3000, 0x2000, 0x1000]

BENCH = """\
module decode_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) busA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) busB();

    apbDecode uAPBDecode (.apbReg(bus), .apbReg_uLeafA(busA), .apbReg_uLeafB(busB), .clk(clk), .rst_n(rst_n));
    leafA uLeafA (.regs(busA), .clk(clk), .rst_n(rst_n));
    leafB uLeafB (.regs(busB), .clk(clk), .rst_n(rst_n));

    int errors = 0;

    // PREADY completes the access phase only, and for one clock.
    logic pready_q = 0;
    always @(posedge clk) begin
        if (rst_n && bus.pready && !(bus.psel && bus.penable)) begin
            $display("TB_FAIL: PREADY high outside an access phase at %0t", $time);
            errors++;
        end
        if (rst_n && bus.pready && pready_q) begin
            $display("TB_FAIL: PREADY high for two clocks at %0t", $time);
            errors++;
        end
        pready_q <= bus.pready;
    end

    // Which child the current transfer selected: 0 none, 1 leafA, 2 leafB.
    int selected;
    always @(posedge clk) begin
        if (busA.psel) selected |= 1;
        if (busB.psel) selected |= 2;
    end

    // One transfer, starting at a negedge. PENABLE stays high through the
    // completing edge. With hold set, PSEL stays high after it and the caller
    // starts the next setup phase at once.
    task automatic access(input logic write, input logic [31:0] addr, input logic [31:0] wdata,
                          input int want_child, input string what, output logic [31:0] rdata,
                          input bit hold = 0);
        int cycles = 0;
        selected = 0;
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
        if (!hold) begin
            bus.psel = 0;
            @(negedge clk);
        end
        if (selected != want_child) begin
            $display("TB_FAIL: %s: 0x%0h selected child %0d, expected %0d", what, addr, selected, want_child);
            errors++;
        end
    endtask

    task automatic write_reg(input logic [31:0] addr, input logic [31:0] wdata, input int want_child,
                             input string what, input bit hold = 0);
        logic [31:0] unused;
        access(1, addr, wdata, want_child, what, unused, hold);
    endtask

    task automatic expect_read(input logic [31:0] addr, input logic [31:0] want, input int want_child,
                               input string what, input bit hold = 0);
        logic [31:0] got;
        access(0, addr, 0, want_child, what, got, hold);
        if (got !== want) begin
            $display("TB_FAIL: %s: read 0x%0h returned 0x%0h, expected 0x%0h", what, addr, got, want);
            errors++;
        end else begin
            $display("TB_OK: %s", what);
        end
    endtask

    initial begin
        logic [31:0] rdata;
        bus.psel = 0; bus.penable = 0; bus.pwrite = 0; bus.paddr = 0; bus.pwdata = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        write_reg(32'h1000, 32'h1111, 1, "write leafA");
        write_reg(32'h3000, 32'h2222, 2, "write leafB");
        expect_read(32'h1000, 32'h1111, 1, "leafA register written");
        expect_read(32'h3000, 32'h2222, 2, "leafB register written");
        // leafB decodes slot 4 itself, so only the routing is checked here
        access(0, 32'h4000, 0, 2, "slot 4 is leafB's second slot", rdata);
        write_reg(32'h0000, 32'h3333, 0, "write gap at address 0");
        write_reg(32'h2000, 32'h4444, 0, "write gap between leaves");
        write_reg(32'h5000, 32'h5555, 0, "write gap above leafB");
        write_reg(32'h7ffc, 32'h6666, 0, "write top of window");
        expect_read(32'h1000, 32'h1111, 1, "gap writes leave leafA unchanged");
        expect_read(32'h3000, 32'h2222, 2, "gap writes leave leafB unchanged");
        expect_read(32'h0000, 32'hBADD_C0DE, 0, "gap at address 0 reads 32'hBADD_C0DE");
        expect_read(32'h2000, 32'hBADD_C0DE, 0, "gap between leaves reads 32'hBADD_C0DE");
        expect_read(32'h5000, 32'hBADD_C0DE, 0, "gap above leafB reads 32'hBADD_C0DE");
        expect_read(32'h7ffc, 32'hBADD_C0DE, 0, "top of window reads 32'hBADD_C0DE");

        // back to back: no idle cycle between transfers
        write_reg(32'h0000, 32'h7777, 0, "back-to-back write gap at address 0", 1);
        expect_read(32'h0000, 32'hBADD_C0DE, 0, "back-to-back gap at address 0 reads 32'hBADD_C0DE", 1);
        write_reg(32'h3000, 32'h8888, 2, "back-to-back write leafB", 1);
        expect_read(32'h2000, 32'hBADD_C0DE, 0, "back-to-back gap between leaves reads 32'hBADD_C0DE", 1);
        write_reg(32'h1000, 32'h9999, 1, "back-to-back write leafA", 1);
        write_reg(32'h6000, 32'haaaa, 0, "back-to-back write gap above leafB", 1);
        expect_read(32'h6000, 32'hBADD_C0DE, 0, "back-to-back gap above leafB reads 32'hBADD_C0DE", 1);
        expect_read(32'h3000, 32'h8888, 2, "back-to-back leafB keeps its write", 1);
        expect_read(32'h1000, 32'h9999, 1, "back-to-back leafA keeps its write");
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
        f.write(PROJECT.replace('fwAccess', 'emptySlot'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'emptySlot.db')
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


def check_decoder_shape(fixture):
    """The unmapped case adds no flop and the select arms compare only their
    start address."""
    with open(os.path.join(fixture, 'rtl', 'apbDecode.sv')) as f:
        text = f.read()
    if 'empty_slot' in text:
        raise AssertionError("the decoder keeps an empty-slot flop for the unmapped case")
    starts = []
    for cond in re.findall(r'if \((.*apb_addr.*)\) begin', text):
        match = re.fullmatch(r"apb_addr >= apbAddrSt'\(32'h([0-9a-f_]+)\)", cond)
        if not match:
            raise AssertionError(f"decode arm is not a single lower-bound compare: {cond}")
        starts.append(int(match.group(1).replace('_', ''), 16))
    if starts != ARM_STARTS:
        raise AssertionError(f"decode arm starts {[hex(a) for a in starts]}, expected {[hex(a) for a in ARM_STARTS]}")


def simulate(fixture):
    bench = os.path.join(fixture, 'decode_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH)
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'apbDecode.sv', 'leafA_regs.sv', 'leafA.sv',
            'leafB_regs.sv', 'leafB.sv')]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'decode_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vdecode_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_empty_slot_')
    try:
        generate(fixture)
        check_decoder_shape(fixture)
        simulate(fixture)
    except Exception as exc:
        print(f"FAIL: unmapped decoder address reads 32'hBADD_C0DE and drops writes: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: unmapped decoder address reads 32'hBADD_C0DE and drops writes")
    return 0


if __name__ == '__main__':
    sys.exit(main())
