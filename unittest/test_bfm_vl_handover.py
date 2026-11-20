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
- pause: 16 beats, the sink reading back to back, stopping for 52 ns before
  beat 8 while the FIFO holds more beats, then reading the rest.
- poweron: one beat sent and read at time 0, while reset is still low.

single, burst, hold and pause run again with BVH_ON_EDGE set, which moves the
send, the hold read and the pause 3 or 2 ns earlier, onto a clock edge. A
model call in the timestep of an edge reaches the RTL at the next edge, on
every simulator, so the same checks hold: the RTL takes the first beat at the
first edge after the send, and no beat is lost or doubled. The check names
carry " on edge".

Where today's BFM breaks the rule, EXPECTED_FAILURES names the check, how it
fails and the BFM line. A marked check that passes, or fails another way than
its row pins, fails the suite, and so does a row no check matched. A fix has
to change its marker.

Reset: the BFMs hold traffic until the first reset releases, and poweron checks
that, and that the RTL takes the first beat at the first edge sampled with
rst_n high. A later reset is not exercised here. The wrapper's reset thread is
the only writer of rst_n, and the testbench cannot pulse it again.
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
PAUSE_BEAT = 8
PAUSE = 52000                   # ps
RUN_TIMEOUT = 120               # s
TIME_LIMIT_US = 5

MODES = ('single', 'burst', 'hold', 'pause', 'poweron')
EDGE_MODES = ('single', 'burst', 'hold', 'pause')
SEND_SHIFT = 3000               # ps BVH_ON_EDGE moves the send, onto the edge at 100 ns
READ_SHIFT = 2000               # ps it moves the hold read and the pause
SIGNALS = ('in_vld', 'in_rdy', 'out_vld', 'out_rdy', 'clk', 'rst_n')

# The checks, by name. Two runs use the same words only where they check the same thing.
RUN_CLEAN = "run exits 0 with no Q_ASSERT"
COMPLETE = "every beat is sent, returned, handshaken and received"
FIRST_VLD = "first beat's vld rises in the timestep of the send"
FIRST_EDGE = "the RTL takes the first beat at the first edge after the send"
SEND_RETURN = "send returns at the RTL's handshake edge"
RTL_LATENCY = "the FIFO gives a beat up one clock after it takes it"
LATENCY = "send-to-receive latency equals the RTL's latency"
RATE_IN = "back to back beats enter the RTL one per clock"
RATE_OUT = "back to back beats reach the sink one per clock"
RECV_EDGE = "each receive returns at the RTL's handshake edge"
HAND_WAITING = "the RTL hands a beat over only while the sink waits in read()"
ORDER = "order kept, no beat lost"
RDY_DROPS = "RTL rdy deasserts while the FIFO is full and the sink holds off"
SEND_BLOCKS = "a send is blocked while the RTL has no room"
NO_AHEAD = "no send returns ahead of the RTL's handshakes"
RELEASE = "the RTL's handshake comes at the first edge after the sink reads"
RESET_HOLD = "no traffic while reset is low"
FIRST_LIVE_EDGE = "the RTL takes the first beat at the first edge sampled with rst_n high"

LATE_RESET = ("waits for an edge and then reads rst_n, which still shows the old value at the edge where it "
              "rises, so the first beat starts an edge late. The src BFM's same wait at line 59 is not "
              "checked here")

# A row marks a check that fails today: the run, the check, how it fails and why.
# how pins the failure.
XFail = namedtuple('XFail', 'mode check how reason')
EXPECTED_FAILURES = [
    XFail('poweron', FIRST_LIVE_EDGE, '+1 clock', f"rdy_vld_bfm.h:139 {LATE_RESET}"),
]

FAILURES = []
XFAILS = []
MATCHED = set()
SKIPPED = set()                 # modes whose checks did not run


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
        return
    MATCHED.add((mode, name))
    if condition:
        print(f"  XPASS: {message}; marked expected failure: {row.reason}")
        FAILURES.append(f"unexpected pass, {message}")
    elif row.how != how:
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


def runMode(rundir, mode, onEdge):
    """Runs one mode with the FIFO Verilated; returns the run and its model log."""
    build = os.path.join(rundir, 'build')
    trace = os.path.join(build, 'simx.vcd')
    if os.path.exists(trace):
        os.remove(trace)
    env = dict(shell_make_env(), BVH_MODE=mode)
    if onEdge:
        env['BVH_ON_EDGE'] = '1'
    run = subprocess.run(['./run', 'bvhTop', '--vlInst', VL_INST, '--vlTrace', '--scTimeLimit', str(TIME_LIMIT_US)],
                         capture_output=True, text=True, timeout=RUN_TIMEOUT, cwd=build, env=env)
    return run, modelLog(run.stdout)


def modelLog(output):
    """The model's calls and returns as lists of (index, ps), and the sink's data as a list of beats."""
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
    timescale = False
    with open(vcd) as fh:
        for line in fh:
            line = line.strip()
            var = re.match(r'\$var \w+ \d+ (\S+) (\w+)', line)
            if re.match(r'\$timescale\s+1ps\s+\$end', line):
                timescale = True
            elif var:
                if var.group(2) in SIGNALS and var.group(1) not in ids:
                    ids[var.group(1)] = var.group(2)
            elif line.startswith('#'):
                now = int(line[1:])
            else:
                value = re.match(r'^([01])(\S+)$', line)
                if value and value.group(2) in ids:
                    changes.setdefault(now, {})[ids[value.group(2)]] = int(value.group(1))
    if not timescale:
        raise RuntimeError(f"{vcd}: the trace timescale is not 1ps, so its times are not picoseconds")
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


def ns(values):
    return [v // 1000 for v in values]


def nextEdge(t):
    return (t // PERIOD + 1) * PERIOD


def times(entries):
    return [t for _, t in entries]


def beatCount(mode):
    return 1 if mode.split()[0] in ('single', 'poweron') else BEATS


def checkRun(mode, run):
    asserted = re.findall(r'^\[Q_ASSERT\].*$', run.stdout + run.stderr, re.M)
    ok = run.returncode == 0 and not asserted
    check(mode, RUN_CLEAN, ok, f"exit {run.returncode}, {asserted[0] if asserted else 'no assert'}",
          f"exit {run.returncode}" if not asserted else asserted[0])
    return ok


def checkComplete(mode, log, inHs, outHs):
    counts = {'sends': len(log['src call']), 'returns': len(log['src ret']), 'receives': len(log['snk recv']),
              'RTL takes': len(inHs), 'RTL gives': len(outHs)}
    ok = all(n == beatCount(mode) for n in counts.values())
    check(mode, COMPLETE, ok, f"expected {beatCount(mode)} of each, got {counts}")
    return ok


def checkOrder(mode, log):
    got = log['data']
    check(mode, ORDER, got == list(range(beatCount(mode))), f"sink got {got}")


def checkRecvEdge(mode, recv, outHs):
    wrong = next((k for k, (r, h) in enumerate(zip(recv, outHs)) if r != h), None)
    check(mode, RECV_EDGE, wrong is None, f"receives at {ns(recv)} ns, RTL out handshakes at {ns(outHs)} ns",
          f"first at beat {wrong}")


def singleChecks(log, changes, inHs, outHs, mode='single'):
    call, ret, recv = log['src call'][0][1], log['src ret'][0][1], log['snk recv'][0][1]
    vld = firstChange(changes, 'in_vld', 1)
    check(mode, FIRST_VLD, vld == call, f"send at {call} ps, vld rose at {vld} ps")
    check(mode, FIRST_EDGE, inHs[0] == nextEdge(call), f"send at {call} ps, RTL took the beat at {inHs[0]} ps")
    if ret == call:
        how = 'at the call'
    else:
        how = 'ahead' if ret < inHs[0] else 'late'
    check(mode, SEND_RETURN, ret == inHs[0], f"returned at {ret} ps, the RTL took the beat at {inHs[0]} ps", how)
    rtlLatency = outHs[0] - inHs[0]
    check(mode, RTL_LATENCY, rtlLatency == PERIOD,
          f"the RTL took the beat at {inHs[0]} ps and gave it up at {outHs[0]} ps")
    want = nextEdge(call) + PERIOD
    check(mode, LATENCY, recv == want,
          f"send at {call} ps, first edge at {nextEdge(call)} ps, FIFO latency {PERIOD} ps; "
          f"the sink received at {recv} ps, expected {want} ps")
    checkOrder(mode, log)


def burstChecks(log, inHs, outHs, mode='burst'):
    steady = all(b - a == PERIOD for a, b in zip(inHs, inHs[1:]))
    check(mode, RATE_IN, steady, f"{len(inHs)} handshakes at {ns(inHs)} ns")
    recv = times(log['snk recv'])
    steady = all(b - a == PERIOD for a, b in zip(recv, recv[1:]))
    check(mode, RATE_OUT, steady, f"{len(recv)} receives at {ns(recv)} ns")
    checkRecvEdge(mode, recv, outHs)
    checkOrder(mode, log)


def holdChecks(log, edges, inHs, outHs, mode='hold', readAt=None):
    readAt = HOLD_READ_AT if readAt is None else readAt
    read = log['snk call'][0][1]
    assert read == readAt, f"the sink starts reading at {read} ps, expected {readAt} ps"
    accepted = [t for t in inHs if t < read]
    full = [(t, p) for t, p in edges if accepted and accepted[-1] < t < read]
    stuck = sum(1 for t, p in full if p['in_vld'] and not p['in_rdy'])
    check(mode, RDY_DROPS, len(accepted) == FIFO_DEPTH and stuck == len(full) and bool(full),
          f"{len(accepted)} beats taken before the read at {read} ps, in.rdy low with vld high on "
          f"{stuck} of {len(full)} edges")
    calls = [t for t in times(log['src call']) if t < read]
    rets = [t for t in times(log['src ret']) if t < read]
    check(mode, SEND_BLOCKS, len(calls) == len(rets) + 1,
          f"{len(calls)} sends called and {len(rets)} returned before the read at {read} ps")
    check(mode, NO_AHEAD, len(rets) == len(accepted),
          f"{len(rets)} returns, {len(accepted)} accepted",
          f"{len(rets)} returns, {len(accepted)} accepted")
    first = next(t for t in outHs if t > read)
    behind = (first - nextEdge(read)) // PERIOD
    check(mode, RELEASE, first == nextEdge(read),
          f"read at {read} ps, first handshake at {first} ps, expected {nextEdge(read)} ps",
          f"{behind:+d} clock")
    checkOrder(mode, log)


def pauseChecks(log, outHs, mode='pause', pause=None):
    pause = PAUSE if pause is None else pause
    recv, calls = times(log['snk recv']), times(log['snk call'])
    assert calls[PAUSE_BEAT] - recv[PAUSE_BEAT - 1] == pause, \
        f"the sink paused {calls[PAUSE_BEAT] - recv[PAUSE_BEAT - 1]} ps, expected {pause} ps"
    checkRecvEdge(mode, recv, outHs)
    early = next((k for k, (c, h) in enumerate(zip(calls, outHs)) if c >= h), None)
    check(mode, HAND_WAITING, early is None,
          f"sink calls at {ns(calls)} ns, RTL out handshakes at {ns(outHs)} ns", f"first at beat {early}")
    checkOrder(mode, log)


def powerOnChecks(log, edges, changes, inHs):
    mode = 'poweron'
    release = firstChange(changes, 'rst_n', 1)
    early = [(t, k) for t in sorted(changes) if release is None or t < release
             for k in ('in_vld', 'out_rdy') if changes[t].get(k) == 1]
    inReset = [t for t, p in edges if p['in_vld'] and p['in_rdy'] and not p['rst_n']]
    check(mode, RESET_HOLD, release is not None and not early and not inReset,
          f"reset released at {release} ps, the model's first send at {log['src call'][0][1]} ps, "
          f"pins raised in reset {early}, handshakes in reset {inReset}")
    live = next((t for t, p in edges if p['rst_n']), None)
    check(mode, FIRST_LIVE_EDGE, inHs[0] == live,
          f"first edge sampled with rst_n high at {live} ps, the RTL took the beat at {inHs[0]} ps",
          f"{(inHs[0] - live) // PERIOD:+d} clock" if live is not None else 'no live edge')
    checkOrder(mode, log)


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

        runs = [(m, False) for m in MODES] + [(m, True) for m in EDGE_MODES]
        for base, onEdge in runs:
            mode = f"{base} on edge" if onEdge else base
            shift = (SEND_SHIFT, READ_SHIFT) if onEdge else (0, 0)
            print(f"\n  {mode}")
            before = len(FAILURES)
            run, log = runMode(rundir, base, onEdge)
            if not checkRun(mode, run):
                print(run.stdout + run.stderr)
                SKIPPED.add(mode)
                continue
            changes = pinChanges(os.path.join(rundir, 'build', 'simx.vcd'))
            edges = posedges(changes)
            inHs, outHs = handshakes(edges, 'in_vld', 'in_rdy'), handshakes(edges, 'out_vld', 'out_rdy')
            if not checkComplete(mode, log, inHs, outHs):
                SKIPPED.add(mode)
            else:
                if base != 'poweron':
                    sendAt = SEND_AT - shift[0]
                    assert log['src call'][0][1] == sendAt, \
                        f"the source sends at {log['src call'][0][1]} ps, expected {sendAt} ps"
                if base == 'single':
                    singleChecks(log, changes, inHs, outHs, mode)
                elif base == 'burst':
                    burstChecks(log, inHs, outHs, mode)
                elif base == 'hold':
                    holdChecks(log, edges, inHs, outHs, mode, HOLD_READ_AT - shift[1])
                elif base == 'pause':
                    pauseChecks(log, outHs, mode, PAUSE - shift[1])
                else:
                    powerOnChecks(log, edges, changes, inHs)
            if len(FAILURES) > before:
                print(run.stdout + run.stderr)
    finally:
        remove_tree(tmp)
    for row in EXPECTED_FAILURES:
        if (row.mode, row.check) in MATCHED:
            continue
        if row.mode in SKIPPED:
            message = f"expected failure not evaluated, the {row.mode} run was incomplete: {row.check}"
        else:
            message = f"unmatched expected failure: {row.mode}: {row.check}"
        FAILURES.append(message)
        print(f"  FAIL: {message}")


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
