#!/usr/bin/env python3
"""The generated AHB-Lite router and register handler RTL answer every transfer correctly.

The fixture has a router with four 0x1000-byte slots, leafA in slot 0 and leafB
in slot 1, so 0x2000 is an empty slot. leafA holds a four-word table at 0x0, rw
cfg at 0x10, ro stat at 0x18 and ext cmd at 0x20, so 0x14 is a gap. leafA's
owner logic refuses a cmd write of 0x0bad and keeps the value it last accepted.

For fileGeneration.regBusErrorResponses off and on, the test generates the
fixture outside the working tree, checks the generated SystemC uses the AHB
channel, and runs a bench under Verilator `--binary --timing`. The bench is an
AHB-Lite master that presents the next address phase in the last cycle of the
current data phase, so it drives back-to-back transfers, and it can put IDLE or
BUSY cycles between them. It drives the router, then a second leafA directly.
For each transfer it checks the read data, HRESP, the two-cycle error response
and the number of wait states. The bench ends with TB_PASS on stdout.
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

from _addrctl_helpers import render_leaf, render_plain_block, render_router
from test_memory_firmware_access import PROJECT, _arch2code, _generated_files

COMMON_SV = os.path.join(base_dir, 'common', 'systemVerilog')
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('ahb', 'status', 'external_reg', 'memory')]

SHARED = """constants:
    DWORD:     { value: 32, desc: "Register bus width" }
    TBL_WORDS: { value: 4,  desc: "Table rows" }

types:
    ahbAddrT: { width: DWORD, desc: "AHB address" }
    ahbDataT: { width: DWORD, desc: "AHB data" }
    cfgT:     { width: 16,    desc: "Register payload" }
    tblAddrT: { width: 2,     desc: "Table row" }

structures:
    ahbAddrSt:
        address: { varType: ahbAddrT, generator: address }
    ahbDataSt:
        data: { varType: ahbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    tblSt:
        data: { varType: ahbDataT }
    tblAddrSt:
        address: { varType: tblAddrT }

interfaces:
    ahbReg:
        desc: "AHB register bus"
        interfaceType: ahb
        structures:
            - { structure: ahbAddrSt, structureType: addr_t }
            - { structure: ahbDataSt, structureType: data_t }
"""

DESIGN = """include:
    - shared.yaml

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAHBDecode: {{ container: top, instanceType: ahbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top }}

connections:
    - {{ interface: ahbReg, src: uCPU, dst: uAHBDecode }}

memories:
    - {{ memory: tbl, block: leafA, structure: tblSt, wordLines: TBL_WORDS, addressStruct: tblAddrSt, memoryType: singlePort, regAccess: true, desc: "table" }}

registers:
    - {{ register: cfg,  regType: rw,  block: leafA, structure: cfgRegSt, desc: "rw register" }}
    - {{ register: stat, regType: ro,  block: leafA, structure: cfgRegSt, desc: "ro register" }}
    - {{ register: cmd,  regType: ext, block: leafA, structure: cfgRegSt, desc: "ext register" }}
    - {{ register: cfgB, regType: rw,  block: leafB, structure: cfgRegSt, desc: "rw register" }}
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('ahbDecode', 'top', address_increment='0x1000', max_address_spaces=4,
                          upstream_port='ahbReg', register_decoder_port='ahbReg')
          + render_leaf('leafA', interface='ahbReg') + render_leaf('leafB', interface='ahbReg'))

# leafA's hand-written logic, appended before its endmodule.
OWNER = """
    assign stat.data.value = 16'h5a5a;
    logic cmdRefused;
    assign cmdRefused = cmd.wdata.value == 16'h0bad;
    assign cmd.pslverr = cmdRefused;
    `DFF_INST(cfgRegSt, cmdReg)
    always_comb begin
        n_cmdReg = cmdReg;
        if (|cmd.write && !cmdRefused) begin
            n_cmdReg = cmd.wdata;
        end
    end
    assign cmd.rdata = cmdReg;
"""

# Each transfer: write, address, write data, HSIZE, HTRANS SEQ, idle cycles
# before its address phase, check read data, expected read data, HRESP ERROR
# expected with the option on, wait states with the option off and on (-1:
# not checked), description.
ROUTER_TRANSFERS = [
    (1, 0x0010, 0x1111, 2, 0, 2, 0, 0,          0, 2, 2, "cfg write"),
    (0, 0x0010, 0,      2, 0, 0, 1, 0x1111,     0, 2, 2, "cfg read, back-to-back"),
    (1, 0x0018, 0xffff, 2, 0, 1, 0, 0,          0, 2, 2, "ro write is dropped without an error"),
    (0, 0x0018, 0,      2, 0, 1, 1, 0x5a5a,     0, 2, 2, "ro read"),
    (1, 0x0020, 0x0bad, 2, 0, 1, 0, 0,          1, 2, 4, "ext write the owner refuses"),
    (1, 0x0020, 0x0001, 2, 0, 0, 0, 0,          0, 2, 2, "ext write the owner accepts, back-to-back"),
    (0, 0x0020, 0,      2, 0, 1, 1, 0x0001,     0, 2, 2, "ext read"),
    (1, 0x0014, 0xffff, 2, 0, 1, 0, 0,          1, 2, 4, "register block gap write"),
    (0, 0x0014, 0,      2, 0, 0, 1, 0xBADDC0DE, 1, 2, 4, "register block gap read, back-to-back"),
    (1, 0x2000, 0xffff, 2, 0, 1, 0, 0,          1, 1, 2, "empty router slot write"),
    (0, 0x2000, 0,      2, 0, 0, 1, 0xBADDC0DE, 1, 1, 2, "empty router slot read, back-to-back"),
    (1, 0x0004, 0xabcd, 2, 0, 1, 0, 0,          0, 2, 2, "table write"),
    (0, 0x0004, 0,      2, 0, 1, 1, 0xabcd,     0, 4, 4, "table read waits on the memory"),
    (1, 0x1000, 0x2222, 2, 0, 0, 0, 0,          0, 2, 2, "leafB write"),
    (0, 0x1000, 0,      2, 0, 0, 1, 0x2222,     0, 2, 2, "leafB read"),
    (1, 0x0010, 0x9999, 0, 0, 1, 0, 0,          1, 2, 4, "byte write is not written"),
    (0, 0x0010, 0,      0, 0, 1, 1, 0x1111,     0, 2, 2, "byte read returns the word, and cfg kept its value"),
    (0, 0x0010, 0,      2, 1, 1, 1, 0x1111,     0, 2, 2, "SEQ read is a single transfer"),
    (0, 0x0018, 0,      2, 0, 3, 1, 0x5a5a,     0, 2, 2, "read after BUSY cycles"),
]

DIRECT_TRANSFERS = [
    (1, 0x0010, 0x1111, 2, 0, 2, 0, 0,          0, 0, 0, "direct cfg write"),
    (0, 0x0010, 0,      2, 0, 0, 1, 0x1111,     0, 1, 1, "direct cfg read, back-to-back"),
    (1, 0x0020, 0x0bad, 2, 0, 0, 0, 0,          1, 1, 2, "direct refused ext write, back-to-back"),
    (0, 0x0020, 0,      2, 0, 0, 1, 0x0000,     0, 1, 1, "direct ext read after the refusal, back-to-back"),
    (1, 0x0008, 0x7777, 2, 0, 1, 0, 0,          0, 0, 0, "direct table write"),
    (1, 0x000c, 0x5555, 2, 0, 1, 0, 0,          0, 0, 0, "direct table write, second row"),
    (0, 0x0008, 0,      2, 0, 1, 1, 0x7777,     0, 2, 2, "direct table read"),
    (0, 0x000c, 0,      2, 0, 0, 1, 0x5555,     0, 3, 3, "direct table read of another row, back-to-back"),
    (1, 0x0014, 0xffff, 2, 0, 0, 0, 0,          1, 1, 2, "direct gap write, back-to-back"),
    (1, 0x0010, 0x9999, 1, 0, 1, 0, 0,          1, 0, 1, "direct halfword write is not written"),
    (0, 0x0010, 0,      2, 0, 0, 1, 0x1111,     0, 1, 1, "direct cfg kept its value, back-to-back"),
]

BENCH = """\
module ahb_tb
    import shared_package::*;
;
    localparam bit ERR = {err};
    localparam int N = {count};

    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) bus();
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) busA();
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) busB();
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) busD();

    ahbDecode uAHBDecode (.ahbReg(bus), .ahbReg_uLeafA(busA), .ahbReg_uLeafB(busB), .clk(clk), .rst_n(rst_n));
    leafA uLeafA (.regs(busA), .clk(clk), .rst_n(rst_n));
    leafB uLeafB (.regs(busB), .clk(clk), .rst_n(rst_n));
    leafA uLeafD (.regs(busD), .clk(clk), .rst_n(rst_n));

    // One master; direct selects busD instead of the router.
    logic direct = 0;
    logic m_hsel = 0, m_hwrite = 0;
    logic [1:0] m_htrans = 0;
    logic [2:0] m_hsize = 2;
    logic [31:0] m_haddr = 0, m_hwdata = 0;
    assign bus.hsel = m_hsel & ~direct;     assign busD.hsel = m_hsel & direct;
    assign bus.htrans = m_htrans;           assign busD.htrans = m_htrans;
    assign bus.haddr = m_haddr;             assign busD.haddr = m_haddr;
    assign bus.hwrite = m_hwrite;           assign busD.hwrite = m_hwrite;
    assign bus.hsize = m_hsize;             assign busD.hsize = m_hsize;
    assign bus.hwdata = m_hwdata;           assign busD.hwdata = m_hwdata;
    assign bus.hready = bus.hreadyout;      assign busD.hready = busD.hreadyout;
    logic s_hreadyout, s_hresp;
    logic [31:0] s_hrdata;
    assign s_hreadyout = direct ? busD.hreadyout : bus.hreadyout;
    assign s_hresp     = direct ? busD.hresp     : bus.hresp;
    assign s_hrdata    = direct ? busD.hrdata    : bus.hrdata;

    logic t_write [N];
    logic [31:0] t_addr [N], t_wdata [N], t_want [N];
    logic [2:0] t_size [N];
    logic t_seq [N], t_check [N], t_err [N];
    int t_idle [N], t_waits [N];
    string t_what [N];
    logic t_direct [N];
    logic [1:0] idle_trans [N];

    int errors = 0;

    task automatic check(input int i, input logic [31:0] rdata, input logic resp, input logic err1, input int waits);
        logic want_err;
        want_err = ERR & t_err[i];
        if (resp !== want_err) begin
            $display("TB_FAIL: %s: HRESP %0b, expected %0b", t_what[i], resp, want_err);
            errors++;
        end else if (want_err && !err1) begin
            $display("TB_FAIL: %s: ERROR without a first cycle with HREADYOUT low", t_what[i]);
            errors++;
        end else if (t_check[i] && rdata !== t_want[i]) begin
            $display("TB_FAIL: %s: read 0x%0h, expected 0x%0h", t_what[i], rdata, t_want[i]);
            errors++;
        end else if (t_waits[i] >= 0 && waits != t_waits[i]) begin
            $display("TB_FAIL: %s: %0d wait states, expected %0d", t_what[i], waits, t_waits[i]);
            errors++;
        end else begin
            $display("TB_OK: %s (%0d wait states)", t_what[i], waits);
        end
    endtask

    // Runs transfers first..last-1. Each negedge drives the cycle up to the
    // next posedge: the address phase of ap and the write data of dp. With
    // HREADYOUT high in that cycle, dp completes and ap is accepted. A
    // transfer with t_idle 0 is presented in the last data-phase cycle of the
    // one before it; otherwise t_idle cycles with no transfer come between.
    task automatic run(input int first, input int last);
        int ap, dp, next, idle, waits, cycles;
        logic err1;
        dp = -1; ap = -1; next = first; idle = 0; waits = 0; err1 = 0; cycles = 0;
        direct = t_direct[first];
        while (next < last || ap >= 0 || dp >= 0) begin
            if (ap < 0 && next < last) begin
                if (idle < t_idle[next]) begin
                    // count only cycles with no transfer in its data phase
                    if (dp < 0) idle++;
                end else begin
                    ap = next; next++; idle = 0;
                end
            end
            m_hsel = 1;
            if (ap >= 0) begin
                m_htrans = t_seq[ap] ? 2'b11 : 2'b10; m_haddr = t_addr[ap];
                m_hwrite = t_write[ap]; m_hsize = t_size[ap];
            end else begin
                m_htrans = next < last ? idle_trans[next] : 2'b00;
                m_hsel = m_htrans != 2'b00; m_haddr = 32'h10; m_hwrite = 1; m_hsize = 2;
            end
            m_hwdata = (dp >= 0 && t_write[dp]) ? t_wdata[dp] : 32'hdead_beef;
            #1;
            if (dp < 0 && !s_hreadyout) begin
                $display("TB_FAIL: HREADYOUT low with no transfer in its data phase");
                errors++;
            end
            if (dp >= 0) begin
                if (s_hreadyout) begin
                    check(dp, s_hrdata, s_hresp, err1, waits);
                    waits = 0; err1 = 0;
                end else begin
                    waits++;
                    err1 = s_hresp;
                end
            end
            if (s_hreadyout) begin
                dp = ap; ap = -1;
            end
            @(negedge clk);
            if (++cycles > 1000) begin
                $display("TB_FAIL: transfers never completed");
                $finish;
            end
        end
    endtask

    initial begin
{fill}
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        run(0, {router_count});
        run({router_count}, N);
        if (errors == 0) $display("TB_PASS");
        $finish;
    end
endmodule
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def generate(fixture, error_responses):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    project = PROJECT.replace('fwAccess', 'ahbRegBus')
    if error_responses:
        project += "    regBusErrorResponses: true\n"
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(project)
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(SHARED)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'ahbRegBus.db')
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
    leaf = os.path.join(fixture, 'rtl', 'leafA.sv')
    with open(leaf) as f:
        text = f.read()
    with open(leaf, 'w') as f:
        f.write(text.replace('endmodule: leafA', OWNER + '\nendmodule: leafA'))


def read(fixture, rel):
    with open(os.path.join(fixture, rel)) as f:
        return f.read()


def check_generated(fixture, error_responses):
    """The SystemC side uses the AHB channel, and the RTL the AHB front end at
    the addresses the bench assumes."""
    label = 'on' if error_responses else 'off'
    check("regBusDecode< ahbAddrSt, ahbDataSt, ahb_in_if, ahb_out_if > decoder;"
          in read(fixture, 'model/ahbDecode.cppm'), f"{label}: router model decodes over the AHB channel")
    check('#include "ahb_channel.h"' in read(fixture, 'model/leafA.cppm'), f"{label}: leafA model includes the AHB channel")
    regs = read(fixture, 'rtl/leafA_regs.sv')
    router = read(fixture, 'rtl/ahbDecode.sv')
    check("parameter bit AHB_READY_1WS = 0" in regs, f"{label}: handler names the AHB wait-state parameter")
    for name, offset in (('TBL', 0x0), ('CFG', 0x10), ('STAT', 0x18), ('CMD', 0x20)):
        check(f"localparam int unsigned REG_LEAFA_{name} = 32'h{offset:08x};" in regs,
              f"{label}: leafA {name.lower()} is at 0x{offset:x}")
    check("psel" not in regs + router, f"{label}: no APB signal in the AHB router or handler")
    subword = "assign ahb_subword_err = ahb_subword_wr;" if error_responses else "assign ahb_subword_err = 1'b0;"
    check(subword in regs, f"{label}: a sub-word write {'is' if error_responses else 'is not'} an error")


def bench_source(error_responses):
    transfers = [(row, 0) for row in ROUTER_TRANSFERS] + [(row, 1) for row in DIRECT_TRANSFERS]
    fill = []
    for i, ((write, addr, wdata, size, seq, idle, check_data, want, err_on, waits_off, waits_on, what),
            direct) in enumerate(transfers):
        waits = waits_on if error_responses else waits_off
        busy = "2'b01" if what.startswith("read after BUSY") else "2'b00"
        fill.append(f"        t_write[{i}] = {write}; t_addr[{i}] = 32'h{addr:x}; t_wdata[{i}] = 32'h{wdata:x}; "
                    f"t_size[{i}] = {size}; t_seq[{i}] = {seq}; t_idle[{i}] = {idle}; t_check[{i}] = {check_data}; "
                    f"t_want[{i}] = 32'h{want:x}; t_err[{i}] = {err_on}; t_waits[{i}] = {waits}; "
                    f"t_what[{i}] = \"{what}\"; t_direct[{i}] = {direct}; idle_trans[{i}] = {busy};")
    return BENCH.format(err=int(error_responses), count=len(transfers),
                        router_count=len(ROUTER_TRANSFERS), fill='\n'.join(fill))


def simulate(fixture, error_responses):
    bench = os.path.join(fixture, 'ahb_tb.sv')
    with open(bench, 'w') as f:
        f.write(bench_source(error_responses))
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'ahbDecode.sv', 'leafA_regs.sv', 'leafA.sv',
            'leafB_regs.sv', 'leafB.sv')]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'ahb_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Vahb_tb')], capture_output=True, text=True, timeout=600)
    print(run.stdout)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stderr}")


def main():
    for error_responses in (False, True):
        label = 'on' if error_responses else 'off'
        fixture = tempfile.mkdtemp(prefix=f'a2c_ahb_reg_bus_{label}_')
        try:
            generate(fixture, error_responses)
            check_generated(fixture, error_responses)
            simulate(fixture, error_responses)
            check(True, f"{label}: RTL bench passes")
        except Exception as exc:
            check(False, f"{label}: {exc}")
        finally:
            shutil.rmtree(fixture, ignore_errors=True)
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        return 1
    print("\n  ALL TESTS PASSED!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
