#!/usr/bin/env python3
"""fileGeneration.regBusErrorResponses decides which register-bus accesses return PSLVERR.

Without the option the generated router and register handlers tie PSLVERR low,
and an ext register's owner need not drive the interface's pslverr. With it, an
access to an empty router slot, an access to an address gap in a register
block, and an ext register write its owner refuses complete with PSLVERR. A
write to a read-only register is still dropped without PSLVERR, and every other
access completes without it.

The fixture has a router with four 0x1000-byte slots, leafA in slot 0 and leafB
in slot 1, so 0x2000 is an empty slot. leafA holds rw cfg at 0x0, ro stat at
0x8 and ext cmd at 0x10, so 0x4 is a gap. leafA's owner logic refuses a cmd
write of 0x0bad, and with the option off it leaves pslverr undriven. leafB
contains an instance, so its handler keeps a model of its own and the
SystemC handler comes from the blockRegs template rather than the leaf's model.

For each setting the test generates the fixture outside the working tree and
checks the generated SystemC passes the option to registerHandler and
decodeThread. A bench then drives the generated RTL over APB under Verilator
`--binary --timing` and checks the read data and PSLVERR of each access. The
bench ends with TB_PASS on stdout.
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
INTF_DIRS = [os.path.join(base_dir, 'interfaces', name) for name in ('apb', 'status', 'external_reg')]

DESIGN = """include:
    - shared.yaml

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top }}
    uInner:     {{ container: leafB, instanceType: inner }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfg,  regType: rw,  block: leafA, structure: cfgRegSt, desc: "rw register" }}
    - {{ register: stat, regType: ro,  block: leafA, structure: cfgRegSt, desc: "ro register" }}
    - {{ register: cmd,  regType: ext, block: leafA, structure: cfgRegSt, desc: "ext register" }}
    - {{ register: cfgB, regType: rw,  block: leafB, structure: cfgRegSt, desc: "rw register" }}
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=4)
          + render_leaf('leafA') + render_plain_block('leafB') + render_plain_block('inner'))

# leafA's hand-written logic, appended before its endmodule. The option-on
# owner refuses a cmd write of 0x0bad.
OWNER = """
    assign stat.data.value = 16'h5a5a;
    assign cmd.rdata.value = 16'h0c0d;
"""
OWNER_REFUSAL = """    assign cmd.pslverr = cmd.wdata.value == 16'h0bad;
"""

BENCH = """\
module err_tb
    import shared_package::*;
;
    localparam bit ERR = {err};

    logic clk = 0;
    logic rst_n = 0;
    always #5 clk = ~clk;

    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) bus();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) busA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) busB();

    apbDecode uAPBDecode (.apbReg(bus), .apbReg_uLeafA(busA), .apbReg_uLeafB(busB), .clk(clk), .rst_n(rst_n));
    leafA uLeafA (.regs(busA), .clk(clk), .rst_n(rst_n));
    leafB uLeafB (.apbReg(busB), .clk(clk), .rst_n(rst_n));

    int errors = 0;

    // One transfer, starting at a negedge. err_on is the PSLVERR expected
    // with the option on; with it off every access expects none.
    task automatic access(input logic write, input logic [31:0] addr, input logic [31:0] wdata,
                          input logic check_data, input logic [31:0] want, input logic err_on,
                          input string what);
        int cycles = 0;
        logic want_err;
        want_err = ERR & err_on;
        bus.psel = 1; bus.penable = 0; bus.pwrite = write; bus.paddr = addr; bus.pwdata = wdata;
        @(negedge clk);
        bus.penable = 1;
        while (!bus.pready) begin
            @(negedge clk);
            cycles++;
            if (cycles > 50) begin
                $display("TB_FAIL: %s: never completed", what);
                $finish;
            end
        end
        if (bus.pslverr !== want_err) begin
            $display("TB_FAIL: %s: PSLVERR %0b, expected %0b", what, bus.pslverr, want_err);
            errors++;
        end else if (check_data && bus.prdata !== want) begin
            $display("TB_FAIL: %s: read 0x%0h, expected 0x%0h", what, bus.prdata, want);
            errors++;
        end else begin
            $display("TB_OK: %s", what);
        end
        @(negedge clk);
        bus.penable = 0;
        bus.psel = 0;
        @(negedge clk);
    endtask

    initial begin
        bus.psel = 0; bus.penable = 0; bus.pwrite = 0; bus.paddr = 0; bus.pwdata = 0;
        repeat (4) @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        access(1, 32'h0000, 32'h1111, 0, 0, 0, "rw write");
        access(0, 32'h0000, 0, 1, 32'h1111, 0, "rw read");
        access(1, 32'h0008, 32'hFFFF, 0, 0, 0, "ro write is dropped without PSLVERR");
        access(0, 32'h0008, 0, 1, 32'h5a5a, 0, "ro read");
        access(1, 32'h0010, 32'h0bad, 0, 0, 1, "ext write the owner refuses");
        access(1, 32'h0010, 32'h0001, 0, 0, 0, "ext write the owner accepts");
        access(0, 32'h0010, 0, 1, 32'h0c0d, 0, "ext read");
        access(1, 32'h0004, 32'hFFFF, 0, 0, 1, "register block gap write");
        access(0, 32'h0004, 0, 1, 32'hBADD_C0DE, 1, "register block gap read");
        access(1, 32'h2000, 32'hFFFF, 0, 0, 1, "empty router slot write");
        access(0, 32'h2000, 0, 1, 32'hBADD_C0DE, 1, "empty router slot read");
        access(1, 32'h1000, 32'h2222, 0, 0, 0, "leafB rw write");
        access(0, 32'h1000, 0, 1, 32'h2222, 0, "leafB rw read");
        access(0, 32'h0000, 0, 1, 32'h1111, 0, "gap writes leave cfg unchanged");
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
    project = PROJECT.replace('fwAccess', 'regsErr')
    if error_responses:
        project += "    regBusErrorResponses: true\n"
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(project)
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS))
    db = os.path.join(fixture, 'regsErr.db')
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
    owner = OWNER + (OWNER_REFUSAL if error_responses else '')
    with open(leaf, 'w') as f:
        f.write(text.replace('endmodule: leafA', owner + '\nendmodule: leafA'))


def read(fixture, rel):
    with open(os.path.join(fixture, rel)) as f:
        return f.read()


def check_generated(fixture, error_responses):
    """The SystemC handlers and decoder get the option as an argument, and the
    option-off RTL keeps PSLVERR tied low."""
    label = 'on' if error_responses else 'off'
    arg = ', true)' if error_responses else ')'
    check(f"registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, regs, (1<<(5))-1{arg}"
          in read(fixture, 'model/leafA.cppm'), f"{label}: leafA model handler call")
    check(f"registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, apbReg, (1<<(3))-1{arg}"
          in read(fixture, 'model/leafB_regs.cppm'), f"{label}: leafB_regs model handler call")
    check(f"decoder.decodeThread({'true' if error_responses else ''});"
          in read(fixture, 'model/apbDecode.cppm'), f"{label}: router model decodeThread call")
    regs = read(fixture, 'rtl/leafA_regs.sv')
    router = read(fixture, 'rtl/apbDecode.sv')
    if error_responses:
        check("assign regs.pslverr = wr_slverr | rd_slverr;" in regs, f"{label}: handler drives PSLVERR")
        check("REG_LEAFA_STAT : ; // read-only: the write is dropped" in regs,
              f"{label}: ro write has its own arm, outside the PSLVERR default")
        check("apbReg_next_pslverr = 1'b1;" in router, f"{label}: router raises PSLVERR on an empty slot")
    else:
        check("assign regs.pslverr = 1'b0;" in regs, f"{label}: handler ties PSLVERR low")
        check("slverr" not in regs.replace('regs.pslverr', ''), f"{label}: handler has no slverr logic")
        check("cmd.pslverr" not in regs, f"{label}: handler does not read the ext owner's pslverr")
        check("apbReg_next_pslverr = 1'b1;" not in router, f"{label}: router keeps PSLVERR low on an empty slot")


def simulate(fixture, error_responses):
    bench = os.path.join(fixture, 'err_tb.sv')
    with open(bench, 'w') as f:
        f.write(BENCH.format(err=int(error_responses)))
    obj_dir = os.path.join(fixture, 'obj')
    rtl = [os.path.join(fixture, 'rtl', name) for name in
           ('shared_package.sv', 'top_package.sv', 'apbDecode.sv', 'leafA_regs.sv', 'leafA.sv',
            'leafB_regs.sv', 'inner.sv', 'leafB.sv')]
    cmd = (['verilator', '--binary', '--timing', '-j', '4', '--top-module', 'err_tb',
            '-Mdir', obj_dir, '+libext+.sv', '-y', COMMON_SV, f'+incdir+{COMMON_SV}']
           + [arg for d in INTF_DIRS for arg in ('-y', d, f'+incdir+{d}')]
           + [os.path.join(COMMON_SV, 'flops.sv')] + rtl + [bench])
    # Timed binaries built through Verilator's ccache wrapper in a fresh
    # temporary directory abort at startup; build without the cache.
    build = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, CCACHE_DISABLE='1'))
    if build.returncode != 0:
        raise AssertionError(f"build failed:\n{build.stdout}{build.stderr}")
    run = subprocess.run([os.path.join(obj_dir, 'Verr_tb')], capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or 'TB_PASS' not in run.stdout:
        raise AssertionError(f"simulation failed (exit {run.returncode}):\n{run.stdout}{run.stderr}")


def main():
    for error_responses in (False, True):
        label = 'on' if error_responses else 'off'
        fixture = tempfile.mkdtemp(prefix=f'a2c_reg_bus_err_{label}_')
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
