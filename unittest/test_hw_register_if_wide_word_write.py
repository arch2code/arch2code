#!/usr/bin/env python3
"""A word write to a wide rw register in a register handler model reaches the child.

A <block>_regs handler model holds each register as an hwRegisterIf, and an rw
register forwards its value to the owning child over status_out. Firmware
writes a 64-bit register one 32-bit word at a time, and the generated RTL
updates [31:0] on the low-word strobe. The model must forward each word write,
or a child sees a low-word-only write in RTL and never in the model.

The probe writes a 64-bit hwRegisterIf over a status channel to three readers:
a model child, a child behind a status thunker, and a status_dst_bfm driving
the HDL pin as in co-sim. After a low-word write each must hold the new low
word with the old high word. Two words written back to back must leave each
holding both, since status carries a level and a reader may merge the two
notifications.
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
#include "status_channel.h"
#include "status_port_thunker.h"
#include "status_bfm.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>

// A 64-bit register payload in a plain word, like a generated struct.
struct regSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = 64;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<64> sc_pack() const { sc_bv<64> p; p = w; return p; }
    void sc_unpack( sc_bv<64> p ) { w = p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:016x}", w ); }
    bool operator==( const regSt& o ) const { return w == o.w; }
};

// A child model: keeps the last value each notification delivers.
SC_MODULE( child )
{
    status_in<regSt> in;
    std::uint64_t seen = 0;
    SC_HAS_PROCESS( child );
    child( sc_module_name n ) : sc_module( n ), in( "in" ) { SC_THREAD( run ); }
    void run() { while (true) { regSt v; in->read( v ); seen = v.w; } }
};

SC_MODULE( probe )
{
    status_out<regSt> out;
    hwRegisterIf<regSt, status_out<regSt>, 8, false> reg;
    status_channel<regSt> ch;
    child direct;
    child behind;
    status_port_thunker<regSt, regSt> thunker;
    sc_clock clk;
    sc_signal<bool> rst_n;
    status_hdl_if<sc_bv<64>> hdl;
    status_dst_bfm<regSt, sc_bv<64>> bfm;
    int failures = 0;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n )
      : sc_module( n ), out( "out" ), reg( &out ), ch( "ch", "tb" ), direct( "direct" ), behind( "behind" ),
        thunker( "thunker", ch, behind.in, "tb" ), clk( "clk", 10, SC_NS ), rst_n( "rst_n", true ), bfm( "bfm" )
    {
        out( ch );
        direct.in( ch );
        bfm.if_p( ch );
        bfm.hdl_if_p( hdl );
        bfm.clk( clk );
        bfm.rst_n( rst_n );
        SC_THREAD( drive );
    }

    void expect( bool ok, const std::string &what )
    {
        std::printf( "%s: %s\\n", ok ? "PASS" : "FAIL", what.c_str() );
        if (!ok) { failures++; }
    }

    void expectAll( std::uint64_t want, const std::string &when )
    {
        std::uint64_t pin = hdl.data.read().to_uint64();
        expect( direct.seen == want, std::format( "{}: model child holds 0x{:016x} (got 0x{:016x})", when, want, direct.seen ) );
        expect( behind.seen == want, std::format( "{}: child behind the thunker holds 0x{:016x} (got 0x{:016x})", when, want, behind.seen ) );
        expect( pin == want, std::format( "{}: status_dst_bfm drives 0x{:016x} (got 0x{:016x})", when, want, pin ) );
    }

    void drive()
    {
        wait( 20, SC_NS );
        reg.cpu_write( 0, 0x11111111u );
        wait( 20, SC_NS );
        expectAll( 0x0000000011111111ull, "low-word write" );
        reg.cpu_write( 4, 0x22222222u );
        wait( 20, SC_NS );
        expectAll( 0x2222222211111111ull, "high-word write" );
        reg.cpu_write( 0, 0x33333333u );
        reg.cpu_write( 4, 0x44444444u );
        wait( 20, SC_NS );
        expectAll( 0x4444444433333333ull, "back-to-back words" );
        std::printf( "failures=%d\\n", failures );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    probe p( "p" );
    sc_start( 1, SC_US );
    return p.failures ? 1 : 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_hw_register_if_wide_word_write():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_hw_register_if_wide_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"hwRegisterIf wide-word probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        before = len(FAILURES)
        check(run.returncode == 0, f"probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == 9 and 'failures=0' in output, "all nine checks pass")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_hw_register_if_wide_word_write()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
