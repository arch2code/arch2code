#!/usr/bin/env python3
"""external_reg_src_bfm forwards each RTL write strobe to the model owner.

The src BFM samples the RTL's `write` strobe at each rising edge and passes the
value to the owner with reg_write_cmd(). external_reg has fixed timing: the RTL
can strobe again on the next edge, so the owner must complete each write in the
time step of its strobe. The BFM asserts when it does not.

The probe puts a stub RTL in front of the BFM. rst_n rises at 22 ns, between
edges, on a 10 ns clock whose rising edges fall on multiples of 10 ns. The stub
drives the strobe and wdata at falling edges.
  * zero: strobes 1, 2, 3 and 4 on four back-to-back edges from 50 ns. An owner
    that publishes in zero time must see all four, in order, at their edges.
  * delta: as zero, but the owner waits one delta after it publishes before
    it returns to read(). The BFM must still drive each published value on
    rdata in the timestep of its strobe, so the RTL samples it at the next
    edge.
  * slow: strobes once. The owner takes 5 ns before it publishes, so the BFM
    must assert with its fixed-timing message.
  * resetEdge: a strobe held at the reset-ending edge, 30 ns. Today the BFM
    skips that edge and the strobe never reaches the owner. The check is an
    expected failure, so it reports when the BFM changes.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = r"""
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "external_reg_channel.h"
#include "external_reg_bfm.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>
#include <vector>

struct regSt {
    std::uint32_t w = 0;
    static constexpr std::uint16_t _bitWidth = 32;
    typedef std::uint32_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<32> sc_pack() const { sc_bv<32> p; p = w; return p; }
    void sc_unpack( sc_bv<32> p ) { w = (std::uint32_t)p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const regSt& o ) const { return w == o.w; }
};

static std::string mode;

SC_MODULE( probe )
{
    external_reg_channel<regSt> ch;
    external_reg_hdl_if<sc_bv<32>> hdl;
    external_reg_src_bfm<regSt, sc_bv<32>> bfm;
    sc_clock clk;
    sc_signal<bool> rst_n;

    SC_CTOR( probe ) : ch( "ch", "tb" ), bfm( "bfm" ), clk( "clk", 10, SC_NS, 0.5, 0, SC_NS, true )
    {
        bfm.if_p( ch );
        bfm.hdl_if_p( hdl );
        bfm.clk( clk );
        bfm.rst_n( rst_n );
        SC_THREAD( rtl );
        SC_THREAD( owner );
        SC_THREAD( rdataLog );
    }

    // Drives `values` on back-to-back strobes, changing them at falling edges
    // so that the rising edge at each `at` ns samples the next value.
    void strobe( int at, const std::vector<std::uint32_t>& values )
    {
        wait( sc_time( at - 5, SC_NS ) - sc_time_stamp() );
        for ( std::uint32_t v : values ) {
            hdl.wdata = v;
            hdl.write = 1;
            wait( 10, SC_NS );
        }
        hdl.write = 0;
    }

    void rtl()
    {
        rst_n = false;
        wait( 22, SC_NS );
        rst_n = true;
        if ( mode == "zero" || mode == "delta" ) {
            strobe( 50, { 1, 2, 3, 4 } );
        } else if ( mode == "slow" ) {
            strobe( 50, { 1 } );
        } else {
            strobe( 30, { 5 } );
        }
        wait( sc_time( 200, SC_NS ) - sc_time_stamp() );
        std::printf( "rtlDone=1\n" );
        sc_stop();
    }

    void owner()
    {
        while ( true ) {
            regSt w;
            ch.read( w );
            std::printf( "owner=0x%x@%s\n", w.w, sc_time_stamp().to_string().c_str() );
            if ( mode == "slow" ) {
                wait( 5, SC_NS );
            }
            regSt r;
            r.w = w.w + 1;
            ch.update_mirror( r );
            if ( mode == "delta" ) {
                wait( SC_ZERO_TIME );
            }
        }
    }

    void rdataLog()
    {
        while ( mode == "delta" ) {
            wait( hdl.rdata.value_changed_event() );
            std::printf( "rdata=0x%x@%s\n", (unsigned)hdl.rdata.read().to_uint64(), sc_time_stamp().to_string().c_str() );
        }
    }
};

int sc_main( int argc, char* argv[] )
{
    mode = argv[1];
    probe p( "probe" );
    sc_start( 1, SC_US );
    return 0;
}
"""

SRC_BFM_RESET_SKIP = ("a strobe held at the reset-ending edge is not sampled: external_reg_bfm.h:45-47 "
                      "takes that edge in its reset wait, and the main loop waits for the next one")

# (mode, output that must be present, output that must be absent, output that
# should be present but is missing today, with the reason)
Case = namedtuple('Case', 'mode present absent xfail reason')
CASES = [
    Case('zero', ('owner=0x1@50 ns\nowner=0x2@60 ns\nowner=0x3@70 ns\nowner=0x4@80 ns\n', 'rtlDone=1'),
         ('[Q_ASSERT]',), (), None),
    Case('delta', ('owner=0x1@50 ns\nrdata=0x2@50 ns\nowner=0x2@60 ns\nrdata=0x3@60 ns\n'
                   'owner=0x3@70 ns\nrdata=0x4@70 ns\nowner=0x4@80 ns\nrdata=0x5@80 ns\n', 'rtlDone=1'),
         ('[Q_ASSERT]',), (), None),
    Case('slow', ('owner=0x1@50 ns', '[Q_ASSERT][probe.bfm] external_reg has fixed timing', 'but it took 5 ns'),
         ('rtlDone=1',), (), None),
    Case('resetEdge', ('rtlDone=1',), ('[Q_ASSERT]',), ('owner=0x5@30 ns',), SRC_BFM_RESET_SKIP),
]

FAILURES = []
XFAILS = []


def check(condition, message, xfail=None):
    """Records a check. A check marked xfail passes the suite only by failing."""
    if xfail is None:
        print(f"  {'PASS' if condition else 'FAIL'}: {message}")
        if not condition:
            FAILURES.append(message)
    elif condition:
        print(f"  XPASS: {message}; marked expected failure: {xfail}")
        FAILURES.append(f"unexpected pass, {message}")
    else:
        print(f"  XFAIL: {message}; {xfail}")
        XFAILS.append(message)


def test_external_reg_src_bfm():
    tmpdir = tempfile.mkdtemp(prefix='a2c_external_reg_src_bfm_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"external_reg src BFM probe must build and link: {binPath}")
            return
        for case in CASES:
            run = subprocess.run([binPath, case.mode], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=os.environ['SYSTEMC_LIBDIR']))
            output = run.stdout + run.stderr
            before = len(FAILURES)
            for needle in case.present:
                check(needle in output, f"{case.mode} prints {needle!r}")
            for needle in case.xfail:
                check(needle in output, f"{case.mode} prints {needle!r}", case.reason)
            for needle in case.absent:
                check(needle not in output, f"{case.mode} does not print {needle!r}")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 72)
    print("TESTING EXTERNAL_REG SRC BFM")
    print("=" * 72)
    test_external_reg_src_bfm()
    print(f"\n  {len(XFAILS)} expected failures")
    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} check(s) FAILED")
        sys.exit(1)
    print("\nRESULT: all external_reg src BFM checks passed")
    sys.exit(0)
