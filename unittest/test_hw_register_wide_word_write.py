#!/usr/bin/env python3
"""A firmware write to one word of a wide register takes effect on its own.

The register bus is 32 bits wide, so firmware writes a 64-bit or wider register
one word at a time. The generated register RTL updates each word on its own
write strobe, so after a low-word write the RTL output already carries it. The
model must agree, or a design reacting to the low word sees it in RTL and not
in the model. An in-block register (hwRegister) therefore updates and notifies
its registered event on every word write.

hwRegisterIf is the register handler model's class for rw, ro and ext
registers. An ext register is no wider than the bus (make db rejects a wider
one), so a write to it through hwRegisterIf issues one reg_write_cmd carrying
the written word. test_hw_register_if_wide_word_write covers a wide rw one.

The probe drives hwRegister at 32, 64, 96 and 128 bits and hwRegisterIf at 32
bits, with a fake external_reg port standing in for the channel. The waiting
process must wake exactly once after each word write, the top word included.
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
#include <format>
#include <string>

// Plain words like a generated register struct, which hwRegister memsets.
template <int W>
struct wideSt {
    uint32_t w[W/32] = {};
    static constexpr uint16_t _bitWidth = W;
    typedef uint64_t _packedSt;
    inline void unpack(const _packedSt &) {}
    inline sc_bv<W> sc_pack(void) const
    {
        sc_bv<W> p;
        for (int n = 0; n < W/32; n++) { p.range(32*n+31, 32*n) = w[n]; }
        return p;
    }
    inline void sc_unpack(sc_bv<W> p)
    {
        for (int n = 0; n < W/32; n++) { w[n] = (uint32_t)p.range(32*n+31, 32*n).to_uint64(); }
    }
    uint32_t word(int n) const { return w[n]; }
};

static int failures = 0;

static void expect(bool ok, const std::string &what)
{
    std::printf("%s: %s\\n", ok ? "PASS" : "FAIL", what.c_str());
    if (!ok) { failures++; }
}

// Stands in for an external_reg port: readNonBlocking() returns the owner's
// read value, reg_write_cmd() records each command.
template <int W>
struct fakeChannel {
    wideSt<W> mirror;
    wideSt<W> lastCmd;
    int cmds = 0;
    wideSt<W> readNonBlocking() { return mirror; }
    void reg_write_cmd(const wideSt<W> &v) { lastCmd = v; cmds++; }
};
template <int W>
struct fakePort {
    fakeChannel<W> ch;
    fakeChannel<W> *operator->() { return &ch; }
};

template <int W>
SC_MODULE(wideProbe)
{
    static constexpr int N = W / 8;
    static constexpr int WORDS = W / 32;
    hwRegister<wideSt<W>, N> reg;
    fakePort<W> port;
    hwRegisterIf<wideSt<W>, fakePort<W>, N, false> ext;
    sc_event regEvent;
    int notifications = 0;

    SC_HAS_PROCESS(wideProbe);
    wideProbe(sc_module_name n) : sc_module(n), ext(&port)
    {
        reg.registerEvent(&regEvent);
        SC_THREAD(count);
        SC_THREAD(drive);
    }

    void count() { while (true) { wait(regEvent); notifications++; } }

    void drive()
    {
        wait(1, SC_NS);
        std::string tag = std::to_string(W) + "-bit";
        // every word, the top one included, wakes the waiter exactly once
        for (int n = 0; n < WORDS; n++) {
            reg.cpu_write(4*n, 0x11110000u + n);
            wait(1, SC_NS);
            expect(reg.read().word(n) == 0x11110000u + n, std::format("{} rw: word {} takes the write", tag, n));
            expect(reg.cpu_read(4*n) == 0x11110000u + n, std::format("{} rw: word {} reads back", tag, n));
            expect(notifications == n + 1, std::format("{} rw: word {} write notifies (got {})", tag, n, notifications));
        }

        if constexpr (WORDS == 1) {
            ext.cpu_write(0, 0x22220000u);
            expect(port.ch.cmds == 1, std::format("{} ext: the write issues one command (got {})", tag, port.ch.cmds));
            expect(port.ch.lastCmd.word(0) == 0x22220000u, tag + " ext: the command carries the written word");
        }
    }
};

int sc_main(int, char **)
{
    wideProbe<32> p32("p32");
    wideProbe<64> p64("p64");
    wideProbe<96> p96("p96");
    wideProbe<128> p128("p128");
    sc_start(100, SC_NS);
    std::printf("failures=%d\\n", failures);
    return failures ? 1 : 0;
}
"""

# rw checks: three per word; ext checks: two, at 32 bits only
EXPECTED_PASSES = sum(3 * (w // 32) for w in (32, 64, 96, 128)) + 2

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_hw_register_wide_word_write():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_hw_register_wide_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"hwRegister probe must build and link: {binPath}")
            return
        run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        output = run.stdout + run.stderr
        check(run.returncode == 0, f"probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == EXPECTED_PASSES and 'failures=0' in output,
              f"all {EXPECTED_PASSES} wide-register checks pass")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_hw_register_wide_word_write()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
