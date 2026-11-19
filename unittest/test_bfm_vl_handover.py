#!/usr/bin/env python3
"""The rdy_vld BFMs hand each beat over at the RTL's handshake edge, on a Verilated FIFO.

test_bfm_handover.py drives the BFMs against RTL written in C++. This test runs
them against Verilated RTL. `unittest/fixtures/bfm-vl-handover` has a model
source, a four-entry FIFO in SystemVerilog and a model sink. `--vlInst`
swaps the FIFO for its Verilated wrapper, so the source reaches the RTL through
the dst BFM and the RTL reaches the sink through the src BFM. The FIFO's own
latency is one clock from the edge that takes a beat to the edge that gives
it up, and its in.rdy follows its fill level only.

The rule any BFM fix keeps: no lost throughput, no added clock of latency,
back-to-back beats one per clock, and the first beat's vld driven in the
timestep of the model's send. The model logs every call and return with its
simulation time. `--vlTrace` gives the RTL pins, and the handshakes are the
posedges where vld and rdy were both high just before the edge.

Runs, picked with BVH_MODE:
- single: one beat sent 3 ns after a clock edge, long after reset releases.
- burst: 16 beats sent back to back, the sink reading back to back.
- hold: 16 beats, the sink starting to read 2 ns after an edge, 400 ns after
  the source starts. The FIFO fills and its in.rdy drops.
- poweron: one beat sent and read at time 0, while reset is still low.

Where today's BFM breaks the rule, EXPECTED_FAILURES names the check, how it
fails and the BFM line. A marked check that passes, or fails another way than
its row pins, fails the suite, so a fix has to change its marker.

Reset: only a power-on reset is supported. The BFMs hold traffic until the first
reset releases, and a later reset has to fail the run with a clear message.
poweron covers the first part and passes today. The generated wrapper drives
rst_n from one thread and gives the testbench no way to pulse it again, so this
test cannot reach the second part. test_bfm_handover.py's reset runs meet it.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple

from _addrctl_helpers import base_dir, test_dir
from _make_helpers import shell_make_env
from _tmp_helpers import remove_tree


FIXTURE = os.path.join(test_dir, 'fixtures', 'bfm-vl-handover')
BUILD_JOBS = '8'
VL_INST = 'tb.bvhTop.uFifo'
PERIOD = 10000                  # ps
FIFO_DEPTH = 4
BEATS = 16
SEND_AT = 103000                # ps, 3 ns after an edge
HOLD_READ_AT = 502000           # ps, 2 ns after an edge
RUN_TIMEOUT = 120               # s
TIME_LIMIT_US = 5

IN_ORDER = list(range(BEATS))
SIGNALS = ('in_vld', 'in_rdy', 'out_vld', 'out_rdy', 'clk', 'rst_n')

# The checks, by name. Two runs use the same words only where they check the same thing.
FIRST_VLD = "first beat's vld rises in the timestep of the send"
FIRST_EDGE = "the RTL takes the first beat at the first edge after the send"
SEND_RETURN = "send returns at the RTL's handshake edge"
LATENCY = "send-to-receive latency equals the RTL's latency"
RATE_IN = "back to back beats enter the RTL one per clock"
RATE_OUT = "back to back beats reach the sink one per clock"
RECV_EDGE = "each receive returns at the RTL's handshake edge"
ORDER = "order kept, no beat lost"
RDY_DROPS = "RTL rdy deasserts while the FIFO is full and the sink holds off"
SEND_BLOCKS = "a send is blocked while the RTL has no room"
NO_AHEAD = "no send returns ahead of the RTL's handshakes"
RELEASE = "the RTL's handshake comes at the first edge after the sink reads"
RESET_HOLD = "no traffic while reset is low"
RUN_CLEAN = "run exits 0 with no Q_ASSERT"

HIDDEN_DST = ("completes the model's write when it copies the beat, one handshake before the RTL takes it, "
              "so the model sees room the RTL does not have")
LATE_READY = ("sets ready from get_rdy() only on a clock edge, so the RTL's ready rises an edge after the "
              "model starts to read")

# A row marks a check that fails today: the run, the check, how it fails and why.
# how pins the failure, and None accepts any failure.
XFail = namedtuple('XFail', 'mode check how reason')
EXPECTED_FAILURES = [
    XFail('single', SEND_RETURN, 'at the call', f"rdy_vld_bfm.h:154 readClocked() {HIDDEN_DST}"),
    XFail('hold', NO_AHEAD, '5 returns, 4 accepted',
          f"rdy_vld_bfm.h:154 readClocked() {HIDDEN_DST}; the FIFO takes {FIFO_DEPTH} beats, "
          f"and the fifth write returns with the RTL still stalled"),
    XFail('hold', RELEASE, '+1 clock', f"rdy_vld_bfm.h:55-60 {LATE_READY}"),
]

FAILURES = []
XFAILS = []


def expectedFailure(mode, name):
    for row in EXPECTED_FAILURES:
        if row.mode == mode and row.check == name:
            return row
    return None


def check(mode, name, condition, detail, how='fails'):
    """Records a check; a marked check passes the suite only by failing as its row says."""
    row = expectedFailure(mode, name)
    message = f"{mode}: {name} ({detail})"
    if row is None:
        print(f"  {'PASS' if condition else 'FAIL'}: {message}")
        if not condition:
            FAILURES.append(message)
    elif condition:
        print(f"  XPASS: {message}; marked expected failure: {row.reason}")
        FAILURES.append(f"unexpected pass, {message}")
    elif row.how is not None and row.how != how:
        print(f"  FAIL: {message}; fails as '{how}', marked to fail as '{row.how}': {row.reason}")
        FAILURES.append(f"fails differently, {message}")
    else:
        print(f"  XFAIL: {message}; {row.reason}")
        XFAILS.append(message)


def make(project, *args, directory=None):
    cmd = ['make', '-C', directory or project, f'-j{BUILD_JOBS}',
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}', *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=shell_make_env())


def require(result, what):
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed (rc={result.returncode}):\n{result.stdout}\n{result.stderr}")


def runMode(rundir, mode):
    """Runs one mode with the FIFO Verilated; returns the run and its model log."""
    build = os.path.join(rundir, 'build')
    run = subprocess.run(['./run', 'bvhTop', '--vlInst', VL_INST, '--vlTrace', '--scTimeLimit', str(TIME_LIMIT_US)],
                         capture_output=True, text=True, timeout=RUN_TIMEOUT, cwd=build,
                         env=dict(shell_make_env(), BVH_MODE=mode))
    return run, modelLog(run.stdout)


def modelLog(output):
    """The model's calls and returns as lists of (index, ps) and the sink's data as a list of beats."""
    log = {'src call': [], 'src ret': [], 'snk call': [], 'snk recv': [], 'data': []}
    for who, what, k, rest in re.findall(r'^BVH (src|snk) (call|ret|recv) (\d+) (.*)$', output, re.M):
        fields = [int(f) for f in rest.split()]
        log[f'{who} {what}'].append((int(k), fields[-1]))
        if what == 'recv':
            log['data'].append(fields[0])
    return log


def pinChanges(vcd):
    """{ps: {signal: value}} for the FIFO wrapper's pins in the trace."""
    ids = {}
    changes = {}
    now = 0
    with open(vcd) as fh:
        for line in fh:
            line = line.strip()
            var = re.match(r'\$var \w+ \d+ (\S+) (\w+)', line)
            if var:
                if var.group(2) in SIGNALS and var.group(1) not in ids:
                    ids[var.group(1)] = var.group(2)
            elif line.startswith('#'):
                now = int(line[1:])
            else:
                value = re.match(r'^([01])(\S+)$', line)
                if value and value.group(2) in ids:
                    changes.setdefault(now, {})[ids[value.group(2)]] = int(value.group(1))
    return changes


def posedges(changes):
    """(ps, pins) for each rising clock edge after time 0; pins are the values just before the edge."""
    pins = dict.fromkeys(SIGNALS, 0)
    edges = []
    for t in sorted(changes):
        before = dict(pins)
        pins.update(changes[t])
        if before['clk'] == 0 and pins['clk'] == 1 and t > 0:
            edges.append((t, before))
    return edges


def handshakes(edges, vld, rdy):
    """Edges where vld and rdy were both high out of reset."""
    return [t for t, p in edges if p[vld] and p[rdy] and p['rst_n']]


def firstChange(changes, signal, value):
    return next((t for t in sorted(changes) if changes[t].get(signal) == value), None)


def ps(values):
    return [v // 1000 for v in values]


def nextEdge(t):
    return (t // PERIOD + 1) * PERIOD


def times(entries):
    return [t for _, t in entries]


def checkRun(mode, run):
    asserted = re.findall(r'^\[Q_ASSERT\].*$', run.stdout + run.stderr, re.M)
    check(mode, RUN_CLEAN, run.returncode == 0 and not asserted,
          f"exit {run.returncode}, {asserted[0] if asserted else 'no assert'}",
          f"exit {run.returncode}" if not asserted else asserted[0])


def checkOrder(mode, log, beats):
    got = log['data']
    check(mode, ORDER, got == list(range(beats)), f"sink got {got}")


def singleChecks(log, edges, changes):
    mode = 'single'
    call, ret, recv = log['src call'][0][1], log['src ret'][0][1], log['snk recv'][0][1]
    vld = firstChange(changes, 'in_vld', 1)
    check(mode, FIRST_VLD, vld == call, f"send at {call} ps, vld rose at {vld} ps")
    inHs, outHs = handshakes(edges, 'in_vld', 'in_rdy'), handshakes(edges, 'out_vld', 'out_rdy')
    check(mode, FIRST_EDGE, inHs[:1] == [nextEdge(call)], f"send at {call} ps, handshake edges {inHs}")
    if not inHs:
        how = 'no handshake'
    elif ret == call:
        how = 'at the call'
    else:
        how = 'ahead' if ret < inHs[0] else 'late'
    check(mode, SEND_RETURN, inHs[:1] == [ret],
          f"returned at {ret} ps, the RTL took the beat at {inHs[0] if inHs else None} ps", how)
    # The FIFO gives a beat up on the edge after it takes it, with out.rdy high long before.
    rtlLatency = outHs[0] - inHs[0]
    check(mode, LATENCY, recv - inHs[0] == rtlLatency,
          f"the RTL took the beat at {inHs[0]} ps and gave it up {rtlLatency} ps later; "
          f"the sink received {recv - inHs[0]} ps after the RTL took it")
    checkOrder(mode, log, 1)


def burstChecks(log, edges):
    mode = 'burst'
    inHs, outHs = handshakes(edges, 'in_vld', 'in_rdy'), handshakes(edges, 'out_vld', 'out_rdy')
    steady = all(b - a == PERIOD for a, b in zip(inHs, inHs[1:]))
    check(mode, RATE_IN, steady and len(inHs) == BEATS, f"{len(inHs)} handshakes at {ps(inHs)} ns")
    recv = times(log['snk recv'])
    steady = all(b - a == PERIOD for a, b in zip(recv, recv[1:]))
    check(mode, RATE_OUT, steady and len(recv) == BEATS, f"{len(recv)} receives at {ps(recv)} ns")
    check(mode, RECV_EDGE, recv == outHs, f"receives at {ps(recv)} ns, RTL out handshakes at {ps(outHs)} ns")
    checkOrder(mode, log, BEATS)


def holdChecks(log, edges):
    mode = 'hold'
    inHs, outHs = handshakes(edges, 'in_vld', 'in_rdy'), handshakes(edges, 'out_vld', 'out_rdy')
    read = log['snk call'][0][1]
    assert read == HOLD_READ_AT, f"the sink starts reading at {read} ps, expected {HOLD_READ_AT} ps"
    accepted = [t for t in inHs if t < read]
    full = [(t, p) for t, p in edges if accepted and accepted[-1] < t < read]
    stuck = all(p['in_vld'] and not p['in_rdy'] for t, p in full)
    check(mode, RDY_DROPS, len(accepted) == FIFO_DEPTH and stuck and bool(full),
          f"{len(accepted)} beats taken before the read at {read} ps, in.rdy low with vld high on "
          f"{sum(1 for t, p in full if p['in_vld'] and not p['in_rdy'])} of {len(full)} edges")
    calls = [t for t in times(log['src call']) if t < read]
    rets = [t for t in times(log['src ret']) if t < read]
    check(mode, SEND_BLOCKS, len(calls) == len(rets) + 1,
          f"{len(calls)} sends called and {len(rets)} returned before the read at {read} ps")
    check(mode, NO_AHEAD, len(rets) == len(accepted),
          f"{len(rets)} returns, {len(accepted)} accepted",
          f"{len(rets)} returns, {len(accepted)} accepted")
    first = next((t for t in outHs if t > read), None)
    behind = (first - nextEdge(read)) // PERIOD if first is not None else None
    check(mode, RELEASE, first == nextEdge(read),
          f"read at {read} ps, first handshake at {first} ps, expected {nextEdge(read)} ps",
          f"{behind:+d} clock" if behind is not None else 'no handshake')
    checkOrder(mode, log, BEATS)


def powerOnChecks(log, edges, changes):
    mode = 'poweron'
    release = firstChange(changes, 'rst_n', 1)
    early = [(t, k) for t in sorted(changes) if release is None or t < release
             for k in ('in_vld', 'out_rdy') if changes[t].get(k) == 1]
    handshakesInReset = [t for t, p in edges if p['in_vld'] and p['in_rdy'] and not p['rst_n']]
    check(mode, RESET_HOLD, release is not None and not early and not handshakesInReset,
          f"reset released at {release} ps, the model's first send at {log['src call'][0][1]} ps, "
          f"pins raised in reset {early}, handshakes in reset {handshakesInReset}")
    checkOrder(mode, log, 1)


def main():
    tmp = tempfile.mkdtemp(prefix='bfm_vl_handover_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'bfm-vl-handover')
        shutil.copytree(FIXTURE, project, ignore=shutil.ignore_patterns(
            '*.db', '*.db-*', '.gen', 'build', 'compile_commands.json'))
        for target in ('db', 'newmodule', 'gen'):
            require(make(project, target), f"make {target}")
        rundir = os.path.join(project, 'rundir')
        require(make(project, 'all', 'VL_DUT=1', 'CCACHE_DISABLE=1', directory=rundir), "make all VL_DUT=1")

        for mode in ('single', 'burst', 'hold', 'poweron'):
            run, log = runMode(rundir, mode)
            print(f"\n  {mode}")
            changes = pinChanges(os.path.join(rundir, 'build', 'simx.vcd'))
            edges = posedges(changes)
            checkRun(mode, run)
            if mode == 'single':
                singleChecks(log, edges, changes)
            elif mode == 'burst':
                burstChecks(log, edges)
            elif mode == 'hold':
                holdChecks(log, edges)
            else:
                powerOnChecks(log, edges, changes)
            if len(FAILURES) and FAILURES[-1].startswith(mode):
                print(run.stdout + run.stderr)
    finally:
        remove_tree(tmp)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print(f"\n  {len(XFAILS)} expected failures")
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
