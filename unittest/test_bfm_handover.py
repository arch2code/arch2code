#!/usr/bin/env python3
"""A BFM hands each beat over at the RTL's handshake edge, with no beat of its own.

Rule 1, no hidden buffer. Model to RTL (dst): the model's write returns in the
timestep of the edge where the RTL samples vld && rdy, so write returns never
run ahead of handshakes. RTL to model (src): the RTL sees rdy high at an edge
only if the model was already blocked in read() before that edge, and each
read returns at its handshake.

Rule 2, no lost throughput and no added clock. With the RTL always ready, or
the model reading back to back, there is one handshake per clock. dst drives
vld in the timestep of the model's send and the RTL takes the first beat at
the next edge. src hands the first beat over at the first edge after the
model calls read() with vld up. A read that starts in an edge's own timestep,
woken by time, runs ahead of that edge's processes, so the RTL takes the beat
at that edge.

A src model that waits on setExternalEvent() and reads only an active port
(rtl=arb) must not deadlock, and moves as fast as a model that waits in
read(). The BFM offers it a beat at the falling edge after vld rises, so the
RTL takes the first beat at the next rising edge. In rtl=arbreset such a
model must not see a beat that reset took off the wire, and in rtl=arbdrop a
beat the RTL dropped with no handshake.

Every run also checks that it ends without a hang or a Q_ASSERT, that order
holds and no beat is lost, and, with no delay, that no model call returns on
a reset edge. The no-backpressure contract checks still report a stall.

pop_ack, push_ack, notify_ack and req_ack run as handshake lanes, the
request as vld and ack as rdy; their src handshake must follow the model's
ack, on the next edge.

memory, apb and ahb run four operations each way. Each is served once with
the right data, a dst call that waits returns at its completion edge and a
posted write at its call, a src completes on the edge after the model, and
first-write and first-read latency and throughput meet the protocol minimum.
The mid-run reset meets an operation in flight. In error runs an apb PSLVERR
or ahb HRESP ERROR reaches the model, or the RTL, on its own transfer and not
the next, and an ahb error takes two cycles.

status, raw and external_reg drive a level through values 1 to 8. The far
side sees every value that stays on the wire across an edge out of reset,
once and in order, on the edge after it is driven; external_reg also checks
the model's mirror and the values it publishes back. memory and the level
channels ignore setTimed(), so they run at delay 0 only.

The probes are the handover section of fixtures/bfm-delayed-call. Where
today's BFM breaks a rule, EXPECTED_FAILURES names the check, the BFM line
and, for most rows, how the check fails: which beats are lost or repeated,
how many writes return ahead of their handshakes, the first beat taken
before the model asked, the clocks of latency added, a hang, or the
Q_ASSERT message. A marked check that passes, or fails another way than its
row pins, fails the suite, so a fix has to change its marker. Rows for a
check that fails only one way, and the dst rows in reset runs, accept any
failure.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(test_dir, 'fixtures', 'bfm-delayed-call', 'bfm_delayed_call.cpp')

PERIOD = 10000                   # ps
BEATS = 8
BURST = 4                        # beats per rvmulti transaction
OPS = 4
IN_ORDER = list(range(BEATS))
DELAYS = (0, 15)
RUN_END = 3_000_000              # ps; a level holds its last value to the end of the run
TIMEOUT = 5                      # s; a probe runs in a few ms
STALL = 'HDL stalled a backpressure: false interface'
SC_STALL = 'SystemC stalled a backpressure: false producer'

# push_ack, pop_ack, notify_ack and req_ack run as handshake lanes, the
# request as vld and ack as rdy. Their src model takes a request in two
# calls, receive then ack(), so the RTL's handshake follows the model's ack.
TWO_PHASE = ('pushack', 'popack', 'notifyack', 'reqack')
HANDSHAKE = ('rv', 'axis', 'ar', 'r', 'aw', 'w', 'b') + TWO_PHASE
BUS = ('mem', 'apb', 'ahb')
LEVEL = ('status', 'raw', 'extreg')
RTL_MODES = ('always', 'hold', 'every3', 'random', 'comb', 'reset')
# Always-valid src runs: the model first reads half a clock after vld rises
# (always), is already in read() when vld rises (waiting), or first reads
# 15 ns after vld rises, so beat 0 sits on the wire across an edge (parked).
FULL_RATE = ('always', 'waiting', 'parked')
# (rtl, busy ns) for src runs: each RTL mode with a model that reads back to
# back, and slow models against an always-valid or random RTL.
SRC_RUNS = ([(m, 0) for m in RTL_MODES] + [('waiting', 0), ('parked', 0)]
            + [('always', 25), ('always', 100), ('random', 25)])

Case = namedtuple('Case', 'family dir rtl busy bp delay')
CASES = [Case(f, 'dst', m, 0, 'allowed', d) for f in HANDSHAKE for m in RTL_MODES for d in DELAYS]
# An _ack src RTL never raises its request because ack is high, so comb is a
# dst mode for those.
CASES += [Case(f, 'src', m, b, 'allowed', d) for f in HANDSHAKE for m, b in SRC_RUNS for d in DELAYS
          if not (f in TWO_PHASE and m == 'comb')]
CASES += [Case('rvmulti', dr, 'always', 0, 'allowed', d) for dr in ('dst', 'src') for d in DELAYS]
CASES += [Case('wfirst', 'src', 'always', 0, 'allowed', d) for d in DELAYS]
# A delayed aw or w src run moves a beat every other edge. Its reset, 55 ns
# after the lane starts, lands while a delayed model call blocks. resetlate
# starts the reset an edge later, where vld and ready are high.
CASES += [Case(f, 'src', 'resetlate', 0, 'allowed', 15) for f in ('aw', 'w')]
CASES += [Case(f, 'dst', 'hold', 0, 'none', 0) for f in ('rv', 'axis')]
CASES += [Case(f, 'src', 'always', 25, 'none', 0) for f in ('rv', 'axis')]
# Bus runs: a completer with wait states or a master with idle edges (slow),
# a parked src model, and errors on operations 1 and 2 (apb and ahb).
BUS_MODES = {'dst': ('always', 'slow', 'reset', 'error'), 'src': ('always', 'parked', 'slow', 'reset', 'error')}
# memory, status, raw and external_reg channels ignore setTimed(), so they run at delay 0 only.
UNTIMED = ('mem',) + LEVEL
# A model that waits on setExternalEvent() and reads only an active port.
CASES += [Case(f, 'src', 'arb', 0, 'allowed', d) for f in ('rv', 'axis', 'ar', 'r', 'aw', 'w', 'b') for d in DELAYS]
# The same model, busy 25 ns after each read, and a reset that meets a beat
# offered to it.
CASES += [Case(f, 'src', 'arbreset', 25, 'allowed', d) for f in ('rv', 'axis', 'ar', 'aw') for d in DELAYS]
# The same busy model, with an RTL that lowers vld on an offered beat for two
# edges, with no handshake.
CASES += [Case(f, 'src', 'arbdrop', 25, 'allowed', 0) for f in ('rv', 'axis', 'ar', 'aw')]
CASES += [Case(f, dr, m, 0, 'allowed', d) for f in BUS for dr in BUS_MODES for m in BUS_MODES[dr] for d in DELAYS
          if not (m == 'error' and f == 'mem') and not (m == 'slow' and f == 'mem' and dr == 'dst')
          and not (f in UNTIMED and d > 0)]
LEVEL_MODES = {'dst': ('always', 'reset'), 'src': ('always', 'every3', 'reset')}
CASES += [Case(f, dr, m, 0, 'allowed', 0) for f in LEVEL for dr in LEVEL_MODES for m in LEVEL_MODES[dr]]

RESET_DST = "ends the beat on an edge with ready high whether or not reset is low"
RESET_SRC = "delivers a beat it samples on a reset edge, and the RTL sends that beat again after reset"
R_DRAIN = ("axi_read_bfm.h:120-148 drops the R beat on the wire at reset and returns the model's remaining "
           "sendDataCycle() calls with no handshake, to drain the burst")
B_DROP = ("axi_write_bfm.h:163-168 takes the model's B on a reset edge and drops it, and 176-183 drops the B "
          "on the wire at reset")
DUMMY_W = ("axi_write_bfm.h:127-145 drains the burst of the last AW at reset: it sends the model a zero W beat, "
           "with that AW's ID, for each beat left, and the model reads them as data. This is a defect in the reset "
           "drain, left for the reset work")
TAKE_IN_RESET = f"rdy_vld_src_driver.h:93-97 {RESET_SRC}"
R_TAKE_IN_RESET = f"axi_read_bfm.h:235 adds no reset handling, and {TAKE_IN_RESET}"
B_TAKE_IN_RESET = f"axi_write_bfm.h:290 adds no reset handling, and {TAKE_IN_RESET}"
DST_RULE_1 = ('dst write returns never run ahead of handshakes', 'dst write returns at its handshake edge')
SRC_RULE_1 = 'src handshake only while the model waits in read()'
SRC_RETURN = 'src read returns at its handshake edge'
SRC_COUNT = 'src read count matches handshakes'
ORDER = 'order kept, no beat lost'
RESET_RETURN = 'no model return on a reset edge'
ACK_RULE_1 = "src handshake only after the model's ack"
ACK_RETURN = "src handshake on the edge after the model's ack"
DONE = 'probe runs to completion'
NO_ASSERT = 'no Q_ASSERT stops the run'
ARB_FIRST = 'an arbitrating reader gets the first beat at the first edge after vld'
ARB_RATE = 'an arbitrating reader moves as fast as a reader that waits in read()'
# Handshake gap of a reader that waits in read(), per delay: a delayed send
# holds ready low until it returns.
WAITING_GAP = {0: PERIOD, 15: 2 * PERIOD}


def anyCase(case):
    return True


def busy(case):
    return case.busy > 0


def inReset(case):
    return case.rtl == 'reset'


def resetDelayed(case):
    return case.rtl == 'reset' and case.delay > 0


def srcResetNow(case):
    return case.rtl == 'reset' and case.delay == 0


def resetLate(case):
    return case.rtl == 'resetlate'


# The src families whose delayed reset the fixture moves off the default 45 ns.
MOVED_RESET = ('rv', 'axis', 'ar', 'aw', 'w')


# A row marks checks that fail today: (families, direction, checks, applies
# to case, how the check fails, reason naming the BFM line). how pins the
# failure, for example which beats are lost, and None accepts any failure.
XFail = namedtuple('XFail', 'families dir checks applies how reason')
EXPECTED_FAILURES = [
    XFail(('rv',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"rdy_vld_bfm.h:151 {RESET_DST}"),
    XFail(('rv',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"rdy_vld_bfm.h:151 {RESET_DST}"),
    XFail(('axis',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"axi4_stream_bfm.h:193 {RESET_DST}"),
    XFail(('axis',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi4_stream_bfm.h:193 {RESET_DST}"),
    XFail(('ar',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"axi_read_bfm.h:227 {RESET_DST}"),
    XFail(('ar',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_read_bfm.h:227 {RESET_DST}"),
    XFail(('aw',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"axi_write_bfm.h:257 {RESET_DST}"),
    XFail(('aw',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_write_bfm.h:257 {RESET_DST}"),
    XFail(('w',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"axi_write_bfm.h:282 {RESET_DST}"),
    XFail(('w',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_write_bfm.h:282 {RESET_DST}"),
    XFail(('r',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, R_DRAIN),
    XFail(('r',), 'dst', (ORDER,), inReset, 'hs missing, model ok', R_DRAIN),
    XFail(('b',), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, B_DROP),
    XFail(('b',), 'dst', (ORDER,), inReset, 'hs missing, model ok', B_DROP),

    XFail(('rv',), 'src', (ORDER,), inReset, 'hs missing, model missing+duplicate', TAKE_IN_RESET),
    XFail(('rv',), 'src', (RESET_RETURN, SRC_COUNT), inReset, None, TAKE_IN_RESET),
    XFail(('rv',), 'src', (SRC_RETURN,), inReset, 'count', TAKE_IN_RESET),
    XFail(('axis',), 'src', (ORDER,), inReset, 'hs missing, model missing+duplicate', TAKE_IN_RESET),
    XFail(('axis',), 'src', (RESET_RETURN, SRC_COUNT), inReset, None, TAKE_IN_RESET),
    XFail(('axis',), 'src', (SRC_RETURN,), inReset, 'count', TAKE_IN_RESET),
    XFail(('r',), 'src', (ORDER,), inReset, 'hs missing, model missing+duplicate', R_TAKE_IN_RESET),
    XFail(('r',), 'src', (RESET_RETURN,), inReset, None, R_TAKE_IN_RESET),
    XFail(('r',), 'src', (SRC_RETURN,), inReset, 'edge', R_TAKE_IN_RESET),
    XFail(('r',), 'src', (NO_ASSERT,), inReset, '[Q_ASSERT][p.dut.ch] last set incorrectly (axi_read_channel.h)',
          f"{R_TAKE_IN_RESET}, so the burst's eighth beat is not the one with rlast"),
    XFail(('b',), 'src', (ORDER,), inReset, 'hs missing, model missing',
          "the assert below stops the run before every B is in"),
    XFail(('b',), 'src', (RESET_RETURN,), inReset, None, B_TAKE_IN_RESET),
    XFail(('b',), 'src', (SRC_RETURN,), inReset, 'edge', B_TAKE_IN_RESET),
    XFail(('b',), 'src', (NO_ASSERT,), inReset, '[Q_ASSERT][p.dut.ch] transaction id not valid (axi_write_channel.h)',
          f"{B_TAKE_IN_RESET}, so the second B finds no write waiting for its ID"),
    XFail(('w',), 'src', (ORDER,), lambda c: inReset(c) or resetLate(c), 'hs missing, model missing+duplicate',
          DUMMY_W),
    XFail(('w',), 'src', (RESET_RETURN, SRC_COUNT), lambda c: inReset(c) or resetLate(c), None, DUMMY_W),
    XFail(('w',), 'src', (SRC_RETURN,), lambda c: inReset(c) or resetLate(c), 'count', DUMMY_W),
]

# The _ack BFMs: (family, src lines, dst lines, how a src reset run loses order, how a dst reset run loses
# order).
ACK_BFMS = (
    ('pushack', 'push_ack_bfm.h:39-49', 'push_ack_bfm.h:80-87',
     'hs missing, model missing+duplicate', 'hs missing, model ok'),
    ('popack', 'pop_ack_bfm.h:37-48', 'pop_ack_bfm.h:81-88',
     'hs missing, model ok', 'hs missing, model missing+duplicate'),
    ('notifyack', 'notify_ack_bfm.h:37-46', 'notify_ack_bfm.h:75-80',
     'hs missing, model ok', 'hs missing, model ok'),
    ('reqack', 'req_ack_bfm.h:39-51', 'req_ack_bfm.h:83-89',
     'hs missing, model missing+duplicate', 'hs missing, model missing+duplicate'),
)
ACK_RESET = "never reads rst_n after the first reset: it serves a request it samples on a reset edge"
for fam, srcLines, dstLines, srcOrder, dstOrder in ACK_BFMS:
    EXPECTED_FAILURES += [
        XFail((fam,), 'src', (ORDER,), srcResetNow, srcOrder, f"{srcLines} {ACK_RESET}"),
        XFail((fam,), 'src', (ACK_RULE_1, ACK_RETURN), srcResetNow, 'count', f"{srcLines} {ACK_RESET}"),
        XFail((fam,), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"{dstLines} {RESET_DST}"),
        XFail((fam,), 'dst', (ORDER,), inReset, dstOrder, f"{dstLines} {RESET_DST}"),
    ]

MEM_RESET = "reads rst_n only before the first reset, never in its loop"
BUS_RESET = "never reads rst_n after the first reset, so a transfer in flight at the reset is lost or completes later"
APB_SRC_RESET = ("apb_bfm.h:44-70 reads rst_n only where it samples a setup phase. A reset that cuts off a "
                 "transfer after the model has answered loses the answer, and the model serves the RTL's repeat "
                 "of it as the next operation")
EXPECTED_FAILURES += [
    XFail(('apb',), 'dst', ('served once',), inReset, None, f"apb_bfm.h:97-140 {BUS_RESET}"),
    XFail(('apb',), 'src', ('served once',), resetDelayed, 'RTL 4/3, model 4', APB_SRC_RESET),
    XFail(('apb',), 'src', ('values',), resetDelayed, None, APB_SRC_RESET),
    XFail(('apb',), 'src', ('an error reaches the RTL on its own transfer',), resetDelayed, '[0, 0, 0]', APB_SRC_RESET),
    XFail(('ahb',), 'dst', ('served once', 'values'), inReset, None, f"ahb_bfm.h:139-189 {BUS_RESET}"),
    XFail(('ahb',), 'src', ('served once', 'values', 'an error reaches the RTL on its own transfer'), inReset, None,
          f"ahb_bfm.h:75-101 {BUS_RESET}; line 99 takes an address phase on a reset edge and sends it to the model"),
    XFail(('mem',), 'dst', ('served once',), inReset, 'RTL 2/2, model 4',
          f"memory_bfm.h:83 {MEM_RESET}: 89-97 drive operations 2 and 3 on reset edges, where the RTL takes "
          "neither, and the model's calls return"),
    XFail(('mem',), 'dst', ('values',), inReset, None,
          f"memory_bfm.h:83 {MEM_RESET}: 101-105 complete the read the RTL never took with the previous read's "
          "word, 0x11"),
    XFail(('mem',), 'src', ('values',), inReset, None,
          f"memory_bfm.h:43 {MEM_RESET}: 46-54 take operation 2 on a reset edge and send it to the model, and "
          "the RTL gets the stale read data"),
    XFail(('mem',), 'src', ('src completes on the edge after the model',), inReset, '+2 clock',
          f"memory_bfm.h:43 {MEM_RESET}: 46-54 take operation 2 on a reset edge and send it to the model"),
]


def expectedFailure(case, check):
    """The row that marks `check` on `case` as failing today, or None."""
    for row in EXPECTED_FAILURES:
        if case.family in row.families and case.dir == row.dir and check in row.checks and row.applies(case):
            return row
    return None


FAILURES = []
XFAILS = []
NUMBERS = []


def check(case, name, condition, detail, how='fails'):
    """Records a check; a marked check passes the suite only by failing as its row says."""
    row = expectedFailure(case, name)
    message = f"{caseTag(case)}: {name} ({detail})"
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


def caseTag(case):
    tag = f"{case.family} {case.dir} rtl={case.rtl} delay={case.delay}"
    if case.busy:
        tag += f" busy={case.busy}"
    if case.bp == 'none':
        tag += ' bp=none'
    return tag


def nextEdge(t):
    return (t // PERIOD + 1) * PERIOD


def liveEdge(t, resetEdges):
    """The first edge after t out of reset."""
    edge = nextEdge(t)
    while edge in resetEdges:
        edge += PERIOD
    return edge


def events(output):
    """Each kind's (value, ps) list, and its sc_delta_count() list."""
    ev, deltas = {}, {}
    for kind, value, ps, delta in re.findall(r'^ev (\w+) (\d+) (\d+) (\d+)$', output, re.M):
        ev.setdefault(kind, []).append((int(value), int(ps)))
        deltas.setdefault(kind, []).append(int(delta))
    return ev, deltas


def beatsHow(values):
    """How a list of beats differs from 0..BEATS-1: missing, duplicate, reordered, or ok."""
    if values == IN_ORDER:
        return 'ok'
    faults = [name for name, fault in (('missing', set(IN_ORDER) - set(values)),
                                       ('duplicate', len(set(values)) < len(values))) if fault]
    return '+'.join(faults) or 'reordered'


def handshakeChecks(case, ev, deltas, output):
    hs, calls, rets, vld = (ev.get(k, []) for k in ('hs', 'call', 'ret', 'vld'))
    if case.rtl == 'arbreset':
        r0 = min(t for _, t in ev['rst'])
        # The model sees the beat active half a clock before the reset edge.
        check(case, 'the reset meets a beat offered to the model',
              r0 in {t for _, t in ev.get('rstvld', [])} - {t for _, t in ev.get('rsths', [])}
              and r0 - PERIOD // 2 in {t for _, t in ev.get('act', [])},
              f"first reset edge {r0}, vld {ev.get('rstvld', [])}, vld and ready {ev.get('rsths', [])}, "
              f"active {[t for _, t in ev.get('act', [])]}")
        check(case, 'an arbitrating reader sees no beat reset took off the wire', not ev.get('rstact'),
              f"isActive() mid-clock after a reset edge at {[t for _, t in ev.get('rstact', [])]}")
    if case.rtl == 'arbdrop':
        # The model sees the beat active half a clock before the RTL lowers
        # vld. The BFM sees vld low at the next falling edge and withdraws
        # the beat, so it is not active then.
        drops, act = ev.get('drop', []), {t for _, t in ev.get('act', [])}
        check(case, 'the RTL drops a beat offered to the model', bool(drops) and drops[0][1] - PERIOD // 2 in act,
              f"drops {drops}, active {sorted(act)}")
        if drops:
            gap = drops[0][1] + PERIOD // 2
            check(case, 'an arbitrating reader sees no beat the RTL dropped', gap not in act,
                  f"drop at {drops[0][1]}, active at {gap}: {gap in act}")
    hsTimes = [t for _, t in hs]
    hsValues, retValues = [v for v, _ in hs], [v for v, _ in rets]
    check(case, ORDER, hsValues == IN_ORDER and retValues == IN_ORDER,
          f"hs={hsValues} model={retValues}", f"hs {beatsHow(hsValues)}, model {beatsHow(retValues)}")
    if case.rtl == 'reset' and case.delay == 0 and rets:
        resetEdges = {t for _, t in ev.get('rst', [])}
        check(case, RESET_RETURN, not resetEdges & {t for _, t in rets},
              f"reset edges {sorted(resetEdges)}, model returns {[t for _, t in rets]}")
    judged = case.family != 'rvmulti' and rets
    if case.family == 'rvmulti' and case.delay == 0 and len(rets) == len(hs) == BEATS:
        # A burst crosses the ping-pong buffer as one transaction. The dst
        # BFM takes it from the writer at the first beat's handshake and
        # reads the other beats from the buffer, so the write that ends a
        # burst returns there. The src BFM writes the beats into the buffer
        # and hands the transaction over with the last one.
        starts = range(0, BEATS, BURST)
        if case.dir == 'dst':
            name, got, want = ('a burst write returns at the handshake of its first beat',
                               [rets[k + BURST - 1][1] for k in starts], [hsTimes[k] for k in starts])
        else:
            name, got, want = ('a burst read returns at the handshake of its last beat',
                               [rets[k][1] for k in starts], [hsTimes[k + BURST - 1] for k in starts])
        check(case, name, got == want, f"returns {got}, handshakes {want}")
    if judged and case.dir == 'dst':
        lead = max(i + 1 - sum(h <= t for h in hsTimes) for i, (_, t) in enumerate(rets))
        check(case, 'dst write returns never run ahead of handshakes', lead <= 0,
              f"returns at most {lead} ahead of handshakes", f"{lead} ahead")
        if case.delay == 0:
            check(case, 'dst write returns at its handshake edge',
                  len(rets) == len(hs) and all(r[1] == h[1] for r, h in zip(rets, hs)),
                  f"returns={[t for _, t in rets]} hs={hsTimes}", f"{lead} ahead")
    elif judged and case.family in TWO_PHASE:
        early = [i for i, (h, r) in enumerate(zip(hsTimes, rets)) if h <= r[1]]
        check(case, ACK_RULE_1, len(rets) == len(hs) and not early,
              f"handshakes at or before the model's ack: {early}, acks={[t for _, t in rets]} hs={hsTimes}",
              f"first at beat {early[0]}" if early else 'count')
        if case.delay == 0:
            check(case, ACK_RETURN, len(rets) == len(hs) and all(h == nextEdge(r[1]) for h, r in zip(hsTimes, rets)),
                  f"acks={[t for _, t in rets]} hs={hsTimes}", 'count' if len(rets) != len(hs) else 'edge')
    elif judged:
        # A read that starts in an edge's timestep, woken by time, runs ahead
        # of that edge's processes, so the RTL sees its ready at that edge.
        # This relies on the RTL sampling rdy in the posedge delta, as dst
        # relies on it to drive vld in the timestep of the model's send.
        callDeltas, hsDeltas = deltas.get('call', []), deltas.get('hs', [])
        unwaited = [i for i, t in enumerate(hsTimes) if i >= len(calls) or calls[i][1] > t
                    or (calls[i][1] == t and callDeltas[i] >= hsDeltas[i])]
        check(case, SRC_RULE_1, not unwaited,
              f"handshakes with no read waiting: {unwaited}, reads={[t for _, t in calls]} hs={hsTimes}",
              f"first at beat {unwaited[0]}" if unwaited else '')
        if case.delay == 0:
            check(case, SRC_RETURN,
                  len(rets) == len(hs) and all(r[1] == h[1] for r, h in zip(rets, hs)),
                  f"returns={[t for _, t in rets]} hs={hsTimes}", 'count' if len(rets) != len(hs) else 'edge')
        else:
            check(case, SRC_COUNT, len(rets) == len(hs),
                  f"{len(rets)} reads returned, {len(hs)} handshakes")
    if case.rtl == 'arb' and hs and vld:
        # The BFM offers each beat at the falling edge after vld rises, so the
        # model's read() raises ready before the next rising edge.
        first = nextEdge(vld[0][1])
        check(case, ARB_FIRST, hsTimes[0] == first,
              f"vld {vld[0][1]}, first handshake {hsTimes[0]}, expected {first}")
        gaps = sorted({b - a for a, b in zip(hsTimes, hsTimes[1:])})
        check(case, ARB_RATE, gaps == [WAITING_GAP[case.delay]],
              f"handshake gaps {gaps} ps, expected {WAITING_GAP[case.delay]}")
        NUMBERS.append(f"{case.family} src rtl=arb delay={case.delay}: handshake gap {gaps} ps; vld {vld[0][1]} ps, "
                       f"first handshake {hsTimes[0]} ps")
    if case.rtl in FULL_RATE and case.delay == 0 and case.busy == 0 and case.bp == 'allowed':
        gaps = sorted({b - a for a, b in zip(hsTimes, hsTimes[1:])})
        check(case, 'throughput', gaps == [PERIOD], f"handshake gaps {gaps} ps")
        if case.family == 'rvmulti' or not hs or not calls or not vld:
            return
        NUMBERS.append(f"{case.family} {case.dir} rtl={case.rtl}: handshake gap {gaps} ps; model call {calls[0][1]} ps, "
                       f"vld {vld[0][1]} ps, first handshake {hsTimes[0]} ps")
        if case.dir == 'dst':
            first = nextEdge(vld[0][1])
            check(case, 'dst latency', vld[0][1] == calls[0][1] and hsTimes[0] == first,
                  f"send {calls[0][1]}, vld {vld[0][1]}, first handshake {hsTimes[0]}, first edge after vld {first}")
        else:
            first = nextEdge(max(calls[0][1], vld[0][1]))
            check(case, 'src latency', hsTimes[0] == first,
                  f"read {calls[0][1]}, vld {vld[0][1]}, first handshake {hsTimes[0]}, expected {first}",
                  f"{(hsTimes[0] - first) // PERIOD:+d} clock")
    if case.dir == 'src' and case.rtl in ('reset', 'resetlate') and case.delay > 0 and case.family in MOVED_RESET:
        # The fixture times these resets to a phase, so a timing change that
        # moves the reset off it fails here.
        r0 = min(t for _, t in ev['rst'])
        if case.rtl == 'resetlate' or case.family in ('rv', 'axis', 'ar'):
            check(case, 'the reset starts on an edge with vld and ready high',
                  r0 in {t for _, t in ev.get('rsths', [])},
                  f"first reset edge {r0}, vld and ready {ev.get('rsths', [])}")
        else:
            inFlight = [hv for hv, h in hs for rv, r in rets if hv == rv and h < r0 < r]
            check(case, 'the reset starts while a delayed model call blocks', bool(inFlight),
                  f"first reset edge {r0}, hs={hs} model={rets}")
    if case.dir == 'src' and case.rtl in ('reset', 'resetlate'):
        # A src BFM has ready high at a reset edge unless the edge falls between
        # a handshake and the return of that beat's delayed model call. Ready
        # is low then, so the reset meets the next beat with vld alone. A
        # resetlate run must meet vld and ready high. An _ack src BFM samples
        # the request alone.
        if case.family in TWO_PHASE:
            met = ev.get('rstvld', [])
        elif case.rtl == 'resetlate':
            met = ev.get('rsths', [])
        else:
            met = ev.get('rsths', []) + [(v, t) for v, t in ev.get('rstvld', [])
                                         if any(hv == rv and h < t < r for hv, h in hs for rv, r in rets)]
        check(case, 'the reset meets a beat on the wire', bool(met), f"reset edges with the beat on the wire: {met}")
    if case.bp == 'none':
        line = STALL if case.dir == 'dst' else SC_STALL
        check(case, 'no-backpressure check reports the stall', f'p.dut.bfm:{line} at ' in output,
              f"'{line}'")


# What a bus run returns: model read data (dst) or RTL completion data (src).
DST_VALUES = [0x11, 0x11, 0x22, 0x22]
SRC_VALUES = [0, 0x11, 0, 0x22]
# Fewest edges between operations: memory and pipelined ahb take one per
# clock, apb a setup and an access phase.
MIN_GAP = {'mem': PERIOD, 'apb': 2 * PERIOD, 'ahb': PERIOD}
# An RTL master's request reaches the model in the timestep of the edge after
# the master drives it: the memory access, the apb setup phase, or the ahb
# address phase. An ahb write's data goes on the wire only after that edge, and
# a BFM reads it on the next one, so every ahb src write takes a wait state.
ERROR_OPS = [0, 1, 1, 0]


def awaitsResponse(case, k):
    """A dst model call that waits for the RTL: a read, or a response-aware write in error runs."""
    return k % 2 == 1 or (case.rtl == 'error' and k != 2)


def busChecks(case, ev):
    req, ack, calls, rets, rerr = (ev.get(k, []) for k in ('req', 'ack', 'call', 'ret', 'rerr'))
    resetEdges = {t for _, t in ev.get('rst', [])}
    # A src RTL logs its operation index, and starts an operation a reset cut off again.
    reqs = len({v for v, _ in req}) if case.dir == 'src' else len(req)
    served = reqs == OPS and len(ack) == OPS and len(rets) == OPS
    check(case, 'served once', served,
          f"RTL requests {req}, RTL completions {len(ack)}, model completions {len(rets)}",
          f"RTL {reqs}/{len(ack)}, model {len(rets)}")
    errorRun = case.rtl == 'error'
    if case.dir == 'dst':
        got = [v for k, (v, _) in enumerate(rets) if not (errorRun and ERROR_OPS[k] and k % 2)]
        want = [v for k, v in enumerate(DST_VALUES[:len(rets)]) if not (errorRun and ERROR_OPS[k] and k % 2)]
        check(case, 'values', got == want, f"model got {[v for v, _ in rets]}")
        if errorRun:
            errs = [v for v, _ in ev.get('err', [])]
            check(case, 'an error reaches the model on its own transfer', errs == [0, 1, 0],
                  f"model errors {errs} for operations 0, 1 and 3; 2 is posted", f"{errs}")
    else:
        check(case, 'values', [v for v, _ in ack] == SRC_VALUES[:len(ack)] and len(ack) == OPS,
              f"RTL got {[v for v, _ in ack]}")
        if case.family != 'mem':
            want = ERROR_OPS if errorRun else [0] * OPS
            check(case, 'an error reaches the RTL on its own transfer', [v for v, _ in rerr] == want,
                  f"RTL errors {[v for v, _ in rerr]}, expected {want}", f"{[v for v, _ in rerr]}")
        if case.family == 'ahb' and errorRun and len(ack) == OPS:
            first = ev.get('errfirst', [])
            want = [(k, ack[k][1] - PERIOD) for k in (1, 2)]
            check(case, 'an ahb error takes two cycles', first == want,
                  f"first error cycles {first}, expected {want}", f"{first}")
    if case.rtl == 'reset':
        # Operations started before the first reset edge outnumber those completed before it.
        r0 = min(t for _, t in ev['rst'])
        started = len([t for _, t in calls if t < r0]) if case.dir == 'dst' else len({v for v, t in req if t < r0})
        done = len([t for _, t in ack if t < r0])
        check(case, 'the reset meets an operation in flight', started > done,
              f"first reset edge {r0}, operations started {started}, completed {done}")
    if not served:
        return
    if case.dir == 'dst':
        waits = [k for k in range(OPS) if awaitsResponse(case, k)]
        if case.delay == 0:
            check(case, 'dst call returns at its completion edge', all(rets[k][1] == ack[k][1] for k in waits),
                  f"model returns {[rets[k][1] for k in waits]}, RTL completion edges {[ack[k][1] for k in waits]}")
            posted = [k for k in range(OPS) if not awaitsResponse(case, k)]
            check(case, 'a posted write returns at its call', all(rets[k][1] == calls[k][1] for k in posted),
                  f"calls {[calls[k][1] for k in posted]}, returns {[rets[k][1] for k in posted]}")
        else:
            check(case, 'dst call returns no earlier than its completion', all(rets[k][1] >= ack[k][1] for k in waits),
                  f"model returns {[rets[k][1] for k in waits]}, RTL completion edges {[ack[k][1] for k in waits]}")
        if case.rtl == 'always' and case.delay == 0:
            check(case, 'dst latency', req[0][1] == nextEdge(calls[0][1]),
                  f"call {calls[0][1]}, RTL sees it {req[0][1]}", f"{(req[0][1] - nextEdge(calls[0][1])) // PERIOD:+d} clock")
            gap = req[1][1] - req[0][1]
            check(case, 'throughput', gap == MIN_GAP[case.family],
                  f"a posted write then a read: RTL sees them {gap} ps apart, protocol minimum {MIN_GAP[case.family]}",
                  f"{gap // PERIOD} edges")
            NUMBERS.append(f"{case.family} dst rtl=always: request gap {gap} ps; model call {calls[0][1]} ps, "
                           f"RTL sees the request {req[0][1]} ps, completes it {ack[0][1]} ps")
        return
    rcalls, rcvs = ev.get('rcall', []), ev.get('rcv', [])
    late = [k for k in range(OPS) if ack[k][1] <= rets[k][1]]
    check(case, 'src completes only after the model', not late, f"RTL completions before the model's: {late}")
    if case.delay == 0:
        # An ahb error response takes a second cycle.
        want = [liveEdge(rets[k][1], resetEdges) + (PERIOD if case.family == 'ahb' and errorRun and ERROR_OPS[k] else 0)
                for k in range(OPS)]
        lag = max(a[1] - w for a, w in zip(ack, want))
        check(case, 'src completes on the edge after the model', [t for _, t in ack] == want,
              f"model completes {[t for _, t in rets]}, RTL completion edges {[t for _, t in ack]}, expected {want}",
              f"{lag // PERIOD:+d} clock")
    if case.rtl in ('always', 'parked') and case.delay == 0:
        # Operation 0 is the first write, and operation 1 the first read. An ahb write's HWDATA goes on the
        # wire in the data phase, after the edge that takes the address phase, so the BFM reads it at the
        # falling edge after that.
        for name, k in (('src latency', 0), ('src read latency', 1)):
            hwdata = PERIOD // 2 if case.family == 'ahb' and k == 0 else 0
            first = max(req[k][1] + PERIOD + hwdata, rcalls[k][1])
            check(case, name, rcvs[k][1] == first,
                  f"RTL request {req[k][1]}, model asks {rcalls[k][1]}, model gets it {rcvs[k][1]}, expected {first}",
                  f"{(rcvs[k][1] - first) // 1000:+d} ns")
    if case.rtl == 'always' and case.delay == 0:
        gaps = sorted({b[1] - a[1] for a, b in zip(ack, ack[1:])})
        check(case, 'throughput', gaps == [MIN_GAP[case.family]],
              f"RTL completion gaps {gaps} ps, protocol minimum {MIN_GAP[case.family]}",
              f"{[g // PERIOD for g in gaps]} edges")
        NUMBERS.append(f"{case.family} src rtl=always: completion gap {gaps} ps; model asks {rcalls[0][1]} ps, "
                       f"RTL request {req[0][1]} ps, model receives it {rcvs[0][1]} ps")


def levelHow(got, want):
    """How a list of values differs from the expected list."""
    if got == want:
        return 'ok'
    faults = [name for name, fault in (('missing', set(want) - set(got)), ('extra', set(got) - set(want)),
                                       ('duplicate', len(set(got)) < len(got))) if fault]
    return '+'.join(faults) or 'reordered'


def lagHow(times, want):
    """The first value that arrives late, or early, against its expected time."""
    off = [(k, t - w) for k, (t, w) in enumerate(zip(times, want)) if t != w]
    return f"value {off[0][0]} {off[0][1] // 1000:+d} ns" if off else 'ok'


def visible(writes, resetEdges, end):
    """Values that stay on a level across an edge out of reset: writes is (value, time) in order."""
    seen = []
    for k, (v, t) in enumerate(writes):
        until = writes[k + 1][1] if k + 1 < len(writes) else end
        if any(e not in resetEdges for e in range(nextEdge(t), until + 1, PERIOD)):
            seen.append(v)
    return seen


def inOrderAcrossReset(case, who, got, want):
    """external_reg drops a write the RTL has not taken at a reset and drives rdata 0 in reset
    (external_reg_bfm.h:50, 112-114, 128-129), so across a reset this checks that the values seen
    come in order, none extra or repeated, and the last one arrives."""
    seen = [v for v in got if v]
    rest = iter(want)
    check(case, f'across a reset the {who} sees values in order and the last one',
          all(v in rest for v in seen) and seen[-1:] == want[-1:], f"sent {want}, {who} saw {got}")


def levelChecks(case, ev):
    """Levels: each value arrives once, in order, on the edge after it is driven."""
    calls, rets, drv, smp, pin = (ev.get(k, []) for k in ('call', 'ret', 'drv', 'smp', 'pin'))
    resetEdges = {t for _, t in ev.get('rst', [])}
    if case.dir == 'dst':
        wire = pin if case.family != 'extreg' else calls
        want = visible(wire, resetEdges, RUN_END)
        got = [v for v, _ in smp]
        if case.family == 'extreg' and case.rtl == 'reset':
            # A write issued in reset, or in the clock before it, may be dropped (external_reg_bfm.h:112-114,
            # 128-129); every other write must reach the RTL.
            kept = [v for v, t in calls if nextEdge(t) not in resetEdges and nextEdge(t) - PERIOD not in resetEdges]
            lost = [v for v in kept if v not in got]
            check(case, 'the RTL sees every write issued out of reset', not lost,
                  f"writes issued out of reset {kept}, RTL saw {got}", f"missing {lost}")
            inOrderAcrossReset(case, 'RTL', got, [v for v, _ in calls])
            return
        check(case, 'the RTL sees every value once, in order', got == want, f"on the wire {want}, RTL saw {got}",
              f"RTL {levelHow(got, want)}")
        if case.family != 'extreg' and case.delay == 0:
            check(case, 'the pin follows the first write in its timestep', pin[0][1] == calls[0][1],
                  f"write {calls[0][1]}, pin {pin[0][1]}")
        if case.rtl == 'always' and case.delay == 0 and got == want:
            check(case, 'the RTL sees each value on the edge after the write',
                  [t for _, t in smp] == [nextEdge(t) for _, t in wire],
                  f"on the wire {[t for _, t in wire]}, RTL samples {[t for _, t in smp]}",
                  lagHow([t for _, t in smp], [nextEdge(t) for _, t in wire]))
            if case.family == 'raw':
                gaps = sorted({b[1] - a[1] for a, b in zip(smp, smp[1:])})
                check(case, 'throughput', gaps == [PERIOD], f"RTL sample gaps {gaps} ps")
        if case.family == 'extreg':
            mirror = [(v, t) for v, t in ev.get('mir', []) if v]
            check(case, "the model's mirror follows the RTL's rdata", [v for v, _ in mirror] == [v for v, _ in drv],
                  f"RTL rdata {[v for v, _ in drv]}, mirror {[v for v, _ in mirror]}")
            if case.delay == 0 and [v for v, _ in mirror] == [v for v, _ in drv]:
                check(case, "the mirror updates on the edge after the RTL's rdata",
                      [t for _, t in mirror] == [t + PERIOD for _, t in drv],
                      f"RTL rdata {[t for _, t in drv]}, mirror {[t for _, t in mirror]}",
                      lagHow([t for _, t in mirror], [t + PERIOD for _, t in drv]))
        return
    if case.family == 'raw':
        # raw has no handshake: the model gets the RTL's value from every edge.
        def valueAt(t):
            return [v for v, d in drv if d <= t][-1]
        first = rets[:BEATS + 4]
        # The read at time 0 gets the value driven at time 0.
        want = [valueAt(max(t - PERIOD, 0)) for _, t in first]
        gaps = sorted({b[1] - a[1] for a, b in zip(first, first[1:])})
        check(case, "the model gets the RTL's value from every edge", [v for v, _ in first] == want and gaps == [PERIOD],
              f"model got {[v for v, _ in first]} at gaps {gaps}, RTL values {want}")
        return
    driven = [v for v, _ in drv]
    if case.family == 'extreg':
        want = driven
    else:
        want = visible(drv, set(), RUN_END)
    got = [v for v, _ in rets]
    if case.family == 'extreg' and case.rtl == 'reset':
        inOrderAcrossReset(case, 'model', got, want)
        inOrderAcrossReset(case, 'RTL', [v for v, _ in smp], [v for v, _ in ev.get('pub', [])])
        return
    check(case, 'the model sees every value once, in order', got == want, f"RTL drove {want}, model got {got}",
          f"model {levelHow(got, want)}")
    if case.delay == 0 and got == want:
        # The model reads the value at time 0 before any edge.
        times = [t for v, t in drv if v in want] if case.family == 'status' else [t for _, t in drv]
        expect = [t + PERIOD if t else 0 for t in times]
        check(case, 'the model sees each value on the edge after the RTL drives it',
              [t for _, t in rets] == expect, f"RTL drives {times}, model gets {[t for _, t in rets]}",
              lagHow([t for _, t in rets], expect))
    if case.family == 'extreg':
        pub, seen = ev.get('pub', []), smp
        check(case, "the RTL sees the model's every published value", [v for v, _ in seen] == [v for v, _ in pub],
              f"model published {[v for v, _ in pub]}, RTL saw {[v for v, _ in seen]}")
        if case.delay == 0 and [v for v, _ in seen] == [v for v, _ in pub]:
            check(case, 'the RTL sees a published value on the edge after it',
                  [t for _, t in seen] == [nextEdge(t) for _, t in pub],
                  f"published {[t for _, t in pub]}, RTL samples {[t for _, t in seen]}",
                  lagHow([t for _, t in seen], [nextEdge(t) for _, t in pub]))


def runCase(binPath, case, scLibdir):
    """Runs one probe; status is None when it hangs, with what it printed before."""
    argv = [binPath, str(case.delay), case.family, case.dir, case.rtl, str(case.busy), case.bp]
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        return case, run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as hang:
        return case, None, ((hang.stdout or b'') + (hang.stderr or b'')).decode()


def test_bfm_handover():
    scLibdir = os.environ['SYSTEMC_LIBDIR']
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_handover_')
    try:
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            FAILURES.append(f"probe must build and link: {binPath}")
            print(f"  FAIL: probe must build and link: {binPath}")
            return
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
            results = list(pool.map(lambda c: runCase(binPath, c, scLibdir), CASES))
        for case, status, output in results:
            before = len(FAILURES)
            check(case, DONE, status is not None and 'probe done' in output,
                  f"status {status}", 'hang' if status is None else f"exit {status}")
            if status is not None:
                asserted = re.search(r'^probe assert (.*)$', output, re.M)
                how = re.sub(r'\((?:\S*/)?([^/:]+):\d+\)', r'(\1)', asserted.group(1)) if asserted else f"exit {status}"
                check(case, NO_ASSERT, status == 0 and not asserted, f"status {status}, {how}", how)
                ev, deltas = events(output)
                if case.family in BUS:
                    busChecks(case, ev)
                elif case.family in LEVEL:
                    levelChecks(case, ev)
                else:
                    handshakeChecks(case, ev, deltas, output)
            if len(FAILURES) > before:
                print(output)
        print("\n  Throughput and latency today (RTL always ready or valid, model back to back, no delay):")
        for line in NUMBERS:
            print(f"    {line}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    assert not FAILURES, f"{len(FAILURES)} checks failed"


if __name__ == '__main__':
    try:
        test_bfm_handover()
    except AssertionError:
        pass
    print(f"\n  {len(XFAILS)} expected failures")
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
