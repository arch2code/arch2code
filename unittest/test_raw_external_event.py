#!/usr/bin/env python3
"""A raw writer is released once its reader takes the value, whichever event
the reader waits on.

write() returns only after the reader has consumed the value, and it waits on
the channel's own event for that. A reader that arbitrates several ports calls
setExternalEvent() and then waits on, and notifies, a shared event instead. The
channel's own event must still fire when such a reader consumes, or the writer
waits forever after the first value.

Each value must also be read before the next write replaces it. One event
serves both directions, so the wake that releases the reader releases the
writer too. A writer that runs first in that delta must not return and
overwrite a value the reader has not taken. Both thread creation orders are
run because they give the two delta orders.

A reader may share one external event across several channels. Taking a value
from one channel must release that channel's writer only, so a writer parked on
a channel the reader has not reached yet stays parked.

The probe is bounded in simulation time, so a writer left waiting shows up as
an unfinished writer and not as a hung test.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(test_dir, 'fixtures', 'raw-external-event', 'raw_external_event.cpp')

TRANSFERS = 8
BASES = {'A': 0x100, 'B': 0x200}
CHANNELS = {'internal': 'A', 'external': 'A', 'shared': 'AB'}

SCENARIOS = [(mode, order) for mode in CHANNELS for order in ('writerFirst', 'readerFirst')]

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def parse(output):
    # The probe prints events in execution order: ("read"|"wrote", channel, value).
    events = [(fields[0], fields[1], int(fields[2], 16))
              for fields in (line.split() for line in output.splitlines())
              if len(fields) == 3 and fields[0] in ('read', 'wrote')]
    done = {}
    for line in output.splitlines():
        if line.startswith('writerDone='):
            done = dict(field.split('=') for field in line.split())
    return events, done


def test_raw_writer_released_on_read():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_raw_external_event_')
    try:
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"raw channel probe must build and link: {binPath}")
            return
        for mode, order in SCENARIOS:
            label = f"{mode}/{order}"
            run = subprocess.run([binPath, mode, order], capture_output=True, text=True, timeout=120,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            events, done = parse(output)
            before = len(FAILURES)
            check(run.returncode == 0, f"{label} exits 0 (got {run.returncode})")
            for chan in CHANNELS[mode]:
                expected = [BASES[chan] + i for i in range(TRANSFERS)]
                received = [v for kind, c, v in events if kind == 'read' and c == chan]
                check(received == expected,
                      f"{label} reads all {TRANSFERS} values of channel {chan} in order, none "
                      f"lost or repeated (got {[hex(v) for v in received]})")
                early = [hex(v) for i, (kind, c, v) in enumerate(events)
                         if kind == 'wrote' and c == chan and ('read', chan, v) not in events[:i]]
                check(not early,
                      f"{label} channel {chan} write() returns only after its own value is "
                      f"read (returned early for {early})")
            check(done.get('writerDone') == '1',
                  f"{label} writer completes: write() must return once the reader has "
                  f"taken the value (got writerDone={done.get('writerDone')})")
            check(done.get('readerDone') == '1',
                  f"{label} reader completes (got readerDone={done.get('readerDone')})")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_raw_writer_released_on_read()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
