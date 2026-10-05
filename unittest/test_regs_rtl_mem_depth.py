#!/usr/bin/env python3
"""A memory decodes only the rows its variant has.

leafA owns four memories and a memory register whose depth is the block
parameter TBL_DEPTH, 4 in the instance's variant and at most 8. The address
map reserves room for 8 rows, so each range holds 4 rows past the variant's
depth. tbl's address type is sized from TBL_DEPTH; tblFixed's is a fixed 3
bits that can name rows the RAM does not have. tblRo is read-only to firmware
and tblWo write-only. memReg is a memory register, backed here by a memory the
fixture adds to leafA.

An access past the variant's depth is no row of the memory. A read there
returns 32'hBADD_C0DE and a write is dropped, as for any address no register or
memory claims. Decoding the worst-case range instead truncates the row index,
so row 4 aliases row 0: the read returns row 0 and the write overwrites it.

The model registers each memory at the variant's depth, so its address map
agrees. A SystemC probe registers a 4-row memory over the same range and
checks the read past it returns 0xBADDC0DE and the write leaves row 0 alone.

The RTL fixture is generated outside the repository working tree, and a small
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
from test_watchdog_no_terminator import buildProbe

COMMON_SV = os.path.join(base_dir, 'common', 'systemVerilog')
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'memory', 'status')]

DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        TBL_DEPTH: {{ value: 4, maxValue: 8, desc: "per-instance memory depth" }}
    types:
        tblAddrT: {{ widthLog2minus1: TBL_DEPTH, desc: "row index sized from the depth" }}

types:
    fixedAddrT: {{ width: 3, desc: "fixed row index" }}

structures:
    tblAddrSt:
        address: {{ varType: tblAddrT, generator: address, desc: "memory address" }}
    fixedAddrSt:
        address: {{ varType: fixedAddrT, generator: address, desc: "memory address" }}
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
    - {{ memory: tbl, block: leafA, structure: memSt, addressStruct: tblAddrSt, wordLines: TBL_DEPTH, regAccess: true, desc: "depth-sized address" }}
    - {{ memory: tblFixed, block: leafA, structure: memSt, addressStruct: fixedAddrSt, wordLines: TBL_DEPTH, regAccess: true, desc: "fixed-width address" }}
    - {{ memory: tblRo, block: leafA, structure: memSt, addressStruct: tblAddrSt, wordLines: TBL_DEPTH, regAccess: ro, desc: "read-only to firmware" }}
    - {{ memory: tblWo, block: leafA, structure: memSt, addressStruct: tblAddrSt, wordLines: TBL_DEPTH, regAccess: wo, desc: "write-only to firmware" }}

registers:
    - {{ register: memReg, block: leafA, regType: memory, structure: memSt, addressStruct: tblAddrSt, wordLines: TBL_DEPTH, desc: "memory register" }}

parameters:
    leafA:
        small:
            TBL_DEPTH: 4
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=2)
          + render_leaf('leafA', extra_block_lines='        params: [TBL_DEPTH]\n'))

BENCH = """\
module depth_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();

    leafA #(.TBL_DEPTH(4)) uLeafA (.regs(bus), .clk(clk), .rst_n(rst_n));

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

    // Firmware cannot read tblWo, so its rows are checked directly.
    task automatic expect_row(input logic [15:0] got, input logic [15:0] want, input string what);
        if (got !== want) begin
            $display("TB_FAIL: %s: row holds 0x%0h, expected 0x%0h", what, got, want);
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
        // Rows 0-3 of tbl at 0x00, tblFixed at 0x20, tblRo at 0x40, tblWo
        // at 0x60 and memReg at 0x80. Firmware cannot write tblRo, so its
        // rows are loaded directly.
        uLeafA.uTblRo.mem[0] = 16'h4444;
        uLeafA.uTblRo.mem[3] = 16'h4747;
        write_reg(32'h00, 32'h1111, "write tbl row 0");
        write_reg(32'h0c, 32'h3333, "write tbl row 3");
        write_reg(32'h20, 32'h5555, "write tblFixed row 0");
        write_reg(32'h2c, 32'h7777, "write tblFixed row 3");
        write_reg(32'h10, 32'hdead, "write tbl row 4, past the depth");
        write_reg(32'h1c, 32'hbeef, "write tbl row 7, past the depth");
        write_reg(32'h30, 32'hdead, "write tblFixed row 4, past the depth");
        write_reg(32'h3c, 32'hbeef, "write tblFixed row 7, past the depth");
        write_reg(32'h60, 32'h6666, "write tblWo row 0");
        write_reg(32'h6c, 32'h6969, "write tblWo row 3");
        write_reg(32'h80, 32'h8888, "write memReg row 0");
        write_reg(32'h8c, 32'h8b8b, "write memReg row 3");
        write_reg(32'h50, 32'hdead, "write tblRo row 4, past the depth");
        write_reg(32'h5c, 32'hbeef, "write tblRo row 7, past the depth");
        write_reg(32'h70, 32'hdead, "write tblWo row 4, past the depth");
        write_reg(32'h7c, 32'hbeef, "write tblWo row 7, past the depth");
        write_reg(32'h90, 32'hdead, "write memReg row 4, past the depth");
        write_reg(32'h9c, 32'hbeef, "write memReg row 7, past the depth");
        expect_read(32'h00, 32'h1111, "tbl row 0 unchanged");
        expect_read(32'h0c, 32'h3333, "tbl row 3 unchanged");
        expect_read(32'h20, 32'h5555, "tblFixed row 0 unchanged");
        expect_read(32'h2c, 32'h7777, "tblFixed row 3 unchanged");
        expect_read(32'h10, 32'hBADD_C0DE, "tbl row 4 reads 32'hBADD_C0DE");
        expect_read(32'h1c, 32'hBADD_C0DE, "tbl row 7 reads 32'hBADD_C0DE");
        expect_read(32'h30, 32'hBADD_C0DE, "tblFixed row 4 reads 32'hBADD_C0DE");
        expect_read(32'h3c, 32'hBADD_C0DE, "tblFixed row 7 reads 32'hBADD_C0DE");
        expect_read(32'h40, 32'h4444, "tblRo row 0 unchanged");
        expect_read(32'h4c, 32'h4747, "tblRo row 3 unchanged");
        expect_read(32'h50, 32'hBADD_C0DE, "tblRo row 4 reads 32'hBADD_C0DE");
        expect_read(32'h5c, 32'hBADD_C0DE, "tblRo row 7 reads 32'hBADD_C0DE");
        expect_row(uLeafA.uTblWo.mem[0], 16'h6666, "tblWo row 0 unchanged");
        expect_row(uLeafA.uTblWo.mem[3], 16'h6969, "tblWo row 3 unchanged");
        expect_read(32'h70, 32'hBADD_C0DE, "tblWo row 4 reads 32'hBADD_C0DE");
        expect_read(32'h7c, 32'hBADD_C0DE, "tblWo row 7 reads 32'hBADD_C0DE");
        expect_read(32'h80, 32'h8888, "memReg row 0 unchanged");
        expect_read(32'h8c, 32'h8b8b, "memReg row 3 unchanged");
        expect_read(32'h90, 32'hBADD_C0DE, "memReg row 4 reads 32'hBADD_C0DE");
        expect_read(32'h9c, 32'hBADD_C0DE, "memReg row 7 reads 32'hBADD_C0DE");
        if (errors == 0) $display("TB_PASS");
        $finish;
    end
endmodule
"""

# The generated model's registration of a 2-byte, 4-row memory at 0x0, over
# the 8-row range the address map reserves for it.
PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "addressMap.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct depthAddrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const depthAddrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct depthDataSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint32_t _getData() const { return value; }
    void _setData( std::uint64_t v ) { value = static_cast<std::uint32_t>( v ); }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const depthDataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

// Rows indexed by the address the map hands over, with room past the depth.
struct stubMem : public addressBase {
    void cpu_write( std::uint64_t address, std::uint32_t val ) override { rows[( address / 4 ) % 8] = val; }
    std::uint32_t cpu_read( std::uint64_t address ) override { return rows[( address / 4 ) % 8]; }
    std::uint32_t rows[8] = {};
};

struct depthHarness : public sc_module
{
    apb_channel<depthAddrSt, depthDataSt> chan;
    sc_port<apb_in_if<depthAddrSt, depthDataSt>> in;
    logBlock log;
    addressMap regs;
    stubMem tbl;

    SC_HAS_PROCESS( depthHarness );
    depthHarness( sc_module_name n )
      : sc_module( n ), chan( "chan", "tb" ), in( "in" ), log( "depthHarness" ), regs( log )
    {
        in( chan );
        regs.addMemory( 0x0, 2, 4, "tbl", &tbl );
        SC_THREAD( handle );
        SC_THREAD( drive );
    }

    void handle() { registerHandler<depthAddrSt, depthDataSt>( regs, in, 0x1f ); }

    void write( std::uint32_t address, std::uint32_t value )
    {
        depthAddrSt addr;
        depthDataSt data;
        addr.value = address;
        data.value = value;
        chan.request( true, addr, data );
    }

    void read( std::uint32_t address )
    {
        depthAddrSt addr;
        depthDataSt data;
        addr.value = address;
        chan.request( false, addr, data );
        std::cout << std::format( "read 0x{:x}=0x{:x}\\n", address, data.value );
    }

    void drive()
    {
        write( 0x0, 0x1111 );
        write( 0x10, 0xdead );
        read( 0x10 );
        read( 0x0 );
        sc_stop();
    }
};

int sc_main( int, char*[] )
{
    depthHarness harness( "harness" );
    sc_start();
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    return code > 0 ? code : 0;
}
"""


def generate(fixture):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'memDepth'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'memDepth.db')
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


def check_model_registration(fixture):
    """The model registers each memory at the variant's depth, the form the
    probe exercises."""
    with open(os.path.join(fixture, 'model', 'leafA.cppm')) as f:
        text = f.read()
    for memory in ('TBL', 'TBLFIXED', 'TBLRO', 'TBLWO', 'MEMREG'):
        want = f"addMemory( REG_ADDR_LEAFA_{memory}, memSt::_byteWidth, Config::TBL_DEPTH,"
        if want not in text:
            raise AssertionError(f"model/leafA.cppm does not register {memory.lower()} at Config::TBL_DEPTH: {want}")


# A memory register's storage is the block's own RTL.
MEMREG_RAM = """\
memory_sp #(.DEPTH(TBL_DEPTH), .data_t(memSt)) uMemReg (.mem_port(memReg), .clk(clk));

endmodule: leafA"""


def simulate(fixture):
    leaf = os.path.join(fixture, 'rtl', 'leafA.sv')
    with open(leaf) as f:
        text = f.read()
    if 'endmodule: leafA' not in text:
        raise AssertionError(
            f"{leaf} has no 'endmodule: leafA' line to insert the memory RAM before")
    with open(leaf, 'w') as f:
        f.write(text.replace('endmodule: leafA', MEMREG_RAM))
    bench = os.path.join(fixture, 'depth_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH)
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'leafA_regs.sv', 'leafA.sv')]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'depth_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vdepth_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def run_probe(tmpdir):
    os.makedirs(tmpdir)
    binPath = buildProbe(tmpdir, PROBE_SRC)
    if not os.path.isfile(binPath):
        raise AssertionError(f"model probe must build and link: {binPath}")
    run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                         env=dict(os.environ, LD_LIBRARY_PATH=os.environ.get('SYSTEMC_LIBDIR', '')))
    output = run.stdout + run.stderr
    if run.returncode != 0:
        raise AssertionError(f"model probe exits with status {run.returncode}:\n{output}")
    for needle in ('read 0x10=0xbaddc0de', 'read 0x0=0x1111'):
        if needle not in output:
            raise AssertionError(f"model probe does not print {needle!r}:\n{output}")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_mem_depth_')
    try:
        generate(fixture)
        check_model_registration(fixture)
        run_probe(os.path.join(fixture, 'probe'))
        simulate(fixture)
    except Exception as exc:
        print(f"FAIL: an access past a memory's variant depth reads 32'hBADD_C0DE and drops the write: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: an access past a memory's variant depth reads 32'hBADD_C0DE and drops the write")
    return 0


if __name__ == '__main__':
    sys.exit(main())
