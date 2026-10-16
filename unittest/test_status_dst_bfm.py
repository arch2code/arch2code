#!/usr/bin/env python3
"""status_dst_bfm leaves the HDL pin at the model's latest status value.

A status channel holds one value and notifies on each change, so the BFM must be
waiting on the channel whenever the model writes. A model that writes twice
inside one clock must have its second value on the pin at the next edge, not the
first.

With the free-running clock, Verilator samples the pin at a rising edge in the
delta after the clock changes. The channel notifies a write one delta later, so
a write made at an edge, even from a process woken by that edge, reaches the RTL
at the following edge and not at the edge itself. Gated socket lockstep moves
the clock write a delta later, and this ordering does not hold there.

The probe drives the shipped BFM from a model writer and latches the pin on each
rising edge, as the Verilated model's eval method does.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(test_dir, 'fixtures', 'status-dst-bfm', 'status_dst_bfm.cpp')

# scenario -> (value latched at each rising edge from 5 ns to 55 ns, final pin, why)
SCENARIOS = {
    'twoInOneClock': ([0, 0, 2, 2, 2, 2], 2,
                      "1 at 17 ns and 2 at 19 ns fall in one clock, so the 25 ns edge "
                      "and every later one must see 2"),
    'onEdge': ([0, 0, 1, 1, 1, 1], 1,
               "1 written by a process woken at the 15 ns edge reaches the RTL at "
               "25 ns, not at 15 ns"),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def parse(output):
    sampled = [int(line.split('sampled=')[1], 16)
               for line in output.splitlines() if line.startswith('edge ')]
    final = [int(line.split('pin=')[1], 16)
             for line in output.splitlines() if line.startswith('final pin=')]
    return sampled, final[0] if final else None


def test_status_dst_bfm_drives_latest_value():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_status_dst_bfm_')
    try:
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"status BFM probe must build and link: {binPath}")
            return
        for scenario, (edges, finalPin, why) in SCENARIOS.items():
            run = subprocess.run([binPath, scenario], capture_output=True, text=True, timeout=120,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            sampled, final = parse(output)
            before = len(FAILURES)
            check(run.returncode == 0, f"{scenario} exits 0 (got {run.returncode})")
            check(sampled == edges, f"{scenario} edges latch {edges} (got {sampled}): {why}")
            check(final == finalPin, f"{scenario} pin ends at {finalPin} (got {final})")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_status_dst_bfm_drives_latest_value()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
