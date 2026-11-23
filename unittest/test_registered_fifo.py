#!/usr/bin/env python3
"""registeredFifo frees a slot for writes on the clock after the read, as
Pro's rdyVldFifo does with its registered full flag.

The probe expects:

- behind a BFM's clock, a slot read in the middle of a clock takes a write
  from the next rising edge, and one read at a rising edge's own time from
  the edge after it. Entries are readable as soon as they are written;
- with no BFM on the clock port's channel, a read frees its slot at once.
  As other BFMs exist, that FIFO is logged once, naming it and its port;
- a model that reads a rdy_vld src BFM into the FIFO in one thread and
  drains it into a rdy_vld dst BFM in another, the FIFO sized DEPTH less the
  two beats its threads hold, accepts and drops exactly the input beats the
  RTL rdyVldFifo of DEPTH does under an input that overruns it, and sends
  each beat on the edge the RTL does. Into an always-ready sink it moves one
  beat per clock. The same model on an sc_fifo takes an input beat a clock
  before the RTL could.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

DEPTH = 8
CLOCKS = 70

PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "registeredFifo.h"
#include "rdy_vld_bfm.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>
#include <vector>

struct wordSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = 32;
    static constexpr std::uint16_t _byteWidth = 4;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<32> sc_pack() const { sc_bv<32> p; p = w; return p; }
    void sc_unpack( sc_bv<32> p ) { w = p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const wordSt& o ) const { return w == o.w; }
};

using bv = sc_bv<32>;
const int DEPTH = @DEPTH@;
const int CLOCKS = @CLOCKS@;
const sc_time SKEW( 100, SC_PS );

std::string ns( void ) { return std::format( "{}", sc_time_stamp().value() / 1000 ); }
std::string join( const std::vector<std::string> &v )
{
    std::string s;
    for (auto &e : v) { s += e + ","; }
    return s;
}

// A depth 2 FIFO with a writer that writes four words from 32 ns. A reader
// reads one at 44 ns, in the high phase of the clock from 40 ns, and one at
// the 60 ns edge's own time. clocked gives the FIFO's clock port a src BFM.
SC_MODULE( direct )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_in<wordSt> in;
    rdy_vld_hdl_if<bv> hdl;
    std::unique_ptr<rdy_vld_src_bfm<wordSt, bv>> bfm;
    registeredFifo<wordSt> fifo;
    std::vector<std::string> writeNs, readNs, vals;
    SC_HAS_PROCESS( direct );
    direct( sc_module_name n, bool clocked ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), in( "in" ),
        fifo( "fifo", 2, in )
    {
        in( ch );
        if (clocked) {
            bfm = std::make_unique<rdy_vld_src_bfm<wordSt, bv>>( "bfm" );
            bfm->if_p( ch ); bfm->hdl_if_p( hdl ); bfm->clk( clk ); bfm->rst_n( rst_n );
        }
        SC_THREAD( writer ); SC_THREAD( reader );
    }
    void writer()
    {
        wait( 32, SC_NS );
        for (int k = 0; k < 4; k++) {
            wordSt v; v.w = k;
            fifo.write( v );
            writeNs.push_back( ns() );
        }
    }
    void reader()
    {
        wait( 44, SC_NS );
        vals.push_back( std::to_string( fifo.read().w ) );
        readNs.push_back( ns() );
        wait( sc_time( 60, SC_NS ) - sc_time_stamp() );
        vals.push_back( std::to_string( fifo.read().w ) );
        readNs.push_back( ns() );
    }
};

// RTL in front of and behind a model that reads in into a FIFO in one thread
// and writes it to out from another. The source offers beat k in the k-th
// clock after reset whether or not rdy is high, so a beat the model refuses
// is lost. The sink is ready in the clocks ready() gives. Both drive one
// step after the rising edge.
template <typename FIFO>
struct relay : sc_module {
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> inCh, outCh;
    rdy_vld_in<wordSt> in;
    rdy_vld_out<wordSt> out;
    rdy_vld_hdl_if<bv> inHdl, outHdl;
    rdy_vld_src_bfm<wordSt, bv> inBfm;
    rdy_vld_dst_bfm<wordSt, bv> outBfm;
    FIFO fifo;
    bool stall;
    std::vector<std::string> accepted, outClocks, outVals;
    SC_HAS_PROCESS( relay );
    relay( sc_module_name n, FIFO *, bool stall_ ) : sc_module( n ), inCh( "inCh", "tb", BACKPRESSURE_ALLOWED ),
        outCh( "outCh", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), out( "out" ), inBfm( "inBfm" ), outBfm( "outBfm" ),
        fifo( make() ), stall( stall_ )
    {
        in( inCh ); inBfm.if_p( inCh ); inBfm.hdl_if_p( inHdl ); inBfm.clk( clk ); inBfm.rst_n( rst_n );
        out( outCh ); outBfm.if_p( outCh ); outBfm.hdl_if_p( outHdl ); outBfm.clk( clk ); outBfm.rst_n( rst_n );
        SC_THREAD( inputThread ); SC_THREAD( outputThread ); SC_THREAD( source ); SC_THREAD( sink );
    }
    FIFO make()
    {
        if constexpr (std::is_same_v<FIFO, registeredFifo<wordSt>>) {
            return FIFO( "fifo", DEPTH - 2, in );
        } else {
            return FIFO( "fifo", DEPTH - 2 );
        }
    }
    void inputThread() { while (true) { wordSt v; in->read( v ); fifo.write( v ); } }
    void outputThread() { while (true) { wordSt v = fifo.read(); out->write( v ); } }
    bool ready( int c ) const { return !stall || !( (c >= 3 && c < 20) || (c >= 25 && c < 27) || (c > 30 && c % 7 == 0) ); }
    void source()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < CLOCKS; k++) {
            wait( SKEW );
            inHdl.vld = 1; inHdl.data = bv( k );
            wait( clk.posedge_event() );
            if (inHdl.rdy) { accepted.push_back( std::to_string( k ) ); }
        }
        wait( SKEW );
        inHdl.vld = 0;
    }
    void sink()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int c = 0; ; c++) {
            wait( SKEW );
            outHdl.rdy = ready( c );
            wait( clk.posedge_event() );
            if (outHdl.vld && outHdl.rdy) {
                outClocks.push_back( std::to_string( c ) );
                outVals.push_back( std::to_string( outHdl.data.read().to_uint64() ) );
            }
        }
    }
};

// sc_fifo, as the models used before registeredFifo, built the same way.
using scFifo = sc_fifo<wordSt>;
std::ostream &operator<<( std::ostream &os, const wordSt &v ) { return os << v.w; }

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    direct timed, untimed;
    relay<registeredFifo<wordSt>> regStall, regStream;
    relay<scFifo> scStall;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n ) : sc_module( n ), clk( "clk", 10, SC_NS ), timed( "timed", true ), untimed( "untimed", false ),
        regStall( "regStall", nullptr, true ), regStream( "regStream", nullptr, false ), scStall( "scStall", nullptr, true )
    {
        timed.clk( clk ); timed.rst_n( rst_n ); untimed.clk( clk ); untimed.rst_n( rst_n );
        regStall.clk( clk ); regStall.rst_n( rst_n ); regStream.clk( clk ); regStream.rst_n( rst_n );
        scStall.clk( clk ); scStall.rst_n( rst_n );
        SC_THREAD( run );
    }

    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        wait( 2, SC_US );
        for (auto *d : { &timed, &untimed }) {
            std::printf( "rec %s write=%s read=%s vals=%s\\n", d->basename(), join( d->writeNs ).c_str(),
                         join( d->readNs ).c_str(), join( d->vals ).c_str() );
        }
        std::printf( "rec regStall accepted=%s outClocks=%s outVals=%s\\n", join( regStall.accepted ).c_str(),
                     join( regStall.outClocks ).c_str(), join( regStall.outVals ).c_str() );
        std::printf( "rec regStream accepted=%s outClocks=%s outVals=%s\\n", join( regStream.accepted ).c_str(),
                     join( regStream.outClocks ).c_str(), join( regStream.outVals ).c_str() );
        std::printf( "rec scStall accepted=%s outClocks=%s outVals=%s\\n", join( scStall.accepted ).c_str(),
                     join( scStall.outClocks ).c_str(), join( scStall.outVals ).c_str() );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
""".replace('@DEPTH@', str(DEPTH)).replace('@CLOCKS@', str(CLOCKS))

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def records(output):
    return {m.group(1): {k: [int(v) for v in vals.split(',') if v] for k, vals in re.findall(r'(\w+)=([\d,]*)', m.group(2))}
            for m in re.finditer(r'^rec (\w+) (.*)$', output, re.M)}


def rdyVldFifo(depth, clocks, ready, horizon):
    """Pro's rdyVldFifo clock by clock: write.rdy is count < depth and read.vld
    count > 0, both from the count registered at the clock's opening edge.
    The source offers beat c in clock c; returns the beats taken and, for
    each beat sent, the clock whose closing edge sent it and its value."""
    count, fifo, accepted, outClocks, outVals = 0, [], [], [], []
    for c in range(horizon):
        push = c < clocks and count < depth
        pop = count > 0 and ready(c)
        if pop:
            outClocks.append(c)
            outVals.append(fifo.pop(0))
        if push:
            accepted.append(c)
            fifo.append(c)
        count = len(fifo)
    return accepted, outClocks, outVals


def stallReady(c):
    return not ((3 <= c < 20) or (25 <= c < 27) or (c > 30 and c % 7 == 0))


def test_registered_fifo():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_registered_fifo_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        before = len(FAILURES)
        check(run.returncode == 0 and 'probe done' in output, f"probe runs to completion (status {run.returncode})")
        rec = records(output)

        r = rec.get('timed', {})
        check(r.get('write') == [32, 32, 50, 70] and r.get('read') == [44, 60] and r.get('vals') == [0, 1],
              f"timed: a slot read at 44 ns takes the third write at the 50 ns edge, and one read at the 60 ns "
              f"edge takes the fourth at 70 ns (write={r.get('write')} read={r.get('read')})")
        r = rec.get('untimed', {})
        check(r.get('write') == [32, 32, 44, 60] and r.get('vals') == [0, 1],
              f"untimed: with no BFM on the clock port's channel a read frees its slot at once "
              f"(write={r.get('write')} read={r.get('read')})")
        unclocked = [line for line in output.splitlines() if "no BFM is bound to the port's channel" in line]
        check(len(unclocked) == 1 and unclocked[0].startswith('fifo:registeredFifo on port p.untimed.in:'),
              f"untimed: in a run with BFMs, the FIFO with none on its clock port's channel is logged once, "
              f"by name and port (got {unclocked})")

        accepted, outClocks, outVals = rdyVldFifo(DEPTH, CLOCKS, stallReady, 200)
        r = rec.get('regStall', {})
        check(r.get('accepted') == accepted,
              f"regStall: the model takes and drops exactly the input beats rdyVldFifo of depth {DEPTH} does "
              f"(model={r.get('accepted')} rtl={accepted})")
        check(r.get('outClocks') == outClocks and r.get('outVals') == outVals,
              f"regStall: the model sends each beat on the RTL's edge (model={r.get('outClocks')} rtl={outClocks})")
        accepted, outClocks, outVals = rdyVldFifo(DEPTH, CLOCKS, lambda c: True, 200)
        r = rec.get('regStream', {})
        check(r.get('accepted') == accepted == list(range(CLOCKS)) and r.get('outClocks') == outClocks
              and sorted({b - a for a, b in zip(outClocks, outClocks[1:])}) == [1],
              f"regStream: into an always-ready sink the model takes every beat and sends one per clock "
              f"(accepted={len(r.get('accepted', []))} out={r.get('outClocks', [])[:6]}...)")
        accepted, _, _ = rdyVldFifo(DEPTH, CLOCKS, stallReady, 200)
        r = rec.get('scStall', {})
        check(r.get('accepted') is not None and r.get('accepted') != accepted,
              f"scStall: the same model on an sc_fifo takes beats the RTL drops (model={r.get('accepted')} "
              f"rtl={accepted})")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_registered_fifo()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
