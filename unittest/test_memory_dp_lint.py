#!/usr/bin/env python3
"""Lint checks for common/systemVerilog/memory_dp.sv and memory_dp_ext.sv.

The two memories take their widths from a parameterised memory_if and cannot
be linted on their own, so each case writes a small top that instantiates one
of them with real widths and lints it with the flags `make lint` uses
(include/make/a2c-rtl.mk, common/systemVerilog/a2c.f). Every
PORTA_READ_ONLY / PORTB_WRITE_ONLY combination is linted for both modules.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

COMMON_DIR = os.path.join(base_dir, 'common', 'systemVerilog')
A2C_F = os.path.join(COMMON_DIR, 'a2c.f')

# (PORTA_READ_ONLY, PORTB_WRITE_ONLY, clkA and clkB on separate nets).
# Two writing ports on separate clocks raise Verilator MULTIDRIVEN on the
# shared array, so the combinations where port A writes are linted with both
# clocks on one net.
CASES = (
    (0, 0, False),
    (0, 1, False),
    (1, 0, True),
    (1, 1, True),
)

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
        .clkA (clkA),
        .clkB ({clkB})
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


def lint_one(module, aRo, bWo, separate):
    isExt = module == 'memory_dp_ext'
    top = TOP.format(module=module, aRo=aRo, bWo=bWo,
                     clkB='clkB' if separate else 'clkA',
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


def main():
    print("=" * 72)
    print("memory_dp / memory_dp_ext lint")
    print("=" * 72)
    ok = []
    for module in ('memory_dp', 'memory_dp_ext'):
        for aRo, bWo, separate in CASES:
            ok.append(_run_case(
                f"{module} PORTA_READ_ONLY={aRo} PORTB_WRITE_ONLY={bWo}, clkA and clkB "
                f"{'on separate nets' if separate else 'on one net'}",
                lambda module=module, aRo=aRo, bWo=bWo, separate=separate:
                    lint_one(module, aRo, bWo, separate)))
    print()
    if all(ok):
        print("RESULT: all memory_dp lint checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory_dp lint checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
