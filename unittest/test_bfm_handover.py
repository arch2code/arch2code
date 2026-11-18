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
model calls read() with vld up.

Every run also checks that it ends without a hang or a Q_ASSERT, that order
holds and no beat is lost, and, with no delay, that no model call returns on
a reset edge. The no-backpressure contract checks still report a stall.
pop_ack, push_ack, notify_ack, req_ack, apb and memory get simpler checks:
each request is served once, with and without a delay, completes on the
right edge, and apb and memory writes are posted.

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
OPS = 4
IN_ORDER = list(range(BEATS))
DELAYS = (0, 15)
TIMEOUT = 5                      # s; a probe runs in a few ms
STALL = 'HDL stalled a backpressure: false interface'
SC_STALL = 'SystemC stalled a backpressure: false producer'

HANDSHAKE = ('rv', 'axis', 'ar', 'r', 'aw', 'w', 'b')
OTHERS = {'popack': ('dst', 'src'), 'pushack': ('dst', 'src'), 'notifyack': ('dst', 'src'),
          'reqack': ('src',), 'apb': ('dst', 'src'), 'mem': ('dst', 'src')}
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
CASES += [Case(f, 'src', m, b, 'allowed', d) for f in HANDSHAKE for m, b in SRC_RUNS for d in DELAYS]
CASES += [Case('rvmulti', dr, 'always', 0, 'allowed', d) for dr in ('dst', 'src') for d in DELAYS]
CASES += [Case('wfirst', 'src', 'always', 0, 'allowed', d) for d in DELAYS]
CASES += [Case(f, 'dst', 'hold', 0, 'none', 0) for f in ('rv', 'axis')]
CASES += [Case(f, 'src', 'always', 25, 'none', 0) for f in ('rv', 'axis')]
CASES += [Case(f, dr, 'always', 0, 'allowed', d) for f, dirs in OTHERS.items() for dr in dirs for d in DELAYS]

HIDDEN_DST = "completes the model's call when it copies the beat, a handshake before the RTL takes it"
HIDDEN_SRC = "restores ready after the model call returns, so the RTL hands over a beat the model is not reading"
LATE_READY = "sets ready from get_rdy() only on a clock edge, so ready rises an edge after the model starts to read"
RESET_DST = "ends the beat on an edge with ready high whether or not reset is low"
RESET_SRC = "delivers a beat it samples on a reset edge, and the RTL sends that beat again after reset"
RESET_SPIN = ("loops in zero time when the edge after a handshake is in reset: the stale valid and ready "
              "skip the inner wait, and the reset branch continues without waiting")
WRITE_SRC_DELAY = ("keeps ready high while a delayed model call blocks, so the RTL hands over beats the BFM never "
                   "samples; every3 offers a beat three or more edges after the last handshake, after the 15 ns "
                   "delay has ended")
R_DRAIN = ("axi_read_bfm.h:132-155 drops the R beat on the wire at reset and returns the model's remaining "
           "sendDataCycle() calls with no handshake, to drain the burst")
B_DROP = ("axi_write_bfm.h:172 takes the model's B on a reset edge and 173-177 drops it, and 184-187 drops "
          "the B on the wire at reset")
DST_RULE_1 = ('dst write returns never run ahead of handshakes', 'dst write returns at its handshake edge')
SRC_RULE_1 = 'src handshake only while the model waits in read()'
SRC_RETURN = 'src read returns at its handshake edge'
SRC_COUNT = 'src read count matches handshakes'
ORDER = 'order kept, no beat lost'
RESET_RETURN = 'no model return on a reset edge'
DONE = 'probe runs to completion'
NO_ASSERT = 'no Q_ASSERT stops the run'


def anyCase(case):
    return True


def busy(case):
    return case.busy > 0


def inReset(case):
    return case.rtl == 'reset'


def resetNoDelay(case):
    return case.rtl == 'reset' and case.delay == 0


def readsAfterVld(case):
    return case.rtl != 'waiting'


def outOfReset(case):
    return case.rtl != 'reset'


def delayLoses(case):
    return case.delay > 0 and case.rtl != 'every3'


# A row marks checks that fail today: (families, direction, checks, applies
# to case, how the check fails, reason naming the BFM line). how pins the
# failure, for example which beats are lost, and None accepts any failure.
XFail = namedtuple('XFail', 'families dir checks applies how reason')
EXPECTED_FAILURES = [
    XFail(('rv',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"rdy_vld_bfm.h:154 readClocked() {HIDDEN_DST}"),
    XFail(('rv',), 'dst', DST_RULE_1, inReset, None,
          f"rdy_vld_bfm.h:154 readClocked() {HIDDEN_DST}; reset adds more"),
    XFail(('axis',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi4_stream_bfm.h:179 receiveInfo() {HIDDEN_DST}"),
    XFail(('axis',), 'dst', DST_RULE_1, inReset, None,
          f"axi4_stream_bfm.h:179 receiveInfo() {HIDDEN_DST}; reset adds more"),
    XFail(('ar',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi_read_bfm.h:204 receiveAddr() {HIDDEN_DST}"),
    XFail(('ar',), 'dst', DST_RULE_1, inReset, None,
          f"axi_read_bfm.h:204 receiveAddr() {HIDDEN_DST}; reset adds more"),
    XFail(('r',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi_read_bfm.h:122 receiveDataCycle() {HIDDEN_DST}"),
    XFail(('r',), 'dst', DST_RULE_1, inReset, None,
          f"axi_read_bfm.h:122 receiveDataCycle() {HIDDEN_DST}; reset adds more"),
    XFail(('aw',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi_write_bfm.h:238 receiveAddr() {HIDDEN_DST}"),
    XFail(('aw',), 'dst', DST_RULE_1, inReset, None,
          f"axi_write_bfm.h:238 receiveAddr() {HIDDEN_DST}; reset adds more"),
    XFail(('w',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi_write_bfm.h:262 receiveDataCycle() {HIDDEN_DST}"),
    XFail(('w',), 'dst', DST_RULE_1, inReset, None,
          f"axi_write_bfm.h:262 receiveDataCycle() {HIDDEN_DST}; reset adds more"),
    XFail(('b',), 'dst', DST_RULE_1, outOfReset, '1 ahead', f"axi_write_bfm.h:172 receiveRespCycle() {HIDDEN_DST}"),
    XFail(('b',), 'dst', DST_RULE_1, inReset, None,
          f"axi_write_bfm.h:172 receiveRespCycle() {HIDDEN_DST}; reset adds more"),

    XFail(('rv',), 'src', (SRC_RULE_1,), busy, 'first at beat 1', f"rdy_vld_bfm.h:74 rdy = rdy {HIDDEN_SRC}"),
    XFail(('rv',), 'src', (SRC_RETURN,), busy, 'edge', f"rdy_vld_bfm.h:74 rdy = rdy {HIDDEN_SRC}"),
    XFail(('axis',), 'src', (SRC_RULE_1,), busy, 'first at beat 1',
          f"axi4_stream_bfm.h:97 tready = tready {HIDDEN_SRC}"),
    XFail(('axis',), 'src', (SRC_RETURN,), busy, 'edge', f"axi4_stream_bfm.h:97 tready = tready {HIDDEN_SRC}"),
    XFail(('ar',), 'src', (SRC_RULE_1,), busy, 'first at beat 1', f"axi_read_bfm.h:107 arready = 1 {HIDDEN_SRC}"),
    XFail(('ar',), 'src', (SRC_RETURN,), busy, 'edge', f"axi_read_bfm.h:107 arready = 1 {HIDDEN_SRC}"),
    XFail(('r',), 'src', (SRC_RULE_1,), busy, 'first at beat 1', f"axi_read_bfm.h:235 rready = 1 {HIDDEN_SRC}"),
    XFail(('r',), 'src', (SRC_RETURN,), busy, 'edge', f"axi_read_bfm.h:235 rready = 1 {HIDDEN_SRC}"),
    XFail(('b',), 'src', (SRC_RULE_1,), lambda c: busy(c) and c.rtl == 'always', 'first at beat 1',
          f"axi_write_bfm.h:290 bready = 1 {HIDDEN_SRC}"),
    XFail(('b',), 'src', (SRC_RULE_1,), lambda c: busy(c) and c.rtl == 'random' and c.delay == 0,
          'first at beat 2',
          f"axi_write_bfm.h:290 bready = 1 {HIDDEN_SRC}"),
    XFail(('b',), 'src', (SRC_RULE_1,), lambda c: busy(c) and c.rtl == 'random' and c.delay > 0,
          'first at beat 6',
          f"axi_write_bfm.h:290 bready = 1 {HIDDEN_SRC}"),
    XFail(('b',), 'src', (SRC_RETURN,), busy, 'edge', f"axi_write_bfm.h:290 bready = 1 {HIDDEN_SRC}"),
    XFail(('aw',), 'src', (SRC_RULE_1,), lambda c: busy(c) or delayLoses(c), 'first at beat 1',
          f"axi_write_bfm.h:111 sendAddr() leaves awready as it was; the BFM {HIDDEN_SRC}, and {WRITE_SRC_DELAY}"),
    XFail(('aw',), 'src', (SRC_RETURN,), busy, 'edge',
          f"axi_write_bfm.h:111 sendAddr() leaves awready as it was; the BFM {HIDDEN_SRC}"),
    XFail(('aw',), 'src', (SRC_COUNT,), delayLoses, None, f"axi_write_bfm.h:111 sendAddr() {WRITE_SRC_DELAY}"),
    XFail(('aw',), 'src', (ORDER,), lambda c: delayLoses(c) and not inReset(c), 'hs ok, model missing',
          f"axi_write_bfm.h:111 sendAddr() {WRITE_SRC_DELAY}"),
    XFail(('w', 'wfirst'), 'src', (SRC_RULE_1,), lambda c: busy(c) or delayLoses(c), 'first at beat 1',
          f"axi_write_bfm.h:159 sendDataCycle() leaves wready as it was; the BFM {HIDDEN_SRC}, and {WRITE_SRC_DELAY}"),
    XFail(('w',), 'src', (SRC_RETURN,), busy, 'edge',
          f"axi_write_bfm.h:159 sendDataCycle() leaves wready as it was; the BFM {HIDDEN_SRC}"),
    XFail(('w', 'wfirst'), 'src', (SRC_COUNT,), delayLoses, None,
          f"axi_write_bfm.h:159 sendDataCycle() {WRITE_SRC_DELAY}"),
    XFail(('w', 'wfirst'), 'src', (ORDER,), delayLoses, 'hs ok, model missing',
          f"axi_write_bfm.h:159 sendDataCycle() {WRITE_SRC_DELAY}"),

    XFail(('rv',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"rdy_vld_bfm.h:55-60 {LATE_READY}"),
    XFail(('axis',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"axi4_stream_bfm.h:72-77 {LATE_READY}"),
    XFail(('ar',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"axi_read_bfm.h:79-89 {LATE_READY}"),
    XFail(('r',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"axi_read_bfm.h:222-226 {LATE_READY}"),
    XFail(('aw',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"axi_write_bfm.h:86-96 {LATE_READY}"),
    XFail(('w', 'wfirst'), 'src', ('src latency',), readsAfterVld, '+1 clock',
          f"axi_write_bfm.h:120-121 and 143 {LATE_READY}"),
    XFail(('b',), 'src', ('src latency',), readsAfterVld, '+1 clock', f"axi_write_bfm.h:279-283 {LATE_READY}"),

    XFail(('rv',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"rdy_vld_bfm.h:162 {RESET_DST}"),
    XFail(('rv',), 'dst', (RESET_RETURN,), inReset, None, f"rdy_vld_bfm.h:162 {RESET_DST}"),
    XFail(('axis',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi4_stream_bfm.h:193 {RESET_DST}"),
    XFail(('axis',), 'dst', (RESET_RETURN,), inReset, None, f"axi4_stream_bfm.h:193 {RESET_DST}"),
    XFail(('ar',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_read_bfm.h:214 {RESET_DST}"),
    XFail(('ar',), 'dst', (RESET_RETURN,), inReset, None, f"axi_read_bfm.h:214 {RESET_DST}"),
    XFail(('aw',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_write_bfm.h:248 {RESET_DST}"),
    XFail(('aw',), 'dst', (RESET_RETURN,), inReset, None, f"axi_write_bfm.h:248 {RESET_DST}"),
    XFail(('w',), 'dst', (ORDER,), inReset, 'hs missing, model ok', f"axi_write_bfm.h:271 {RESET_DST}"),
    XFail(('w',), 'dst', (RESET_RETURN,), inReset, None, f"axi_write_bfm.h:271 {RESET_DST}"),
    XFail(('r',), 'dst', (ORDER,), inReset, 'hs missing, model ok', R_DRAIN),
    XFail(('r',), 'dst', (RESET_RETURN,), inReset, None, R_DRAIN),
    XFail(('b',), 'dst', (ORDER,), inReset, 'hs missing, model ok', B_DROP),
    XFail(('b',), 'dst', (RESET_RETURN,), inReset, None, B_DROP),

    XFail(('rv',), 'src', (ORDER,), inReset, 'hs ok, model missing+duplicate', f"rdy_vld_bfm.h:64-73 {RESET_SRC}"),
    XFail(('rv',), 'src', (RESET_RETURN,), inReset, None, f"rdy_vld_bfm.h:64-73 {RESET_SRC}"),
    XFail(('rv',), 'src', (SRC_RETURN,), inReset, 'edge', f"rdy_vld_bfm.h:64-73 {RESET_SRC}"),
    XFail(('axis',), 'src', (ORDER,), inReset, 'hs ok, model missing+duplicate',
          f"axi4_stream_bfm.h:81-96 {RESET_SRC}"),
    XFail(('axis',), 'src', (RESET_RETURN,), inReset, None, f"axi4_stream_bfm.h:81-96 {RESET_SRC}"),
    XFail(('axis',), 'src', (SRC_RETURN,), inReset, 'edge', f"axi4_stream_bfm.h:81-96 {RESET_SRC}"),
    XFail(('r',), 'src', (ORDER,), inReset, 'hs ok, model missing+duplicate',
          f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}"),
    XFail(('r',), 'src', (RESET_RETURN,), inReset, None, f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}"),
    XFail(('r',), 'src', (SRC_RETURN,), inReset, 'count',
          f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}; the assert stops the run a beat early"),
    XFail(('r',), 'src', (SRC_COUNT,), inReset, None,
          f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}; the assert stops the run a beat early"),
    XFail(('r',), 'src', (NO_ASSERT,), resetNoDelay,
          '[Q_ASSERT][p.dut.ch] last set incorrectly (axi_read_channel.h)',
          f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}, so the burst's eighth beat is not "
          "the one with rlast"),
    XFail(('r',), 'src', (NO_ASSERT,), lambda c: inReset(c) and c.delay > 0,
          '[Q_ASSERT][p.dut.ch] transaction id not valid (axi_read_channel.h)',
          f"axi_read_bfm.h:222-226 has no reset check and {RESET_SRC}, so the burst ends a beat early and "
          "the last beat has no read open for its ID"),
    XFail(('b',), 'src', (ORDER,), inReset, 'hs missing, model missing',
          "the assert below stops the run before every B is in"),
    XFail(('b',), 'src', (RESET_RETURN,), inReset, None,
          f"axi_write_bfm.h:279-283 has no reset check and {RESET_SRC}"),
    XFail(('b',), 'src', (SRC_RETURN,), inReset, 'edge', f"axi_write_bfm.h:279-283 has no reset check and {RESET_SRC}"),
    XFail(('b',), 'src', (NO_ASSERT,), inReset,
          '[Q_ASSERT][p.dut.ch] transaction id not valid (axi_write_channel.h)',
          f"axi_write_bfm.h:279-283 has no reset check and {RESET_SRC}, so the second B finds no write "
          "waiting for its ID"),
    XFail(('aw',), 'src', (NO_ASSERT,), lambda c: inReset(c) and c.delay > 0,
          '[Q_ASSERT][p.dut.ch] transaction id not valid (axi_write_channel.h)',
          "axi_write_bfm.h:123-137 sends the model a dummy W beat at reset for the burst of the last AW, "
          "with wid 0 (line 134) against an AW with ID 1"),
    XFail(('aw',), 'src', (ORDER,), lambda c: inReset(c) and c.delay > 0, 'hs missing, model missing',
          f"axi_write_bfm.h:111 sendAddr() {WRITE_SRC_DELAY}, and the assert above stops the run"),
    XFail(('ar',), 'src', (DONE,), inReset, 'hang', f"axi_read_bfm.h:91-92 {RESET_SPIN}"),
    XFail(('aw',), 'src', (DONE,), resetNoDelay, 'hang', f"axi_write_bfm.h:98-99 {RESET_SPIN}"),
    XFail(('w',), 'src', (DONE,), resetNoDelay, 'hang',
          f"axi_write_bfm.h:145-146 {RESET_SPIN}"),

    XFail(('apb',), 'src', ('completion edge',), anyCase, None,
          "apb_bfm.h:61 waits an edge after request() returns before line 62 raises pready, so the RTL "
          "completes one edge late"),
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


def events(output):
    ev = {}
    for kind, value, ps in re.findall(r'^ev (\w+) (\d+) (\d+)$', output, re.M):
        ev.setdefault(kind, []).append((int(value), int(ps)))
    return ev


def beatsHow(values):
    """How a list of beats differs from 0..BEATS-1: missing, duplicate, reordered, or ok."""
    if values == IN_ORDER:
        return 'ok'
    faults = [name for name, fault in (('missing', set(IN_ORDER) - set(values)),
                                       ('duplicate', len(set(values)) < len(values))) if fault]
    return '+'.join(faults) or 'reordered'


def handshakeChecks(case, ev, output):
    hs, calls, rets, vld = (ev.get(k, []) for k in ('hs', 'call', 'ret', 'vld'))
    hsTimes = [t for _, t in hs]
    hsValues, retValues = [v for v, _ in hs], [v for v, _ in rets]
    check(case, ORDER, hsValues == IN_ORDER and retValues == IN_ORDER,
          f"hs={hsValues} model={retValues}", f"hs {beatsHow(hsValues)}, model {beatsHow(retValues)}")
    if case.rtl == 'reset' and case.delay == 0 and rets:
        resetEdges = {t for _, t in ev.get('rst', [])}
        check(case, RESET_RETURN, not resetEdges & {t for _, t in rets},
              f"reset edges {sorted(resetEdges)}, model returns {[t for _, t in rets]}")
    judged = case.family != 'rvmulti' and rets
    if judged and case.dir == 'dst':
        lead = max(i + 1 - sum(h <= t for h in hsTimes) for i, (_, t) in enumerate(rets))
        check(case, 'dst write returns never run ahead of handshakes', lead <= 0,
              f"returns at most {lead} ahead of handshakes", f"{lead} ahead")
        check(case, 'dst write returns at its handshake edge',
              len(rets) == len(hs) and all(r[1] == h[1] for r, h in zip(rets, hs)),
              f"returns={[t for _, t in rets]} hs={hsTimes}", f"{lead} ahead")
    elif judged:
        unwaited = [i for i, t in enumerate(hsTimes) if i >= len(calls) or calls[i][1] >= t]
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
    if case.rtl in FULL_RATE and case.delay == 0 and case.busy == 0 and case.bp == 'allowed':
        gaps = sorted({b - a for a, b in zip(hsTimes, hsTimes[1:])})
        check(case, 'throughput', gaps == [PERIOD], f"handshake gaps {gaps} ps")
        if case.family == 'rvmulti' or not hs or not calls or not vld:
            return
        NUMBERS.append((case.family, case.dir, case.rtl, gaps, calls[0][1], vld[0][1], hsTimes[0]))
        if case.dir == 'dst':
            first = nextEdge(vld[0][1])
            check(case, 'dst latency', vld[0][1] == calls[0][1] and hsTimes[0] == first,
                  f"send {calls[0][1]}, vld {vld[0][1]}, first handshake {hsTimes[0]}, first edge after vld {first}")
        else:
            first = nextEdge(max(calls[0][1], vld[0][1]))
            check(case, 'src latency', hsTimes[0] == first,
                  f"read {calls[0][1]}, vld {vld[0][1]}, first handshake {hsTimes[0]}, expected {first}",
                  f"{(hsTimes[0] - first) // PERIOD:+d} clock")
    if case.dir == 'src' and case.rtl == 'reset':
        # Holds for today's BFMs, which leave ready high into a reset edge.
        check(case, 'the reset meets a beat on the wire', 'rsths' in ev, f"edges with vld and ready high in reset: "
              f"{ev.get('rsths', [])}")
    if case.bp == 'none':
        line = STALL if case.dir == 'dst' else SC_STALL
        check(case, 'no-backpressure check reports the stall', f'p.dut.bfm:{line} at ' in output,
              f"'{line}'")


# Model return values (dst) or RTL completion values (src) per family.
DST_VALUES = {'popack': list(range(OPS)), 'pushack': list(range(OPS)), 'notifyack': list(range(OPS)),
              'apb': [0x11, 0x11, 0x22, 0x22], 'mem': [0x11, 0x11, 0x22, 0x22]}
SRC_VALUES = {'popack': list(range(OPS)), 'pushack': list(range(OPS)), 'notifyack': list(range(OPS)),
              'reqack': list(range(OPS)), 'apb': [0, 0x11, 0, 0x22], 'mem': [0, 0x11, 0, 0x22]}
POSTED = ('apb', 'mem')


def otherChecks(case, ev):
    req, ack, calls, rets = (ev.get(k, []) for k in ('req', 'ack', 'call', 'ret'))
    check(case, 'served once', len(req) == OPS and len(ack) == OPS and len(rets) == OPS,
          f"RTL requests {len(req)}, RTL completions {len(ack)}, model completions {len(rets)}")
    if case.dir == 'dst':
        check(case, 'values', [v for v, _ in rets] == DST_VALUES[case.family], f"model got {[v for v, _ in rets]}")
    else:
        check(case, 'values', [v for v, _ in ack] == SRC_VALUES[case.family], f"RTL got {[v for v, _ in ack]}")
    if case.delay or len(ack) != OPS or len(rets) != OPS:
        return
    if case.dir == 'dst':
        reads = [k for k in range(OPS) if case.family not in POSTED or k % 2]
        check(case, 'completion edge', all(rets[k][1] == ack[k][1] for k in reads),
              f"model returns {[rets[k][1] for k in reads]}, RTL completion edges {[ack[k][1] for k in reads]}")
        if case.family in POSTED:
            writes = [k for k in range(OPS) if k % 2 == 0]
            check(case, 'posted write returns at its call', all(rets[k][1] == calls[k][1] for k in writes),
                  f"calls {[calls[k][1] for k in writes]}, returns {[rets[k][1] for k in writes]}")
    else:
        check(case, 'completion edge', all(ack[k][1] == nextEdge(rets[k][1]) for k in range(OPS)),
              f"model completes {[t for _, t in rets]}, RTL completion edges {[t for _, t in ack]}")


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
                ev = events(output)
                if case.family in OTHERS:
                    otherChecks(case, ev)
                else:
                    handshakeChecks(case, ev, output)
            if len(FAILURES) > before:
                print(output)
        print("\n  Throughput and latency today (RTL always ready or valid, model back to back, no delay):")
        for family, direction, rtl, gaps, call, vld, first in NUMBERS:
            print(f"    {family} {direction} rtl={rtl}: handshake gap {gaps} ps; model call {call} ps, vld {vld} ps, "
                  f"first handshake {first} ps")
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
