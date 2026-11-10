#!/usr/bin/env python3
"""ahb_channel keeps posted writes posted and carries HRESP ERROR on request.

ahb_channel and apb_channel share their transfer behaviour through
regBusChannel, so the AHB channel must pass the probe the APB channel passes
(see test_apb_channel_response.py): a plain request() write is posted and its
late complete() does not complete the next read, and the response-aware calls
wait for complete() and return its error bit for reads and writes. The probe
here is that one with ahb_channel in place of apb_channel.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe
from test_apb_channel_response import EXPECTED_PASSES, PROBE_SRC

AHB_PROBE_SRC = (PROBE_SRC.replace('#include "apb_channel.h"', '#include "ahb_channel.h"')
                 .replace('apb_channel<addrSt, dataSt>', 'ahb_channel<addrSt, dataSt>')
                 .replace('PSLVERR', 'HRESP ERROR'))

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_ahb_channel_response():
    check('apb' not in AHB_PROBE_SRC, "the probe uses no APB class")
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_ahb_channel_response_')
    try:
        binPath = buildProbe(tmpdir, AHB_PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"ahb_channel probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "the ahb_channel probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        check(run.returncode == 0, f"the probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == EXPECTED_PASSES and 'failures=0' in output,
              f"all {EXPECTED_PASSES} channel checks pass")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_ahb_channel_response()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
