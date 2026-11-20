#!/usr/bin/env python3
"""read() returns the beat the channel transferred, whichever side runs first.

A rdy_vld transfer wakes the writer and the reader on one event. A src BFM
offers the RTL's next beat as soon as its write() returns, so if the writer
runs first, the offer replaces the channel's value before the reader copies
it. Which side runs first depends on the kernel: the OSCI kernel runs the
reader first when the reader waited first, and the writer first when the
writer waited first. Xcelium's kernel can run the writer first in either case.

The probe runs both orders. The writer sends 10 and then offers 11, as the
src BFM does. The reader must get 10 each time.
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
#include "rdy_vld_channel.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>

struct wordSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = 32;
    static constexpr std::uint16_t _byteWidth = 4;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
};

struct top : sc_module {
    rdy_vld_channel<wordSt> ch;
    bool readerFirst;
    SC_HAS_PROCESS( top );
    top( sc_module_name n, bool rf ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), readerFirst( rf )
    {
        SC_THREAD( writer );
        SC_THREAD( reader );
    }
    // The side that waits first starts at 0 ns, the other at 1 ns.
    void writer()
    {
        if (readerFirst) { wait( 1, SC_NS ); }
        wordSt v;
        v.w = 10;
        ch.write( v );
        v.w = 11;
        ch.offer( v );
    }
    void reader()
    {
        if (!readerFirst) { wait( 1, SC_NS ); }
        wordSt v;
        ch.read( v );
        std::printf( "got %llu\\n", (unsigned long long)v.w );
    }
};

int sc_main( int argc, char *argv[] )
{
    top t( "t", std::string( argv[1] ) == "reader" );
    sc_start( 10, SC_NS );
    return 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_rdy_vld_read_latch():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_rdy_vld_latch_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for first in ('reader', 'writer'):
            try:
                run = subprocess.run([binPath, first], capture_output=True, text=True, timeout=60,
                                     env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            except subprocess.TimeoutExpired:
                check(False, f"{first} waits first: probe finishes within 60 s")
                continue
            output = run.stdout + run.stderr
            check(run.returncode == 0 and 'got 10' in output,
                  f"{first} waits first: read() returns the beat written, not the one offered after "
                  f"({output.strip().splitlines()[-1] if output.strip() else 'no output'})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_rdy_vld_read_latch()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
