#!/usr/bin/env python3
"""The AHB-Lite BFMs and channel put the right cycles on the pins.

Builds and runs `fixtures/ahb-bfm/ahb_bfm_runtime.cpp` under the SystemC kernel.
Each scenario runs a pin-level protocol monitor that samples the pins at every
clock edge and counts violations of these AHB-Lite rules:

- hsel, htrans, haddr and the control signals of a NONSEQ or SEQ address phase
  hold while hready is low, and hwdata holds through a write's data phase;
- an ERROR response is two cycles, hready low then hready high, both with hresp;
- hready is high and hresp OKAY when no transfer is in its data phase, which
  makes IDLE and BUSY zero-wait;
- SEQ and BUSY follow a NONSEQ, stay inside the burst length, keep the burst's
  control signals, and carry the burst's incrementing or wrapping address;
- an incrementing burst ends where its next beat would cross a 1KB boundary;
- IDLE never appears while a fixed-length burst has beats left;
- hmastlock stays high on the cycles between two locked transfers.

The scenarios:

- `loopback`: model manager -> `ahb_dst_bfm` -> pins -> `ahb_src_bfm` -> model
  subordinate. A 23-transfer script covers single, INCR4 and WRAP4 bursts
  (NONSEQ then SEQ, wrap 0x238 -> 0x23c -> 0x230 -> 0x234), read data matching
  written data, wait states, and two back-to-back ERROR responses. The model
  manager runs one thread per phase with its data thread registered first, so
  write data reaches the channel before its address.
- `srcBfm`: a scripted pin manager drives the same transfers with IDLE (hsel
  low and high) and BUSY cycles in between, against `ahb_src_bfm`. Its first
  NONSEQ is on the bus at the edge that releases reset.
- `dstBfm`: the same script through `ahb_dst_bfm` into a scripted pin
  subordinate that inserts the scripted wait states and ERRORs.
- `slowMgr`: a single-thread model manager that finishes each beat and pauses
  two cycles before the next, through `ahb_dst_bfm` into the scripted pin
  subordinate. It runs a locked INCR4 write, a WRAP4 read, an INCR write and
  locked single reads, so the BFM must fill the gaps with BUSY inside each
  burst (9 gaps of 4 cycles) and hold hmastlock between the locked reads. Its last
  burst is an INCR write at 0x3f8 and 0x3fc, after which the next beat would
  cross the 1KB boundary at 0x400, so the BFM must drive IDLE in that gap.
- `selfTest`: scripted illegal traffic. The monitor must report exactly one
  violation of each rule it enforces, so a monitor that stopped detecting
  fails here.
- `errCancel` and `errContinue`: an INCR4 read whose first beat answers ERROR.
  The manager either cancels the burst with IDLE in the second ERROR cycle or
  carries on with the remaining beats. Both are legal, so the monitor must
  report nothing.
- `docWrites` and `docMixed`: a model manager written as the two-thread example
  in `rules/skills/systemc-interfaces.md`, with four writes and with two writes
  then two reads, through `ahb_dst_bfm` into a zero-wait pin subordinate. Each
  address phase must be taken at the edge after the one before.
- `resetAssert`, run on its own because its assert stops the simulation: reset
  asserted while a write waits in its data phase. `ahb_dst_bfm` must assert
  rather than return OKAY for a write the subordinate dropped.

Before the scenarios run, the fixture builds an `ahbRespSt` in storage full of
0xff and checks `hrdata` packs to zero, for generated-style payloads with an
array `_packedSt` (over 64 bits) and a scalar `_packedSt`.

The fixture also pins, edge by edge, that the address phase of transfer N+1 is
taken at the edge that ends the data phase of transfer N, that each data phase
lasts one cycle plus its wait states (plus one for ERROR), and that the
hready-low cycle count equals the scripted wait states plus ERROR cycles.

The build reuses `test_thunker_runtime.py`'s toolchain and flags, so a header
that trips a warning the real model build rejects fails here.
"""

import os
import shutil
import subprocess
import sys
import tempfile

import test_thunker_runtime as thunker_runtime
from _tmp_helpers import remove_tree

test_dir = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(test_dir, 'fixtures', 'ahb-bfm', 'ahb_bfm_runtime.cpp')

# The fixture's own accounting, pinned so a scenario or check that stopped
# running fails here instead of shrinking the evidence silently.
EXPECTED_CHECKS = 1540
EXPECTED_SCENARIOS = [
    'scenario loopback transfers:23 pipelined:22 waitCycles:12 errors:2 violations:0',
    'scenario srcBfm transfers:23 pipelined:18 waitCycles:12 errors:2 busy:2 violations:0',
    'scenario dstBfm transfers:23 pipelined:22 waitCycles:12 errors:2 violations:0',
    'scenario slowMgr transfers:16 busy:36 busyZeroWait:36 violations:0',
    'scenario selfTest violations:STABLE,WDATA,ERR1,SEQ,WRAP,CTRL,LEN,BURSTIDLE,LOCK,ERR2,ERRIDLE,ZEROWAIT,BUSY,STABLE,WRAP',
    'scenario errCancel transfers:1 errors:1 violations:0',
    'scenario errContinue transfers:4 errors:1 violations:0',
    'scenario docWrites edges:3,4,5,6 violations:0',
    'scenario docMixed edges:3,4,5,6 violations:0',
]
RESET_ASSERT = '[Q_ASSERT][reset.bfm] ahb reset during a transfer is not supported'
RESET_SCENARIO = 'scenario resetAssert responses:0 exitCode:1'
RESET_SUMMARY = 'checks:3 failures:0'


def test_ahb_bfms_drive_and_answer_the_pins_correctly():
    """Build and run the fixture; every pinned cycle, value and rule must hold."""
    env = thunker_runtime.toolchain_env()
    assert shutil.which(thunker_runtime.CXX), f"{thunker_runtime.CXX} not found on PATH"
    build_dir = tempfile.mkdtemp(prefix='a2c_ahb_bfm_')
    try:
        result, binary = thunker_runtime.build_and_run(build_dir, env, FIXTURE)
        reset = subprocess.run([binary, 'resetAssert'], capture_output=True, text=True, timeout=300)
    finally:
        remove_tree(build_dir)

    output = result.stdout + result.stderr
    failures = [line for line in output.splitlines() if line.startswith(('FAIL', 'VIOLATION'))]
    assert not failures, "AHB checks failed:\n" + "\n".join(failures[:40]) + f"\n(exit {result.returncode})"
    assert result.returncode == 0, f"fixture exited {result.returncode}:\n{output}"
    lines = output.splitlines()
    for expected in EXPECTED_SCENARIOS:
        assert expected in lines, f"missing line {expected!r}:\n{output}"
    summary = [line for line in lines if line.startswith('checks:')]
    assert len(summary) == 1, f"expected one summary line, got {summary!r}:\n{output}"
    checks, failed = summary[0].split()
    assert failed == 'failures:0', output
    count = int(checks.split(':')[1])
    assert count == EXPECTED_CHECKS, f"expected {EXPECTED_CHECKS} checks, got {count}:\n{output}"
    print(f"  {count} pin, cycle and data checks across 9 scenarios, 0 failures, 0 protocol violations")

    reset_output = reset.stdout + reset.stderr
    reset_lines = reset_output.splitlines()
    assert any(line.startswith(RESET_ASSERT) for line in reset_lines), \
        f"ahb_dst_bfm did not assert on reset during a transfer:\n{reset_output}"
    for expected in (RESET_SCENARIO, RESET_SUMMARY):
        assert expected in reset_lines, f"missing line {expected!r}:\n{reset_output}"
    assert reset.returncode == 0, f"resetAssert exited {reset.returncode}:\n{reset_output}"
    print("  reset during a transfer asserts and returns no response")


def run_all_tests():
    tests = [test_ahb_bfms_drive_and_answer_the_pins_correctly]
    print("=" * 70)
    print("AHB BFM TESTS")
    print("=" * 70)
    results = []
    for test_func in tests:
        print(f"\n{test_func.__name__}:")
        try:
            test_func()
            results.append((test_func.__name__, True))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))

    print("\n" + "=" * 70 + "\nTEST SUMMARY\n" + "=" * 70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
