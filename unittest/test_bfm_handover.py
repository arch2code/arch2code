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

pop_ack, push_ack, notify_ack and req_ack run as handshake lanes, the
request as vld and ack as rdy; their src handshake must follow the model's
ack, on the next edge.

memory, apb and ahb run four operations each way. Each is served once with
the right data, a dst call that waits returns at its completion edge and a
posted write at its call, a src completes on the edge after the model, and
first-transfer latency and throughput meet the protocol minimum. In error
runs an apb PSLVERR or ahb HRESP ERROR reaches the model, or the RTL, on its
own transfer and not the next, and an ahb error takes two cycles.

status, raw and external_reg drive a level through values 1 to 8. The far
side sees every value that stays on the wire across an edge out of reset,
once and in order, on the edge after it is driven; external_reg also checks
the model's mirror and the values it publishes back.

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
CASES += [Case(f, 'dst', 'hold', 0, 'none', 0) for f in ('rv', 'axis')]
CASES += [Case(f, 'src', 'always', 25, 'none', 0) for f in ('rv', 'axis')]
# Bus runs: a completer with wait states or a master with idle edges (slow),
# a parked src model, and errors on operations 1 and 2 (apb and ahb).
BUS_MODES = {'dst': ('always', 'slow', 'reset', 'error'), 'src': ('always', 'parked', 'slow', 'reset', 'error')}
CASES += [Case(f, dr, m, 0, 'allowed', d) for f in BUS for dr in BUS_MODES for m in BUS_MODES[dr] for d in DELAYS
          if not (m == 'error' and f == 'mem') and not (m == 'slow' and f == 'mem' and dr == 'dst')]
LEVEL_MODES = {'dst': ('always', 'reset'), 'src': ('always', 'every3', 'reset')}
CASES += [Case(f, dr, m, 0, 'allowed', d) for f in LEVEL for dr in LEVEL_MODES for m in LEVEL_MODES[dr] for d in DELAYS]

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
ACK_RULE_1 = "src handshake only after the model's ack"
ACK_RETURN = "src handshake on the edge after the model's ack"
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

    XFail(('apb',), 'src', ('src completes on the edge after the model',), anyCase, '+1 clock',
          "apb_bfm.h:61 waits an edge after requestWithResponse() returns before line 62 raises pready, so "
          "the RTL completes one edge late"),
]

# The _ack BFMs: (family, src lines, dst lines, dst throughput line, how a src reset run loses order, how a
# dst reset run loses order).
ACK_BFMS = (
    ('pushack', 'push_ack_bfm.h:39-46', 'push_ack_bfm.h:76-83', None,
     'hs missing, model missing+duplicate', 'hs missing, model ok'),
    ('popack', 'pop_ack_bfm.h:37-45', 'pop_ack_bfm.h:77-85', 'pop_ack_bfm.h:85',
     'hs missing, model ok', 'hs missing, model missing+duplicate'),
    ('notifyack', 'notify_ack_bfm.h:37-43', 'notify_ack_bfm.h:71-76', None,
     'hs missing, model ok', 'hs missing, model ok'),
    ('reqack', 'req_ack_bfm.h:39-48', 'req_ack_bfm.h:79-86', 'req_ack_bfm.h:86',
     'hs missing, model missing+duplicate', 'hs missing, model missing+duplicate'),
)
ACK_LATE = "samples the request only on a clock edge, so the model gets it an edge after the RTL raises it"
ACK_RATE = "drops ack for the edge after each transfer and then waits an edge to sample the request again"
ACK_RESET = "never reads rst_n after the first reset: it serves a request it samples on a reset edge"
for fam, srcLines, dstLines, dstRate, srcOrder, dstOrder in ACK_BFMS:
    EXPECTED_FAILURES += [
        XFail((fam,), 'src', ('src latency',), lambda c: c.rtl in ('always', 'waiting'), '+1 clock',
              f"{srcLines} {ACK_LATE}"),
        XFail((fam,), 'src', ('throughput',), anyCase, None, f"{srcLines} {ACK_RATE}, one transfer per two clocks"),
        XFail((fam,), 'src', (ORDER,), inReset, srcOrder, f"{srcLines} {ACK_RESET}"),
        XFail((fam,), 'src', (RESET_RETURN,), inReset, None, f"{srcLines} {ACK_RESET}"),
        XFail((fam,), 'src', (ACK_RULE_1, ACK_RETURN), inReset, 'count', f"{srcLines} {ACK_RESET}"),
        XFail((fam,), 'dst', DST_RULE_1 + (RESET_RETURN,), inReset, None, f"{dstLines} {RESET_DST}"),
        XFail((fam,), 'dst', (ORDER,), inReset, dstOrder, f"{dstLines} {RESET_DST}"),
    ]
    if dstRate:
        EXPECTED_FAILURES.append(XFail((fam,), 'dst', ('throughput',), anyCase, None,
                                       f"{dstRate} waits an edge after the model's ack, one transfer per two clocks"))

APB_PHANTOM = ("drops penable but holds psel until after complete() returns, so while a delayed complete() "
               "blocks the RTL sees psel without penable, a setup phase, and serves a transfer the model never sent")
BUS_RESET = "never reads rst_n after the first reset, so a transfer in flight at the reset is lost or completes later"
EXPECTED_FAILURES += [
    XFail(('apb',), 'dst', ('served once',), lambda c: c.delay > 0 and not inReset(c), 'RTL 5/4, model 4',
          f"apb_bfm.h:130-140 {APB_PHANTOM}"),
    XFail(('apb',), 'dst', ('values',), lambda c: c.delay > 0 and not inReset(c), None,
          f"apb_bfm.h:130-140 {APB_PHANTOM}, and the model's last read gets that transfer's data"),
    XFail(('apb',), 'dst', ('served once',), inReset, None, f"apb_bfm.h:101-144 {BUS_RESET}"),
    XFail(('apb',), 'src', ('served once', 'values', 'an error reaches the RTL on its own transfer'),
          lambda c: inReset(c) and c.delay > 0, None,
          f"apb_bfm.h:44-74 {BUS_RESET}: pready for the transfer the reset cut off completes the RTL's next one"),
    XFail(('apb',), 'src', ('src latency',), lambda c: c.rtl == 'always', '+10 ns',
          "apb_bfm.h:52 waits for the access phase before it sends the request, a clock after the setup phase "
          "has the whole request on the wire"),
    XFail(('apb',), 'src', ('src latency',), lambda c: c.rtl == 'parked', '+5 ns',
          "apb_bfm.h:52 samples psel and penable only on a clock edge, so a model that asks mid-cycle waits for "
          "the next edge"),
    XFail(('apb',), 'src', ('throughput',), anyCase, '[4] edges',
          "apb_bfm.h:52 sends the request in the access phase, 61 waits an edge before pready, and 67-73 wait "
          "another edge after it: one transfer per four clocks, against two for apb"),
    XFail(('ahb',), 'dst', ('throughput',), anyCase, '2 edges',
          "ahb_bfm.h:139-164 takes the next request only after the data phase completes, so address phases do "
          "not overlap data phases"),
    XFail(('ahb',), 'dst', ('served once', 'values'), inReset, None, f"ahb_bfm.h:135-166 {BUS_RESET}"),
    XFail(('ahb',), 'src', ('throughput',), anyCase, '[2] edges',
          "ahb_bfm.h:78 drives HREADYOUT low for at least one wait state on every transfer"),
    XFail(('ahb',), 'src', ('served once', 'values', 'an error reaches the RTL on its own transfer'), inReset, None,
          f"ahb_bfm.h:72-98 {BUS_RESET}; line 96 takes an address phase on a reset edge and sends it to the model"),
    XFail(('extreg',), 'dst', ('the RTL sees each value on the edge after the write',), anyCase, 'value 1 +10 ns',
          "external_reg_bfm.h:126 waits an edge after each write strobe, so queued writes reach the RTL one per "
          "two clocks"),
    XFail(('extreg',), 'src', ('the RTL sees a published value on the edge after it',), anyCase, 'value 0 +10 ns',
          "external_reg_bfm.h:48-49 drives rdata from the mirror once per edge, before the model answers that "
          "edge's write strobe, so the RTL sees the model's value an edge late"),
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
        # Holds for today's BFMs, which leave ready high into a reset edge. An
        # _ack src BFM samples the request alone.
        seen = 'rstvld' if case.family in TWO_PHASE else 'rsths'
        check(case, 'the reset meets a beat on the wire', seen in ev, f"reset edges with the beat on the wire: "
              f"{ev.get(seen, [])}")
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
# Edges from the edge an RTL master drives operation 0, a write, to the
# first edge its whole request is on the wire: ahb write data follows its
# address phase.
REQUEST_EDGES = {'mem': 1, 'apb': 1, 'ahb': 2}
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
            first = [(v, t) for v, t in ev.get('errfirst', [])]
            want = [(k, ack[k][1] - PERIOD) for k in (1, 2)]
            check(case, 'an ahb error takes two cycles', first == want,
                  f"first error cycles {first}, expected {want}", f"{first}")
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
            NUMBERS.append((case.family, case.dir, case.rtl, [gap], calls[0][1], req[0][1], ack[0][1]))
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
        first = max(req[0][1] + REQUEST_EDGES[case.family] * PERIOD, rcalls[0][1])
        check(case, 'src latency', rcvs[0][1] == first,
              f"RTL request {req[0][1]}, model asks {rcalls[0][1]}, model gets it {rcvs[0][1]}, expected {first}",
              f"{(rcvs[0][1] - first) // 1000:+d} ns")
    if case.rtl == 'always' and case.delay == 0:
        gaps = sorted({b[1] - a[1] for a, b in zip(ack, ack[1:])})
        check(case, 'throughput', gaps == [MIN_GAP[case.family]],
              f"RTL completion gaps {gaps} ps, protocol minimum {MIN_GAP[case.family]}",
              f"{[g // PERIOD for g in gaps]} edges")
        NUMBERS.append((case.family, case.dir, case.rtl, gaps, rcalls[0][1], req[0][1], rcvs[0][1]))


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
    (external_reg_bfm.h:43, 93-95, 108-109), so a reset run checks only that the values seen
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
        want = visible([(v, t) for v, t in wire], resetEdges, 3_000_000)
        got = [v for v, _ in smp]
        if case.family == 'extreg' and case.rtl == 'reset':
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
        want = visible([(v, t) for v, t in drv], set(), 3_000_000)
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
                ev = events(output)
                if case.family in BUS:
                    busChecks(case, ev)
                elif case.family in LEVEL:
                    levelChecks(case, ev)
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
