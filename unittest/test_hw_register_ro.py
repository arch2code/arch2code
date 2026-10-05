#!/usr/bin/env python3
"""A firmware write to a read-only in-block register leaves it unchanged.

The generated register RTL gives an `ro` register no write strobe: an APB write
to its address is acknowledged and changes nothing, and the register keeps the
value the hardware drives. The model must agree, or firmware that writes an RO
register sees different read data in the model than in RTL. The hardware side
still owns the value, so `write()` must keep updating it, and a read-write
register must keep taking CPU writes.

The probe drives the shipped hwRegister directly through cpu_write(), write()
and cpu_read().
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "hwRegister.h"
#include <cstdint>
#include <cstdio>

struct regSt {
    std::uint32_t v = 0;
    static constexpr uint16_t _bitWidth = 32;
    typedef uint64_t _packedSt;
    inline void unpack(const _packedSt &src) { v = (std::uint32_t)src; }
    inline sc_bv<32> sc_pack(void) const { sc_bv<32> p; p.range(31, 0) = v; return p; }
    inline void sc_unpack(sc_bv<32> p) { v = (std::uint32_t)p.range(31, 0).to_uint64(); }
};

static int failures = 0;

static void expect(bool ok, const char *what)
{
    std::printf("%s: %s\\n", ok ? "PASS" : "FAIL", what);
    if (!ok) { failures++; }
}

int sc_main(int, char **)
{
    hwRegister<regSt, 4, true> ro;
    ro.cpu_write(0, 0x55);
    expect(ro.read().v == 0, "ro: cpu_write leaves the reset value");
    regSt hw;
    hw.v = 0x77;
    ro.write(hw);
    expect(ro.read().v == 0x77, "ro: hardware write() updates the value");
    expect(ro.cpu_read(0) == 0x77, "ro: cpu_read returns the hardware value");
    ro.cpu_write(0, 0x11);
    expect(ro.cpu_read(0) == 0x77, "ro: cpu_write after a hardware write leaves it unchanged");

    hwRegister<regSt, 4> rw;
    rw.cpu_write(0, 0x55);
    expect(rw.cpu_read(0) == 0x55, "rw: cpu_write updates the value");

    std::printf("failures=%d\\n", failures);
    return failures ? 1 : 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_hw_register_ro_ignores_cpu_write():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_hw_register_ro_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"hwRegister probe must build and link: {binPath}")
            return
        run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        output = run.stdout + run.stderr
        check(run.returncode == 0, f"probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == 5 and 'failures=0' in output,
              "all five hwRegister checks pass")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_hw_register_ro_ignores_cpu_write()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
