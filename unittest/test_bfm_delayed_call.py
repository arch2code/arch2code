#!/usr/bin/env python3
"""BFMs keep the HDL from transferring while a delayed model call blocks.

Under --delay N a model call first waits N ns, so it keeps the BFM thread away
for several edges after a handshake. req_ack_dst_bfm must drop req before
ack(). axi_read_src_bfm, axi_read_dst_bfm and axi_write_dst_bfm must hold
arready, rready and bready low around sendAddr, sendDataCycle and sendRespCycle.
fixtures/bfm-delayed-call runs one probe per BFM, with no delay and with
setTimed(10).
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(test_dir, 'fixtures', 'bfm-delayed-call', 'bfm_delayed_call.cpp')

REQ = [0xa0 + i for i in range(3)]
ACK = [v + 0x1000 for v in REQ]
AR = [0x1000 * (n + 1) for n in range(2)]
R = [0x100 * (n + 1) + i for n in range(2) for i in range(4)]
B = [1, 2]

# probe -> (BFM, modes, what the HDL transfers, what the BFM passes to the
# model, what the other side gets)
PROBES = {
    'req_ack': ('req_ack_dst_bfm', ('fast', 'slow'), REQ, ACK, ACK),
    'ar': ('axi_read_src_bfm', ('seq', 'pipe'), AR, AR, R),
    'r': ('axi_read_dst_bfm', ('seq', 'pipe'), R, R, R),
    'b': ('axi_write_dst_bfm', ('each', 'batch'), B, B, B),
}
CASES = [(name, mode, delay) for name, spec in PROBES.items() for mode in spec[1] for delay in (0, 10)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def hexes(s):
    return [int(v, 16) for v in s.split(',') if v]


def runCase(binPath, name, mode, delay, scLibdir):
    bfm, _, expHdl, expBfm, expRecv = PROBES[name]
    tag = f"{bfm} {mode}, delay {delay} ns"
    try:
        run = subprocess.run([binPath, str(delay), name, mode], capture_output=True, text=True,
                             timeout=60, env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl=(\S*) bfm=(\S*) recv=(\S*)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdl, calls, recv = (hexes(m.group(i)) for i in range(1, 4))
        check(hdl == expHdl, f"{tag}: the HDL made each transfer once ({[hex(v) for v in hdl]})")
        check(calls == expBfm, f"{tag}: the BFM made one model call per transfer ({[hex(v) for v in calls]})")
        check(recv == expRecv, f"{tag}: the other side got every transfer in order ({[hex(v) for v in recv]})")
    if len(FAILURES) > before:
        print(output)


def test_bfm_delayed_call():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_delayed_call_')
    try:
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for name, mode, delay in CASES:
            runCase(binPath, name, mode, delay, scLibdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_bfm_delayed_call()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
