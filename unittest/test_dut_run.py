#!/usr/bin/env python3
"""dutRun.py runs a test on the snapshot its arguments name.

A regression file names one base binary, and each test's own arguments pick
the simulator snapshot <base>_<topology> it runs on. --vlInst, --vlType and
--vlTandem give the DUT topologies of vcs_snapshots and xrun_snapshots, and a
test without --vlInst runs on `model`. A UVM test carries --uvmDut <dut> and
--uvmTop <top> and runs on uvm_<top>_<dut>, which uvm_snapshots builds;
--uvmDut without --uvmTop, or --uvmTop without --uvmDut, names no snapshot
and stops the run. Each case runs dutRun.py over a directory of stand-in
snapshots that print the arguments they were given, and checks which
snapshot ran with which arguments.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
DUT_RUN = os.path.join(base_dir, 'dutRun.py')

SNAPSHOTS = ['run_model', 'run_top_verif', 'run_top_verif_tandem', 'run_top_model_tandem',
             'run_top.u_a_verif', 'run_uvm_top_default_model', 'run_uvm_top_default_rtl',
             'run_uvm_top_wide_rtl']

# (label, arguments, snapshot that must run)
RUNS = [
    ('no --vlInst', ['top', '--seed', '1'], 'run_model'),
    ('a verif instance', ['top', '--vlInst', 'top'], 'run_top_verif'),
    ('a verif instance, = form', ['top', '--vlInst=top', '--vlType=verif'], 'run_top_verif'),
    ('a verif tandem', ['top', '--vlInst', 'top', '--vlTandem'], 'run_top_verif_tandem'),
    ('a model tandem', ['top', '--vlInst', 'top', '--vlType', 'model', '--vlTandem'], 'run_top_model_tandem'),
    ('a model instance without tandem', ['top', '--vlInst', 'top', '--vlType', 'model'], 'run_model'),
    ('a dotted instance', ['top', '--vlInst', 'top.u_a'], 'run_top.u_a_verif'),
    ('a UVM model DUT', ['top_uvm', '--uvmDut', 'model', '--uvmTop', 'top_default', '+UVM_TESTNAME=t'],
     'run_uvm_top_default_model'),
    ('a UVM rtl DUT, top first', ['top_uvm', '--uvmTop', 'top_default', '--uvmDut', 'rtl'],
     'run_uvm_top_default_rtl'),
    ('a UVM rtl DUT, = form', ['top_uvm', '--uvmDut=rtl', '--uvmTop=top_wide', '--seed', '0x1f'],
     'run_uvm_top_wide_rtl'),
]

# (label, arguments, text the error must hold)
REJECTED = [
    ('--uvmDut without --uvmTop', ['top_uvm', '--uvmDut', 'model'],
     'dutRun: --uvmDut model needs --uvmTop <top> to pick the UVM snapshot'),
    ('--uvmTop without --uvmDut', ['top_uvm', '--uvmTop', 'top_default', '+UVM_TESTNAME=t'],
     'dutRun: --uvmTop top_default needs --uvmDut <dut> to pick the UVM snapshot'),
    ('a UVM top with no snapshot', ['top_uvm', '--uvmDut', 'model', '--uvmTop', 'top_wide'],
     'no snapshot'),
    ('an instance with no snapshot', ['top', '--vlInst', 'other'], 'no snapshot'),
]


def make_snapshots(work):
    for name in SNAPSHOTS:
        path = os.path.join(work, name)
        with open(path, 'w') as f:
            f.write('#!/bin/sh\nprintf "%s\\n" "$(basename "$0")" "$@"\n')
        os.chmod(path, 0o755)


def dut_run(work, args):
    return subprocess.run([sys.executable, DUT_RUN, os.path.join(work, 'run')] + args,
                          capture_output=True, text=True)


def run_all_tests():
    print("\n" + "=" * 70)
    print("dutRun.py SNAPSHOT SELECTION")
    print("=" * 70)
    ok = True
    with tempfile.TemporaryDirectory(prefix='dutrun_', dir=test_dir) as work:
        make_snapshots(work)
        for label, args, snapshot in RUNS:
            result = dut_run(work, args)
            got = result.stdout.splitlines()
            if result.returncode != 0 or got != [snapshot] + args:
                print(f"  FAIL: {label}: ran {got} (exit {result.returncode}, {result.stderr.strip()!r}), "
                      f"expected {[snapshot] + args}")
                ok = False
            else:
                print(f"  PASS: {label} runs {snapshot}")
        for label, args, text in REJECTED:
            result = dut_run(work, args)
            if result.returncode == 0 or text not in result.stderr or result.stdout:
                print(f"  FAIL: {label}: exit {result.returncode}, stdout {result.stdout!r}, "
                      f"stderr {result.stderr!r}; expected a failure naming {text!r}")
                ok = False
            else:
                print(f"  PASS: {label} is rejected")
    if ok:
        print("\nPASS: dutRun.py picks the snapshot each test's arguments name")
        return 0
    print("\nFAIL")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
