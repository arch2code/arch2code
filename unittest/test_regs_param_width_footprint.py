#!/usr/bin/env python3
"""Firmware sees a parameterizable-width register or memory at the address
map's worst-case footprint, the same way in the RTL and in the model.

leafA has the block parameter DW, 40 by default (`value:`) and at most 96
(`maxValue:`). Two variants bind it: wide (96) and narrow (8). The address
map sizes everything from the worst case, 96 bits.

- cfg is a rw register of DW bits. The map gives it three words. In the wide
  variant every word holds data. In the narrow variant the words above bit 7
  read 0 and drop writes.
- mem is a firmware-accessible memory of DW-bit rows, and memReg a memory
  register of the same shape whose RAM the block supplies. The map gives
  each row 16 bytes, so row N of every variant sits at N * 16. Bytes of a row
  above the variant's width read 0 and drop writes.

One firmware access sequence runs on the generated RTL under Verilator
`--binary --timing` and on a SystemC probe built from the generated model's
own declarations, initializers and address-map registration. The test
compares the two runs with each other and with the expected values. It does
so for two fixtures. In the first, leafA's own model decodes the registers.
In the second, leafA contains an instance, so a generated leafA_regs model
decodes them and reaches the storage through channels.
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
from test_watchdog_no_terminator import buildProbe

COMMON_SV = os.path.join(base_dir, 'common', 'systemVerilog')
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'memory', 'status')]

VARIANTS = {'wide': 96, 'narrow': 8}

DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        DW: {{ value: 40, maxValue: 96, desc: "per-instance data width" }}
    types:
        dataT: {{ width: DW, maxBitwidth: 96, desc: "parameterizable payload" }}

constants:
    MEM_DEPTH: {{ value: 8, desc: "memory depth" }}

types:
    memAddrT: {{ width: 3, desc: "row index" }}

structures:
    memAddrSt:
        address: {{ varType: memAddrT, generator: address, desc: "memory address" }}
    wideRegSt:
        data: {{ varType: dataT, generator: register, desc: "register payload" }}
    wideMemSt:
        data: {{ varType: dataT, generator: memory, desc: "memory payload" }}

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWide:      {{ container: top, instanceType: leafA, addressGroup: top, variant: wide }}
    uNarrow:    {{ container: top, instanceType: leafA, addressGroup: top, variant: narrow }}
{child}
connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfg, block: leafA, regType: rw, structure: wideRegSt, desc: "parameterizable register" }}
    - {{ register: memReg, block: leafA, regType: memory, structure: wideMemSt, addressStruct: memAddrSt, wordLines: MEM_DEPTH, desc: "parameterizable memory register" }}

memories:
    - {{ memory: mem, block: leafA, structure: wideMemSt, addressStruct: memAddrSt, wordLines: MEM_DEPTH, regAccess: true, desc: "parameterizable-width memory" }}

parameters:
    leafA:
        wide:
            DW: 96
        narrow:
            DW: 8
"""

CHILD = "    uChild:     { container: leafA, instanceType: child }\n"

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=4)
          + render_leaf('leafA', extra_block_lines='        params: [DW]\n'))

# Offsets as calcAddresses lays them out: the two 128-byte memories, then cfg.
OFFSETS = {'MEM': 0x000, 'MEMREG': 0x080, 'CFG': 0x100}
MEMORIES = {'mem': OFFSETS['MEM'], 'memReg': OFFSETS['MEMREG']}
CFG = OFFSETS['CFG']
CFG_WORDS = (0x11111111, 0x22222222, 0x33333333)
ROW = 16


def build_sequence():
    """(variant, write?, address, data) accesses, and the reads and rows they
    should leave. Every write precedes the reads."""
    writes, reads, want_reads, want_rows = [], [], {}, {}
    for v, width in VARIANTS.items():
        mask = (1 << width) - 1
        for n, d in enumerate(CFG_WORDS):
            writes.append((v, CFG + 4 * n, d))
            reads.append((v, CFG + 4 * n))
            want_reads[(v, CFG + 4 * n)] = d & (mask >> (32 * n)) & 0xffffffff
    for name, base in MEMORIES.items():
        # Rows 1 and 4 of the narrow variant, plus a word of each row above
        # the variant's width.
        for row, d, above in ((1, 0xa1, 4), (4, 0xa4, 8)):
            writes.append(('narrow', base + row * ROW, d))
            writes.append(('narrow', base + row * ROW + above, 0xdeadbeef))
            reads += [('narrow', base + row * ROW), ('narrow', base + row * ROW + above)]
            want_reads[('narrow', base + row * ROW)] = d
            want_reads[('narrow', base + row * ROW + above)] = 0
        # Every word of row 1 of the wide variant, then the word above its
        # 96 bits.
        for n, d in enumerate(CFG_WORDS):
            writes.append(('wide', base + ROW + 4 * n, d))
        for n in range(4):
            reads.append(('wide', base + ROW + 4 * n))
            want_reads[('wide', base + ROW + 4 * n)] = CFG_WORDS[n] if n < 3 else 0
        for v in VARIANTS:
            for row in range(8):
                want_rows[(v, name, row)] = 0
        want_rows[('narrow', name, 1)] = 0xa1
        want_rows[('narrow', name, 4)] = 0xa4
        want_rows[('wide', name, 1)] = (CFG_WORDS[2] << 64) | (CFG_WORDS[1] << 32) | CFG_WORDS[0]
    sequence = [(v, True, a, d) for v, a, d in writes] + [(v, False, a, 0) for v, a in reads]
    return sequence, want_reads, want_rows


BENCH = """\
module footprint_tb
    import shared_package::*;
;
    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus_wide();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus_narrow();

    leafA #(.DW(96)) uWide (.regs(bus_wide), .clk(clk), .rst_n(rst_n));
    leafA #(.DW(8)) uNarrow (.regs(bus_narrow), .clk(clk), .rst_n(rst_n));

    // One APB master; sel picks the instance it reaches.
    logic sel_narrow = 0;
    logic psel = 0, penable = 0, pwrite = 0;
    logic [31:0] paddr = 0, pwdata = 0;
    assign bus_wide.psel = psel & !sel_narrow;
    assign bus_narrow.psel = psel & sel_narrow;
    assign bus_wide.penable = penable;
    assign bus_narrow.penable = penable;
    assign bus_wide.pwrite = pwrite;
    assign bus_narrow.pwrite = pwrite;
    assign bus_wide.paddr = paddr;
    assign bus_narrow.paddr = paddr;
    assign bus_wide.pwdata = pwdata;
    assign bus_narrow.pwdata = pwdata;
    wire pready = sel_narrow ? bus_narrow.pready : bus_wide.pready;
    wire [31:0] prdata = sel_narrow ? bus_narrow.prdata : bus_wide.prdata;

    // One transfer, starting at a negedge.
    task automatic access(input logic narrow, input logic write, input logic [31:0] addr,
                          input logic [31:0] wdata);
        int cycles = 0;
        sel_narrow = narrow;
        psel = 1; penable = 0; pwrite = write; paddr = addr; pwdata = wdata;
        @(negedge clk);
        penable = 1;
        while (!pready) begin
            @(negedge clk);
            cycles++;
            if (cycles > 50) begin
                $display("TB_FAIL: %s 0x%0h never completed", write ? "write" : "read", addr);
                $finish;
            end
        end
        if (!write && narrow) $display("narrow read 0x%0h=0x%0h", addr, prdata);
        if (!write && !narrow) $display("wide read 0x%0h=0x%0h", addr, prdata);
        @(negedge clk);
        penable = 0;
        psel = 0;
        repeat (3) @(negedge clk);
    endtask

    initial begin
        for (int i = 0; i < 8; i++) begin
            uWide.uMem.mem[i] = '0;
            uNarrow.uMem.mem[i] = '0;
            uWide.uMemReg.mem[i] = '0;
            uNarrow.uMemReg.mem[i] = '0;
        end
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
{accesses}
        for (int i = 0; i < 8; i++) begin
            $display("wide mem row %0d=0x%0h", i, uWide.uMem.mem[i]);
            $display("narrow mem row %0d=0x%0h", i, uNarrow.uMem.mem[i]);
            $display("wide memReg row %0d=0x%0h", i, uWide.uMemReg.mem[i]);
            $display("narrow memReg row %0d=0x%0h", i, uNarrow.uMemReg.mem[i]);
        end
        $display("TB_DONE");
        $finish;
    end
endmodule
"""

# memReg's RAM is the block's own RTL.
MEMREG_RAM = """\
memory_sp #(.DEPTH(MEM_DEPTH), .data_t(wideMemSt)) uMemReg (.mem_port(memReg), .clk(clk));

endmodule: leafA"""

# The generated model's member declarations, constructor initializers and
# constructor body lines are pasted into {cls}, which derives from {base}, a
# stand-in for the generated base class. {extras} adds what the rest of the
# design provides: memReg's RAM and, when a separate handler model decodes
# the registers, the channels and memories its ports reach.
PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
#include "memory_channel.h"
#include "status_channel.h"
#include <algorithm>
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct busAddrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const busAddrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct busDataSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint32_t _getData() const { return value; }
    void _setData( std::uint64_t v ) { value = static_cast<std::uint32_t>( v ); }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const busDataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct memAddrSt {
    static constexpr uint16_t _bitWidth = 3;
    static constexpr uint16_t _byteWidth = 1;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    void unpack( const _packedSt& p ) { value = p; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const memAddrSt& o ) const { return value == o.value; }
    std::uint64_t value = 0;
};

// A W-bit payload with the members the generated structures have.
template<uint32_t W>
struct payload_v {
    std::uint64_t word[2] = {0, 0};
    static constexpr uint16_t _bitWidth = W;
    static constexpr uint16_t _byteWidth = ( W + 7 ) >> 3;
    typedef std::uint64_t _packedSt[2];
    payload_v() {}
    explicit payload_v( const _packedSt& p ) { unpack( p ); }
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return word[0]; }
    void unpack( const _packedSt& p )
    {
        word[0] = W >= 64 ? p[0] : p[0] & ( ( 1ull << W ) - 1 );
        word[1] = W > 64 ? p[1] & ( W >= 128 ? ~0ull : ( ( 1ull << ( W - 64 ) ) - 1 ) ) : 0;
    }
    sc_bv<W> sc_pack() const
    {
        sc_bv<W> b;
        b.range( std::min<uint32_t>( W, 64 ) - 1, 0 ) = word[0];
        if constexpr ( W > 64 ) b.range( W - 1, 64 ) = word[1];
        return b;
    }
    void sc_unpack( sc_bv<W> b )
    {
        word[0] = b.range( std::min<uint32_t>( W, 64 ) - 1, 0 ).to_uint64();
        if constexpr ( W > 64 ) word[1] = b.range( W - 1, 64 ).to_uint64();
    }
    bool operator==( const payload_v& o ) const { return word[0] == o.word[0] && word[1] == o.word[1]; }
    std::string prt( bool = false ) const { return hex(); }
    std::string hex() const
    {
        return word[1] ? std::format( "0x{:x}{:016x}", word[1], word[0] ) : std::format( "0x{:x}", word[0] );
    }
};

template<typename Config> using wideRegSt = payload_v<Config::DW>;
template<typename Config> using wideMemSt = payload_v<Config::DW>;
constexpr uint32_t MEM_DEPTH = 8;

struct wideConfig { static constexpr uint32_t DW = 96; };
struct narrowConfig { static constexpr uint32_t DW = 8; };

template<typename Config>
struct {base} {
    using wideRegSt = ::wideRegSt<Config>;
    using wideMemSt = ::wideMemSt<Config>;
{base_ports}
};

template<typename Config>
struct {cls} : public sc_module, public {base}<Config>
{
    apb_channel<busAddrSt, busDataSt> chan;
    sc_port<apb_in_if<busAddrSt, busDataSt>> in;
    logBlock log_;
    addressMap _a2cRegs;
    memories mems;
{decls}
    using typename {base}<Config>::wideRegSt;
    using typename {base}<Config>::wideMemSt;
{extras}

    SC_HAS_PROCESS( {cls} );
    {cls}( sc_module_name n )
      : sc_module( n ), chan( "chan", "tb" ), in( "in" ), log_( "{cls}" ), _a2cRegs( log_ )
{inits}
{extra_inits}
    {
        in( chan );
{body}
{binds}
        SC_THREAD( handle );
    }

    void handle() { registerHandler<busAddrSt, busDataSt>( _a2cRegs, in, 0x1ff ); }

    void access( bool write, std::uint32_t address, std::uint32_t value, const char* variant )
    {
        busAddrSt addr;
        busDataSt data;
        addr.value = address;
        data.value = value;
        chan.request( write, addr, data );
        if ( !write ) std::cout << std::format( "{} read 0x{:x}=0x{:x}\\n", variant, address, data.value );
    }

    void dump( const char* variant )
    {
        for ( int i = 0; i < 8; i++ ) {
            std::cout << std::format( "{} mem row {}={}\\n", variant, i, {mem_rows}[i].hex() );
            std::cout << std::format( "{} memReg row {}={}\\n", variant, i, memRegStore[i].hex() );
        }
    }
};

struct driver : public sc_module
{
    {cls}<wideConfig> wide;
    {cls}<narrowConfig> narrow;

    SC_HAS_PROCESS( driver );
    driver( sc_module_name n ) : sc_module( n ), wide( "wide" ), narrow( "narrow" ) { SC_THREAD( run ); }

    void run()
    {
{accesses}
        wide.dump( "wide" );
        narrow.dump( "narrow" );
        std::cout << "TB_DONE\\n";
        sc_stop();
    }
};

int sc_main( int, char*[] )
{
    driver top( "top" );
    sc_start();
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    return code > 0 ? code : 0;
}
"""

# Per fixture: the generated model file, its class and base, and the probe's
# stand-ins for the rest of the design.
MODELS = {
    'flat': dict(
        file='leafA.cppm', cls='leafA', base='leafABase', base_ports='',
        extras='    hwMemory< wideMemSt > memRegStore;',
        extra_inits='        ,memRegStore( name(), "memRegStore", mems, MEM_DEPTH )',
        binds='        memRegStore.bindPort( memReg_channel );',
        mem_rows='mem'),
    'hier': dict(
        file='leafA_regs.cppm', cls='leafA_regs', base='leafA_regsBase',
        base_ports=('    status_out< wideRegSt > cfg{ "cfg" };\n'
                    '    memory_out< memAddrSt, wideMemSt > memReg{ "memReg" };\n'
                    '    memory_out< memAddrSt, wideMemSt > mem{ "mem" };'),
        extras=('    status_channel< wideRegSt > cfg_channel;\n'
                '    memory_channel< memAddrSt, wideMemSt > mem_channel;\n'
                '    memory_channel< memAddrSt, wideMemSt > memReg_channel;\n'
                '    hwMemory< wideMemSt > memStore;\n'
                '    hwMemory< wideMemSt > memRegStore;'),
        extra_inits=('        ,cfg_channel( "cfg_channel", "leafA" )\n'
                     '        ,mem_channel( "mem_channel", "leafA" )\n'
                     '        ,memReg_channel( "memReg_channel", "leafA" )\n'
                     '        ,memStore( name(), "memStore", mems, MEM_DEPTH )\n'
                     '        ,memRegStore( name(), "memRegStore", mems, MEM_DEPTH )'),
        binds=('        this->cfg( cfg_channel );\n'
               '        this->mem( mem_channel );\n'
               '        this->memReg( memReg_channel );\n'
               '        memStore.bindPort( mem_channel );\n'
               '        memRegStore.bindPort( memReg_channel );'),
        mem_rows='memStore'),
}


def generate(fixture, hier):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'paramWidth'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    blocks = BLOCKS + (render_plain_block('child') if hier else '')
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=blocks, child=CHILD if hier else ''))
    db = os.path.join(fixture, 'paramWidth.db')
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


def generated_regions(path):
    """The generated header, constructor-initializer and constructor-body
    regions of a model file, in that order."""
    with open(path) as f:
        text = f.read()
    regions = re.findall(r'GENERATED_CODE_BEGIN (--template=\S+(?: --section=\S+)?)\n(.*?)GENERATED_CODE_END',
                         text, re.S)
    by_name = {name: body.splitlines() for name, body in regions}
    header = by_name.get('--template=classDecl') or by_name['--template=blockRegs --section=header']
    init = by_name.get('--template=constructor --section=init') or by_name['--template=blockRegs --section=init']
    body = by_name.get('--template=constructor --section=body') or by_name['--template=blockRegs --section=body']
    return header, init, body


def model_lines(fixture, model):
    """The generated lines the probe pastes: register and memory member
    declarations, their initializers, the address constants, the address-map
    registration and the local port bindings."""
    path = os.path.join(fixture, 'model', model['file'])
    header, init, body = generated_regions(path)
    decls = [re.sub(r'\s*//.*$', '', line) for line in header
             if re.match(r'\s*(hwRegister|hwRegisterIf|hwMemory|hwMemoryPort|memory_channel|memory_out)<', line)]
    inits = [line for line in init
             if line.lstrip().startswith(',') and not re.match(r'\s*,(blockBase|\w+Base<Config>|_a2cRegs)\(', line)]
    stmts = [line for line in body
             if re.match(r'\s*(constexpr uint64_t REG_ADDR_|_a2cRegs\.add|\w+_port\(\w+_channel\);)', line)]
    found = {name: int(value, 16) for name, value in
             (re.match(r'\s*constexpr uint64_t REG_ADDR_LEAFA_(\w+) = 0x([0-9a-f]+);', line).groups()
              for line in stmts if line.lstrip().startswith('constexpr'))}
    if found != OFFSETS:
        raise AssertionError(f"{path} places the registers at {found}, the sequence assumes {OFFSETS}")
    return decls, inits, stmts


def run_model(fixture, kind, sequence):
    model = MODELS[kind]
    decls, inits, stmts = model_lines(fixture, model)
    accesses = '\n'.join(
        f"        {v}.access( {'true' if w else 'false'}, 0x{a:x}, 0x{d:x}, \"{v}\" );"
        for v, w, a, d in sequence)
    src = PROBE_SRC
    for key, value in (('{decls}', '\n'.join(decls)), ('{inits}', '\n'.join(inits)),
                       ('{body}', '\n'.join(stmts)), ('{accesses}', accesses),
                       ('{base_ports}', model['base_ports']), ('{extras}', model['extras']),
                       ('{extra_inits}', model['extra_inits']), ('{binds}', model['binds']),
                       ('{mem_rows}', model['mem_rows']), ('{base}', model['base']), ('{cls}', model['cls'])):
        src = src.replace(key, value)
    probe_dir = os.path.join(fixture, 'probe')
    os.makedirs(probe_dir)
    binPath = buildProbe(probe_dir, src)
    if not os.path.isfile(binPath):
        raise AssertionError(f"model probe must build and link: {binPath}")
    run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                         env=dict(os.environ, LD_LIBRARY_PATH=os.environ.get('SYSTEMC_LIBDIR', '')))
    output = run.stdout + run.stderr
    if run.returncode != 0 or 'TB_DONE' not in run.stdout:
        raise AssertionError(f"model probe exits with status {run.returncode}:\n{output[-3000:]}")
    return output


def run_rtl(fixture, sequence):
    leaf = os.path.join(fixture, 'rtl', 'leafA.sv')
    with open(leaf) as f:
        text = f.read()
    if 'endmodule: leafA' not in text:
        raise AssertionError(f"{leaf} has no 'endmodule: leafA' line to insert memReg's RAM before")
    rtl_names = ['shared_package.sv', 'top_package.sv', 'leafA_regs.sv', 'leafA.sv']
    if os.path.exists(os.path.join(fixture, 'rtl', 'child.sv')):
        rtl_names.append('child.sv')
    with open(leaf, 'w') as f:
        f.write(text.replace('endmodule: leafA', MEMREG_RAM))
    accesses = '\n'.join(
        f"        access({int(v == 'narrow')}, {int(w)}, 32'h{a:x}, 32'h{d:x});"
        for v, w, a, d in sequence)
    bench = os.path.join(fixture, 'footprint_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH.replace('{accesses}', accesses))
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in rtl_names]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'footprint_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vfootprint_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_DONE' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")
    return run.stdout


def parse(output):
    reads = {(m[0], int(m[1], 16)): int(m[2], 16)
             for m in re.findall(r'^(\w+) read 0x([0-9a-f]+)=0x([0-9a-f]+)', output, re.M)}
    rows = {(m[0], m[1], int(m[2])): int(m[3], 16)
            for m in re.findall(r'^(\w+) (\w+) row (\d+)=0x([0-9a-f]+)', output, re.M)}
    return reads, rows


def key_name(key):
    """('narrow', 0x40) -> narrow@0x40; ('wide', 'mem', 1) -> wide@mem@1."""
    return '@'.join(hex(p) if isinstance(p, int) and p >= 8 else str(p) for p in key)


def fmt(values, keys):
    return ', '.join(f"{key_name(k)}={hex(values[k]) if k in values else 'missing'}" for k in keys) or 'none'


def compare(rtl_out, model_out, want_reads, want_rows):
    """Report every read and row where the RTL, the model and the expected
    value disagree."""
    rtl_reads, rtl_rows = parse(rtl_out)
    model_reads, model_rows = parse(model_out)
    problems = []
    for name, want, got_rtl, got_model in (('reads', want_reads, rtl_reads, model_reads),
                                           ('rows', want_rows, rtl_rows, model_rows)):
        keys = [k for k in sorted(set(want) | set(got_rtl) | set(got_model))
                if got_rtl.get(k) != want.get(k) or got_model.get(k) != want.get(k)]
        if keys:
            problems.append(f"{name} where the RTL or the model differs from the expected value:\n"
                            f"  RTL:      {fmt(got_rtl, keys)}\n"
                            f"  model:    {fmt(got_model, keys)}\n"
                            f"  expected: {fmt(want, keys)}")
    if problems:
        raise AssertionError('\n'.join(problems))


def check(kind):
    sequence, want_reads, want_rows = build_sequence()
    fixture = tempfile.mkdtemp(prefix=f'a2c_param_width_{kind}_')
    try:
        generate(fixture, kind == 'hier')
        model_out = run_model(fixture, kind, sequence)
        rtl_out = run_rtl(fixture, sequence)
        compare(rtl_out, model_out, want_reads, want_rows)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def main():
    checks = [
        ('flat', "leafA's model and RTL decode the parameterizable register, memory and memory "
                 "register at the worst-case footprint"),
        ('hier', "a generated leafA_regs model and the RTL decode the parameterizable register, memory "
                 "and memory register at the worst-case footprint"),
    ]
    failed = 0
    for kind, label in checks:
        try:
            check(kind)
        except Exception as exc:
            print(f"FAIL: {label}: {exc}")
            failed += 1
        else:
            print(f"PASS: {label}")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
