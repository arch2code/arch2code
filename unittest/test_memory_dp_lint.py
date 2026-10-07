#!/usr/bin/env python3
"""Lint checks for common/systemVerilog/memory_dp.sv, memory_dp_ext.sv and
memory_dp_2clk.sv.

The memories take their widths from a parameterised memory_if and cannot be
linted on their own, so each case writes a small top that instantiates one of
them with real widths and lints it with the flags `make lint` uses
(include/make/a2c-rtl.mk, common/systemVerilog/a2c.f). Every
PORTA_READ_ONLY / PORTB_WRITE_ONLY combination is linted for each module,
memory_dp_2clk on two clocks.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

COMMON_DIR = os.path.join(base_dir, 'common', 'systemVerilog')
A2C_F = os.path.join(COMMON_DIR, 'a2c.f')

# (PORTA_READ_ONLY, PORTB_WRITE_ONLY)
CASES = ((0, 0), (0, 1), (1, 0), (1, 1))

TWO_CLK_INFO = 'memory_dp_2clk: two write ports on two clocks'

TOP = """module memory_lint_top (
    input  logic clkA,
    input  logic clkB,
    input  logic [8:0] addrA, addrB,
    input  logic [17:0] wdataA, wdataB,
    input  logic enA, enB, weA, weB,
    output logic [17:0] rdataA, rdataB{mem_port}
);
    typedef logic [17:0] data_t;
    typedef logic [8:0] addr_t;
    memory_if #(.data_t(data_t), .addr_t(addr_t)) portA();
    memory_if #(.data_t(data_t), .addr_t(addr_t)) portB();
    assign portA.addr = addrA;
    assign portA.write_data = wdataA;
    assign portA.enable = enA;
    assign portA.wr_en = weA;
    assign portB.addr = addrB;
    assign portB.write_data = wdataB;
    assign portB.enable = enB;
    assign portB.wr_en = weB;
    assign rdataA = portA.read_data;
    assign rdataB = portB.read_data;
    {module} #(.DEPTH(320), .data_t(data_t), .PORTA_READ_ONLY(1'b{aRo}), .PORTB_WRITE_ONLY(1'b{bWo})) uMem (
        .mem_portA (portA),
        .mem_portB (portB),{mem_bind}
        {clocks}
    );
endmodule
"""


def _run_case(label, fn):
    try:
        fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"PASS: {label}")
    return True


def lint_one(module, aRo, bWo):
    isExt = module == 'memory_dp_ext'
    clocks = ('.clkA (clkA),\n        .clkB (clkB)' if module == 'memory_dp_2clk'
              else '.clk (clkA)')
    top = TOP.format(module=module, aRo=aRo, bWo=bWo, clocks=clocks,
                     mem_port=',\n    output logic [17:0] mem [320-1:0]' if isExt else '',
                     mem_bind='\n        .mem (mem),' if isExt else '')
    with tempfile.TemporaryDirectory() as tmp:
        top_sv = os.path.join(tmp, 'memory_lint_top.sv')
        with open(top_sv, 'w') as f:
            f.write(top)
        # a2c.f names its directories relative to common/systemVerilog.
        cmd = ['verilator', '--no-timing', '--lint-only', '--top-module', 'memory_lint_top',
               '-F', A2C_F, os.path.join(COMMON_DIR, f'{module}.sv'), top_sv]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=COMMON_DIR, timeout=300)
        if result.returncode != 0:
            raise AssertionError(f"lint failed:\n{result.stdout}{result.stderr}")
        # Two writers on two clocks are a supported simulation mode, reported
        # but never a lint failure.
        twoWriters = module == 'memory_dp_2clk' and not aRo
        if (TWO_CLK_INFO in result.stdout + result.stderr) != twoWriters:
            raise AssertionError(
                f"expected the two-writer $info {'' if twoWriters else 'not '}to be "
                f"reported:\n{result.stdout}{result.stderr}")


def main():
    print("=" * 72)
    print("memory_dp / memory_dp_ext / memory_dp_2clk lint")
    print("=" * 72)
    ok = []
    for module in ('memory_dp', 'memory_dp_ext', 'memory_dp_2clk'):
        for aRo, bWo in CASES:
            ok.append(_run_case(
                f"{module} PORTA_READ_ONLY={aRo} PORTB_WRITE_ONLY={bWo}",
                lambda module=module, aRo=aRo, bWo=bWo: lint_one(module, aRo, bWo)))
    print()
    if all(ok):
        print("RESULT: all memory_dp lint checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory_dp lint checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
