#!/usr/bin/env python3
"""config/regrRules/uvm.json fails a UVM run on what UVM itself reports.

A UVM testbench reports a failure as a UVM_ERROR or UVM_FATAL line, which may
or may not carry a file location, and counts each severity in the report
summary at the end of the run. The summary also prints zero counts, and a run
that dies before the report phase prints no summary at all. Each case runs the
regrLauncher log analyzer, with uvm.json loaded, over a synthetic log and
checks which filters fire.
"""

import os
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from regrLauncher.runner import logParserAnalyzer

RULES = os.path.join(base_dir, 'config', 'regrRules', 'uvm.json')

RUN = '\n'.join([
    "UVM_INFO /work/tb/tb_pkg.sv(163) @ 6505000: uvm_test_top.env.mon [A2C_TXN] A2C_TXN 6504.500 "
    "uvm_test_top.env.mon.out dst '{data:'h81} hex=81",
    "UVM_INFO /work/uvm/src/base/uvm_report_catcher.svh(705) @ 6523000: reporter [UVM/REPORT/CATCHER] ",
    "--- UVM Report catcher Summary ---",
    "",
    "Number of demoted UVM_ERROR reports  :    0",
    "Number of caught UVM_ERROR reports   :    0",
    "",
])


def summary(errors=0, fatals=0):
    return '\n'.join([
        "UVM_INFO /work/uvm/src/base/uvm_report_server.svh(851) @ 6523000: reporter [UVM/REPORT/SERVER] ",
        "--- UVM Report Summary ---",
        "",
        "** Report counts by severity",
        "UVM_INFO : 4878",
        "UVM_WARNING :    0",
        f"UVM_ERROR :    {errors}",
        f"UVM_FATAL :    {fatals}",
        "** Report counts by id",
        "[A2C_TXN]  4862",
        "",
    ])


ERROR_AT_FILE = ("UVM_ERROR /work/tb/tb_pkg.sv(186) @ 200138000: uvm_test_top.env.sb [A2C_SB] "
                 "expected 129 output beats, received 128")
ERROR_NO_FILE = "UVM_ERROR @ 0: reporter [NOCOMP] No components instantiated."
FATAL_AT_FILE = ("UVM_FATAL /work/tb/tb_pkg.sv(90) @ 5000: uvm_test_top.env.drv [A2C_CFG] "
                 "no virtual interface for port in")
FATAL_NO_FILE = "UVM_FATAL @ 0: reporter [INVTST] Requested test from command line +UVM_TESTNAME=x not found."

# (label, log, [(filter, msg, file)] the analyzer must report, in filter order)
CASES = [
    ('a clean run, whose summary prints UVM_ERROR :    0', RUN + summary(), []),
    ('UVM_ERROR with a file location', RUN + ERROR_AT_FILE + '\n' + summary(errors=1),
     [('uvm_error', '[A2C_SB] expected 129 output beats, received 128', '/work/tb/tb_pkg.sv(186)'),
      ('uvm_summary_count', 'UVM report summary: 1 UVM_ERROR', None)]),
    ('UVM_ERROR without a file location', RUN + ERROR_NO_FILE + '\n' + summary(errors=1),
     [('uvm_error', '[NOCOMP] No components instantiated.', ''),
      ('uvm_summary_count', 'UVM report summary: 1 UVM_ERROR', None)]),
    ('UVM_FATAL with a file location', RUN + FATAL_AT_FILE + '\n' + summary(fatals=1),
     [('uvm_fatal', '[A2C_CFG] no virtual interface for port in', '/work/tb/tb_pkg.sv(90)'),
      ('uvm_summary_count', 'UVM report summary: 1 UVM_FATAL', None)]),
    ('UVM_FATAL without a file location', RUN + FATAL_NO_FILE + '\n',
     [('uvm_fatal', '[INVTST] Requested test from command line +UVM_TESTNAME=x not found.', ''),
      ('uvm_summary_missing', 'no UVM report summary in the log', None)]),
    ('a non-zero summary count with no report line', RUN + summary(errors=12),
     [('uvm_summary_count', 'UVM report summary: 12 UVM_ERROR', None)]),
    ('a log with no UVM report summary', RUN,
     [('uvm_summary_missing', 'no UVM report summary in the log', None)]),
]

FAILURES = []


def analyze(analyzer, log):
    with tempfile.NamedTemporaryFile('w', suffix='.log', prefix='a2c_uvm_rules_', delete=False) as fh:
        fh.write(log)
        path = fh.name
    try:
        return [(f['name'], f['msg'], f['file']) for f in analyzer.analyze(path)]
    finally:
        os.remove(path)


def test_uvm_rules():
    analyzer = logParserAnalyzer([RULES])
    for label, log, expected in CASES:
        found = analyze(analyzer, log)
        ok = found == expected
        print(f"  {'PASS' if ok else 'FAIL'}: {label}")
        if not ok:
            print(f"    expected {expected}")
            print(f"    found    {found}")
            FAILURES.append(label)
    severities = {f['sev'] for f in analyzer.filters.values()}
    ok = severities <= {'error', 'fatal'}
    print(f"  {'PASS' if ok else 'FAIL'}: every uvm.json filter fails the run (severities {sorted(severities)})")
    if not ok:
        FAILURES.append('severities')


if __name__ == '__main__':
    test_uvm_rules()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
